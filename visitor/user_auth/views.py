from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, CustomUserCreationForm
import cv2
import pytesseract
import re
import numpy as np
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import io
import logging
from cryptography.fernet import Fernet
from django.conf import settings
from .models import GuestVerifications
from django.http import HttpResponse, Http404


# Inisialisasi Fernet dengan kunci global
fernet = Fernet(settings.ENCRYPTION_KEY)

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@login_required
def serve_protected_image(request, verification_id, image_type):
    try:
        verification = GuestVerifications.objects.get(id=verification_id)
        if request.user != verification.user and not request.user.is_staff:
            raise Http404("Anda tidak memiliki izin untuk mengakses gambar ini.")
        
        if image_type == 'selfie':
            image_path = verification.foto_selfie.path
        elif image_type == 'ktp':
            image_path = verification.foto_ktp.path
        else:
            raise Http404("Jenis gambar tidak valid.")
        
        # Baca file terenkripsi
        with open(image_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Dekripsi data dengan kunci global
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Tentukan content type
        content_type = 'image/jpeg' if image_path.endswith('.jpg') or image_path.endswith('.jpeg') else 'image/png'
        return HttpResponse(decrypted_data, content_type=content_type)
    except GuestVerifications.DoesNotExist:
        raise Http404("Gambar tidak ditemukan.")
    except Exception as e:
        raise Http404(f"Error: {str(e)}")

@csrf_exempt
def detect_nik(request):
    if request.method == 'POST' and request.FILES.get('foto_ktp'):
        try:
            # Ambil file KTP dari request
            foto_ktp = request.FILES['foto_ktp']
            
            # Buka gambar dengan PIL
            image = Image.open(foto_ktp)
            
            # Konversi gambar PIL ke format OpenCV (numpy array)
            image_np = np.array(image)
            if len(image_np.shape) == 3:  # Jika gambar berwarna (RGB)
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            # Preprocessing gambar
            gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            denoised = cv2.GaussianBlur(thresh, (5, 5), 0)
            processed_image = Image.fromarray(denoised)
            
            # Konfigurasi Tesseract
            custom_config = r'--oem 3 --psm 6'
            
            # Jalankan OCR dengan Tesseract
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            logger.debug("Teks mentah dari Tesseract:\n%s", text)
            
            # Verifikasi apakah gambar adalah KTP
            ktp_keywords = [
                "KARTU TANDA PENDUDUK", "PROVINSI", "KABUPATEN", "NIK",
                "Nama", "Tempat/Tgl Lahir", "Jenis Kelamin", "Alamat",
                "RT/RW", "Kel/Desa", "Kecamatan", "Agama", "Status Perkawinan",
                "Pekerjaan", "Kewarganegaraan", "Berlaku Hingga"
            ]
            is_ktp = any(keyword.lower() in text.lower() for keyword in ktp_keywords)
            
            if not is_ktp:
                logger.debug("Gambar tidak terdeteksi sebagai KTP.")
                return JsonResponse({'status': 'error', 'message': 'Gambar yang diunggah bukan KTP. Silakan unggah gambar KTP yang valid.'})
            
            # Cari pola NIK (16 digit, boleh ada karakter tambahan)
            nik_pattern = r'\d{16}[^\d]*'
            match = re.search(nik_pattern, text)
            
            if match:
                nik = match.group()
                nik = re.sub(r'[^\d]', '', nik)[:16]  # Bersihkan karakter non-digit
                logger.debug("NIK yang ditemukan: %s", nik)
                return JsonResponse({
                    'status': 'success',
                    'nik': nik,
                    'raw_text': text
                })
            else:
                logger.debug("NIK tidak ditemukan dalam teks.")
                return JsonResponse({
                    'status': 'error',
                    'message': 'NIK tidak ditemukan. Silakan masukkan secara manual.',
                    'raw_text': text
                })
        except Exception as e:
            logger.error("Error saat mendeteksi NIK: %s", str(e))
            return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'})
    return JsonResponse({'status': 'error', 'message': 'File KTP tidak ditemukan.'})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            logger.debug(f"Mencoba autentikasi untuk email: {email}")
            user = authenticate(request, email=email, password=password)
            if user is not None:
                logger.debug(f"Autentikasi berhasil untuk email: {email}")
                login(request, user)
                return redirect('home')
            else:
                logger.debug(f"Autentikasi gagal untuk email: {email}")
                form.add_error(None, "Email atau password salah.")
        else:
            logger.debug(f"Form tidak valid: {form.errors}")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form, 'hide_component': True})


def register(request):
    if request.method == 'POST':
        print("request.FILES:", request.FILES)  # Debugging
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            print("form.cleaned_data['foto_selfie']:", form.cleaned_data['foto_selfie'])  # Debugging
            print("form.cleaned_data['foto_ktp']:", form.cleaned_data['foto_ktp'])  # Debugging
            # Ambil NIK yang diisi pengguna
            nomor_identitas = form.cleaned_data['nomor_identitas']
            
            # Ambil teks mentah OCR dari input tersembunyi
            ocr_raw_text = request.POST.get('ocr_raw_text', '')
            
            # Jika OCR gagal mendeteksi NIK, validasi kemiripan
            nik_detected = form.cleaned_data.get('nik_detected', False)
            if not nik_detected:
                # Cari semua kemungkinan digit dalam teks mentah OCR
                ocr_digits = re.findall(r'\d+', ocr_raw_text)
                
                # Bandingkan NIK yang diisi pengguna dengan teks OCR
                user_nik = re.sub(r'[^\d]', '', nomor_identitas)  # Bersihkan karakter non-digit
                max_matching_digits = 0
                
                for digit_sequence in ocr_digits:
                    # Hitung jumlah digit yang cocok
                    matching_digits = sum(a == b for a, b in zip(user_nik, digit_sequence) if a == b)
                    max_matching_digits = max(max_matching_digits, matching_digits)
                
                # Pastikan minimal 4 digit cocok
                if max_matching_digits < 4:
                    form.add_error('nomor_identitas', 'NIK yang Anda masukkan tidak cukup mirip dengan data pada KTP. Pastikan NIK sesuai dengan KTP.')
                    return render(request, 'register.html', {'form': form, 'hide_component': True})
            
            # Simpan user jika validasi lolos
            user = form.save()
            # Login user dengan backend default
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Registrasi berhasil! Anda sekarang sudah login.')
            return redirect('landing')
        else:
            print("Form errors:", form.errors)  # Debugging
            return render(request, 'register.html', {'form': form, 'hide_component': True})
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form, 'hide_component': True})
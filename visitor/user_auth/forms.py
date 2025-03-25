import cv2
import pytesseract
import re
import numpy as np
import os
from django import forms
from django.contrib.auth.forms import UserCreationForm
from PIL import Image
from .models import Users, GuestVerifications
from cryptography.fernet import Fernet
from django.core.files.base import ContentFile
from django.conf import settings
import uuid
import logging

logger = logging.getLogger(__name__)


# Inisialisasi Fernet dengan kunci global
fernet = Fernet(settings.ENCRYPTION_KEY)

class LoginForm(forms.Form):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)



# Konfigurasi path Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  

def verify_selfie(image):
    """
    Memverifikasi apakah ada wajah di foto selfie menggunakan OpenCV.
    Args:
        image: Objek gambar (PIL Image).
    Returns:
        bool: True jika wajah terdeteksi, False jika tidak.
    """
    try:
        # Preprocessing: Resize gambar untuk mempercepat deteksi
        image = image.resize((300, 300))  # Resize ke 300x300
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        # Load classifier wajah
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # Deteksi wajah
        faces = face_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5)
        if len(faces) > 0:
            print(f"Sukses: {len(faces)} wajah terdeteksi di foto selfie.")
            return True
        else:
            print("Gagal: Tidak ada wajah yang terdeteksi di foto selfie.")
            return False
    except Exception as e:
        print(f"Error saat memverifikasi foto selfie: {str(e)}")
        return False

def verify_ktp(image):
    """
    Mengekstrak NIK dari foto KTP menggunakan Tesseract OCR.
    Args:
        image: Objek gambar (PIL Image).
    Returns:
        str or None: NIK (16 digit) jika ditemukan, None jika tidak.
    """
    try:
        # Preprocessing gambar untuk OCR
        image = image.resize((600, 400))  # Resize untuk mempercepat
        image = image.convert('L')  # Konversi ke grayscale
        image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Biner (threshold)
        # Ekstrak teks menggunakan Tesseract
        text = pytesseract.image_to_string(image)
        print("Teks yang diekstrak dari KTP:", text)  # Debugging
        # Cari NIK (16 digit) menggunakan regex
        nik_pattern = r'\b\d{16}\b'
        match = re.search(nik_pattern, text)
        if match:
            return match.group()
        return None
    except Exception as e:
        print(f"Error saat ekstraksi NIK: {str(e)}")
        return None
    

class CustomUserCreationForm(UserCreationForm):
    foto_selfie = forms.ImageField(required=True)
    foto_ktp = forms.ImageField(required=True)
    nomor_identitas = forms.CharField(max_length=50, required=False)
    ocr_raw_text = forms.CharField(widget=forms.HiddenInput(), required=False)
    nik_detected = forms.BooleanField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Users
        fields = ('email', 'password1', 'password2', 'nama_lengkap', 'nomor_telepon', 'foto_selfie', 'nomor_identitas', 'foto_ktp')

    def clean_nomor_identitas(self):
        nomor_identitas = self.cleaned_data.get('nomor_identitas')
        if nomor_identitas and not re.match(r'^\d{16}$', nomor_identitas):
            raise forms.ValidationError('NIK harus terdiri dari 16 digit.')
        return nomor_identitas

    def clean_foto_selfie(self):
        foto_selfie = self.cleaned_data.get('foto_selfie')
        if foto_selfie:
            # Batasi ukuran file (misalnya, maksimal 5 MB)
            max_size = 5 * 1024 * 1024  # 5 MB dalam bytes
            if foto_selfie.size > max_size:
                raise forms.ValidationError("Ukuran foto selfie terlalu besar. Maksimal 5 MB.")
            try:
                # Reset file pointer sebelum membaca
                foto_selfie.seek(0)
                image = Image.open(foto_selfie)
                image_np = np.array(image)
                if len(image_np.shape) == 3:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
                else:
                    image_np = cv2.cvtColor(image_np, cv2.COLOR_GRAY2BGR)
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                if face_cascade.empty():
                    raise forms.ValidationError("Gagal memuat classifier untuk deteksi wajah. Silakan coba lagi.")
                faces = face_cascade.detectMultiScale(image_np, scaleFactor=1.1, minNeighbors=5)
                if len(faces) == 0:
                    raise forms.ValidationError("Foto selfie harus menampilkan wajah Anda.")
                # Reset file pointer setelah validasi
                foto_selfie.seek(0)
            except Exception as e:
                raise forms.ValidationError(f"Error saat memproses foto selfie: {str(e)}")
        return foto_selfie

    def clean_foto_ktp(self):
        foto_ktp = self.cleaned_data.get('foto_ktp')
        if foto_ktp:
            # Batasi ukuran file (misalnya, maksimal 5 MB)
            max_size = 5 * 1024 * 1024  # 5 MB dalam bytes
            if foto_ktp.size > max_size:
                raise forms.ValidationError("Ukuran foto KTP terlalu besar. Maksimal 5 MB.")
            # Reset file pointer
            foto_ktp.seek(0)
        return foto_ktp

    def save(self, commit=True):
        user = super().save(commit=False)
        user.nama_lengkap = self.cleaned_data['nama_lengkap']
        user.nomor_telepon = self.cleaned_data['nomor_telepon']
        user.nomor_identitas = self.cleaned_data['nomor_identitas']
        user.role = 'tamu'
        if commit:
            user.save()
            foto_selfie = self.cleaned_data['foto_selfie']
            foto_ktp = self.cleaned_data['foto_ktp']

            # Reset file pointer sebelum membaca
            foto_selfie.seek(0)
            foto_ktp.seek(0)

            foto_selfie_data = foto_selfie.read()
            foto_ktp_data = foto_ktp.read()

            logger.info(f"Original selfie size: {len(foto_selfie_data)} bytes")
            logger.info(f"Original KTP size: {len(foto_ktp_data)} bytes")

            encrypted_selfie = fernet.encrypt(foto_selfie_data)
            encrypted_ktp = fernet.encrypt(foto_ktp_data)

            logger.info(f"Encrypted selfie size: {len(encrypted_selfie)} bytes")
            logger.info(f"Encrypted KTP size: {len(encrypted_ktp)} bytes")

            foto_selfie_name = f"{user.id}_{uuid.uuid4()}_{user.created_at.strftime('%Y%m%d')}.enc"
            foto_ktp_name = f"{user.id}_{uuid.uuid4()}_{user.created_at.strftime('%Y%m%d')}.enc"

            logger.info(f"Saving selfie as: {foto_selfie_name}")
            logger.info(f"Saving KTP as: {foto_ktp_name}")

            selfie_content_type = foto_selfie.content_type
            ktp_content_type = foto_ktp.content_type

            GuestVerifications.objects.create(
                user=user,
                foto_selfie=ContentFile(encrypted_selfie, name=foto_selfie_name),  # Hapus prefix 'selfies/'
                foto_ktp=ContentFile(encrypted_ktp, name=foto_ktp_name),  # Hapus prefix 'ktp/'
                selfie_content_type=selfie_content_type,
                ktp_content_type=ktp_content_type,
            )
        return user
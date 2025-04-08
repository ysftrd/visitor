import cv2
import pytesseract
import re
import numpy as np
from PIL import Image

# Konfigurasi path Tesseract (sesuaikan dengan sistem Anda)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Untuk Windows

def verify_selfie(image_path):
    """
    Memverifikasi apakah ada wajah di foto selfie menggunakan OpenCV.
    Args:
        image_path (str): Path ke file gambar selfie.
    Returns:
        bool: True jika wajah terdeteksi, False jika tidak.
    """
    try:
        # Baca gambar menggunakan PIL
        image = Image.open(image_path)
        # Konversi ke format yang bisa digunakan OpenCV
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

def verify_ktp(image_path):
    """
    Mengekstrak NIK dari foto KTP menggunakan Tesseract OCR.
    Args:
        image_path (str): Path ke file gambar KTP.
    Returns:
        str or None: NIK (16 digit) jika ditemukan, None jika tidak.
    """
    try:
        # Baca gambar menggunakan PIL
        image = Image.open(image_path)
        # Ekstrak teks menggunakan Tesseract
        text = pytesseract.image_to_string(image)
        # Cari NIK (16 digit) menggunakan regex
        nik_pattern = r'\b\d{16}\b'
        match = re.search(nik_pattern, text)
        if match:
            nik = match.group()
            print(f"Sukses: NIK ditemukan - {nik}")
            return nik
        else:
            print("Gagal: NIK tidak ditemukan di foto KTP.")
            return None
    except Exception as e:
        print(f"Error saat memverifikasi foto KTP: {str(e)}")
        return None

def main():
    # Minta input path gambar dari pengguna
    selfie_path = "image copy 2.png"
    ktp_path = "image.png"

    # Verifikasi foto selfie
    print("\nMemverifikasi foto selfie...")
    selfie_verified = verify_selfie(selfie_path)

    # Verifikasi foto KTP
    print("\nMemverifikasi foto KTP...")
    nik = verify_ktp(ktp_path)

    # Tampilkan hasil
    print("\n=== Hasil Verifikasi ===")
    if selfie_verified and nik:
        print("Verifikasi berhasil!")
        print(f"NIK: {nik}")
    else:
        print("Verifikasi gagal. Silakan periksa gambar yang diunggah.")

if __name__ == "__main__":
    main()
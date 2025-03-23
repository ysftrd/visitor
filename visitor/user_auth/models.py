from django.db import models
from django.contrib.auth.models import AbstractUser

class Users(AbstractUser):
    nama_lengkap = models.CharField(max_length=255, blank=True, null=True)
    nomor_identitas = models.CharField(max_length=50, blank=True, null=True)
    nomor_telepon = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class GuestVerifications(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='verifications')
    foto_selfie = models.ImageField(upload_to='selfies/', blank=True, null=True)
    foto_ktp = models.ImageField(upload_to='ktp/', blank=True, null=True)
    tanda_tangan_digital = models.ImageField(upload_to='signatures/', blank=True, null=True)
    tanggal_upload = models.DateTimeField(auto_now_add=True)
    status_verifikasi = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    catatan_admin = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Verification for {self.user.username}"
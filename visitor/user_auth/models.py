from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email harus diisi.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser harus memiliki is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser harus memiliki is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class Users(AbstractUser):
    ROLE_CHOICES = (
        ('tamu', 'Tamu'),
        ('karyawan', 'Karyawan'),
        ('resepsionis', 'Resepsionis'),
        ('admin', 'Admin'),
    )
    username = None
    email = models.EmailField(unique=True)
    nama_lengkap = models.CharField(max_length=255, blank=True, null=True)
    nomor_identitas = models.CharField(max_length=50, blank=True, null=True, unique=True)
    nomor_telepon = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='tamu')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()  # Tambahkan ini untuk menggunakan UserManager kustom

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nama_lengkap', 'nomor_telepon']

    def __str__(self):
        return self.email

class GuestVerifications(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='verifications')
    foto_selfie = models.ImageField(upload_to='selfies/', blank=True, null=True)
    foto_ktp = models.ImageField(upload_to='ktp/', blank=True, null=True)
    tanggal_upload = models.DateTimeField(auto_now_add=True)
    selfie_content_type = models.CharField(max_length=50, blank=True, null=True)
    ktp_content_type = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"Verification for {self.user.email}"
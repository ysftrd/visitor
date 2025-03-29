from django.db import models
from user_auth.models import Users
import random
import string
from django.utils import timezone


def generate_unique_code():
    while True:
        date_str = timezone.now().strftime('%Y%m%d')  # Format: YYYYMMDD
        random_digits = ''.join(random.choices(string.digits, k=4))
        code = f'RES-{date_str}-{random_digits}'
        if not Reservasi.objects.filter(kode_unik=code).exists():
            return code

class Reservasi(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('checkin', 'Check-in'),
        ('completed', 'Completed'),
    )
    tamu = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='tamu_reservasi')
    karyawan = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='karyawan_reservasi')
    tanggal_pertemuan = models.DateTimeField(null=True, blank=True)
    tujuan_pertemuan = models.TextField()
    kode_unik = models.CharField(max_length=20, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.kode_unik:
            self.kode_unik = generate_unique_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservasi {self.kode_unik} oleh {self.tamu.email}"

    class Meta:
        permissions = [
            ('can_checkin', 'Can check-in reservations'),
        ]

class Histori(models.Model):
    reservasi = models.ForeignKey(Reservasi, on_delete=models.CASCADE, related_name='history')
    status_lama = models.CharField(max_length=20, choices=Reservasi.STATUS_CHOICES)
    status_baru = models.CharField(max_length=20, choices=Reservasi.STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, related_name='reservation_changes')

    def __str__(self):
        return f"{self.reservasi.kode_unik}: {self.status_lama} -> {self.status_baru}"
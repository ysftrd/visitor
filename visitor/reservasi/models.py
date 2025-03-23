from django.db import models
from user_auth.models import Users

class Reservasi(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    tamu = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='tamu_Reservasi')
    karyawan = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='karyawan_Reservasi')
    tanggal_pertemuan = models.DateTimeField()
    tujuan_pertemuan = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    qr_code = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk:  # Jika sudah ada di database (update)
            old_reservasi = Reservasi.objects.get(pk=self.pk)
            if old_reservasi.status != self.status:  # Jika status berubah
                Histori.objects.create(
                    reservasi=self,
                    status_lama=old_reservasi.status,
                    status_baru=self.status,
                    user=self.karyawan
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reservation {self.id} - {self.tamu.username}"
    
    class Meta:
        permissions = [
            ('Menerima_reservasi', 'Menerima Reservasi'),
            ('scan_qrcode', 'Scan QR codes'),
        ]

class Histori(models.Model):
    reservasi = models.ForeignKey(Reservasi, on_delete=models.CASCADE, related_name='history')
    status_lama = models.CharField(max_length=20, choices=Reservasi.STATUS_CHOICES)
    status_baru = models.CharField(max_length=20, choices=Reservasi.STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, related_name='reservation_changes')

    def __str__(self):
        return f"{self.reservasi.id}: {self.status_lama} -> {self.status_baru}"
    
class QRCodes(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('used', 'Used'),
        ('expired', 'Expired'),
    )
    reservasi = models.OneToOneField(Reservasi, on_delete=models.CASCADE, related_name='qrcode')
    kode = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    tanggal_kadaluarsa = models.DateField()

    def __str__(self):
        return self.kode
from django.db import models
from user_auth.models import Users

class Jadwal(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked'),
    )
    karyawan = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='Jadwal')
    tanggal = models.DateField()
    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"Schedule for {self.karyawan.username} on {self.tanggal}"
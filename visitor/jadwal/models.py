from django.db import models
from user_auth.models import Users

class Jadwal(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked'),
    )
    karyawan = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='jadwals')
    tanggal = models.DateField()
    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField()
    capacity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_by = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, related_name='jadwals_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('karyawan', 'tanggal', 'jam_mulai', 'jam_selesai')

    def __str__(self):
        return f"{self.karyawan.email} - {self.tanggal} ({self.jam_mulai} - {self.jam_selesai})"
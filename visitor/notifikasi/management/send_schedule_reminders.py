from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from user_auth.models import Users
from jadwal.models import Jadwal
from notifikasi.models import Notification
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Send reminders to employees if their schedules are about to run out.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        reminder_date = today + timedelta(days=3)  # Kirim pengingat 3 hari sebelum jadwal habis
        karyawans = Users.objects.filter(role='karyawan')

        for karyawan in karyawans:
            # Cari jadwal terakhir karyawan
            last_schedule = Jadwal.objects.filter(
                karyawan=karyawan,
                tanggal__gte=today
            ).order_by('-tanggal').first()

            if last_schedule and last_schedule.tanggal <= reminder_date:
                # Kirim notifikasi in-app
                Notification.objects.create(
                    user=karyawan,
                    type='in_app',
                    message=f"Jadwal Anda hanya tersedia hingga {last_schedule.tanggal}. Silakan atur jadwal untuk periode berikutnya."
                )

                # Kirim email
                subject = "Pengingat: Jadwal Anda Akan Habis"
                message = (
                    f"Halo {karyawan.nama_lengkap},\n\n"
                    f"Jadwal Anda hanya tersedia hingga {last_schedule.tanggal}. "
                    f"Silakan atur jadwal untuk periode berikutnya melalui halaman Jadwal.\n\n"
                    f"Terima kasih!"
                )
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [karyawan.email],
                    fail_silently=False
                )

                self.stdout.write(self.style.SUCCESS(f"Reminder sent to {karyawan.email}"))
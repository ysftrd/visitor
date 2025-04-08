from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import holidays
from user_auth.models import Users
from jadwal.models import Jadwal

class Command(BaseCommand):
    help = 'Generate fallback schedules for employees who have not set their schedules.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        end_date = today + timedelta(days=7)  # Fallback untuk 7 hari ke depan
        id_holidays = holidays.Indonesia(years=[today.year, end_date.year])
        karyawans = Users.objects.filter(role='karyawan')

        for karyawan in karyawans:
            # Cek apakah karyawan memiliki jadwal untuk 7 hari ke depan
            has_schedule = Jadwal.objects.filter(
                karyawan=karyawan,
                tanggal__gte=today,
                tanggal__lte=end_date
            ).exists()

            if not has_schedule:
                self.stdout.write(self.style.WARNING(f"Generating fallback schedule for {karyawan.email}"))
                current_date = today
                while current_date <= end_date:
                    # Kecualikan hari libur dan akhir pekan
                    day_name = current_date.strftime('%A')
                    if day_name in ['Saturday', 'Sunday'] or current_date in id_holidays:
                        current_date += timedelta(days=1)
                        continue

                    # Buat slot default (08:00 - 17:00)
                    current_time = datetime.combine(current_date, datetime.strptime('08:00', '%H:%M').time())
                    end_datetime = datetime.combine(current_date, datetime.strptime('17:00', '%H:%M').time())
                    while current_time < end_datetime:
                        next_time = (current_time + timedelta(hours=1)).time()
                        Jadwal.objects.get_or_create(
                            karyawan=karyawan,
                            tanggal=current_date,
                            jam_mulai=current_time.time(),
                            jam_selesai=next_time,
                            defaults={
                                'status': 'available',
                                'created_by': karyawan
                            }
                        )
                        current_time += timedelta(hours=1)

                    current_date += timedelta(days=1)

                self.stdout.write(self.style.SUCCESS(f"Fallback schedule created for {karyawan.email}"))
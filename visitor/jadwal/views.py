from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Jadwal
from user_auth.models import Users
from django import forms 
from datetime import datetime, timedelta
import holidays
from django.utils import timezone


def is_karyawan(user):
    return user.is_authenticated and user.role == 'karyawan'

@login_required
@user_passes_test(is_karyawan, login_url='user_auth:user_login')
def schedule_setup(request):
    class ScheduleSetupForm(forms.Form):
        start_date = forms.DateField(
            label="Tanggal Mulai",
            widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            required=True
        )
        end_date = forms.DateField(
            label="Tanggal Selesai",
            widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            required=True
        )
        start_time = forms.TimeField(
            label="Waktu Mulai",
            widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            initial='08:00'
        )
        end_time = forms.TimeField(
            label="Waktu Selesai",
            widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            initial='17:00'
        )
        working_days = forms.MultipleChoiceField(
            label="Hari Kerja",
            choices=[
                ('Monday', 'Senin'),
                ('Tuesday', 'Selasa'),
                ('Wednesday', 'Rabu'),
                ('Thursday', 'Kamis'),
                ('Friday', 'Jumat'),
                ('Saturday', 'Sabtu'),
                ('Sunday', 'Minggu'),
            ],
            widget=forms.CheckboxSelectMultiple,
            initial=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        )
        exclude_dates = forms.CharField(
            label="Tanggal Pengecualian (pisahkan dengan koma, format: YYYY-MM-DD)",
            widget=forms.TextInput(attrs={'class': 'form-control'}),
            required=False
        )

        def clean(self):
            cleaned_data = super().clean()
            start_date = cleaned_data.get('start_date')
            end_date = cleaned_data.get('end_date')
            start_time = cleaned_data.get('start_time')
            end_time = cleaned_data.get('end_time')

            if start_date and end_date and start_date > end_date:
                raise forms.ValidationError("Tanggal mulai harus sebelum tanggal selesai.")
            if start_time and end_time and start_time >= end_time:
                raise forms.ValidationError("Waktu mulai harus sebelum waktu selesai.")
            return cleaned_data

    if request.method == 'POST':
        form = ScheduleSetupForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']
            working_days = form.cleaned_data['working_days']
            exclude_dates = form.cleaned_data['exclude_dates'].split(',') if form.cleaned_data['exclude_dates'] else []
            exclude_dates = [date.strip() for date in exclude_dates if date.strip()]

            # Konversi exclude_dates ke objek datetime.date
            exclude_dates_set = set()
            for date_str in exclude_dates:
                try:
                    exclude_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    exclude_dates_set.add(exclude_date)
                except ValueError:
                    messages.error(request, f"Format tanggal pengecualian salah: {date_str}. Gunakan format YYYY-MM-DD.")

            # Dapatkan hari libur nasional (Indonesia)
            id_holidays = holidays.Indonesia(years=[start_date.year, end_date.year])

            # Buat slot jadwal
            current_date = start_date
            while current_date <= end_date:
                # Cek apakah hari ini adalah hari kerja
                day_name = current_date.strftime('%A')
                if day_name not in working_days:
                    current_date += timedelta(days=1)
                    continue

                # Cek apakah hari ini adalah hari libur nasional atau tanggal pengecualian
                if current_date in id_holidays or current_date in exclude_dates_set:
                    current_date += timedelta(days=1)
                    continue

                # Buat slot per jam
                current_time = datetime.combine(current_date, start_time)
                end_datetime = datetime.combine(current_date, end_time)
                while current_time < end_datetime:
                    next_time = (current_time + timedelta(hours=1)).time()
                    Jadwal.objects.create(
                        karyawan=request.user,
                        tanggal=current_date,
                        jam_mulai=current_time.time(),
                        jam_selesai=next_time,
                        status='available',
                        created_by=request.user
                    )
                    current_time += timedelta(hours=1)

                current_date += timedelta(days=1)

            messages.success(request, "Jadwal berhasil dibuat!")
            return redirect('jadwal:schedule_list')
    else:
        form = ScheduleSetupForm()

    return render(request, 'schedule_setup.html', {'form': form})

@login_required
def schedule_list(request):
    karyawans = Users.objects.filter(role='karyawan')
    return render(request, 'schedule_list.html', {'karyawans': karyawans})

@login_required
def schedule_api(request):
    karyawan_id = request.GET.get('karyawan_id')
    if not karyawan_id:
        return JsonResponse({'error': 'Karyawan ID diperlukan'}, status=400)

    jadwals = Jadwal.objects.filter(karyawan_id=karyawan_id)
    events = []
    for jadwal in jadwals:
        events.append({
            'title': f"{jadwal.karyawan.nama_lengkap} ({jadwal.status})",
            'start': f"{jadwal.tanggal}T{jadwal.jam_mulai}",
            'end': f"{jadwal.tanggal}T{jadwal.jam_selesai}",
            'color': 'green' if jadwal.status == 'available' else 'red',
            'extendedProps': {
                'jadwal_id': jadwal.id,
                'capacity': jadwal.capacity,
            }
        })
    return JsonResponse(events, safe=False)
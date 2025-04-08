from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from .models import Reservasi, Histori  # Hapus Jadwal dari sini
from jadwal.models import Jadwal  # Impor Jadwal dari jadwal.models
from log_aktivitas.models import ActivityLog
from notifikasi.models import Notification
from user_auth.models import Users
from datetime import datetime, timedelta
from django.utils import timezone
from notifikasi.utils import send_reservation_email

@login_required
def reservation_create(request):
    karyawans = Users.objects.filter(role='karyawan')
    hours = [f"{h:02d}:00" for h in range(8, 18)]  # Jam 06:00 - 17:00

    if request.method == 'POST':
        karyawan_id = request.POST.get('karyawan')
        tanggal_str = request.POST.get('tanggal')
        start_time_str = request.POST.get('start_time')
        duration = int(request.POST.get('duration'))
        tujuan_pertemuan = request.POST.get('tujuan_pertemuan')

        try:
            karyawan = Users.objects.get(id=karyawan_id, role='karyawan')
            tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            start_datetime = datetime.combine(tanggal, start_time)
            end_datetime = start_datetime + timedelta(hours=duration)
            end_time = end_datetime.time()

            # Validasi ketersediaan slot
            with transaction.atomic():
                slots = Jadwal.objects.filter(
                    karyawan=karyawan,
                    tanggal=tanggal,
                    jam_mulai__gte=start_time,
                    jam_mulai__lt=end_time
                ).order_by('jam_mulai')

                if not slots.exists():
                    return render(request, 'reservation_form.html', {
                        'karyawans': karyawans,
                        'hours': hours,
                        'error': 'Tidak ada slot tersedia pada waktu tersebut.'
                    })

                for slot in slots:
                    if slot.status != 'available':
                        return render(request, 'reservation_form.html', {
                            'karyawans': karyawans,
                            'hours': hours,
                            'error': f"Slot pada {slot.jam_mulai} - {slot.jam_selesai} tidak tersedia."
                        })

                # Buat reservasi
                reservasi = Reservasi.objects.create(
                    tamu=request.user,
                    karyawan=karyawan,
                    tujuan_pertemuan=tujuan_pertemuan,
                    tanggal_pertemuan=start_datetime,  # Isi tanggal_pertemuan
                    status='pending'
                )

                # Update status slot menjadi booked dan kaitkan dengan reservasi
                for slot in slots:
                    slot.status = 'booked'
                    slot.reservasi = reservasi
                    slot.save()

                # Kirim email ke karyawan
                send_reservation_email(reservasi, request)

                ActivityLog.objects.create(
                    user=request.user,
                    action="Created reservation",
                    description=f"Reservasi {reservasi.kode_unik}"
                )

                return redirect('reservasi:reservation_list')

        except Users.DoesNotExist:
            return render(request, 'reservation_form.html', {
                'karyawans': karyawans,
                'hours': hours,
                'error': 'Karyawan tidak ditemukan.'
            })
        except ValueError:
            return render(request, 'reservation_form.html', {
                'karyawans': karyawans,
                'hours': hours,
                'error': 'Format tanggal atau waktu salah.'
            })

    return render(request, 'reservation_form.html', {
        'karyawans': karyawans,
        'hours': hours
    })

@login_required
def reservation_list(request):
    # Tentukan reservasi berdasarkan peran pengguna
    if request.user.role == 'tamu':
        reservations = Reservasi.objects.filter(tamu=request.user)
    elif request.user.role == 'karyawan':
        reservations = Reservasi.objects.filter(karyawan=request.user)
    else:
        reservations = Reservasi.objects.none()  # Jika peran tidak dikenali, kembalikan queryset kosong

    return render(request, 'reservation_list.html', {'reservations': reservations})

@login_required
def approve_reservation(request, reservation_id):
    reservasi = get_object_or_404(Reservasi, id=reservation_id)
    if request.user != reservasi.karyawan:
        return redirect('reservasi:reservation_list')

    reservasi.status = 'approved'
    reservasi.save()

    # Ambil slot jadwal yang terkait
    slots = reservasi.jadwals.all().order_by('jam_mulai')
    if slots.exists():
        tanggal = slots.first().tanggal
        start_time = slots.first().jam_mulai
        end_time = slots.last().jam_selesai
    else:
        tanggal = reservasi.tanggal_pertemuan.date() if reservasi.tanggal_pertemuan else 'N/A'
        start_time = reservasi.tanggal_pertemuan.time() if reservasi.tanggal_pertemuan else 'N/A'
        end_time = 'N/A'

    # Kirim email ke tamu
    subject = "Reservasi Anda Disetujui"
    message = (
        f"Halo {reservasi.tamu.nama_lengkap},\n\n"
        f"Reservasi Anda ({reservasi.kode_unik}) untuk bertemu dengan {reservasi.karyawan.nama_lengkap} telah disetujui.\n"
        f"Waktu: {tanggal} {start_time} - {end_time}\n"
        f"Silakan tunjukkan kode reservasi ini saat tiba."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [reservasi.tamu.email])

    Notification.objects.create(
        user=reservasi.tamu,
        type='in_app',
        message=f"Reservasi Anda ({reservasi.kode_unik}) telah disetujui."
    )

    ActivityLog.objects.create(
        user=request.user,
        action="Approved reservation",
        description=f"Reservasi {reservasi.kode_unik}"
    )

    return redirect('reservasi:reservation_list')

@login_required
def reject_reservation(request, reservation_id):
    reservasi = get_object_or_404(Reservasi, id=reservation_id)
    if request.user != reservasi.karyawan:
        return redirect('reservasi:reservation_list')

    # Ubah status slot jadwal yang terkait menjadi available
    slots = reservasi.jadwals.all()
    for slot in slots:
        slot.status = 'available'
        slot.reservasi = None
        slot.save()

    reservasi.status = 'rejected'
    reservasi.save()

    # Kirim email ke tamu
    subject = "Reservasi Anda Ditolak"
    message = (
        f"Halo {reservasi.tamu.nama_lengkap},\n\n"
        f"Reservasi Anda ({reservasi.kode_unik}) untuk bertemu dengan {reservasi.karyawan.nama_lengkap} telah ditolak.\n"
        f"Silakan ajukan reservasi dengan waktu lain."
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [reservasi.tamu.email])

    Notification.objects.create(
        user=reservasi.tamu,
        type='in_app',
        message=f"Reservasi Anda ({reservasi.kode_unik}) telah ditolak."
    )

    ActivityLog.objects.create(
        user=request.user,
        action="Rejected reservation",
        description=f"Reservasi {reservasi.kode_unik}"
    )

    return redirect('reservasi:reservation_list')

@login_required
def checkin_reservation(request):
    if not request.user.has_perm('reservasi.can_checkin'):
        return redirect('reservasi:reservation_list')

    if request.method == 'POST':
        kode_unik = request.POST.get('kode_unik')
        reservasi = get_object_or_404(Reservasi, kode_unik=kode_unik)

        if reservasi.status != 'approved':
            return render(request, 'checkin.html', {
                'error': 'Reservasi ini belum disetujui atau sudah check-in.'
            })

        reservasi.status = 'checkin'
        reservasi.save()

        ActivityLog.objects.create(
            user=request.user,
            action="Checked in reservation",
            description=f"Reservasi {reservasi.kode_unik}"
        )

        return render(request, 'checkin.html', {
            'success': f"Tamu {reservasi.tamu.nama_lengkap} telah check-in untuk bertemu {reservasi.karyawan.nama_lengkap}."
        })

    return render(request, 'checkin.html')

@login_required
def feedback_form(request, reservation_id):
    reservasi = get_object_or_404(Reservasi, id=reservation_id)
    if request.user != reservasi.tamu or reservasi.status != 'completed':
        return redirect('reservasi:reservation_list')

    if request.method == 'POST':
        feedback = request.POST.get('feedback')
        reservasi.feedback = feedback
        reservasi.save()

        ActivityLog.objects.create(
            user=request.user,
            action="Submitted feedback",
            description=f"Feedback untuk reservasi {reservasi.kode_unik}"
        )

        return redirect('reservasi:reservation_list')

    return render(request, 'feedback_form.html', {'reservasi': reservasi})
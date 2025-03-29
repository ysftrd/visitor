from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .models import Reservasi, Jadwal, Histori
from log_aktivitas.models import ActivityLog
from notifikasi.models import Notification
from user_auth.models import Users
from datetime import datetime, timedelta
from django.utils import timezone

@login_required
def reservation_create(request, jadwal_id=None):
    jadwal = get_object_or_404(Jadwal, id=jadwal_id) if jadwal_id else None

    if request.method == 'POST':
        tujuan_pertemuan = request.POST.get('tujuan_pertemuan')
        if jadwal:
            if jadwal.status != 'available':
                return render(request, 'reservation_form.html', {
                    'jadwal': jadwal,
                    'error': 'Jadwal ini sudah dipesan.'
                })
            reservasi = Reservasi.objects.create(
                tamu=request.user,
                karyawan=jadwal.karyawan,
                jadwal=jadwal,
                tujuan_pertemuan=tujuan_pertemuan,
            )
            jadwal.status = 'booked'
            jadwal.save()

            # Kirim email ke karyawan
            subject = f"Permintaan Reservasi dari {request.user.email}"
            message = (
                f"Halo {jadwal.karyawan.nama_lengkap},\n\n"
                f"Tamu {request.user.nama_lengkap} ({request.user.email}) telah mengajukan reservasi.\n"
                f"Kode Reservasi: {reservasi.kode_unik}\n"
                f"Waktu: {jadwal.tanggal} {jadwal.jam_mulai} - {jadwal.jam_selesai}\n"
                f"Tujuan: {reservasi.tujuan_pertemuan}\n\n"
                f"Setujui: {request.build_absolute_uri(f'/reservasi/approve/{reservasi.id}/')}\n"
                f"Tolak: {request.build_absolute_uri(f'/reservasi/reject/{reservasi.id}/')}"
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [jadwal.karyawan.email])

            ActivityLog.objects.create(
                user=request.user,
                action="Created reservation",
                description=f"Reservasi {reservasi.kode_unik}"
            )

        return redirect('reservasi:reservation_list')

    return render(request, 'reservation_form.html', {
        'jadwal': jadwal,
        'karyawans': Users.objects.filter(role='karyawan'),
    })

@login_required
def reservation_list(request):
    reservations = Reservasi.objects.filter(tamu=request.user)
    return render(request, 'reservation_list.html', {'reservations': reservations})

@login_required
def approve_reservation(request, reservation_id):
    reservasi = get_object_or_404(Reservasi, id=reservation_id)
    if request.user != reservasi.karyawan:
        return redirect('reservasi:reservation_list')

    reservasi.status = 'approved'
    reservasi.save()

    # Kirim email ke tamu
    subject = "Reservasi Anda Disetujui"
    message = (
        f"Halo {reservasi.tamu.nama_lengkap},\n\n"
        f"Reservasi Anda ({reservasi.kode_unik}) untuk bertemu dengan {reservasi.karyawan.nama_lengkap} telah disetujui.\n"
        f"Waktu: {reservasi.jadwal.tanggal} {reservasi.jadwal.jam_mulai} - {reservasi.jadwal.jam_selesai}\n"
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

    reservasi.status = 'rejected'
    reservasi.jadwal.status = 'available'
    reservasi.jadwal.save()
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
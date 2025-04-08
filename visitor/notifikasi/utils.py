from django.core.mail import send_mail
from django.conf import settings

def send_reservation_email(reservasi, request):
    # Ambil slot jadwal yang terkait dengan reservasi
    slots = reservasi.jadwals.all().order_by('jam_mulai')
    if slots.exists():
        tanggal = slots.first().tanggal
        start_time = slots.first().jam_mulai
        end_time = slots.last().jam_selesai
    else:
        tanggal = reservasi.tanggal_pertemuan.date() if reservasi.tanggal_pertemuan else 'N/A'
        start_time = reservasi.tanggal_pertemuan.time() if reservasi.tanggal_pertemuan else 'N/A'
        end_time = 'N/A'

    subject = f"Permintaan Reservasi dari {reservasi.tamu.email}"
    message = (
        f"Halo {reservasi.karyawan.nama_lengkap},\n\n"
        f"Tamu {reservasi.tamu.nama_lengkap} ({reservasi.tamu.email}) telah mengajukan reservasi.\n"
        f"Kode Reservasi: {reservasi.kode_unik}\n"
        f"Waktu: {tanggal} {start_time} - {end_time}\n"
        f"Tujuan: {reservasi.tujuan_pertemuan}\n\n"
        f"Setujui: {request.build_absolute_uri(f'/reservasi/approve/{reservasi.id}/')}\n"
        f"Tolak: {request.build_absolute_uri(f'/reservasi/reject/{reservasi.id}/')}"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [reservasi.karyawan.email])
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Jadwal
from user_auth.models import Users

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
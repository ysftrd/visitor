from django.contrib import admin
from .models import Reservasi, Histori, QRCodes
# Register your models here.

admin.site.register(Reservasi)
admin.site.register(Histori)
admin.site.register(QRCodes)
from django.contrib import admin
from .models import Users, GuestVerifications
# Register your models here.

admin.site.register(Users)
admin.site.register(GuestVerifications)

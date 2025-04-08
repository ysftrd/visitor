from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Users, GuestVerifications
from django.utils.html import format_html

class CustomUserAdmin(UserAdmin):
    model = Users
    list_display = ('email', 'nama_lengkap', 'nomor_telepon', 'role', 'is_active', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'nama_lengkap')
    ordering = ('email',)

    # Field yang hanya bisa dilihat (read-only)
    readonly_fields = ('created_at', 'updated_at')

    # Konfigurasi form edit
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('nama_lengkap', 'nomor_telepon', 'nomor_identitas', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('created_at', 'updated_at')}),  # Field ini akan read-only
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'nama_lengkap', 'nomor_telepon', 'role', 'is_active', 'is_staff'),
        }),
    )

admin.site.register(Users, CustomUserAdmin)

@admin.register(GuestVerifications)
class GuestVerificationsAdmin(admin.ModelAdmin):
    list_display = ('user', 'tanggal_upload', 'foto_selfie_link', 'foto_ktp_link')
    list_filter = ('tanggal_upload',)
    search_fields = ('user__email',)

    def foto_selfie_link(self, obj):
        if obj.foto_selfie:
            return format_html('<a href="{}" target="_blank">Lihat Selfie</a>', 
                             f'/media/verification/{obj.id}/selfie/')
        return "-"
    foto_selfie_link.short_description = "Foto Selfie"

    def foto_ktp_link(self, obj):
        if obj.foto_ktp:
            return format_html('<a href="{}" target="_blank">Lihat KTP</a>', 
                             f'/media/verification/{obj.id}/ktp/')
        return "-"
    foto_ktp_link.short_description = "Foto KTP"
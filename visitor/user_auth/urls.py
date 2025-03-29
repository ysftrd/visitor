from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import reverse_lazy  # Impor reverse_lazy

app_name = 'user_auth'

urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    path('register/', views.register, name='register'),
    path('detect-nik/', views.detect_nik, name='detect_nik'),
    # URL untuk lupa password
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='user_auth/password_reset_form.html',
        email_template_name='user_auth/password_reset_email.html',
        subject_template_name='user_auth/password_reset_subject.txt',
        success_url=reverse_lazy('user_auth:password_reset_done')  # Gunakan reverse_lazy
    ), name='password_reset'),
    
    # URL untuk halaman konfirmasi email terkirim
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user_auth/password_reset_done.html'
    ), name='password_reset_done'),
    
    # URL untuk halaman reset password (dari tautan di email)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user_auth/password_reset_confirm.html',
        success_url=reverse_lazy('user_auth:password_reset_complete')  # Gunakan reverse_lazy
    ), name='password_reset_confirm'),
    
    # URL untuk halaman konfirmasi password berhasil direset
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user_auth/password_reset_complete.html'
    ), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
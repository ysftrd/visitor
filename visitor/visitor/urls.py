"""
URL configuration for visitor project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from user_auth import views
from django.contrib.auth.views import LogoutView
from home.views import home


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('home.urls')),
    path('auth/', include('user_auth.urls')),
    path('logout/', LogoutView.as_view(next_page='user_auth:user_login'), name='logout'),
    path('reservasi/', include('reservasi.urls')),
    path('jadwal/', include('jadwal.urls')),
    # path('notifikasi/', include('notifikasi.urls')),
    # path('log/', include('log_aktivation.urls')),
    path('media/verification/<int:verification_id>/<str:image_type>/', views.serve_protected_image, name='serve_protected_image'),
]

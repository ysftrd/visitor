from django.urls import path
from . import views

app_name = 'jadwal'
urlpatterns = [
    path('', views.schedule_list, name='schedule_list'),
    path('api/', views.schedule_api, name='schedule_api'),
    path('setup/', views.schedule_setup, name='schedule_setup'),
]
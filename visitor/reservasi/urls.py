from django.urls import path
from . import views

app_name = 'reservasi'
urlpatterns = [
    path('create/', views.reservation_create, name='reservation_create'),
    path('list/', views.reservation_list, name='reservation_list'),
    path('approve/<int:reservation_id>/', views.approve_reservation, name='approve_reservation'),
    path('reject/<int:reservation_id>/', views.reject_reservation, name='reject_reservation'),
    path('checkin/', views.checkin_reservation, name='checkin_reservation'),
    path('feedback/<int:reservation_id>/', views.feedback_form, name='feedback_form'),
]
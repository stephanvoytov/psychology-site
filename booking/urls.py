from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('schedule/', views.choose_psychologist, name='schedule'),          # выбор психолога
    path('schedule/<int:psychologist_id>/', views.schedule, name='psychologist_schedule'),  # расписание
    path('book/<int:slot_id>/', views.book, name='book'),
    path('success/', views.success, name='success'),
    path('contacts/', views.contacts, name='contacts'),
    path('my-appointment/', views.my_appointment, name='my_appointment'),
    path('my-appointment/cancel/', views.cancel_appointment_direct, name='cancel_appointment_direct'),
]
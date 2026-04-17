from django.urls import path
from . import views
from .views import test_email

urlpatterns = [
    path('', views.home, name='home'),
    path('schedule/', views.choose_psychologist, name='schedule'),          # выбор психолога
    path('schedule/<int:psychologist_id>/', views.schedule, name='psychologist_schedule'),  # расписание
    path('book/<int:slot_id>/', views.book, name='book'),
    path('success/', views.success, name='success'),
    path('contacts/', views.contacts, name='contacts'),
]
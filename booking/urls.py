from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),              # Главная
    path('schedule/', views.schedule, name='schedule'),  # Расписание
    path('book/<int:slot_id>/', views.book, name='book'),  # Запись на слот
    path('success/', views.success, name='success'),      # Успешная запись
    path('contacts/', views.contacts, name='contacts'),   # Контакты
]

from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    """
    Форма записи на приём. Поля автоматически берутся из модели Appointment.
    """
    class Meta:
        model = Appointment
        fields = ['full_name', 'who', 'grade', 'phone', 'email', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Иванова Мария Сергеевна',
                'class': 'form-input'
            }),
            'who': forms.Select(attrs={'class': 'form-input'}),
            'grade': forms.TextInput(attrs={
                'placeholder': '9А',
                'class': 'form-input'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': '+7 (999) 123-45-67',
                'class': 'form-input'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'email@example.com',
                'class': 'form-input'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'Опишите кратко причину обращения (необязательно)',
                'rows': 3,
                'class': 'form-input'
            }),
        }
        labels = {
            'full_name': 'ФИО',
            'who': 'Кто записывается',
            'grade': 'Класс',
            'phone': 'Телефон',
            'email': 'Email',
            'message': 'Примечание',
        }

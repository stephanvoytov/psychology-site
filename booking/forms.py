from django import forms
from .models import Appointment


class AppointmentForm(forms.ModelForm):
    # Тип приёма — выпадающий список из того что добавлено в админке
    appointment_type = forms.ChoiceField(
        choices=Appointment.TYPE_CHOICES,
        label='Цель обращения',
        widget=forms.RadioSelect(attrs={'class': 'form-radio'}),
    )

    class Meta:
        model  = Appointment
        fields = ['appointment_type', 'full_name', 'who', 'grade', 'phone', 'email', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Иванова Мария Сергеевна', 'class': 'form-input'}),
            'who':     forms.Select(attrs={'class': 'form-input'}),
            'grade':   forms.TextInput(attrs={
                'placeholder': '9А или 5 лет', 'class': 'form-input'}),
            'phone':   forms.TextInput(attrs={
                'placeholder': '+7 (999) 123-45-67', 'class': 'form-input'}),
            'email':   forms.EmailInput(attrs={
                'placeholder': 'email@example.com', 'class': 'form-input'}),
            'message': forms.Textarea(attrs={
                'rows': 3, 'class': 'form-input',
                'placeholder': 'Опишите кратко причину обращения (необязательно)'}),
        }
        labels = {
            'full_name': 'ФИО',
            'who':       'Кто записывается',
            'grade':     'Класс / возраст ребёнка',
            'phone':     'Телефон',
            'email':     'Email',
            'message':   'Примечание',
        }
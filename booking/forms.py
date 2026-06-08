from django import forms
from .models import Appointment, AppointmentType


class AppointmentForm(forms.ModelForm):
    child_birthdate = forms.DateField(
        required=False,
        label='Дата рождения ребёнка',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )

    class Meta:
        model  = Appointment
        fields = [
            'appointment_type',
            'full_name', 'who', 'grade', 'phone', 'email', 'message',
            'child_name', 'child_birthdate', 'kindergarten', 'address', 'parent_name', 'parent_phone',
        ]
        widgets = {
            'appointment_type': forms.Select(attrs={'class': 'form-select'}),
            'full_name':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванова Мария Сергеевна'}),
            'who':          forms.Select(attrs={'class': 'form-select'}),
            'grade':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9А'}),
            'phone':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'email':        forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'message':      forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'child_name':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванов Иван Иванович'}),
            'kindergarten': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Детский сад №15'}),
            'address':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'г. Москва, ул. Ленина, д. 1'}),
            'parent_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Иванова Мария Петровна'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
        }

    def __init__(self, *args, appointment_types=None, **kwargs):
        super().__init__(*args, **kwargs)
        if appointment_types is not None:
            self.fields['appointment_type'].queryset = appointment_types

        self.fields['phone'].required = False
        self.fields['appointment_type'].required = False

    def clean(self):
        cleaned = super().clean()
        apt = cleaned.get('appointment_type')
        if not apt:
            return cleaned

        if apt.form_type == 'consultation':
            for field in ['full_name', 'who', 'phone']:
                if not cleaned.get(field):
                    self.add_error(field, 'Обязательное поле')

        elif apt.form_type == 'preschool_exam':
            for field in ['child_name', 'child_birthdate', 'kindergarten', 'address', 'parent_name', 'parent_phone']:
                if not cleaned.get(field):
                    self.add_error(field, 'Обязательное поле')

        return cleaned
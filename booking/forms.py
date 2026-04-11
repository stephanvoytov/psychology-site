from django import forms
from .models import Appointment, AppointmentType


class AppointmentForm(forms.ModelForm):
    appointment_type = forms.ModelChoiceField(
        queryset=AppointmentType.objects.all(),
        label='Цель обращения',
        empty_label='— Выберите —',
        widget=forms.Select(attrs={'class': 'form-input', 'id': 'id_appointment_type'}),
    )
    # Дата рождения — отдельный виджет с type=date
    child_birthdate = forms.DateField(
        required=False,
        label='Дата рождения ребёнка',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
    )

    class Meta:
        model  = Appointment
        fields = [
            'appointment_type',
            # консультация
            'full_name', 'who', 'grade', 'phone', 'email', 'message',
            # дошкольник
            'child_name', 'child_birthdate', 'kindergarten', 'address', 'parent_name','parent_phone',
        ]
        widgets = {
            'full_name':   forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Иванова Мария Сергеевна'}),
            'who':         forms.Select(attrs={'class': 'form-input'}),
            'grade':       forms.TextInput(attrs={'class': 'form-input', 'placeholder': '9А'}),
            'phone':       forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+7 (999) 123-45-67'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+7 (999) 123-45-67'}),
            'email':       forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'email@example.com'}),
            'message':     forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'child_name':  forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Иванов Иван Иванович'}),
            'kindergarten':forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Детский сад №15'}),
            'address':     forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'г. Москва, ул. Ленина, д. 1'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Иванова Мария Петровна'}),
        }

    def clean(self):
        cleaned = super().clean()
        apt = cleaned.get('appointment_type')
        if not apt:
            return cleaned

        if apt.form_type == 'consultation':
            if not cleaned.get('full_name'):
                self.add_error('full_name', 'Обязательное поле')
            if not cleaned.get('who'):
                self.add_error('who', 'Обязательное поле')
            if not cleaned.get('phone'):
                self.add_error('phone', 'Обязательное поле')


        elif apt.form_type == 'preschool_exam':

            for field in ['child_name', 'child_birthdate', 'kindergarten', 'address', 'parent_name', 'parent_phone']:

                if not cleaned.get(field):
                    self.add_error(field, 'Обязательное поле')

        return cleaned
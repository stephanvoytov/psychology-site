from django import forms
from datetime import date, timedelta
from .models import Psychologist

WEEKDAY_CHOICES = [
    (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'),
    (3, 'Четверг'),     (4, 'Пятница'),
]
INTERVAL_CHOICES = [
    (30, '30 минут'), (45, '45 минут'), (60, '1 час'),
]

class SlotGeneratorForm(forms.Form):
    appointment_type = forms.ModelChoiceField(
        queryset=AppointmentType.objects.all(),
        label='Тип приёма',
        required=False,
        empty_label='— Любой (не указывать) —',
    )
    psychologist = forms.ModelChoiceField(
        queryset=Psychologist.objects.all(),
        label='Психолог',
        empty_label='— Выберите психолога —',
    )
    date_from = forms.DateField(
        label='Начало периода',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=date.today,
    )
    date_to = forms.DateField(
        label='Конец периода',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        initial=lambda: date.today() + timedelta(weeks=2),
    )
    weekdays = forms.MultipleChoiceField(
        label='Рабочие дни',
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        initial=[0, 1, 2, 3, 4],
    )
    time_from = forms.TimeField(
        label='Начало приёма',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        initial='12:00',
    )
    time_to = forms.TimeField(
        label='Конец приёма',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        initial='16:00',
    )
    interval = forms.ChoiceField(
        label='Длительность приёма',
        choices=INTERVAL_CHOICES,
        initial=60,
    )

    def clean(self):
        cleaned = super().clean()
        d_from, d_to   = cleaned.get('date_from'), cleaned.get('date_to')
        t_from, t_to   = cleaned.get('time_from'), cleaned.get('time_to')
        if d_from and d_to and d_from > d_to:
            raise forms.ValidationError('Дата начала не может быть позже даты конца.')
        if t_from and t_to and t_from >= t_to:
            raise forms.ValidationError('Время начала должно быть раньше времени конца.')
        return cleaned
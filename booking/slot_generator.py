from django import forms
from datetime import date, timedelta

# Дни недели для мультивыбора
WEEKDAY_CHOICES = [
    (0, 'Понедельник'),
    (1, 'Вторник'),
    (2, 'Среда'),
    (3, 'Четверг'),
    (4, 'Пятница'),
]

# Интервалы между слотами
INTERVAL_CHOICES = [
    (20, '20 минут'),
    (30, '30 минут'),
    (45, '45 минут'),
    (60, '1 час'),
]


class SlotGeneratorForm(forms.Form):
    """
    Форма генератора слотов.
    Психолог выбирает период, дни недели, время начала/конца и интервал.
    """
    date_from = forms.DateField(
        label='Начало периода',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'vDateField form-control'}),
        initial=date.today,
    )
    date_to = forms.DateField(
        label='Конец периода',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'vDateField form-control'}),
        initial=lambda: date.today() + timedelta(weeks=2),
    )
    weekdays = forms.MultipleChoiceField(
        label='Рабочие дни',
        choices=WEEKDAY_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        initial=[0, 1, 2, 3, 4],  # По умолчанию — все будние
    )
    time_from = forms.TimeField(
        label='Начало приёма',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'vTimeField form-control'}),
        initial='12:00',
    )
    time_to = forms.TimeField(
        label='Конец приёма',
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'vTimeField form-control'}),
        initial='16:00',
    )
    interval = forms.ChoiceField(
        label='Длительность одного приёма',
        choices=INTERVAL_CHOICES,
        initial=60,
    )

    def clean(self):
        cleaned = super().clean()
        date_from = cleaned.get('date_from')
        date_to = cleaned.get('date_to')
        time_from = cleaned.get('time_from')
        time_to = cleaned.get('time_to')

        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError('Дата начала не может быть позже даты конца.')

        if time_from and time_to and time_from >= time_to:
            raise forms.ValidationError('Время начала должно быть раньше времени конца.')

        return cleaned

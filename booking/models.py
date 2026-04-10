from django.db import models


class Psychologist(models.Model):
    name    = models.CharField(max_length=200, verbose_name='ФИО')
    grades  = models.CharField(max_length=100, verbose_name='Классы/категория')
    cabinet = models.CharField(max_length=50, blank=True, verbose_name='Кабинет')
    phone   = models.CharField(max_length=20, blank=True, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Психолог'
        verbose_name_plural = 'Психологи'

    def __str__(self):
        return f'{self.name} ({self.grades})'



class TimeSlot(models.Model):
    # Слот просто принадлежит психологу — никакого типа приёма здесь нет
    psychologist = models.ForeignKey(
        Psychologist, on_delete=models.CASCADE,
        related_name='slots', verbose_name='Психолог'
    )
    date         = models.DateField(verbose_name='Дата')
    time         = models.TimeField(verbose_name='Время')
    is_available = models.BooleanField(default=True, verbose_name='Доступен')

    class Meta:
        verbose_name = 'Временной слот'
        verbose_name_plural = 'Временные слоты'
        ordering = ['date', 'time']
        unique_together = ['psychologist', 'date', 'time']

    def __str__(self):
        status = '✓' if self.is_available else '✗'
        return f'{self.psychologist} | {self.date:%d.%m.%Y} {self.time:%H:%M} {status}'


class Appointment(models.Model):
    TYPE_CHOICES = [
        ('consultation', 'Консультация'),
        ('preschool_exam', 'Обследование дошкольника'),
    ]
    WHO_CHOICES = [
        ('student',     'Ученик'),
        ('parent',      'Родитель'),
        ('teacher',     'Учитель'),
    ]

    slot             = models.OneToOneField(
        TimeSlot, on_delete=models.CASCADE,
        related_name='appointment', verbose_name='Слот'
    )
    # Тип приёма выбирает пользователь при записи
    appointment_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='Тип обращения'
    )
    full_name  = models.CharField(max_length=200, verbose_name='ФИО')
    who        = models.CharField(max_length=20, choices=WHO_CHOICES, verbose_name='Кто записывается')
    grade      = models.CharField(max_length=10, blank=True, verbose_name='Класс / возраст ребёнка')
    phone      = models.CharField(max_length=20, verbose_name='Телефон')
    email      = models.EmailField(blank=True, verbose_name='Email')
    message    = models.TextField(blank=True, verbose_name='Примечание')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['slot__date', 'slot__time']

    def __str__(self):
        return f'{self.full_name} → {self.slot.psychologist} | {self.appointment_type}'
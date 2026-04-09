from django.db import models


class TimeSlot(models.Model):
    """
    Временной слот — один доступный интервал в расписании психолога.
    Администратор создаёт слоты через панель управления.
    """
    date = models.DateField(verbose_name='Дата')
    time = models.TimeField(verbose_name='Время')
    is_available = models.BooleanField(default=True, verbose_name='Доступен')

    class Meta:
        verbose_name = 'Временной слот'
        verbose_name_plural = 'Временные слоты'
        ordering = ['date', 'time']
        unique_together = ['date', 'time']  # Нельзя создать два одинаковых слота

    def __str__(self):
        status = '✓ свободен' if self.is_available else '✗ занят'
        return f"{self.date.strftime('%d.%m.%Y')} {self.time.strftime('%H:%M')} — {status}"


class Appointment(models.Model):
    """
    Запись ученика или родителя на приём к психологу.
    """
    # Кто записывается
    WHO_CHOICES = [
        ('student', 'Ученик'),
        ('parent', 'Родитель'),
        ('teacher', 'Учитель'),
    ]

    slot = models.OneToOneField(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='appointment',
        verbose_name='Дата и время'
    )
    full_name = models.CharField(max_length=200, verbose_name='ФИО')
    who = models.CharField(max_length=20, choices=WHO_CHOICES, verbose_name='Кто записывается')
    grade = models.CharField(max_length=10, blank=True, verbose_name='Класс (если ученик)')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email (необязательно)')
    message = models.TextField(blank=True, verbose_name='Примечание (необязательно)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['slot__date', 'slot__time']

    def __str__(self):
        return f"{self.full_name} — {self.slot}"

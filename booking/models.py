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


class AppointmentType(models.Model):
    FORM_CHOICES = [
        ('consultation',  'Обычная консультация'),   # поля: ФИО, кто, класс, телефон
        ('preschool_exam', 'Обследование дошкольника'),  # поля: ФИО ребёнка, дата рождения, сад, адрес, ФИО родителя, телефон
    ]
    name      = models.CharField(max_length=200, verbose_name='Название')
    form_type = models.CharField(
        max_length=20, choices=FORM_CHOICES,
        verbose_name='Тип формы',
        help_text='Определяет какие поля показываются при записи'
    )
    description = models.TextField(blank=True, verbose_name='Описание для пользователя')

    class Meta:
        verbose_name = 'Тип приёма'
        verbose_name_plural = 'Типы приёмов'

    def __str__(self):
        return self.name


class TimeSlot(models.Model):
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
    WHO_CHOICES = [
        ('student',     'Ученик'),
        ('parent',      'Родитель'),
        ('preschooler', 'Родитель дошкольника'),
        ('teacher',     'Учитель'),
    ]

    slot             = models.OneToOneField(
        TimeSlot, on_delete=models.CASCADE,
        related_name='appointment', verbose_name='Слот'
    )
    appointment_type = models.ForeignKey(
        AppointmentType, on_delete=models.SET_NULL,
        null=True, verbose_name='Тип приёма'
    )

    # --- Поля для обычной консультации ---
    full_name = models.CharField(max_length=200, verbose_name='ФИО', blank=True)
    who       = models.CharField(max_length=20, choices=WHO_CHOICES,
                                  verbose_name='Кто записывается', blank=True)
    grade     = models.CharField(max_length=10, blank=True, verbose_name='Класс')
    phone     = models.CharField(max_length=20, verbose_name='Телефон')
    email     = models.EmailField(blank=True, verbose_name='Email')
    message   = models.TextField(blank=True, verbose_name='Примечание')

    # --- Поля для обследования дошкольника ---
    child_name      = models.CharField(max_length=200, blank=True, verbose_name='ФИО ребёнка')
    child_birthdate = models.DateField(null=True, blank=True, verbose_name='Дата рождения ребёнка')
    kindergarten    = models.CharField(max_length=200, blank=True, verbose_name='Номер детского сада')
    address         = models.CharField(max_length=300, blank=True, verbose_name='Место проживания')
    parent_name     = models.CharField(max_length=200, blank=True, verbose_name='ФИО родителя')
    # phone используется для обоих типов

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')

    class Meta:
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['slot__date', 'slot__time']

    def __str__(self):
        name = self.child_name or self.full_name
        return f'{name} → {self.slot.psychologist} | {self.appointment_type}'
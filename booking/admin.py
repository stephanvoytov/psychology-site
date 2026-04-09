from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from datetime import datetime, timedelta, date

from .models import TimeSlot, Appointment
from .slot_generator import SlotGeneratorForm


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    """
    Управление расписанием.
    Вверху списка — кнопка «Сгенерировать слоты».
    """
    list_display = ('date', 'time', 'is_available', 'get_who_booked')
    list_filter = ('is_available', 'date')
    list_editable = ('is_available',)
    ordering = ('date', 'time')
    date_hierarchy = 'date'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['generator_url'] = 'generate_slots/'
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'generate_slots/',
                self.admin_site.admin_view(self.generate_slots_view),
                name='booking_timeslot_generate',
            ),
        ]
        return custom + urls

    def generate_slots_view(self, request):
        if request.method == 'POST':
            form = SlotGeneratorForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                created, skipped = self._create_slots(data)
                if created:
                    messages.success(request, f'✅ Создано слотов: {created}. Пропущено (уже существуют): {skipped}.')
                else:
                    messages.warning(request, f'Все слоты уже существуют ({skipped} шт.). Ничего не добавлено.')
                return redirect('..')
        else:
            form = SlotGeneratorForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'title': 'Генератор расписания',
            'opts': self.model._meta,
        }
        return render(request, 'admin/booking/generate_slots.html', context)

    def _create_slots(self, data):
        """
        Перебирает все дни в периоде, фильтрует по дням недели,
        нарезает время на слоты с заданным интервалом и сохраняет в БД.
        """
        date_from = data['date_from']
        date_to   = data['date_to']
        weekdays  = [int(d) for d in data['weekdays']]
        time_from = data['time_from']
        time_to   = data['time_to']
        interval  = int(data['interval'])

        created = 0
        skipped = 0
        current_date = date_from

        while current_date <= date_to:
            if current_date.weekday() in weekdays:
                current_time = datetime.combine(current_date, time_from)
                end_time     = datetime.combine(current_date, time_to)

                while current_time < end_time:
                    _, was_created = TimeSlot.objects.get_or_create(
                        date=current_date,
                        time=current_time.time(),
                        defaults={'is_available': True}
                    )
                    if was_created:
                        created += 1
                    else:
                        skipped += 1
                    current_time += timedelta(minutes=interval)

            current_date += timedelta(days=1)

        return created, skipped

    def get_who_booked(self, obj):
        if hasattr(obj, 'appointment'):
            return obj.appointment.full_name
        return '—'
    get_who_booked.short_description = 'Кто записан'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'who', 'grade', 'phone', 'slot', 'created_at')
    list_filter = ('who', 'slot__date')
    search_fields = ('full_name', 'phone', 'grade')
    readonly_fields = ('created_at',)
    ordering = ('slot__date', 'slot__time')


admin.site.site_header = 'Лицей №23 — Кабинет психолога'
admin.site.site_title  = 'Психолог Лицей №23'
admin.site.index_title = 'Управление сайтом'

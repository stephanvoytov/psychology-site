from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.contrib import messages
from datetime import datetime, timedelta

from django.utils.html import format_html

from .models import TimeSlot, Appointment, Psychologist, AppointmentType
from .slot_generator import SlotGeneratorForm


@admin.register(Psychologist)
class PsychologistAdmin(admin.ModelAdmin):
    list_display = ('name', 'grades', 'cabinet', 'phone')


@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display  = ('psychologist', 'date', 'time', 'is_available', 'get_who_booked', 'get_appointment_type')
    list_filter   = ('psychologist', 'is_available', 'date')
    list_editable = ('is_available',)
    ordering      = ('date', 'time')
    date_hierarchy = 'date'

    def get_urls(self):
        urls = super().get_urls()
        return [
            path('generate_slots/',
                 self.admin_site.admin_view(self.generate_slots_view),
                 name='booking_timeslot_generate'),
        ] + urls

    def generate_slots_view(self, request):
        if request.method == 'POST':
            form = SlotGeneratorForm(request.POST)
            if form.is_valid():
                created, skipped = self._create_slots(form.cleaned_data)
                if created:
                    messages.success(request, f'✅ Создано: {created}. Пропущено: {skipped}.')
                else:
                    messages.warning(request, f'Все слоты уже есть ({skipped} шт.).')
                return redirect('..')
        else:
            form = SlotGeneratorForm()

        return render(request, 'admin/booking/generate_slots.html', {
            **self.admin_site.each_context(request),
            'form': form,
            'title': 'Генератор расписания',
            'opts': self.model._meta,
        })

    def _create_slots(self, data):
        psychologist = data['psychologist']
        date_from    = data['date_from']
        date_to      = data['date_to']
        weekdays     = [int(d) for d in data['weekdays']]
        time_from    = data['time_from']
        time_to      = data['time_to']
        interval     = int(data['interval'])

        created = skipped = 0
        current_date = date_from

        while current_date <= date_to:
            if current_date.weekday() in weekdays:
                current_time = datetime.combine(current_date, time_from)
                end_time     = datetime.combine(current_date, time_to)
                while current_time < end_time:
                    _, was_created = TimeSlot.objects.get_or_create(
                        psychologist=psychologist,
                        date=current_date,
                        time=current_time.time(),
                        defaults={'is_available': True}
                    )
                    created += was_created
                    skipped += not was_created
                    current_time += timedelta(minutes=interval)
            current_date += timedelta(days=1)

        return created, skipped

    def get_who_booked(self, obj):
        try:
            app = obj.appointment
            name = app.full_name or app.parent_name or '—'
            url = reverse('admin:booking_appointment_change', args=[app.id])
            return format_html('<a href="{}">{}</a>', url, name)
        except Appointment.DoesNotExist:
            return '—'

    get_who_booked.short_description = 'Кто записан'

    def get_appointment_type(self, obj):
        try:
            return obj.appointment.appointment_type.name if obj.appointment.appointment_type else '—'
        except Appointment.DoesNotExist:
            return '—'

    get_appointment_type.short_description = 'Цель обращения'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display  = ('get_name', 'get_who', 'grade', 'phone', 'appointment_type', 'slot', 'created_at')
    list_filter   = ('appointment_type', 'who', 'slot__psychologist', 'slot__date')
    search_fields = ('full_name', 'parent_name', 'child_name', 'phone')
    readonly_fields = ('created_at',)

    def get_name(self, obj):
        if obj.parent_name:
            return f'{obj.parent_name} (ребёнок: {obj.child_name})'
        return obj.full_name or '—'
    get_name.short_description = 'ФИО'

    def get_who(self, obj):
        if obj.who:
            return obj.get_who_display()
        return 'Родитель дошкольника'
    get_who.short_description = 'Кто записывается'

admin.site.site_header = 'Лицей №23 — Кабинет психолога'
admin.site.site_title  = 'Психолог Лицей №23'
admin.site.index_title = 'Управление сайтом'
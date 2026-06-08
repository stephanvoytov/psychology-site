import os
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import path, reverse
from django.contrib import messages
from datetime import datetime, timedelta, date

from django.utils.html import format_html

from .models import TimeSlot, Appointment, Psychologist, AppointmentType
from .slot_generator import SlotGeneratorForm


# Скрываем ненужные разделы — психологу/секретарю не надо управлять пользователями
admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(Psychologist)
class PsychologistAdmin(admin.ModelAdmin):
    list_display = ('name', 'grades', 'cabinet', 'phone', 'email_warning', 'photo_preview')
    list_filter = ('grades',)
    search_fields = ('name',)

    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="/static/{}" style="width:40px;height:40px;border-radius:50%;object-fit:cover;">',
                obj.photo
            )
        return '—'
    photo_preview.short_description = 'Фото'

    def email_warning(self, obj):
        if obj.email:
            return obj.email
        return format_html(
            '<span style="color:#dc3545;">⚠️ не указан</span>'
        )
    email_warning.short_description = 'Email'

    def render_change_form(self, request, context, *args, **kwargs):
        obj = kwargs.get('obj')
        if obj and not obj.email:
            messages.warning(
                request,
                '⚠️ У психолога не указан email — уведомления о новых записях '
                'и отменах приходить НЕ БУДУТ. Добавьте email в поле ниже.'
            )
        return super().render_change_form(request, context, *args, **kwargs)


@admin.register(AppointmentType)
class AppointmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'form_type', 'description')
    filter_horizontal = ('psychologists',)


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    actions = None
    change_list_template = 'admin/booking/timeslot/change_list.html'
    list_display  = ('psychologist', 'date', 'time', 'is_available', 'get_who_booked', 'get_appointment_type')
    list_filter   = ('psychologist', 'is_available', 'date')
    list_editable = ('is_available',)
    ordering      = ('date', 'time')
    date_hierarchy = 'date'
    list_select_related = ('psychologist',)

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
    actions = None
    list_display  = ('get_name', 'get_phone', 'message_short', 'appointment_type', 'get_psychologist', 'get_date', 'get_time')
    list_filter   = ('appointment_type', 'slot__psychologist', 'slot__date')
    search_fields = ('full_name', 'parent_name', 'child_name', 'phone', 'parent_phone', 'message')
    readonly_fields = ('slot', 'created_at',)
    date_hierarchy = 'slot__date'
    ordering = ('-slot__date', '-slot__time')
    list_select_related = ('slot', 'slot__psychologist', 'appointment_type')

    fieldsets = (
        (None, {
            'fields': ('appointment_type', 'slot')
        }),
        ('Консультация', {
            'classes': ('wide',),
            'fields': ('full_name', 'who', 'grade', 'phone', 'email', 'message'),
        }),
        ('Обследование дошкольника', {
            'classes': ('wide',),
            'fields': ('child_name', 'child_birthdate', 'kindergarten', 'address', 'parent_name', 'parent_phone'),
        }),
        ('Служебное', {
            'classes': ('collapse',),
            'fields': ('created_at',),
        }),
    )

    def get_name(self, obj):
        name = obj.full_name or obj.parent_name or obj.child_name or '—'
        if obj.child_name and obj.parent_name:
            return f'{obj.parent_name} → {obj.child_name}'
        if obj.child_name:
            return f'{obj.child_name} (ребёнок)'
        return name
    get_name.short_description = 'ФИО / Ребёнок'
    get_name.admin_order_field = 'full_name'

    def get_phone(self, obj):
        return obj.phone or obj.parent_phone or '—'
    get_phone.short_description = 'Телефон'
    get_phone.admin_order_field = 'phone'

    def message_short(self, obj):
        if not obj.message:
            return '—'
        return format_html(
            '<span title="{}">{}…</span>',
            obj.message.replace('"', '&quot;'),
            obj.message[:50]
        )
    message_short.short_description = 'Примечание'

    def get_psychologist(self, obj):
        return obj.slot.psychologist.name if obj.slot and obj.slot.psychologist else '—'
    get_psychologist.short_description = 'Психолог'
    get_psychologist.admin_order_field = 'slot__psychologist'

    def get_date(self, obj):
        return obj.slot.date if obj.slot else '—'
    get_date.short_description = 'Дата'
    get_date.admin_order_field = 'slot__date'

    def get_time(self, obj):
        return obj.slot.time.strftime('%H:%M') if obj.slot and obj.slot.time else '—'
    get_time.short_description = 'Время'
    get_time.admin_order_field = 'slot__time'

admin.site.site_header = 'Лицей №23 — Кабинет психолога'
admin.site.site_title  = 'Психолог Лицей №23'
admin.site.index_title = 'Управление сайтом'


# ── Добавляем статистику на главную админки ──
from django.contrib.admin import AdminSite
_admin_index = AdminSite.index

def _patched_admin_index(self, request, extra_context=None):
    extra_context = extra_context or {}

    # Статистика по записям
    today = date.today()
    week_end = today + timedelta(days=6)
    extra_context['stats'] = {
        'today': Appointment.objects.filter(slot__date=today).count(),
        'week': Appointment.objects.filter(
            slot__date__gte=today, slot__date__lte=week_end
        ).count(),
        'free': TimeSlot.objects.filter(is_available=True).count(),
    }

    # Информация о настройках email (NotiSend HTTP API)
    has_key = bool(os.environ.get('NOTISEND_API_KEY'))

    # Статус email у каждого психолога
    psychologists = Psychologist.objects.all()
    extra_context['psych_email_status'] = [
        {
            'name': p.name,
            'has_email': bool(p.email),
            'email': p.email or '—',
        }
        for p in psychologists
    ]

    extra_context['email_info'] = {
        'backend': '📧 NotiSend (HTTP API)' if not settings.DEBUG else '🔧 Консоль (только лог)',
        'sender': settings.DEFAULT_FROM_EMAIL,
        'has_key': has_key,
    }

    extra_context['settings'] = settings

    return _admin_index(self, request, extra_context=extra_context)

AdminSite.index = _patched_admin_index
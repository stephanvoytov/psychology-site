
import logging

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from .email_utils import send_appointment_notification, send_cancellation_notification
from .models import TimeSlot, Appointment, Psychologist, AppointmentType
from .forms import AppointmentForm

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'booking/home.html')


def choose_psychologist(request):
    """Страница выбора психолога — показывается перед расписанием."""
    psychologists = Psychologist.objects.prefetch_related('appointment_types').all()
    return render(request, 'booking/choose_psychologist.html', {
        'psychologists': psychologists,
    })


def schedule(request, psychologist_id):
    """Расписание конкретного психолога."""
    today = timezone.now().date()
    psychologist = get_object_or_404(Psychologist, id=psychologist_id)

    slots = TimeSlot.objects.filter(
        psychologist=psychologist,
        is_available=True,
        date__gte=today
    )

    slots_by_date = {}
    for slot in slots:
        if slot.date not in slots_by_date:
            slots_by_date[slot.date] = []
        slots_by_date[slot.date].append(slot)

    return render(request, 'booking/schedule.html', {
        'psychologist': psychologist,
        'slots_by_date': slots_by_date,
    })


def book(request, slot_id):
    slot = get_object_or_404(TimeSlot, id=slot_id, is_available=True)
    psychologist = slot.psychologist
    # Только типы приёмов доступные у этого психолога
    appointment_types = AppointmentType.objects.filter(psychologists=psychologist)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, appointment_types=appointment_types)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.slot = slot
            appointment.save()
            slot.is_available = False
            slot.save()
            apt_type = appointment.appointment_type
            send_appointment_notification(appointment)

            # Store in session for success page
            apt_data = {
                'id': appointment.id,
                'psychologist': psychologist.name,
                'psychologist_cabinet': psychologist.cabinet,
                'psychologist_phone': psychologist.phone or '',
                'date': str(slot.date),
                'time': str(slot.time),
                'appointment_type': apt_type.name if apt_type else '',
                'form_type': apt_type.form_type if apt_type else '',
                'phone': appointment.phone or appointment.parent_phone or '',
                'child_name': appointment.child_name or '',
                'full_name': appointment.full_name or '',
                'kindergarten': appointment.kindergarten or '',
                'address': appointment.address or '',
                'parent_name': appointment.parent_name or '',
                'parent_phone': appointment.parent_phone or '',
            }
            request.session['last_appointment'] = apt_data

            if apt_type and apt_type.form_type == 'preschool_exam':
                messages.success(request, '''Cобеседование проходит в кабинете психолога на I этаже.
Ребенка приводят только родители (законные представители). Длительность собеседования 30-40 мин.
Просим приходить заблаговременно - за 3-5 мин до начала встречи.''')
            else:
                messages.success(request, 'Вы успешно записались! Ждём вас.')
            return redirect('success')

    else:
        form = AppointmentForm(appointment_types=appointment_types)

    return render(request, 'booking/book.html', {
        'slot': slot,
        'psychologist': psychologist,
        'form': form,
        'appointment_types': appointment_types,
    })


def success(request):
    last_appointment = request.session.pop('last_appointment', '{}')
    return render(request, 'booking/success.html', {
        'last_appointment': last_appointment,
    })


def my_appointment(request):
    """Страница «Моя запись» — информация из localStorage."""
    return render(request, 'booking/my_appointment.html')


def cancel_appointment_direct(request):
    """Отмена записи в один шаг — по ID записи (POST)."""
    if request.method == 'POST':
        app_id = request.POST.get('app_id', '').strip()
        if app_id:
            try:
                app = Appointment.objects.select_related(
                    'slot__psychologist', 'appointment_type'
                ).get(id=app_id, slot__date__gte=timezone.now().date())
                slot = app.slot
                send_cancellation_notification(app)
                app.delete()
                slot.is_available = True
                slot.save()
                messages.success(request, 'Запись успешно отменена.')
                redirect_url = redirect('my_appointment')
                redirect_url['Location'] += '?cancelled=1'
                return redirect_url
            except Appointment.DoesNotExist:
                messages.warning(request, 'Запись не найдена. Возможно, она уже отменена.')
        return redirect('my_appointment')

    return redirect('my_appointment')


def contacts(request):
    """Контакты психологов с fallback-данными, если БД недоступна."""
    try:
        psychologists = list(Psychologist.objects.all())
        if not psychologists:
            raise Psychologist.DoesNotExist
    except Exception:
        psychologists = [
            {
                'id': 2,
                'name': 'Ганьева Алина Маратовна',
                'grades': '1-11 классы',
                'cabinet': '201',
                'phone': '+7 (999) 111-22-33',
                'photo': 'images/psychologist/ganieva.jpg',
            },
            {
                'id': 3,
                'name': 'Ворожеикина Екатерина Алексеевна',
                'grades': '5-11 классы',
                'cabinet': '205',
                'phone': '+7 (999) 444-55-66',
                'photo': 'images/psychologist/vorozheikina.jpg',
            },
        ]
    return render(request, 'booking/contacts.html', {'psychologists': psychologists})



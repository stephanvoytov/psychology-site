from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone

from .email_utils import send_appointment_notification
from .models import TimeSlot, Appointment, Psychologist, AppointmentType
from .forms import AppointmentForm


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
            try:
                send_appointment_notification(appointment)
            except Exception as e:
                print(f'Ошибка отправки email: {e}')
            if apt_type and apt_type.form_type == 'preschool_exam':
                messages.success(request, '''Cобеседование проходит в кабинете психолога на I этаже.
Ребенка приводят только родители (законные представители). Длительность собеседования 30-40 мин.
Просим приходить заблаговременно - за 3-5 мин до начала встречи.''')
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
    return render(request, 'booking/success.html')


def contacts(request):
    psychologists = Psychologist.objects.all()
    return render(request, 'booking/contacts.html', {'psychologists': psychologists})
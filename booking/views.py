from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import TimeSlot, Appointment, Psychologist
from .forms import AppointmentForm


def home(request):
    return render(request, 'booking/home.html')


def schedule(request):
    today = timezone.now().date()

    psychologists    = Psychologist.objects.all()

    # Фильтры из GET-параметров
    psych_id = request.GET.get('psychologist')
    type_id  = request.GET.get('type')

    slots = TimeSlot.objects.filter(
        is_available=True, date__gte=today
    ).select_related('psychologist', 'appointment_type')

    if psych_id:
        slots = slots.filter(psychologist_id=psych_id)
    if type_id:
        slots = slots.filter(appointment_type_id=type_id)

    # Группировка: {психолог: {дата: [слоты]}}
    grouped = {}
    for slot in slots:
        p = slot.psychologist
        d = slot.date
        if p not in grouped:
            grouped[p] = {}
        if d not in grouped[p]:
            grouped[p][d] = []
        grouped[p][d].append(slot)

    return render(request, 'booking/schedule.html', {
        'grouped':            grouped,
        'psychologists':      psychologists,
        'selected_psych':     psych_id,
        'selected_type':      type_id,
    })


def book(request, slot_id):
    slot = get_object_or_404(TimeSlot, id=slot_id, is_available=True)

    if request.method == 'POST':
        form = AppointmentForm(request.POST, slot=slot)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.slot             = slot
            appointment.appointment_type = slot.appointment_type
            appointment.save()
            slot.is_available = False
            slot.save()
            messages.success(request, 'Вы успешно записались! Ждём вас.')
            return redirect('success')
    else:
        form = AppointmentForm(slot=slot)

    return render(request, 'booking/book.html', {'slot': slot, 'form': form})


def success(request):
    return render(request, 'booking/success.html')


def contacts(request):
    psychologists = Psychologist.objects.all()
    return render(request, 'booking/contacts.html', {'psychologists': psychologists})
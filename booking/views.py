from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import TimeSlot, Appointment
from .forms import AppointmentForm


def home(request):
    """Главная страница — информация о психологе и кнопка записи."""
    return render(request, 'booking/home.html')


def schedule(request):
    """
    Страница расписания — показывает все доступные слоты.
    Группирует слоты по дате для удобного отображения.
    """
    today = timezone.now().date()

    # Берём только будущие свободные слоты
    available_slots = TimeSlot.objects.filter(
        is_available=True,
        date__gte=today
    ).select_related('appointment')

    # Группируем по датам: {дата: [слоты]}
    slots_by_date = {}
    for slot in available_slots:
        if slot.date not in slots_by_date:
            slots_by_date[slot.date] = []
        slots_by_date[slot.date].append(slot)

    return render(request, 'booking/schedule.html', {
        'slots_by_date': slots_by_date
    })


def book(request, slot_id):
    """
    Страница записи на конкретный слот.
    GET — показывает форму.
    POST — сохраняет запись.
    """
    slot = get_object_or_404(TimeSlot, id=slot_id, is_available=True)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.slot = slot
            appointment.save()

            # Помечаем слот как занятый
            slot.is_available = False
            slot.save()

            messages.success(request, 'Вы успешно записались! Ждём вас.')
            return redirect('success')
    else:
        form = AppointmentForm()

    return render(request, 'booking/book.html', {
        'slot': slot,
        'form': form
    })


def success(request):
    """Страница подтверждения успешной записи."""
    return render(request, 'booking/success.html')


def contacts(request):
    """Страница с контактами психолога."""
    return render(request, 'booking/contacts.html')

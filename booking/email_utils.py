import logging
import threading
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def _send_mail_async(subject, message, recipient_list):
    """Отправка письма в отдельном потоке — не блокирует ответ пользователю."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception as e:
        logger.error('Ошибка отправки email: %s', e, exc_info=True)


def send_appointment_notification(appointment):
    slot = appointment.slot
    psychologist = slot.psychologist

    if not psychologist.email:
        return

    apt_type = appointment.appointment_type
    is_preschool = apt_type and apt_type.form_type == 'preschool_exam'

    if is_preschool:
        details = (
            f"ФИО ребёнка: {appointment.child_name}\n"
            f"Дата рождения: {appointment.child_birthdate}\n"
            f"Детский сад: {appointment.kindergarten}\n"
            f"Адрес: {appointment.address}\n"
            f"ФИО родителя: {appointment.parent_name}\n"
            f"Телефон родителя: {appointment.parent_phone}"
        )
    else:
        details = (
            f"ФИО: {appointment.full_name}\n"
            f"Кто записывается: {appointment.get_who_display() if appointment.who else '—'}\n"
            f"Класс: {appointment.grade or '—'}\n"
            f"Телефон: {appointment.phone}\n"
            f"Email: {appointment.email or '—'}\n"
            f"Примечание: {appointment.message or '—'}"
        )

    message = (
        f"Новая запись на приём\n\n"
        f"Психолог: {psychologist.name}\n"
        f"Дата и время: {slot.date.strftime('%d.%m.%Y')} в {slot.time.strftime('%H:%M')}\n"
        f"Тип обращения: {apt_type.name if apt_type else '—'}\n\n"
        f"{details}\n\n"
        f"Лицей №23 · Кабинет психолога"
    )

    recipient_list = [psychologist.email] + getattr(settings, 'NOTIFICATION_BCC_LIST', [])

    thread = threading.Thread(
        target=_send_mail_async,
        args=(f"Новая запись: {slot.date.strftime('%d.%m.%Y')} в {slot.time.strftime('%H:%M')}",
              message, recipient_list),
        daemon=True,
    )
    thread.start()


def send_cancellation_notification(appointment):
    """Уведомление об отмене записи."""
    slot = appointment.slot
    psychologist = slot.psychologist

    if not psychologist.email:
        return

    apt_type = appointment.appointment_type
    is_preschool = apt_type and apt_type.form_type == 'preschool_exam'

    if is_preschool:
        details = (
            f"ФИО ребёнка: {appointment.child_name}\n"
            f"Дата рождения: {appointment.child_birthdate}\n"
            f"Детский сад: {appointment.kindergarten}\n"
            f"Адрес: {appointment.address}\n"
            f"ФИО родителя: {appointment.parent_name}\n"
            f"Телефон родителя: {appointment.parent_phone}"
        )
    else:
        details = (
            f"ФИО: {appointment.full_name}\n"
            f"Кто записывается: {appointment.get_who_display() if appointment.who else '—'}\n"
            f"Класс: {appointment.grade or '—'}\n"
            f"Телефон: {appointment.phone}\n"
            f"Email: {appointment.email or '—'}\n"
            f"Примечание: {appointment.message or '—'}"
        )

    message = (
        f"Отмена записи\n\n"
        f"Психолог: {psychologist.name}\n"
        f"Дата и время: {slot.date.strftime('%d.%m.%Y')} в {slot.time.strftime('%H:%M')}\n"
        f"Тип обращения: {apt_type.name if apt_type else '—'}\n\n"
        f"{details}\n\n"
        f"Лицей №23 · Кабинет психолога"
    )

    recipient_list = [psychologist.email] + getattr(settings, 'NOTIFICATION_BCC_LIST', [])

    thread = threading.Thread(
        target=_send_mail_async,
        args=(f"Отмена записи: {slot.date.strftime('%d.%m.%Y')} в {slot.time.strftime('%H:%M')}",
              message, recipient_list),
        daemon=True,
    )
    thread.start()

import logging
import threading
from datetime import date
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def _send_mail_async(subject, plain_text, html_message, recipient_list):
    """Отправка в отдельном потоке — не блокирует ответ пользователю.

    В DEBUG=True — console backend (печать в консоль).
    В production — SMTP через VPS relay (103.71.21.98:2587) → Яндекс.
    """
    try:
        send_mail(
            subject=subject,
            message=plain_text,
            html_message=html_message,
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

    days_until = (slot.date - date.today()).days

    context = {
        'psychologist_name': psychologist.name,
        'date': slot.date.strftime('%d.%m.%Y'),
        'time': slot.time.strftime('%H:%M'),
        'appointment_type': apt_type.name if apt_type else '—',
        'days_until': days_until,
        'is_preschool': is_preschool,
    }

    if is_preschool:
        context.update({
            'child_name': appointment.child_name,
            'child_birthdate': appointment.child_birthdate,
            'kindergarten': appointment.kindergarten,
            'address': appointment.address,
            'parent_name': appointment.parent_name,
            'parent_phone': appointment.parent_phone,
        })
    else:
        context.update({
            'full_name': appointment.full_name,
            'who': appointment.get_who_display() if appointment.who else None,
            'grade': appointment.grade,
            'phone': appointment.phone,
            'email': appointment.email,
            'message': appointment.message,
        })

    html_message = render_to_string('email/new_appointment.html', context)
    plain_text = strip_tags(html_message)

    recipient_list = [psychologist.email] + getattr(settings, 'NOTIFICATION_BCC_LIST', [])

    thread = threading.Thread(
        target=_send_mail_async,
        args=(f"Новая запись: {slot.date.strftime('%d.%m.%Y')} в {slot.time.strftime('%H:%M')}",
              plain_text, html_message, recipient_list),
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

    days_until = (slot.date - date.today()).days

    context = {
        'psychologist_name': psychologist.name,
        'date': slot.date.strftime('%d.%m.%Y'),
        'time': slot.time.strftime('%H:%M'),
        'appointment_type': apt_type.name if apt_type else '—',
        'days_until': days_until,
        'is_preschool': is_preschool,
    }

    if is_preschool:
        context.update({
            'child_name': appointment.child_name,
            'child_birthdate': appointment.child_birthdate,
            'kindergarten': appointment.kindergarten,
            'address': appointment.address,
            'parent_name': appointment.parent_name,
            'parent_phone': appointment.parent_phone,
        })
    else:
        context.update({
            'full_name': appointment.full_name,
            'who': appointment.get_who_display() if appointment.who else None,
            'grade': appointment.grade,
            'phone': appointment.phone,
            'email': appointment.email,
            'message': appointment.message,
        })

    html_message = render_to_string('email/cancellation.html', context)
    plain_text = strip_tags(html_message)

    recipient_list = [psychologist.email] + getattr(settings, 'NOTIFICATION_BCC_LIST', [])

    thread = threading.Thread(
        target=_send_mail_async,
        args=(f"Отмена записи: {slot.date.strftime('%d.%m.%Y')} в {slot.time.strftime('%H:%M')}",
              plain_text, html_message, recipient_list),
        daemon=True,
    )
    thread.start()

import logging
import smtplib
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connection, OperationalError
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

logger = logging.getLogger(__name__)


def _check_smtp():
    """Проверка SMTP: relay + AUTH."""
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    user = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD

    if not password:
        return 'no_password', None

    try:
        server = smtplib.SMTP(host, port, timeout=5)
        server.ehlo_or_helo_if_needed()
        server.starttls()
        server.ehlo_or_helo_if_needed()
        server.login(user, password)
        server.quit()
        return 'ok', None
    except smtplib.SMTPAuthenticationError as e:
        return 'auth_failed', str(e)
    except smtplib.SMTPException as e:
        return 'smtp_error', str(e)
    except OSError as e:
        return 'connection_error', str(e)


def health_check(request):
    """Health check endpoint — только БД (мгновенно)."""
    db_status = 'error'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        db_status = 'ok'
    except OperationalError:
        db_status = 'error'

    return JsonResponse({
        'status': 'ok' if db_status == 'ok' else 'degraded',
        'database': db_status,
    })


@staff_member_required
def email_check_view(request):
    """Проверка SMTP — для админки (нажимается кнопка)."""
    result, error = _check_smtp()
    context = {
        'result': result,
        'error': error,
        'host': settings.EMAIL_HOST,
        'port': settings.EMAIL_PORT,
        'sender': settings.DEFAULT_FROM_EMAIL,
        'has_password': bool(settings.EMAIL_HOST_PASSWORD),
        'is_debug': settings.DEBUG,
    }

    if result == 'ok':
        messages.success(request, 'SMTP работает: подключение и AUTH прошли успешно.')
    elif result == 'auth_failed':
        messages.error(request, 'Ошибка авторизации: неверный пароль (YA_PASSWORD).')
    elif result == 'no_password':
        messages.warning(request, 'Пароль не задан (YA_PASSWORD). Письма не уйдут.')
    elif result == 'connection_error':
        messages.error(request, f'SMTP-реле недоступно: {error}')
    else:
        messages.error(request, f'Ошибка SMTP: {error}')

    return render(request, 'admin/email_check.html', context)

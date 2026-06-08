import smtplib
import logging
from django.http import JsonResponse
from django.db import connection, OperationalError
from django.conf import settings

logger = logging.getLogger(__name__)


def _check_smtp():
    """Проверка SMTP: relay + AUTH (пароль).

    Подключается через STARTTLS, логинится в Яндекс — но письмо НЕ
    отправляет. Таймаут 5 секунд.
    """
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT
    user = settings.EMAIL_HOST_USER
    password = settings.EMAIL_HOST_PASSWORD

    if not password:
        return 'no_password'

    try:
        server = smtplib.SMTP(host, port, timeout=3)
        server.ehlo_or_helo_if_needed()
        server.starttls()
        server.ehlo_or_helo_if_needed()
        server.login(user, password)
        server.quit()
        return 'ok'
    except smtplib.SMTPAuthenticationError:
        logger.warning('SMTP health: AUTH failed')
        return 'auth_failed'
    except (smtplib.SMTPException, OSError) as e:
        logger.debug('SMTP health: %s', e)
        return 'error'


def health_check(request):
    """Health check endpoint — БД + SMTP-реле."""
    db_status = 'error'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        db_status = 'ok'
    except OperationalError:
        db_status = 'error'

    smtp_status = _check_smtp() if not settings.DEBUG else 'skipped'

    overall = 'ok'
    if db_status != 'ok':
        overall = 'degraded'
    if smtp_status in ('error', 'refused', 'dns_error'):
        overall = 'degraded'

    return JsonResponse({
        'status': overall,
        'database': db_status,
        'smtp': smtp_status,
    })

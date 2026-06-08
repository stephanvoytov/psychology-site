import socket
import logging
from django.http import JsonResponse
from django.db import connection, OperationalError
from django.conf import settings

logger = logging.getLogger(__name__)


def _check_smtp():
    """Проверка доступности SMTP-реле.

    Подключается к SMTP-серверу и проверяет, что он отдаёт 220 (готов к
    работе). Таймаут 5 секунд — не блокируем health endpoint.
    """
    host = settings.EMAIL_HOST
    port = settings.EMAIL_PORT

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    try:
        sock.connect((host, port))
        banner = sock.recv(1024).decode('utf-8', errors='ignore')
        if banner.startswith('220'):
            sock.sendall(b'QUIT\r\n')
            return 'ok'
        else:
            logger.warning('SMTP health: unexpected banner: %s', banner.strip())
            return 'unexpected_banner'
    except socket.timeout:
        logger.warning('SMTP health: connection timeout to %s:%s', host, port)
        return 'timeout'
    except ConnectionRefusedError:
        logger.warning('SMTP health: connection refused to %s:%s', host, port)
        return 'refused'
    except socket.gaierror:
        logger.warning('SMTP health: DNS resolution failed for %s', host)
        return 'dns_error'
    except Exception as e:
        logger.warning('SMTP health: %s: %s', type(e).__name__, e)
        return 'error'
    finally:
        sock.close()


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

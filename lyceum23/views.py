from django.http import JsonResponse
from django.db import connection, OperationalError


def health_check(request):
    """Health check endpoint that verifies DB connectivity."""
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

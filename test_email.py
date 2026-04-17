from django.core.mail import send_mail
from django.conf import settings

try:
    result = send_mail(
        subject='Тест от сайта записи',
        message='Проверка связи',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=['stepanvoytov@yandex.ru'],
        fail_silently=False,
    )
    print(f"Результат: {result}")
    print(f"Настройки: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
except Exception as e:
    print(f"Ошибка: {e}")
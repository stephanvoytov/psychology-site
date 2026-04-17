from django.contrib import admin
from django.core.mail import send_mail
from django.http import HttpResponse
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('booking.urls')),
    path('test-email/', lambda request: (send_mail('Test', 'Body', 'stepanvoytov@yandex.ru', ['voytov.st.vi@gmail.com']), HttpResponse('Sent')) )
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.template.loader import render_to_string

from . import views

from django.conf import settings
from django.conf.urls.static import static

def robots_txt(request):
    return HttpResponse(render_to_string('robots.txt', request=request), content_type='text/plain')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/check-email/', views.email_check_view, name='email_check'),
    path('health/', views.health_check, name='health_check'),
    path('robots.txt', robots_txt),
    path('', include('booking.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
import os

from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.urls import path, include


def index(request):
    p = os.path.join(settings.BASE_DIR, 'static', 'index.html')
    if os.path.exists(p):
        with open(p, encoding='utf-8') as f:
            return HttpResponse(f.read())
    return HttpResponse('前端尚未构建，请先执行: cd frontend && npm install && npm run build',
                        content_type='text/plain; charset=utf-8')


urlpatterns = [
    path('api/', include('apps.core.urls')),
    path('', index),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

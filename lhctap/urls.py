from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from apps.core.views import health_check

def redirect_to_dashboard(request):
    """Redireciona usuários autenticados para dashboard"""
    if request.user.is_authenticated:
        return redirect('taps:dashboard')
    return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', redirect_to_dashboard, name='home'),
    path('accounts/', include('apps.accounts.urls')),
    path('dashboard/', include('apps.taps.urls')),
    path('api/tap/', include('apps.taps.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('health/', health_check, name='health_check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

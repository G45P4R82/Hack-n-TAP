from django.urls import path
from . import views

app_name = 'taps'

urlpatterns = [
    # Dashboard do usuário
    path('', views.dashboard, name='dashboard'),
    
    # API simplificada: POST /api/tap/<tap_id>/ com device_id no body
    path('<int:tap_id>/', views.check_tap_access, name='check_tap_access'),
    
    # Endpoints auxiliares
    path('list/', views.list_taps, name='list_taps'),
    path('<int:tap_id>/status/', views.tap_status, name='tap_status'),
]
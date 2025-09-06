from django.urls import path
from . import views

app_name = 'taps'

urlpatterns = [
    # API endpoints para dispositivos leitores
    path('validate/', views.validate_token, name='validate_token'),
    path('<int:tap_id>/status/', views.tap_status, name='tap_status'),
]
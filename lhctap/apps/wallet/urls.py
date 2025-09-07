from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # Dashboard e funcionalidades do usuário
    path('', views.dashboard, name='dashboard'),
    path('generate-token/', views.generate_token, name='generate_token'),
    path('qr/<str:token>/', views.generate_qr_image, name='generate_qr_image'),
    path('statement/', views.statement, name='statement'),
    path('profile/', views.profile, name='profile'),
    
    # Gerenciamento de créditos
    path('add-credits/', views.add_credits, name='add_credits'),
    path('process-credits/', views.process_credits, name='process_credits'),
]
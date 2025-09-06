from django.urls import path
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    # URLs básicas de autenticação serão implementadas posteriormente
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

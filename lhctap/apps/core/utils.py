import secrets
from django.utils import timezone
from datetime import timedelta


def generate_secure_token(length=32):
    """Gera token criptograficamente seguro"""
    return secrets.token_urlsafe(length)


def get_client_ip(request):
    """Extrai IP do cliente considerando proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def format_currency(cents):
    """Formata centavos para moeda brasileira"""
    return f"R$ {cents / 100:.2f}"


def is_token_expired(created_at, expiry_seconds=30):
    """Verifica se token está expirado"""
    expiry_time = created_at + timedelta(seconds=expiry_seconds)
    return timezone.now() > expiry_time


class TokenGenerator:
    """Gerador de tokens com configurações específicas"""
    
    @staticmethod
    def generate_tap_token():
        return generate_secure_token(32)
    
    @staticmethod
    def generate_api_key():
        return generate_secure_token(48)
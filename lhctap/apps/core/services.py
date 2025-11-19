from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.taps.models import TapUsage
from .exceptions import RateLimitExceededError


class RateLimitService:
    """Serviço para controle de rate limiting e prevenção de abuso"""
    
    @staticmethod
    def check_device_rate_limit(device_id, window_minutes=1, max_requests=10):
        """Verifica rate limit por device_id"""
        window_start = timezone.now() - timedelta(minutes=window_minutes)
        
        recent_attempts = TapUsage.objects.filter(
            device_id=device_id,
            created_at__gte=window_start
        ).count()
        
        return recent_attempts < max_requests
    
    @staticmethod
    def check_ip_rate_limit(ip_address, window_minutes=5, max_requests=50):
        """Verifica rate limit por IP"""
        window_start = timezone.now() - timedelta(minutes=window_minutes)
        
        recent_attempts = TapUsage.objects.filter(
            ip_address=ip_address,
            created_at__gte=window_start
        ).count()
        
        return recent_attempts < max_requests
    
    @staticmethod
    def get_suspicious_devices(days=1, error_threshold=0.5):
        """Identifica dispositivos com alta taxa de erro"""
        since = timezone.now() - timedelta(days=days)
        
        device_stats = TapUsage.objects.filter(
            created_at__gte=since
        ).values('device_id').annotate(
            total_attempts=models.Count('id'),
            error_count=models.Count(
                'id',
                filter=~models.Q(result='ok')
            )
        ).annotate(
            error_rate=models.Case(
                models.When(total_attempts=0, then=0),
                default=models.F('error_count') * 100.0 / models.F('total_attempts')
            )
        ).filter(
            total_attempts__gte=5,  # mínimo de tentativas
            error_rate__gte=error_threshold * 100
        ).order_by('-error_rate')
        
        return device_stats
    
    @staticmethod
    def validate_rate_limits(device_id, ip_address=None):
        """Valida todos os rate limits aplicáveis"""
        # Rate limit por device
        if not RateLimitService.check_device_rate_limit(device_id):
            raise RateLimitExceededError(
                f"Rate limit excedido para device {device_id}"
            )
        
        # Rate limit por IP (se fornecido)
        if ip_address and not RateLimitService.check_ip_rate_limit(ip_address):
            raise RateLimitExceededError(
                f"Rate limit excedido para IP {ip_address}"
            )
        
        return True

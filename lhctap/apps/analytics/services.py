from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from apps.taps.models import TapUsage, Tap


class MetricsService:
    """Serviço para métricas e dashboards administrativos"""
    
    @staticmethod
    def get_daily_metrics(date=None):
        """Métricas do dia específico ou hoje"""
        if date is None:
            date = timezone.now().date()
        
        start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_of_day = start_of_day + timedelta(days=1)
        
        usages = TapUsage.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
            result='ok'  # apenas usos bem-sucedidos
        )
        
        return {
            'total_uses': usages.count(),
            'unique_users': usages.values('user').distinct().count(),
            'unique_devices': usages.values('device_id').distinct().count(),
            'unique_taps': usages.values('tap').distinct().count(),
            'by_tap': usages.values('tap__name', 'tap__type').annotate(
                count=models.Count('id')
            )
        }
    
    @staticmethod
    def get_tap_performance(days=7):
        """Performance por tap nos últimos N dias"""
        since = timezone.now() - timedelta(days=days)
        
        return TapUsage.objects.filter(
            created_at__gte=since,
            result='ok',
            tap__isnull=False
        ).values(
            'tap__name',
            'tap__type'
        ).annotate(
            total_uses=models.Count('id'),
            unique_users=models.Count('user', distinct=True),
            unique_devices=models.Count('device_id', distinct=True)
        ).order_by('-total_uses')
    
    @staticmethod
    def get_top_users(days=30, limit=10):
        """Top usuários do período"""
        since = timezone.now() - timedelta(days=days)
        
        return TapUsage.objects.filter(
            created_at__gte=since,
            result='ok',
            user__isnull=False
        ).values(
            'user__username',
            'user__first_name',
            'user__last_name'
        ).annotate(
            total_uses=models.Count('id'),
            unique_taps=models.Count('tap', distinct=True)
        ).order_by('-total_uses')[:limit]
    
    @staticmethod
    def get_error_rates(days=7):
        """Taxa de erro nas validações"""
        since = timezone.now() - timedelta(days=days)
        
        total_attempts = TapUsage.objects.filter(
            created_at__gte=since
        ).count()
        
        if total_attempts == 0:
            return {'error_rate': 0, 'total_attempts': 0}
        
        errors_by_type = TapUsage.objects.filter(
            created_at__gte=since
        ).values('result').annotate(
            count=models.Count('id')
        )
        
        success_count = next(
            (item['count'] for item in errors_by_type if item['result'] == 'ok'),
            0
        )
        
        return {
            'error_rate': ((total_attempts - success_count) / total_attempts) * 100,
            'total_attempts': total_attempts,
            'success_count': success_count,
            'errors_by_type': {
                item['result']: item['count'] 
                for item in errors_by_type 
                if item['result'] != 'ok'
            }
        }
    
    @staticmethod
    def get_dashboard_summary():
        """Resumo geral para dashboard administrativo"""
        today = timezone.now().date()
        week_ago = timezone.now() - timedelta(days=7)
        month_ago = timezone.now() - timedelta(days=30)
        
        # Métricas de hoje
        today_metrics = MetricsService.get_daily_metrics(today)
        
        # Métricas da semana
        week_usages = TapUsage.objects.filter(
            created_at__gte=week_ago,
            result='ok'
        )
        
        week_uses = week_usages.count()
        week_unique_users = week_usages.values('user').distinct().count()
        week_unique_taps = week_usages.values('tap').distinct().count()
        
        # Métricas do mês
        month_usages = TapUsage.objects.filter(
            created_at__gte=month_ago,
            result='ok'
        )
        
        month_uses = month_usages.count()
        month_unique_users = month_usages.values('user').distinct().count()
        month_unique_taps = month_usages.values('tap').distinct().count()
        
        # Taxa de erro
        error_rates = MetricsService.get_error_rates(7)
        
        return {
            'today': {
                'total_uses': today_metrics['total_uses'],
                'unique_users': today_metrics['unique_users'],
                'unique_taps': today_metrics['unique_taps'],
            },
            'week': {
                'total_uses': week_uses,
                'unique_users': week_unique_users,
                'unique_taps': week_unique_taps,
            },
            'month': {
                'total_uses': month_uses,
                'unique_users': month_unique_users,
                'unique_taps': month_unique_taps,
            },
            'system': {
                'error_rate': error_rates['error_rate'],
                'total_attempts': error_rates['total_attempts'],
                'success_count': error_rates['success_count']
            }
        }

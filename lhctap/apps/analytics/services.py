from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from apps.wallet.models import Transaction
from apps.taps.models import TapValidationAudit


class MetricsService:
    """Serviço para métricas e dashboards administrativos"""
    
    @staticmethod
    def get_daily_metrics(date=None):
        """Métricas do dia específico ou hoje"""
        if date is None:
            date = timezone.now().date()
        
        start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_of_day = start_of_day + timedelta(days=1)
        
        transactions = Transaction.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
            amount_cents__lt=0  # apenas consumos
        )
        
        return {
            'total_volume_ml': transactions.aggregate(
                total=models.Sum('volume_ml')
            )['total'] or 0,
            'total_transactions': transactions.count(),
            'total_revenue_cents': abs(transactions.aggregate(
                total=models.Sum('amount_cents')
            )['total'] or 0),
            'unique_users': transactions.values('user').distinct().count(),
            'by_category': transactions.values('category').annotate(
                volume=models.Sum('volume_ml'),
                count=models.Count('id'),
                revenue=models.Sum('amount_cents')
            )
        }
    
    @staticmethod
    def get_tap_performance(days=7):
        """Performance por tap nos últimos N dias"""
        since = timezone.now() - timedelta(days=days)
        
        return Transaction.objects.filter(
            created_at__gte=since,
            amount_cents__lt=0,
            ref_session__tap__isnull=False
        ).values(
            'ref_session__tap__name',
            'ref_session__tap__type'
        ).annotate(
            total_volume=models.Sum('volume_ml'),
            transaction_count=models.Count('id'),
            total_revenue=models.Sum('amount_cents'),
            unique_users=models.Count('user', distinct=True)
        ).order_by('-total_volume')
    
    @staticmethod
    def get_top_consumers(days=30, limit=10):
        """Top consumidores do período"""
        since = timezone.now() - timedelta(days=days)
        
        return Transaction.objects.filter(
            created_at__gte=since,
            amount_cents__lt=0
        ).values(
            'user__username',
            'user__first_name',
            'user__last_name'
        ).annotate(
            total_volume=models.Sum('volume_ml'),
            total_spent=models.Sum('amount_cents'),
            transaction_count=models.Count('id')
        ).order_by('-total_volume')[:limit]
    
    @staticmethod
    def get_error_rates(days=7):
        """Taxa de erro nas validações"""
        since = timezone.now() - timedelta(days=days)
        
        total_attempts = TapValidationAudit.objects.filter(
            created_at__gte=since
        ).count()
        
        if total_attempts == 0:
            return {'error_rate': 0, 'total_attempts': 0}
        
        errors_by_type = TapValidationAudit.objects.filter(
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
        week_transactions = Transaction.objects.filter(
            created_at__gte=week_ago,
            amount_cents__lt=0
        )
        
        week_volume = week_transactions.aggregate(
            total=models.Sum('volume_ml')
        )['total'] or 0
        
        week_revenue = abs(week_transactions.aggregate(
            total=models.Sum('amount_cents')
        )['total'] or 0)
        
        # Métricas do mês
        month_transactions = Transaction.objects.filter(
            created_at__gte=month_ago,
            amount_cents__lt=0
        )
        
        month_volume = month_transactions.aggregate(
            total=models.Sum('volume_ml')
        )['total'] or 0
        
        month_revenue = abs(month_transactions.aggregate(
            total=models.Sum('amount_cents')
        )['total'] or 0)
        
        # Taxa de erro
        error_rates = MetricsService.get_error_rates(7)
        
        return {
            'today': {
                'volume_ml': today_metrics['total_volume_ml'],
                'transactions': today_metrics['total_transactions'],
                'revenue_cents': today_metrics['total_revenue_cents'],
                'unique_users': today_metrics['unique_users']
            },
            'week': {
                'volume_ml': week_volume,
                'revenue_cents': week_revenue,
                'transactions': week_transactions.count()
            },
            'month': {
                'volume_ml': month_volume,
                'revenue_cents': month_revenue,
                'transactions': month_transactions.count()
            },
            'system': {
                'error_rate': error_rates['error_rate'],
                'total_attempts': error_rates['total_attempts'],
                'success_count': error_rates['success_count']
            }
        }

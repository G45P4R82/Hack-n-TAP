from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.taps.models import TapSession, TapValidationAudit


class Command(BaseCommand):
    help = 'Limpa tokens expirados e logs antigos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Dias para manter tokens expirados (padrão: 7)'
        )
        parser.add_argument(
            '--audit-days',
            type=int,
            default=90,
            help='Dias para manter logs de auditoria (padrão: 90)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        audit_days = options['audit_days']
        
        # Limpar tokens expirados
        cutoff_date = timezone.now() - timedelta(days=days)
        expired_sessions = TapSession.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['expired', 'used']
        )
        
        sessions_count = expired_sessions.count()
        expired_sessions.delete()
        
        # Limpar logs de auditoria antigos
        audit_cutoff = timezone.now() - timedelta(days=audit_days)
        old_audits = TapValidationAudit.objects.filter(
            created_at__lt=audit_cutoff
        )
        
        audits_count = old_audits.count()
        old_audits.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Limpeza concluída: {sessions_count} sessões e {audits_count} logs removidos'
            )
        )

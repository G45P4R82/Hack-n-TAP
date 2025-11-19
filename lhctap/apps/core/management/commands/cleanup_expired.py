from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.taps.models import TapUsage


class Command(BaseCommand):
    help = 'Limpa logs antigos de uso dos taps'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Dias para manter logs de uso (padrão: 90)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        
        # Limpar logs antigos
        cutoff_date = timezone.now() - timedelta(days=days)
        old_usages = TapUsage.objects.filter(
            created_at__lt=cutoff_date
        )
        
        usages_count = old_usages.count()
        old_usages.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Limpeza concluída: {usages_count} registros de uso removidos'
            )
        )

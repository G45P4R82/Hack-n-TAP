from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.taps.models import TapUsage, Tap
from apps.accounts.models import Device


class Command(BaseCommand):
    help = 'Limpa dados de teste (histórico de uso, dispositivos, etc)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Remove também usuários, taps e dispositivos (CUIDADO!)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🧹 Iniciando limpeza dos dados de teste...')
        )
        
        # Limpar histórico de uso
        usage_count = TapUsage.objects.count()
        TapUsage.objects.all().delete()
        self.stdout.write(f'  🗑️  {usage_count} registros de uso removidos')
        
        if options['all']:
            self.stdout.write(
                self.style.WARNING('⚠️  Removendo TODOS os dados (usuários, taps e dispositivos)...')
            )
            
            # Remover dispositivos
            device_count = Device.objects.count()
            Device.objects.all().delete()
            self.stdout.write(f'  🔑 {device_count} dispositivos removidos')
            
            # Remover usuários (exceto superuser)
            users_count = User.objects.filter(is_superuser=False).count()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(f'  👥 {users_count} usuários removidos')
            
            # Remover taps
            taps_count = Tap.objects.count()
            Tap.objects.all().delete()
            self.stdout.write(f'  🍺 {taps_count} taps removidos')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Limpeza concluída!')
        )
        
        if not options['all']:
            self.stdout.write(
                self.style.SUCCESS('💡 Para remover tudo (usuários, taps e dispositivos), use: --all')
            )

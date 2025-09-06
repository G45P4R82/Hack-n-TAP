from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.wallet.models import Transaction
from apps.taps.models import TapSession, TapValidationAudit


class Command(BaseCommand):
    help = 'Limpa dados de teste (transações, sessões, auditoria)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Remove também usuários e taps (CUIDADO!)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING('🧹 Iniciando limpeza dos dados de teste...')
        )
        
        # Limpar transações
        transaction_count = Transaction.objects.count()
        Transaction.objects.all().delete()
        self.stdout.write(f'  🗑️  {transaction_count} transações removidas')
        
        # Limpar sessões
        session_count = TapSession.objects.count()
        TapSession.objects.all().delete()
        self.stdout.write(f'  🗑️  {session_count} sessões removidas')
        
        # Limpar auditoria
        audit_count = TapValidationAudit.objects.count()
        TapValidationAudit.objects.all().delete()
        self.stdout.write(f'  🗑️  {audit_count} registros de auditoria removidos')
        
        # Resetar saldos das carteiras
        from apps.wallet.models import Wallet
        wallets_updated = 0
        for wallet in Wallet.objects.all():
            if wallet.balance_cents > 0:
                wallet.balance_cents = 0
                wallet.save()
                wallets_updated += 1
        self.stdout.write(f'  💰 {wallets_updated} carteiras resetadas')
        
        if options['all']:
            self.stdout.write(
                self.style.WARNING('⚠️  Removendo TODOS os dados (usuários e taps)...')
            )
            
            # Remover usuários (exceto superuser)
            users_count = User.objects.filter(is_superuser=False).count()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(f'  👥 {users_count} usuários removidos')
            
            # Remover taps
            from apps.taps.models import Tap
            taps_count = Tap.objects.count()
            Tap.objects.all().delete()
            self.stdout.write(f'  🍺 {taps_count} taps removidos')
        
        self.stdout.write(
            self.style.SUCCESS('✅ Limpeza concluída!')
        )
        
        if not options['all']:
            self.stdout.write(
                self.style.SUCCESS('💡 Para remover tudo (usuários e taps), use: --all')
            )

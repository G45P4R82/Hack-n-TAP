from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.wallet.services import WalletService


class Command(BaseCommand):
    help = 'Testa a funcionalidade de adição de créditos'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧪 Testando funcionalidade de créditos...')
        )
        
        # Buscar usuário de teste
        try:
            user = User.objects.get(username='joao')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Usuário "joao" não encontrado. Execute: python manage.py create_test_data')
            )
            return
        
        # Saldo inicial
        initial_balance = user.wallet.balance_cents
        self.stdout.write(f'💰 Saldo inicial de {user.username}: R$ {initial_balance/100:.2f}')
        
        # Testar adição de créditos
        test_amounts = [3000, 5000, 10000]  # R$ 30, 50, 100
        
        for amount in test_amounts:
            try:
                self.stdout.write(f'💳 Testando adição de R$ {amount/100:.2f}...')
                
                # Adicionar créditos
                transaction = WalletService.add_credits(
                    user, 
                    amount, 
                    f"Teste de recarga - R$ {amount/100:.2f}"
                )
                
                # Verificar saldo
                user.wallet.refresh_from_db()
                new_balance = user.wallet.balance_cents
                
                self.stdout.write(f'  ✅ Sucesso! Transação ID: {transaction.id}')
                self.stdout.write(f'  💰 Novo saldo: R$ {new_balance/100:.2f}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Erro: {str(e)}')
                )
        
        # Saldo final
        final_balance = user.wallet.balance_cents
        total_added = final_balance - initial_balance
        
        self.stdout.write('\n📊 RESUMO DO TESTE:')
        self.stdout.write(f'💰 Saldo inicial: R$ {initial_balance/100:.2f}')
        self.stdout.write(f'💰 Saldo final: R$ {final_balance/100:.2f}')
        self.stdout.write(f'💳 Total adicionado: R$ {total_added/100:.2f}')
        
        if total_added == sum(test_amounts):
            self.stdout.write(
                self.style.SUCCESS('✅ Teste passou! Funcionalidade de créditos está funcionando.')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Teste falhou! Valores não conferem.')
            )

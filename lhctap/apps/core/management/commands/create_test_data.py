from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.wallet.models import Wallet, Transaction
from apps.taps.models import Tap


class Command(BaseCommand):
    help = 'Cria dados de teste para desenvolvimento'
    
    def handle(self, *args, **options):
        # Criar usuários de teste
        users_data = [
            {'username': 'admin', 'email': 'admin@lhc.com', 'role': 'admin', 'balance': 5000},
            {'username': 'joao', 'email': 'joao@lhc.com', 'role': 'member', 'balance': 3000},
            {'username': 'maria', 'email': 'maria@lhc.com', 'role': 'member', 'balance': 2500},
            {'username': 'pedro', 'email': 'pedro@lhc.com', 'role': 'member', 'balance': 1500},
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['username'].title(),
                    'is_staff': user_data['role'] == 'admin',
                    'is_superuser': user_data['role'] == 'admin'
                }
            )
            
            if created:
                user.set_password('123456')
                user.save()
                
                # Profile e Wallet são criados automaticamente pelos signals
                # Apenas atualizar o role do profile
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': user_data['role']}
                )
                if not profile_created:
                    profile.role = user_data['role']
                    profile.save()
                
                # Adicionar saldo inicial
                wallet, wallet_created = Wallet.objects.get_or_create(user=user)
                if wallet_created or wallet.balance_cents == 0:
                    wallet.balance_cents = user_data['balance']
                    wallet.save()
                    
                    # Criar transação de recarga inicial
                    Transaction.objects.create(
                        user=user,
                        amount_cents=user_data['balance'],
                        category='topup',
                        description='Saldo inicial de teste'
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Usuário {user.username} criado com sucesso')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Usuário {user.username} já existe')
                )
        
        # Verificar se taps existem
        tap_count = Tap.objects.count()
        if tap_count == 0:
            self.stdout.write(
                self.style.WARNING('Nenhum tap encontrado. Execute: python manage.py loaddata lhctap/fixtures/initial_data.json')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'{tap_count} taps encontrados')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Dados de teste criados com sucesso!')
        )
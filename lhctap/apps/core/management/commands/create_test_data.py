from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from datetime import timedelta
import random
from apps.accounts.models import UserProfile
from apps.wallet.models import Wallet, Transaction
from apps.wallet.services import WalletService
from apps.taps.models import Tap, TapSession


class Command(BaseCommand):
    help = 'Cria dados de teste para desenvolvimento'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando simulação completa do sistema LHC Tap...')
        )
        
        # 1. Criar taps se não existirem
        self.create_taps()
        
        # 2. Criar usuários de teste
        users = self.create_test_users()
        
        # 3. Simular transações de recarga
        self.simulate_credit_transactions(users)
        
        # 4. Simular consumos
        self.simulate_consumptions(users)
        
        # 5. Mostrar resumo
        self.show_summary()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Simulação completa finalizada!')
        )
    
    def create_taps(self):
        """Cria taps de teste se não existirem"""
        self.stdout.write('📋 Criando taps de teste...')
        
        taps_data = [
            {'name': 'Chope Pilsen', 'type': 'beer', 'dose_ml': 300, 'price_cents': 800, 'location': 'Bar Principal'},
            {'name': 'Chope IPA', 'type': 'beer', 'dose_ml': 300, 'price_cents': 1000, 'location': 'Bar Principal'},
            {'name': 'Chope Weiss', 'type': 'beer', 'dose_ml': 300, 'price_cents': 1200, 'location': 'Bar Principal'},
            {'name': 'Mate Tradicional', 'type': 'mate', 'dose_ml': 500, 'price_cents': 600, 'location': 'Área Externa'},
            {'name': 'Mate Gelado', 'type': 'mate', 'dose_ml': 500, 'price_cents': 700, 'location': 'Área Externa'},
        ]
        
        for tap_data in taps_data:
            tap, created = Tap.objects.get_or_create(
                name=tap_data['name'],
                defaults=tap_data
            )
            if created:
                self.stdout.write(f'  ✅ Tap "{tap.name}" criado')
            else:
                self.stdout.write(f'  ⚠️  Tap "{tap.name}" já existe')
    
    def create_test_users(self):
        """Cria usuários de teste"""
        self.stdout.write('👥 Criando usuários de teste...')
        
        users_data = [
            {'username': 'admin', 'email': 'admin@lhc.com', 'role': 'admin', 'balance': 10000},
            {'username': 'joao', 'email': 'joao@lhc.com', 'role': 'member', 'balance': 5000},
            {'username': 'maria', 'email': 'maria@lhc.com', 'role': 'member', 'balance': 3000},
            {'username': 'pedro', 'email': 'pedro@lhc.com', 'role': 'member', 'balance': 2000},
            {'username': 'ana', 'email': 'ana@lhc.com', 'role': 'member', 'balance': 1500},
        ]
        
        users = []
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
                
                self.stdout.write(f'  ✅ Usuário {user.username} criado (R$ {user_data["balance"]/100:.2f})')
            else:
                self.stdout.write(f'  ⚠️  Usuário {user.username} já existe')
            
            users.append(user)
        
        return users
    
    def simulate_credit_transactions(self, users):
        """Simula transações de recarga de créditos"""
        self.stdout.write('💰 Simulando recargas de crédito...')
        
        credit_amounts = [3000, 4000, 5000, 10000, 20000]  # R$ 30, 40, 50, 100, 200
        
        for user in users:
            if user.username == 'admin':
                continue  # Admin não precisa de recargas
            
            # Simular 1-3 recargas por usuário
            num_recharges = random.randint(1, 3)
            for _ in range(num_recharges):
                amount = random.choice(credit_amounts)
                description = f"Recarga de R$ {amount/100:.2f}"
                
                # Usar o serviço para adicionar créditos
                transaction = WalletService.add_credits(user, amount, description)
                
                # Simular data no passado
                days_ago = random.randint(1, 30)
                transaction.created_at = timezone.now() - timedelta(days=days_ago)
                transaction.save()
                
                self.stdout.write(f'  💳 {user.username}: {description}')
    
    def simulate_consumptions(self, users):
        """Simula consumos nos taps"""
        self.stdout.write('🍺 Simulando consumos...')
        
        taps = Tap.objects.filter(is_active=True)
        
        for user in users:
            if user.username == 'admin':
                continue  # Admin não consome
            
            # Simular 2-5 consumos por usuário
            num_consumptions = random.randint(2, 5)
            for _ in range(num_consumptions):
                tap = random.choice(taps)
                
                # Verificar se tem saldo suficiente
                if user.wallet.balance_cents >= tap.price_cents:
                    # Simular consumo
                    try:
                        # Criar sessão simulada
                        session = TapSession.objects.create(
                            user=user,
                            tap=tap,
                            token=f"test_{random.randint(1000, 9999)}",
                            status='used',
                            expires_at=timezone.now() + timedelta(minutes=5),
                            used_at=timezone.now() - timedelta(days=random.randint(1, 20))
                        )
                        
                        # Processar consumo
                        transaction = WalletService.process_consumption(user, tap, session)
                        
                        # Simular data no passado
                        days_ago = random.randint(1, 20)
                        transaction.created_at = timezone.now() - timedelta(days=days_ago)
                        transaction.save()
                        
                        self.stdout.write(f'  🍺 {user.username}: {tap.name} (R$ {tap.price_cents/100:.2f})')
                        
                    except Exception as e:
                        self.stdout.write(f'  ❌ Erro ao simular consumo para {user.username}: {e}')
    
    def show_summary(self):
        """Mostra resumo da simulação"""
        self.stdout.write('\n📊 RESUMO DA SIMULAÇÃO:')
        self.stdout.write('=' * 50)
        
        # Estatísticas gerais
        total_users = User.objects.count()
        total_taps = Tap.objects.count()
        total_transactions = Transaction.objects.count()
        total_volume = Transaction.objects.aggregate(
            total_volume=models.Sum('volume_ml')
        )['total_volume'] or 0
        
        self.stdout.write(f'👥 Usuários: {total_users}')
        self.stdout.write(f'🍺 Taps: {total_taps}')
        self.stdout.write(f'📋 Transações: {total_transactions}')
        self.stdout.write(f'🥤 Volume total: {total_volume}ml')
        
        # Saldos dos usuários
        self.stdout.write('\n💰 SALDOS ATUAIS:')
        for user in User.objects.all():
            balance = user.wallet.balance_cents
            self.stdout.write(f'  {user.username}: R$ {balance/100:.2f}')
        
        # Taps disponíveis
        self.stdout.write('\n🍺 TAPS DISPONÍVEIS:')
        for tap in Tap.objects.filter(is_active=True):
            self.stdout.write(f'  {tap.name}: R$ {tap.price_cents/100:.2f} ({tap.dose_ml}ml)')
        
        self.stdout.write('\n🔑 CREDENCIAIS DE TESTE:')
        self.stdout.write('  Usuário: joao | Senha: 123456')
        self.stdout.write('  Usuário: admin | Senha: 123456')
        self.stdout.write('  Usuário: maria | Senha: 123456')
        
        self.stdout.write('\n🌐 ACESSO:')
        self.stdout.write('  Dashboard: http://192.168.0.122:8000/dashboard/')
        self.stdout.write('  Admin: http://192.168.0.122:8000/admin/')
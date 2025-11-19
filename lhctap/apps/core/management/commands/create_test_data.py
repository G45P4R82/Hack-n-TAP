from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from apps.accounts.models import UserProfile, Device
from apps.taps.models import Tap, TapUsage


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
        
        # 3. Criar dispositivos (cartões RFID) e vincular aos usuários
        self.create_devices(users)
        
        # 4. Simular usos nos taps
        self.simulate_usages(users)
        
        # 5. Mostrar resumo
        self.show_summary()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Simulação completa finalizada!')
        )
    
    def create_taps(self):
        """Cria taps de teste se não existirem"""
        self.stdout.write('📋 Criando taps de teste...')
        
        taps_data = [
            {'name': 'Chope Pilsen', 'type': 'beer', 'dose_ml': 300, 'location': 'Bar Principal'},
            {'name': 'Chope IPA', 'type': 'beer', 'dose_ml': 300, 'location': 'Bar Principal'},
            {'name': 'Chope Weiss', 'type': 'beer', 'dose_ml': 300, 'location': 'Bar Principal'},
            {'name': 'Mate Tradicional', 'type': 'mate', 'dose_ml': 500, 'location': 'Área Externa'},
            {'name': 'Mate Gelado', 'type': 'mate', 'dose_ml': 500, 'location': 'Área Externa'},
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
            {'username': 'admin', 'email': 'admin@lhc.com', 'role': 'admin'},
            {'username': 'joao', 'email': 'joao@lhc.com', 'role': 'member'},
            {'username': 'maria', 'email': 'maria@lhc.com', 'role': 'member'},
            {'username': 'pedro', 'email': 'pedro@lhc.com', 'role': 'member'},
            {'username': 'ana', 'email': 'ana@lhc.com', 'role': 'member'},
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
                
                # Profile é criado automaticamente pelo signal
                # Apenas atualizar o role do profile
                profile, profile_created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={'role': user_data['role']}
                )
                if not profile_created:
                    profile.role = user_data['role']
                    profile.save()
                
                self.stdout.write(f'  ✅ Usuário {user.username} criado')
            else:
                self.stdout.write(f'  ⚠️  Usuário {user.username} já existe')
            
            users.append(user)
        
        return users
    
    def create_devices(self, users):
        """Cria dispositivos (cartões RFID) e vincula aos usuários"""
        self.stdout.write('🔑 Criando dispositivos (cartões RFID)...')
        
        device_counter = 1
        
        for user in users:
            # Cada usuário terá 1-2 dispositivos
            num_devices = random.randint(1, 2)
            
            for i in range(num_devices):
                device_id = f"RFID-{device_counter:04d}"
                device_name = f"Cartão {i+1}" if num_devices > 1 else "Cartão Principal"
                
                device, created = Device.objects.get_or_create(
                    device_id=device_id,
                    defaults={
                        'name': f"{device_name} - {user.username}",
                        'status': 'active',
                        'notes': f'Dispositivo de teste para {user.username}'
                    }
                )
                
                if created:
                    device.users.add(user)
                    self.stdout.write(f'  ✅ Dispositivo {device_id} criado e vinculado a {user.username}')
                else:
                    # Se já existe, garantir que está vinculado ao usuário
                    if user not in device.users.all():
                        device.users.add(user)
                        self.stdout.write(f'  🔗 Dispositivo {device_id} vinculado a {user.username}')
                    else:
                        self.stdout.write(f'  ⚠️  Dispositivo {device_id} já vinculado a {user.username}')
                
                device_counter += 1
    
    def simulate_usages(self, users):
        """Simula usos nos taps"""
        self.stdout.write('🍺 Simulando usos nos taps...')
        
        taps = Tap.objects.filter(is_active=True)
        
        for user in users:
            if user.username == 'admin':
                continue  # Admin não usa taps
            
            # Obter dispositivos do usuário
            user_devices = user.devices.filter(status='active')
            if not user_devices.exists():
                self.stdout.write(f'  ⚠️  Usuário {user.username} não tem dispositivos ativos')
                continue
            
            # Simular 3-10 usos por usuário
            num_usages = random.randint(3, 10)
            for _ in range(num_usages):
                tap = random.choice(list(taps))
                device = random.choice(list(user_devices))
                
                # Simular uso bem-sucedido (90% das vezes)
                if random.random() < 0.9:
                    result = 'ok'
                else:
                    # Simular alguns erros ocasionais
                    result = random.choice(['device_inactive', 'tap_inactive'])
                
                # Criar registro de uso
                usage = TapUsage.objects.create(
                    device_id=device.device_id,
                    user=user if result == 'ok' else None,
                    tap=tap if result == 'ok' else None,
                    result=result,
                    ip_address=f"192.168.1.{random.randint(1, 254)}",
                    user_agent='Test Device Simulator'
                )
                
                # Simular data no passado (últimos 30 dias)
                days_ago = random.randint(0, 30)
                usage.created_at = timezone.now() - timedelta(days=days_ago)
                usage.save()
                
                if result == 'ok':
                    self.stdout.write(f'  🍺 {user.username}: {tap.name} via {device.device_id}')
                else:
                    self.stdout.write(f'  ❌ {user.username}: Erro ({result}) ao usar {tap.name}')
    
    def show_summary(self):
        """Mostra resumo da simulação"""
        self.stdout.write('\n📊 RESUMO DA SIMULAÇÃO:')
        self.stdout.write('=' * 50)
        
        # Estatísticas gerais
        total_users = User.objects.count()
        total_taps = Tap.objects.count()
        total_devices = Device.objects.count()
        total_usages = TapUsage.objects.filter(result='ok').count()
        total_errors = TapUsage.objects.exclude(result='ok').count()
        
        self.stdout.write(f'👥 Usuários: {total_users}')
        self.stdout.write(f'🍺 Taps: {total_taps}')
        self.stdout.write(f'🔑 Dispositivos: {total_devices}')
        self.stdout.write(f'✅ Usos bem-sucedidos: {total_usages}')
        self.stdout.write(f'❌ Erros: {total_errors}')
        
        # Dispositivos por usuário
        self.stdout.write('\n🔑 DISPOSITIVOS POR USUÁRIO:')
        for user in User.objects.all():
            devices = user.devices.filter(status='active')
            device_ids = ', '.join([d.device_id for d in devices])
            if device_ids:
                self.stdout.write(f'  {user.username}: {device_ids}')
            else:
                self.stdout.write(f'  {user.username}: Nenhum dispositivo')
        
        # Taps disponíveis
        self.stdout.write('\n🍺 TAPS DISPONÍVEIS:')
        for tap in Tap.objects.filter(is_active=True):
            self.stdout.write(f'  {tap.name} ({tap.get_type_display()}): {tap.dose_ml}ml - {tap.location}')
        
        self.stdout.write('\n🔑 CREDENCIAIS DE TESTE:')
        self.stdout.write('  Usuário: joao | Senha: 123456')
        self.stdout.write('  Usuário: admin | Senha: 123456')
        self.stdout.write('  Usuário: maria | Senha: 123456')
        
        self.stdout.write('\n🌐 ACESSO:')
        self.stdout.write('  Dashboard: http://localhost:8000/dashboard/')
        self.stdout.write('  Admin: http://localhost:8000/admin/')
        self.stdout.write('  API: http://localhost:8000/api/validate/')

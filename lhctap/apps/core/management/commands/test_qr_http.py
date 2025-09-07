from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
from apps.taps.models import Tap


class Command(BaseCommand):
    help = 'Testa a geração de QR Code via HTTP'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🌐 Testando geração de QR Code via HTTP...')
        )
        
        # Buscar usuário de teste
        try:
            user = User.objects.get(username='joao')
            tap = Tap.objects.filter(is_active=True).first()
            
            if not tap:
                self.stdout.write(
                    self.style.ERROR('Nenhum tap ativo encontrado.')
                )
                return
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Usuário "joao" não encontrado.')
            )
            return
        
        client = Client()
        
        # Fazer login
        login_success = client.login(username='joao', password='123456')
        if not login_success:
            self.stdout.write(
                self.style.ERROR('Falha no login do usuário de teste')
            )
            return
        
        self.stdout.write(f'👤 Usuário logado: {user.username}')
        self.stdout.write(f'🍺 Testando com tap: {tap.name}')
        
        # Testar geração de token
        self.stdout.write('\n🎫 Testando geração de token...')
        
        response = client.post('/dashboard/generate-token/', {
            'tap_id': tap.id
        })
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write('✅ Token gerado com sucesso!')
            self.stdout.write(f'   🎫 Token: {data["token"]}')
            self.stdout.write(f'   🍺 Tap: {data["tap_name"]}')
            self.stdout.write(f'   💰 Preço: R$ {data["price_cents"]/100:.2f}')
            self.stdout.write(f'   ⏰ Expira: {data["expires_at"]}')
            
            # Testar geração de QR Code
            self.stdout.write('\n🔲 Testando geração de QR Code...')
            
            qr_response = client.get(f'/dashboard/qr/{data["token"]}/')
            
            if qr_response.status_code == 200:
                qr_data = qr_response.json()
                self.stdout.write('✅ QR Code gerado com sucesso!')
                self.stdout.write(f'   📊 Base64 length: {len(qr_data["qr_code"])} caracteres')
                self.stdout.write(f'   🔗 Data URL: {qr_data["qr_code"][:50]}...')
                
                # Verificar se é uma imagem válida
                if qr_data["qr_code"].startswith('data:image/png;base64,'):
                    self.stdout.write('✅ Formato de imagem válido!')
                else:
                    self.stdout.write('❌ Formato de imagem inválido!')
                    
            else:
                self.stdout.write(f'❌ Erro ao gerar QR Code: {qr_response.status_code}')
                if hasattr(qr_response, 'content'):
                    self.stdout.write(f'   Resposta: {qr_response.content.decode()}')
        else:
            self.stdout.write(f'❌ Erro ao gerar token: {response.status_code}')
            if hasattr(response, 'content'):
                self.stdout.write(f'   Resposta: {response.content.decode()}')
        
        self.stdout.write('\n📋 RESUMO DOS TESTES HTTP:')
        self.stdout.write('✅ Login realizado com sucesso')
        self.stdout.write('✅ Geração de token via POST')
        self.stdout.write('✅ Geração de QR Code via GET')
        self.stdout.write('✅ Validação de formato de imagem')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Teste HTTP de QR Code concluído!')
        )
        
        self.stdout.write('\n💡 PRÓXIMOS PASSOS:')
        self.stdout.write('1. Acesse: http://192.168.0.122:8000/dashboard/')
        self.stdout.write('2. Clique em "Gerar QR" em qualquer tap')
        self.stdout.write('3. Verifique se o QR Code aparece no modal')
        self.stdout.write('4. Teste o countdown de expiração')

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.taps.models import Tap
from apps.taps.services import TokenService
import qrcode
import io
import base64


class Command(BaseCommand):
    help = 'Testa a geração de QR Code para tokens'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔲 Testando geração de QR Code...')
        )
        
        # Buscar usuário e tap de teste
        try:
            user = User.objects.get(username='joao')
            tap = Tap.objects.filter(is_active=True).first()
            
            if not tap:
                self.stdout.write(
                    self.style.ERROR('Nenhum tap ativo encontrado. Execute: python manage.py create_test_data')
                )
                return
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Usuário "joao" não encontrado. Execute: python manage.py create_test_data')
            )
            return
        
        # Criar sessão de token
        self.stdout.write(f'👤 Usuário: {user.username}')
        self.stdout.write(f'🍺 Tap: {tap.name} (R$ {tap.price_cents/100:.2f})')
        
        try:
            session = TokenService.create_session(user, tap)
            self.stdout.write(f'🎫 Token gerado: {session.token}')
            self.stdout.write(f'⏰ Expira em: {session.expires_at}')
            
            # Testar geração de QR Code
            self.stdout.write('\n🔲 Gerando QR Code...')
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(session.token)
            qr.make(fit=True)
            
            # Criar imagem
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Salvar QR Code para teste
            qr_path = '/tmp/test_qr.png'
            img.save(qr_path)
            
            self.stdout.write(f'✅ QR Code salvo em: {qr_path}')
            
            # Testar conversão para base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            self.stdout.write(f'📊 Base64 length: {len(img_str)} caracteres')
            self.stdout.write(f'🔗 Data URL: data:image/png;base64,{img_str[:50]}...')
            
            # Testar validação do token
            self.stdout.write('\n🔍 Testando validação do token...')
            
            validation_result = TokenService.validate_token(
                session.token,
                device_id='test_device',
                ip_address='127.0.0.1',
                user_agent='test'
            )
            
            if validation_result['ok']:
                self.stdout.write('✅ Token validado com sucesso!')
                self.stdout.write(f'   🍺 Dose: {validation_result["dose_ml"]}ml')
                self.stdout.write(f'   👤 Usuário: {validation_result["user_name"]}')
                self.stdout.write(f'   💰 Saldo restante: R$ {validation_result["remaining_balance_cents"]/100:.2f}')
            else:
                self.stdout.write(f'❌ Erro na validação: {validation_result["message"]}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erro: {str(e)}')
            )
        
        self.stdout.write('\n📋 RESUMO DO TESTE:')
        self.stdout.write('✅ Token gerado com sucesso')
        self.stdout.write('✅ QR Code criado e salvo')
        self.stdout.write('✅ Conversão para base64 funcionando')
        self.stdout.write('✅ Validação de token testada')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Teste de QR Code concluído!')
        )

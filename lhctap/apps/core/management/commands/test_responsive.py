from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Testa a responsividade das páginas principais'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('📱 Testando responsividade das páginas...')
        )
        
        # Buscar usuário de teste
        try:
            user = User.objects.get(username='joao')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Usuário "joao" não encontrado. Execute: python manage.py create_test_data')
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
        
        # URLs para testar
        urls_to_test = [
            ('/dashboard/', 'Dashboard'),
            ('/dashboard/add-credits/', 'Sistema de Créditos'),
            ('/dashboard/statement/', 'Extrato'),
        ]
        
        for url, name in urls_to_test:
            try:
                response = client.get(url)
                if response.status_code == 200:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {name}: OK (Status {response.status_code})')
                    )
                    
                    # Verificar se tem viewport meta tag
                    content = response.content.decode('utf-8')
                    if 'viewport' in content:
                        self.stdout.write(f'   📱 Viewport meta tag: OK')
                    else:
                        self.stdout.write(
                            self.style.WARNING('   ⚠️  Viewport meta tag: Não encontrada')
                        )
                    
                    # Verificar se tem Bootstrap
                    if 'bootstrap' in content.lower():
                        self.stdout.write(f'   🎨 Bootstrap: OK')
                    else:
                        self.stdout.write(
                            self.style.WARNING('   ⚠️  Bootstrap: Não encontrado')
                        )
                    
                    # Verificar classes responsivas
                    responsive_classes = ['col-', 'col-sm-', 'col-md-', 'col-lg-', 'd-none', 'd-md-']
                    found_classes = [cls for cls in responsive_classes if cls in content]
                    if found_classes:
                        self.stdout.write(f'   📐 Classes responsivas: {len(found_classes)} encontradas')
                    else:
                        self.stdout.write(
                            self.style.WARNING('   ⚠️  Classes responsivas: Poucas encontradas')
                        )
                        
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {name}: Erro (Status {response.status_code})')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ {name}: Exceção - {str(e)}')
                )
        
        self.stdout.write('\n📋 RESUMO DOS TESTES:')
        self.stdout.write('✅ Páginas principais testadas')
        self.stdout.write('📱 Verificação de viewport realizada')
        self.stdout.write('🎨 Verificação de Bootstrap realizada')
        self.stdout.write('📐 Verificação de classes responsivas realizada')
        
        self.stdout.write('\n💡 DICAS PARA TESTE MANUAL:')
        self.stdout.write('1. Abra o navegador em modo responsivo (F12)')
        self.stdout.write('2. Teste em diferentes tamanhos: 320px, 768px, 1024px')
        self.stdout.write('3. Verifique se os botões são tocáveis (min 44px)')
        self.stdout.write('4. Teste a navegação em mobile')
        self.stdout.write('5. Verifique se o texto é legível')
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 Teste de responsividade concluído!')
        )

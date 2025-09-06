#!/usr/bin/env python3
"""
Script para executar migrações do Django manualmente
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lhctap.settings.development')
# Adicionar o diretório lhctap ao path para encontrar o módulo apps
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lhctap'))

try:
    django.setup()
    
    print("🔄 Executando migrações do Django...")
    
    # Executar migrações
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("✅ Migrações executadas com sucesso!")
    print("🎯 Banco de dados configurado e pronto para uso")
    
except Exception as e:
    print(f"❌ Erro nas migrações: {e}")
    sys.exit(1)

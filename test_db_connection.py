#!/usr/bin/env python3
"""
Script para testar conexão com PostgreSQL
"""
import os
import sys
import django
from urllib.parse import urlparse

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lhctap.settings.development')
# Adicionar o diretório lhctap ao path para encontrar o módulo apps
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lhctap'))

try:
    django.setup()
    from django.db import connection
    
    print("🔍 Testando conexão com PostgreSQL...")
    print("📊 String de conexão: postgresql://casaos:casaos@192.168.0.48:32769/lhctap")
    
    # Testar conexão
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Conexão bem-sucedida!")
        print(f"📋 Versão do PostgreSQL: {version[0]}")
        
        # Testar criação de tabela
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_connection (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("INSERT INTO test_connection (message) VALUES (%s);", ["Teste de conexão LHC Tap"])
        cursor.execute("SELECT * FROM test_connection ORDER BY id DESC LIMIT 1;")
        result = cursor.fetchone()
        
        print(f"✅ Teste de escrita/leitura bem-sucedido!")
        print(f"📝 Registro criado: ID {result[0]}, Mensagem: {result[1]}")
        
        # Limpar tabela de teste
        cursor.execute("DROP TABLE test_connection;")
        print("🧹 Tabela de teste removida")
        
except Exception as e:
    print(f"❌ Erro na conexão: {e}")
    sys.exit(1)

print("\n🎉 Banco de dados configurado e funcionando!")
print("🚀 Pronto para executar migrações do Django")

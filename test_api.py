#!/usr/bin/env python3
"""
Script de teste para API de validação de dispositivos
Uso: python test_api.py [device_id] [tap_id]
Exemplo: python test_api.py "Card UID: 3A B4 B5 1" 3
"""

import requests
import json
import sys

API_BASE = "http://127.0.0.1:8000/api/tap"

# Valores padrão (dispositivos e taps disponíveis)
DEVICE_ID = sys.argv[1] if len(sys.argv) > 1 else "Card UID: 3A B4 B5 1"
TAP_ID = int(sys.argv[2]) if len(sys.argv) > 2 else 3

API_URL = f"{API_BASE}/{TAP_ID}/"

print("🧪 Testando API de Validação")
print("=" * 50)
print(f"Device ID: {DEVICE_ID}")
print(f"Tap ID: {TAP_ID}")
print(f"URL: {API_URL}")
print()

try:
    # POST request com device_id no body
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "device_id": DEVICE_ID
    }
    
    response = requests.post(API_URL, headers=headers, json=data)
    
    print(f"Status HTTP: {response.status_code}")
    print()
    print("Resposta:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code == 200 and response.json().get('liberado'):
        print()
        print("✅ LIBERADO! O tap pode ser usado.")
    else:
        print()
        print("❌ NÃO LIBERADO! O tap não pode ser usado.")
        
except requests.exceptions.ConnectionError:
    print("❌ Erro: Não foi possível conectar ao servidor.")
    print("   Certifique-se de que o servidor Django está rodando:")
    print("   python manage.py runserver")
except Exception as e:
    print(f"❌ Erro: {e}")


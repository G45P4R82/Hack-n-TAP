#!/bin/bash

# Script de teste para API de validação de dispositivos
# Uso: ./test_api.sh <device_id> <tap_id>
# Exemplo: ./test_api.sh "Card UID: 3A B4 B5 1" 3

API_URL="http://127.0.0.1:8000/api/tap"
DEVICE_ID="${1:-Card UID: 3A B4 B5 1}"
TAP_ID="${2:-3}"

echo "🧪 Testando API de Validação"
echo "================================"
echo "Device ID: $DEVICE_ID"
echo "Tap ID: $TAP_ID"
echo "URL: $API_URL/$TAP_ID/"
echo ""

curl -X POST "$API_URL/$TAP_ID/" \
  -H "Content-Type: application/json" \
  -d "{\"device_id\": \"$DEVICE_ID\"}" \
  -w "\n\nHTTP Status: %{http_code}\n"


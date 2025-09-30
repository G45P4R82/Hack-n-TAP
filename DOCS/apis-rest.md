# 🔧 APIs REST - LHC Tap System

## 🎯 Visão Geral

O sistema oferece APIs REST para integração com dispositivos leitores de QR code e monitoramento do sistema. As APIs são otimizadas para alta performance, segurança e confiabilidade em ambiente de produção.

## 🔑 Endpoint Crítico: Validação de Token

### POST `/api/tap/validate/`

**Descrição:** Endpoint principal para validação de tokens QR por dispositivos leitores.

**Headers Obrigatórios:**
```
Content-Type: application/json
X-Device-ID: device_001
```

**Request Body:**
```json
{
    "token": "abc123...",
    "device_id": "device_001"
}
```

**Resposta de Sucesso (200):**
```json
{
    "ok": true,
    "dose_ml": 300,
    "user_name": "João Silva",
    "tap_name": "Chope 01",
    "remaining_balance_cents": 2500,
    "transaction_id": 12345
}
```

**Respostas de Erro:**

**Token Expirado (400):**
```json
{
    "ok": false,
    "error": "expired",
    "message": "Token expirado"
}
```

**Token Já Utilizado (400):**
```json
{
    "ok": false,
    "error": "used",
    "message": "Token já foi utilizado"
}
```

**Saldo Insuficiente (400):**
```json
{
    "ok": false,
    "message": "Saldo insuficiente"
}
```

**Token Não Encontrado (400):**
```json
{
    "ok": false,
    "error": "not_found",
    "message": "Token não encontrado"
}
```

**Rate Limit Excedido (429):**
```json
{
    "ok": false,
    "error": "rate_limited",
    "message": "Rate limit excedido",
    "retry_after": 60
}
```

**Tap Inativo (400):**
```json
{
    "ok": false,
    "error": "tap_inactive",
    "message": "Tap temporariamente indisponível"
}
```

**Erro Interno (500):**
```json
{
    "ok": false,
    "error": "internal_error",
    "message": "Erro interno do servidor"
}
```

### Características de Segurança

**Rate Limiting:**
- 10 validações por minuto por device_id
- 100 validações por hora por IP
- Headers de retry-after em caso de limite

**Validações:**
- Device ID obrigatório no header
- Consistência entre header e body
- Verificação de saldo com lock de banco
- Transações atômicas

**Auditoria:**
- Todas as tentativas são registradas
- Informações de IP e User-Agent
- Timestamp preciso de cada validação

## 📊 Endpoint de Status

### GET `/api/tap/{tap_id}/status/`

**Descrição:** Verifica status operacional de um tap específico.

**Request:**
```http
GET /api/tap/1/status/
```

**Resposta de Sucesso (200):**
```json
{
    "tap_id": 1,
    "name": "Chope 01",
    "is_active": true,
    "dose_ml": 300,
    "price_cents": 1000,
    "last_transaction": "2025-09-06T14:30:00Z",
    "transactions_today": 45
}
```

**Resposta de Erro (404):**
```json
{
    "error": "tap_not_found",
    "message": "Tap não encontrado ou inativo"
}
```

**Características:**
- Cache: `never_cache` para dados sempre atualizados
- Informações de última transação
- Contador de transações do dia
- Status de disponibilidade

## 🏥 Health Check

### GET `/health/`

**Descrição:** Endpoint para monitoramento de saúde do sistema.

**Request:**
```http
GET /health/
```

**Resposta de Sucesso (200):**
```json
{
    "status": "healthy",
    "timestamp": "2025-09-06T14:30:00Z",
    "database": "connected",
    "version": "1.0.0"
}
```

**Resposta de Erro (503):**
```json
{
    "status": "unhealthy",
    "timestamp": "2025-09-06T14:30:00Z",
    "error": "Database connection failed"
}
```

**Características:**
- Verificação de conexão com banco
- Timestamp ISO 8601
- Versionamento do sistema
- Ideal para load balancers

## 🎫 Geração de Token (Web)

### POST `/dashboard/generate-token/`

**Descrição:** Gera token QR para consumo (endpoint web).

**Headers:**
```
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: csrf_token
```

**Request Body:**
```
tap_id=1
```

**Resposta de Sucesso (200):**
```json
{
    "token": "abc123...",
    "expires_at": "2025-09-06T14:30:30Z",
    "tap_name": "Chope 01",
    "dose_ml": 300,
    "price_cents": 1000
}
```

**Respostas de Erro:**

**Tap Não Encontrado (404):**
```json
{
    "error": "Tap não encontrado ou inativo"
}
```

**Saldo Insuficiente (400):**
```json
{
    "error": "Saldo insuficiente",
    "required": 1000,
    "available": 500
}
```

### Geração de QR Code

### GET `/dashboard/qr-image/{token}/`

**Descrição:** Gera imagem do QR code para um token específico.

**Request:**
```http
GET /dashboard/qr-image/abc123.../
```

**Resposta de Sucesso (200):**
```json
{
    "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "token": "abc123...",
    "expires_at": "2025-09-06T14:30:30Z"
}
```

**Resposta de Erro (404):**
```json
{
    "error": "Token não encontrado"
}
```

**Resposta de Erro (410):**
```json
{
    "error": "Token expirado"
}
```

## 🔒 Segurança e Rate Limiting

### Rate Limiting por Device ID

**Configuração:**
```python
@ratelimit(key='header:X-Device-ID', rate='10/m', method='POST')
def validate_token(request):
    # 10 validações por minuto por device_id
```

**Headers de Resposta:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1630934400
```

### Rate Limiting por IP

**Configuração:**
```python
@ratelimit(key='ip', rate='100/h', method='POST')
def validate_token(request):
    # 100 validações por hora por IP
```

### Validação de Device ID

**Requisitos:**
- Device ID obrigatório no header `X-Device-ID`
- Consistência entre header e body da requisição
- Formato alfanumérico (recomendado: `device_001`, `reader_01`)

**Exemplo de Validação:**
```python
device_id = request.META.get('HTTP_X_DEVICE_ID')
device_id_from_body = data.get('device_id')

if device_id != device_id_from_body:
    return JsonResponse({
        'ok': False,
        'error': 'device_id_mismatch',
        'message': 'Device ID inconsistente'
    }, status=400)
```

## 📝 Logs e Auditoria

### Estrutura de Logs

**Log de Validação:**
```json
{
    "timestamp": "2025-09-06T14:30:00Z",
    "device_id": "device_001",
    "token": "abc123...",
    "result": "ok",
    "user_id": 123,
    "tap_id": 1,
    "ip_address": "192.168.1.100",
    "user_agent": "LHC-Reader/1.0",
    "response_time_ms": 45
}
```

**Log de Erro:**
```json
{
    "timestamp": "2025-09-06T14:30:00Z",
    "device_id": "device_001",
    "token": "expired_token",
    "result": "expired",
    "user_id": null,
    "tap_id": null,
    "ip_address": "192.168.1.100",
    "user_agent": "LHC-Reader/1.0",
    "response_time_ms": 12
}
```

### Métricas de Auditoria

**Taxa de Sucesso:**
```python
success_rate = successful_validations / total_validations * 100
```

**Dispositivos Suspeitos:**
```python
suspicious_devices = devices_with_error_rate > 50%
```

**Padrões de Uso:**
- Horários de pico
- Taps mais utilizados
- Usuários mais ativos
- Tentativas de fraude

## 🚀 Performance e Otimização

### Otimizações de Banco

**Select for Update:**
```python
wallet = Wallet.objects.select_for_update().get(user=user)
```

**Índices Otimizados:**
- Token (único)
- Device ID + timestamp
- Status + expiração

**Transações Atômicas:**
```python
@transaction.atomic
def validate_token(token, device_id):
    # Operações atômicas garantem consistência
```

### Cache Strategy

**Cache de Status de Tap:**
```python
@never_cache
def tap_status(request, tap_id):
    # Sempre dados frescos para status operacional
```

**Cache de Health Check:**
```python
# Health check sem cache para monitoramento real-time
```

### Timeout e Retry

**Configurações Recomendadas:**
- Timeout de requisição: 5 segundos
- Retry em caso de erro 5xx: 3 tentativas
- Backoff exponencial: 1s, 2s, 4s

## 🔧 Integração com Hardware

### Exemplo de Integração

**Python Client:**
```python
import requests
import time

class LHCTapClient:
    def __init__(self, base_url, device_id):
        self.base_url = base_url
        self.device_id = device_id
    
    def validate_token(self, token):
        headers = {
            'Content-Type': 'application/json',
            'X-Device-ID': self.device_id
        }
        
        data = {
            'token': token,
            'device_id': self.device_id
        }
        
        response = requests.post(
            f"{self.base_url}/api/tap/validate/",
            json=data,
            headers=headers,
            timeout=5
        )
        
        return response.json()
    
    def get_tap_status(self, tap_id):
        response = requests.get(
            f"{self.base_url}/api/tap/{tap_id}/status/",
            timeout=3
        )
        return response.json()

# Uso
client = LHCTapClient("http://localhost:8000", "device_001")
result = client.validate_token("abc123...")

if result['ok']:
    print(f"Sucesso! Dose: {result['dose_ml']}ml")
    print(f"Usuário: {result['user_name']}")
    print(f"Saldo restante: R$ {result['remaining_balance_cents']/100:.2f}")
else:
    print(f"Erro: {result['message']}")
```

**JavaScript Client:**
```javascript
class LHCTapClient {
    constructor(baseUrl, deviceId) {
        this.baseUrl = baseUrl;
        this.deviceId = deviceId;
    }
    
    async validateToken(token) {
        const response = await fetch(`${this.baseUrl}/api/tap/validate/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Device-ID': this.deviceId
            },
            body: JSON.stringify({
                token: token,
                device_id: this.deviceId
            })
        });
        
        return await response.json();
    }
    
    async getTapStatus(tapId) {
        const response = await fetch(`${this.baseUrl}/api/tap/${tapId}/status/`);
        return await response.json();
    }
}

// Uso
const client = new LHCTapClient('http://localhost:8000', 'device_001');
const result = await client.validateToken('abc123...');

if (result.ok) {
    console.log(`Sucesso! Dose: ${result.dose_ml}ml`);
    console.log(`Usuário: ${result.user_name}`);
    console.log(`Saldo restante: R$ ${(result.remaining_balance_cents/100).toFixed(2)}`);
} else {
    console.log(`Erro: ${result.message}`);
}
```

## 📊 Monitoramento e Alertas

### Métricas Importantes

**Disponibilidade:**
- Uptime do endpoint de validação
- Tempo de resposta médio
- Taxa de erro 5xx

**Performance:**
- Transações por minuto
- Tempo de processamento
- Throughput de validações

**Segurança:**
- Tentativas de fraude
- Rate limits atingidos
- Dispositivos suspeitos

### Alertas Recomendados

**Críticos:**
- Endpoint de validação indisponível
- Taxa de erro > 5%
- Tempo de resposta > 2s

**Importantes:**
- Rate limit atingido
- Dispositivo com alta taxa de erro
- Saldo insuficiente frequente

**Informativos:**
- Pico de uso
- Novo dispositivo detectado
- Limpeza de tokens executada

## 🧪 Testes de API

### Testes Automatizados

**Teste de Validação:**
```python
def test_validate_token_success():
    response = client.post('/api/tap/validate/', {
        'token': 'valid_token',
        'device_id': 'test_device'
    }, HTTP_X_DEVICE_ID='test_device')
    
    assert response.status_code == 200
    assert response.json()['ok'] == True
    assert 'dose_ml' in response.json()
```

**Teste de Rate Limiting:**
```python
def test_rate_limit():
    for i in range(11):  # Exceder limite de 10/min
        response = client.post('/api/tap/validate/', {
            'token': f'token_{i}',
            'device_id': 'test_device'
        }, HTTP_X_DEVICE_ID='test_device')
    
    assert response.status_code == 429
    assert 'rate_limited' in response.json()['error']
```

### Testes de Carga

**Ferramentas Recomendadas:**
- Apache Bench (ab)
- wrk
- Artillery
- Locust

**Cenários de Teste:**
- Validação normal (100 req/s)
- Pico de uso (500 req/s)
- Rate limiting (1000 req/s)
- Stress test (2000 req/s)

## 🔄 Versionamento e Compatibilidade

### Versionamento de API

**Estratégia:**
- Versionamento por URL: `/api/v1/tap/validate/`
- Backward compatibility por 6 meses
- Deprecation warnings em headers
- Migration guide para breaking changes

**Headers de Versionamento:**
```
API-Version: 1.0
API-Deprecated: false
API-Sunset: 2025-12-31
```

### Compatibilidade

**Clientes Suportados:**
- Python 3.8+
- Node.js 14+
- C# .NET 5+
- Java 11+

**Protocolos:**
- HTTP/1.1
- HTTP/2 (recomendado)
- HTTPS obrigatório em produção

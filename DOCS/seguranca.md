# 🔒 Segurança - LHC Tap System

## 🎯 Visão Geral

O LHC Tap System implementa múltiplas camadas de segurança para proteger contra fraudes, ataques e uso indevido. A arquitetura de segurança é baseada em princípios de "defesa em profundidade" com validações em múltiplos níveis.

## 🛡️ Camadas de Segurança

### 1. Autenticação e Autorização

#### Sistema de Usuários
- **Autenticação:** Django Auth Framework
- **Sessões:** Cookies seguros com HttpOnly
- **CSRF Protection:** Tokens em todas as requisições
- **Login Required:** Decorators em todas as views protegidas

#### Roles e Permissões
```python
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('member', 'Membro'),
        ('admin', 'Administrador'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    
    def is_admin(self):
        return self.role == 'admin'
```

**Controle de Acesso:**
- Membros: Acesso ao dashboard e funcionalidades básicas
- Administradores: Acesso completo + Django Admin
- Verificação de permissões em todas as operações críticas

### 2. Rate Limiting

#### Rate Limiting por Device ID
```python
@ratelimit(key='header:X-Device-ID', rate='10/m', method='POST')
def validate_token(request):
    # 10 validações por minuto por device_id
```

**Configurações:**
- **Device ID:** 10 validações/minuto
- **IP Address:** 100 validações/hora
- **Global:** 1000 validações/hora (configurável)

#### Implementação Customizada
```python
class RateLimitService:
    @staticmethod
    def check_device_rate_limit(device_id, window_minutes=1, max_requests=10):
        window_start = timezone.now() - timedelta(minutes=window_minutes)
        
        recent_attempts = TapValidationAudit.objects.filter(
            device_id=device_id,
            created_at__gte=window_start
        ).count()
        
        return recent_attempts < max_requests
```

**Headers de Resposta:**
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1630934400
Retry-After: 60
```

### 3. Validação de Tokens

#### Geração Segura de Tokens
```python
import secrets

class TokenService:
    @staticmethod
    def generate_secure_token(length=32):
        """Gera token criptograficamente seguro"""
        return secrets.token_urlsafe(length)
```

**Características:**
- **Algoritmo:** `secrets.token_urlsafe()` (cryptographically secure)
- **Tamanho:** 32 bytes (256 bits)
- **Entropia:** ~43 caracteres URL-safe
- **Unicidade:** Verificação de duplicatas no banco

#### Expiração e Invalidação
```python
class TapSession(models.Model):
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    def is_expired(self):
        return timezone.now() > self.expires_at
```

**Regras de Expiração:**
- **Tempo de Vida:** 30 segundos (configurável)
- **Invalidação:** Automática após uso
- **Limpeza:** Comando de limpeza diária
- **Verificação:** Em todas as validações

### 4. Transações Atômicas

#### Locks de Banco de Dados
```python
@transaction.atomic
def process_consumption(user, tap, session):
    # Lock da carteira para evitar race conditions
    wallet = Wallet.objects.select_for_update().get(user=user)
    
    # Verificação de saldo com lock
    if wallet.balance_cents < tap.price_cents:
        raise InsufficientBalanceError()
    
    # Débito atômico
    wallet.balance_cents -= tap.price_cents
    wallet.save()
    
    # Registro da transação
    transaction_record = Transaction.objects.create(...)
    
    return transaction_record
```

**Proteções:**
- **Select for Update:** Locks pessimistas
- **Atomic Transactions:** Rollback automático em caso de erro
- **Constraint Checks:** Validações no nível de banco
- **Deadlock Prevention:** Ordem consistente de locks

### 5. Auditoria Completa

#### Modelo de Auditoria
```python
class TapValidationAudit(models.Model):
    RESULT_CHOICES = [
        ('ok', 'Sucesso'),
        ('expired', 'Token Expirado'),
        ('used', 'Token Já Utilizado'),
        ('insufficient', 'Saldo Insuficiente'),
        ('not_found', 'Token Não Encontrado'),
        ('rate_limited', 'Rate Limit Excedido'),
        ('tap_inactive', 'Tap Inativo'),
    ]
    
    device_id = models.CharField(max_length=64)
    token = models.CharField(max_length=64)
    result = models.CharField(max_length=16, choices=RESULT_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tap = models.ForeignKey(Tap, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**Dados Coletados:**
- **Device ID:** Identificação do dispositivo leitor
- **Token:** Token validado (para rastreamento)
- **Resultado:** Sucesso ou tipo de erro
- **Usuário/Tap:** Relacionamentos (nullable para erros)
- **IP Address:** Endereço de origem
- **User Agent:** Informações do dispositivo
- **Timestamp:** Momento exato da validação

#### Análise de Padrões Suspeitos
```python
@staticmethod
def get_suspicious_devices(days=1, error_threshold=0.5):
    """Identifica dispositivos com alta taxa de erro"""
    since = timezone.now() - timedelta(days=days)
    
    device_stats = TapValidationAudit.objects.filter(
        created_at__gte=since
    ).values('device_id').annotate(
        total_attempts=models.Count('id'),
        error_count=models.Count('id', filter=~models.Q(result='ok'))
    ).annotate(
        error_rate=models.Case(
            models.When(total_attempts=0, then=0),
            default=models.F('error_count') * 100.0 / models.F('total_attempts')
        )
    ).filter(
        total_attempts__gte=5,  # mínimo de tentativas
        error_rate__gte=error_threshold * 100
    ).order_by('-error_rate')
    
    return device_stats
```

### 6. Validação de Entrada

#### Sanitização de Dados
```python
def validate_token(request):
    # Verificar headers obrigatórios
    device_id = request.META.get('HTTP_X_DEVICE_ID')
    if not device_id:
        return JsonResponse({
            'ok': False,
            'error': 'missing_device_id',
            'message': 'Header X-Device-ID é obrigatório'
        }, status=400)
    
    # Validar JSON
    try:
        data = json.loads(request.body)
        token = data.get('token')
        device_id_from_body = data.get('device_id')
    except json.JSONDecodeError:
        return JsonResponse({
            'ok': False,
            'error': 'invalid_json',
            'message': 'JSON inválido'
        }, status=400)
    
    # Verificar parâmetros obrigatórios
    if not token or not device_id_from_body:
        return JsonResponse({
            'ok': False,
            'error': 'missing_parameters',
            'message': 'Token e device_id são obrigatórios'
        }, status=400)
```

**Validações:**
- **Headers Obrigatórios:** X-Device-ID
- **JSON Válido:** Parsing seguro
- **Parâmetros Obrigatórios:** Token e device_id
- **Consistência:** Device ID entre header e body
- **Formato:** Validação de tipos e tamanhos

### 7. Headers de Segurança

#### Configuração de Headers
```python
# settings/base.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

**Headers Implementados:**
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

### 8. Middleware de Segurança

#### Audit Middleware
```python
class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Log de requisições suspeitas
        if self.is_suspicious_request(request):
            self.log_suspicious_activity(request)
        
        response = self.get_response(request)
        return response
    
    def is_suspicious_request(self, request):
        # Verificar padrões suspeitos
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ip_address = self.get_client_ip(request)
        
        # Verificar user agents suspeitos
        suspicious_agents = ['bot', 'crawler', 'scanner']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            return True
        
        # Verificar IPs suspeitos (implementar blacklist)
        if self.is_blacklisted_ip(ip_address):
            return True
        
        return False
```

## 🚨 Detecção de Ameaças

### 1. Análise de Comportamento

#### Padrões de Uso Anômalos
```python
def detect_anomalous_patterns():
    """Detecta padrões de uso anômalos"""
    
    # Dispositivos com alta taxa de erro
    suspicious_devices = RateLimitService.get_suspicious_devices()
    
    # Tentativas de validação em horários suspeitos
    night_attempts = TapValidationAudit.objects.filter(
        created_at__hour__in=[0, 1, 2, 3, 4, 5],
        result__in=['not_found', 'expired']
    ).count()
    
    # Múltiplos tokens do mesmo usuário em sequência
    rapid_attempts = TapValidationAudit.objects.filter(
        created_at__gte=timezone.now() - timedelta(minutes=1)
    ).values('user').annotate(
        count=models.Count('id')
    ).filter(count__gt=5)
    
    return {
        'suspicious_devices': suspicious_devices,
        'night_attempts': night_attempts,
        'rapid_attempts': rapid_attempts
    }
```

### 2. Monitoramento em Tempo Real

#### Alertas de Segurança
```python
def check_security_alerts():
    """Verifica alertas de segurança"""
    alerts = []
    
    # Rate limit excedido
    recent_rate_limits = TapValidationAudit.objects.filter(
        result='rate_limited',
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if recent_rate_limits > 10:
        alerts.append({
            'type': 'rate_limit_spike',
            'message': f'{recent_rate_limits} rate limits na última hora',
            'severity': 'high'
        })
    
    # Tentativas de fraude
    fraud_attempts = TapValidationAudit.objects.filter(
        result__in=['not_found', 'expired'],
        created_at__gte=timezone.now() - timedelta(hours=1)
    ).count()
    
    if fraud_attempts > 50:
        alerts.append({
            'type': 'fraud_attempts',
            'message': f'{fraud_attempts} tentativas de fraude na última hora',
            'severity': 'critical'
        })
    
    return alerts
```

### 3. Blacklist de Dispositivos

#### Sistema de Blacklist
```python
class DeviceBlacklist(models.Model):
    device_id = models.CharField(max_length=64, unique=True)
    reason = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'device_blacklist'

def is_device_blacklisted(device_id):
    """Verifica se dispositivo está na blacklist"""
    return DeviceBlacklist.objects.filter(
        device_id=device_id,
        is_active=True,
        expires_at__gt=timezone.now()
    ).exists()
```

## 🔐 Criptografia e Hash

### 1. Tokens Seguros

#### Geração Criptográfica
```python
import secrets
import hashlib

class TokenService:
    @staticmethod
    def generate_secure_token(length=32):
        """Gera token criptograficamente seguro"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def hash_token(token):
        """Hash do token para armazenamento (se necessário)"""
        return hashlib.sha256(token.encode()).hexdigest()
```

### 2. Senhas e Autenticação

#### Configuração de Senhas
```python
# settings/base.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Configurações de sessão
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_COOKIE_SECURE = True  # HTTPS apenas
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
```

## 🛠️ Ferramentas de Segurança

### 1. Comandos de Segurança

#### Limpeza de Dados Sensíveis
```python
# management/commands/cleanup_security.py
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=90)
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Limpar auditoria antiga
        cutoff_date = timezone.now() - timedelta(days=days)
        old_audits = TapValidationAudit.objects.filter(
            created_at__lt=cutoff_date
        )
        
        if dry_run:
            self.stdout.write(f'Removeria {old_audits.count()} registros de auditoria')
        else:
            deleted_count = old_audits.delete()[0]
            self.stdout.write(f'Removidos {deleted_count} registros de auditoria')
```

#### Análise de Segurança
```python
# management/commands/security_audit.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Análise de dispositivos suspeitos
        suspicious_devices = RateLimitService.get_suspicious_devices()
        
        # Análise de padrões anômalos
        anomalies = detect_anomalous_patterns()
        
        # Relatório de segurança
        self.stdout.write("=== RELATÓRIO DE SEGURANÇA ===")
        self.stdout.write(f"Dispositivos suspeitos: {len(suspicious_devices)}")
        self.stdout.write(f"Tentativas noturnas: {anomalies['night_attempts']}")
        self.stdout.write(f"Tentativas rápidas: {len(anomalies['rapid_attempts'])}")
```

### 2. Monitoramento e Alertas

#### Logs de Segurança
```python
import logging

security_logger = logging.getLogger('lhctap.security')

def log_security_event(event_type, details):
    """Log de eventos de segurança"""
    security_logger.warning(f"Security Event: {event_type} - {details}")

# Uso
log_security_event('rate_limit_exceeded', {
    'device_id': device_id,
    'ip_address': ip_address,
    'attempts': attempt_count
})
```

#### Alertas por Email
```python
from django.core.mail import send_mail
from django.conf import settings

def send_security_alert(alert_type, details):
    """Envia alerta de segurança por email"""
    subject = f"[LHC Tap] Alerta de Segurança: {alert_type}"
    message = f"""
    Tipo: {alert_type}
    Detalhes: {details}
    Timestamp: {timezone.now()}
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        settings.SECURITY_ALERT_EMAILS,
        fail_silently=False,
    )
```

## 📊 Métricas de Segurança

### 1. KPIs de Segurança

#### Métricas Principais
- **Taxa de Sucesso:** % de validações bem-sucedidas
- **Rate Limit Hits:** Número de rate limits atingidos
- **Tentativas de Fraude:** Tokens inválidos/expirados
- **Dispositivos Suspeitos:** Dispositivos com alta taxa de erro
- **Tempo de Resposta:** Latência das validações

#### Dashboard de Segurança
```python
def get_security_metrics(days=7):
    """Métricas de segurança para dashboard"""
    since = timezone.now() - timedelta(days=days)
    
    total_validations = TapValidationAudit.objects.filter(
        created_at__gte=since
    ).count()
    
    successful_validations = TapValidationAudit.objects.filter(
        created_at__gte=since,
        result='ok'
    ).count()
    
    rate_limits = TapValidationAudit.objects.filter(
        created_at__gte=since,
        result='rate_limited'
    ).count()
    
    fraud_attempts = TapValidationAudit.objects.filter(
        created_at__gte=since,
        result__in=['not_found', 'expired']
    ).count()
    
    return {
        'total_validations': total_validations,
        'success_rate': (successful_validations / total_validations * 100) if total_validations > 0 else 0,
        'rate_limits': rate_limits,
        'fraud_attempts': fraud_attempts,
        'suspicious_devices': len(RateLimitService.get_suspicious_devices(days))
    }
```

### 2. Relatórios de Segurança

#### Relatório Diário
```python
def generate_daily_security_report():
    """Gera relatório diário de segurança"""
    yesterday = timezone.now() - timedelta(days=1)
    
    metrics = get_security_metrics(days=1)
    anomalies = detect_anomalous_patterns()
    
    report = {
        'date': yesterday.date(),
        'metrics': metrics,
        'anomalies': anomalies,
        'alerts': check_security_alerts()
    }
    
    return report
```

## 🔄 Atualizações de Segurança

### 1. Processo de Atualização

#### Checklist de Segurança
- [ ] Atualizar dependências
- [ ] Revisar logs de segurança
- [ ] Testar rate limiting
- [ ] Verificar headers de segurança
- [ ] Validar transações atômicas
- [ ] Testar cenários de fraude

#### Testes de Segurança
```python
def test_security_scenarios():
    """Testes de cenários de segurança"""
    
    # Teste de rate limiting
    for i in range(11):
        response = client.post('/api/tap/validate/', {
            'token': f'token_{i}',
            'device_id': 'test_device'
        }, HTTP_X_DEVICE_ID='test_device')
    
    assert response.status_code == 429
    
    # Teste de token expirado
    expired_token = create_expired_token()
    response = client.post('/api/tap/validate/', {
        'token': expired_token,
        'device_id': 'test_device'
    }, HTTP_X_DEVICE_ID='test_device')
    
    assert response.json()['error'] == 'expired'
```

### 2. Monitoramento Contínuo

#### Health Checks de Segurança
```python
def security_health_check():
    """Health check específico de segurança"""
    checks = {
        'rate_limiting': check_rate_limiting(),
        'audit_logging': check_audit_logging(),
        'token_generation': check_token_generation(),
        'database_locks': check_database_locks()
    }
    
    return {
        'status': 'healthy' if all(checks.values()) else 'unhealthy',
        'checks': checks,
        'timestamp': timezone.now().isoformat()
    }
```

## 📋 Políticas de Segurança

### 1. Política de Retenção

#### Dados de Auditoria
- **Período:** 90 dias (configurável)
- **Backup:** Backup antes da limpeza
- **Análise:** Análise de tendências antes da remoção
- **Compliance:** Conformidade com LGPD

#### Tokens e Sessões
- **Tokens Expirados:** 7 dias
- **Sessões Utilizadas:** Permanente
- **Sessões Pendentes:** Limpeza automática

### 2. Política de Acesso

#### Controle de Acesso
- **Princípio do Menor Privilégio:** Acesso mínimo necessário
- **Separação de Funções:** Admin vs Member
- **Auditoria de Acesso:** Log de todas as operações
- **Rotação de Credenciais:** Senhas com expiração

#### Dispositivos
- **Registro Obrigatório:** Device ID único
- **Monitoramento:** Análise contínua de comportamento
- **Blacklist:** Bloqueio de dispositivos suspeitos
- **Whitelist:** Lista de dispositivos confiáveis (futuro)

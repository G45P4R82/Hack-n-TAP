# Especificação Técnica Refinada: Sistema de Controle de Consumo em Taps

**Versão:** 1.0  
**Data:** 06 de setembro de 2025  
**Autor:** Manus AI  
**Stack Principal:** Django + PostgreSQL + Bootstrap + anime.js

## Resumo Executivo

Este documento apresenta uma especificação técnica refinada para o desenvolvimento de um MVP (Minimum Viable Product) de controle de consumo em taps de chope e mate utilizando sistema de créditos e validação por QR dinâmico. O sistema será construído com Django como framework backend, PostgreSQL como banco de dados, e uma interface web responsiva utilizando Bootstrap e anime.js para microanimações.

O objetivo principal é criar uma solução robusta, escalável e segura que permita o controle automatizado de consumo através de tokens QR descartáveis, com validação em tempo real por dispositivos leitores (Raspberry Pi) instalados nos taps. O sistema deve garantir transações atômicas, auditoria completa e prevenção contra fraudes através de rate limiting e tokens de uso único com expiração curta.

## Arquitetura Técnica Detalhada

### Stack Tecnológica Definida

**Backend Framework:** Django 4.2+ com as seguintes características específicas:
- Utilização do sistema de templates nativo do Django (não Jinja2, mas Django Template Language)
- Django ORM para abstração de banco de dados
- Django Admin para interface administrativa
- Sistema de autenticação nativo do Django (django.contrib.auth)
- Middleware de CSRF habilitado para todas as views web
- API REST com @csrf_exempt apenas para endpoints específicos do leitor

**Banco de Dados:** PostgreSQL 14+ com configurações específicas:
- Timezone configurado para UTC
- Extensões necessárias: uuid-ossp (se necessário para tokens)
- Configuração de conexão: `postgresql://casaos:casaos@192.168.0.48:32769/lhctap`
- Índices otimizados para consultas frequentes
- Constraints de integridade referencial com CASCADE apropriado

**Frontend:** Interface web responsiva com:
- Bootstrap 5.x para componentes UI e grid system
- anime.js para microanimações e feedback visual
- JavaScript vanilla para interações dinâmicas
- QR Code generation via biblioteca JavaScript (qrcode.js)
- Countdown timer para expiração de tokens

**Segurança e Performance:**
- Rate limiting implementado via django-ratelimit
- Auditoria completa de todas as operações críticas
- Transações atômicas para operações financeiras
- Validação de entrada rigorosa em todos os endpoints
- Headers de segurança configurados (CSRF, XSS Protection, etc.)

### Arquitetura de Componentes

O sistema será estruturado em camadas bem definidas seguindo o padrão MVT (Model-View-Template) do Django:

**Camada de Modelos (Models):** Responsável pela definição das entidades de negócio e relacionamentos. Inclui UserProfile para extensão do modelo User nativo, Wallet para controle de créditos, Tap para cadastro de equipamentos, TapSession para tokens QR, Transaction para histórico financeiro e TapValidationAudit para logs de segurança.

**Camada de Views:** Dividida em views web (Class-Based Views para interface do usuário) e API views (Function-Based Views para endpoints REST). As views web utilizam mixins de autenticação e autorização, enquanto as API views implementam validação específica para dispositivos externos.

**Camada de Templates:** Templates Django responsivos com herança de template base, componentes reutilizáveis para cards de dashboard, formulários com validação client-side e componentes específicos para geração e exibição de QR codes.

**Camada de Serviços:** Classes de serviço para lógica de negócio complexa, incluindo TokenService para geração e validação de tokens, WalletService para operações financeiras, AuditService para logs de segurança e MetricsService para cálculos de KPIs administrativos.




## Especificação Detalhada dos Modelos Django

### Modelo UserProfile (apps/accounts/models.py)

O modelo UserProfile estende o sistema de usuários nativo do Django para incluir informações específicas do domínio de negócio. Este modelo mantém uma relação OneToOne com o modelo User padrão, permitindo a utilização completa do sistema de autenticação do Django enquanto adiciona campos customizados.

```python
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('member', 'Membro'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['role']),
        ]
```

**Características Técnicas:**
- Utiliza signal post_save para criação automática do profile ao criar usuário
- Implementa método `is_admin()` para verificação de permissões
- Relacionamento OneToOne garante integridade referencial
- Índice em 'role' para consultas de autorização eficientes

### Modelo Wallet (apps/wallet/models.py)

O modelo Wallet gerencia o saldo de créditos de cada usuário, implementando controles rigorosos para prevenir inconsistências financeiras. Todos os valores são armazenados em centavos para evitar problemas de precisão com números decimais.

```python
class Wallet(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance_cents = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance_cents__gte=0),
                name='positive_balance'
            )
        ]
```

**Métodos de Negócio:**
- `debit(amount_cents)`: Débito com validação de saldo suficiente
- `credit(amount_cents)`: Crédito com validação de valor positivo
- `get_balance_display()`: Formatação do saldo para exibição (R$ X,XX)
- `has_sufficient_balance(amount_cents)`: Verificação de saldo disponível

**Controles de Integridade:**
- CheckConstraint para garantir saldo não negativo
- Transações atômicas obrigatórias para todas as operações
- Logs automáticos de todas as alterações de saldo
- Validação de concorrência com select_for_update()

### Modelo Tap (apps/taps/models.py)

O modelo Tap representa os equipamentos físicos (chopeiras e mateiras) e suas configurações operacionais. Cada tap possui configurações específicas de dose e preço que são utilizadas nas validações de consumo.

```python
class Tap(models.Model):
    TYPE_CHOICES = [
        ('beer', 'Chope'),
        ('mate', 'Mate'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    location = models.CharField(max_length=120, blank=True, null=True)
    dose_ml = models.PositiveIntegerField(default=300)
    price_cents = models.PositiveIntegerField(default=1000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'taps'
        indexes = [
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['location']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(dose_ml__gt=0),
                name='positive_dose'
            ),
            models.CheckConstraint(
                check=models.Q(price_cents__gt=0),
                name='positive_price'
            )
        ]
```

**Funcionalidades Específicas:**
- Método `get_price_display()` para formatação monetária
- Método `is_available()` para verificar disponibilidade operacional
- Manager customizado `ActiveTapsManager` para filtrar taps ativos
- Validação de unicidade de nome case-insensitive
- Soft delete através do campo `is_active`

### Modelo TapSession (apps/taps/models.py)

O modelo TapSession gerencia os tokens QR dinâmicos, implementando o sistema de segurança baseado em tokens de uso único com expiração temporal. Este é o componente crítico para a segurança do sistema.

```python
class TapSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('used', 'Utilizado'),
        ('expired', 'Expirado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tap = models.ForeignKey(Tap, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tap_sessions'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'tap']),
            models.Index(fields=['expires_at']),
            models.Index(
                fields=['status'],
                condition=models.Q(status='pending'),
                name='pending_sessions_idx'
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(expires_at__gt=models.F('created_at')),
                name='valid_expiration'
            )
        ]
```

**Geração de Tokens:**
- Utiliza `secrets.token_urlsafe(32)` para tokens criptograficamente seguros
- Expiração padrão de 30 segundos configurável via settings
- Validação automática de expiração via método `is_expired()`
- Método `mark_as_used()` para transição atômica de status

**Segurança Implementada:**
- Tokens únicos com 256 bits de entropia
- Expiração temporal rigorosa
- Status imutável após uso
- Índice parcial para consultas eficientes de tokens pendentes
- Cleanup automático de tokens expirados via management command

### Modelo Transaction (apps/wallet/models.py)

O modelo Transaction implementa o sistema de extrato financeiro completo, registrando todas as movimentações de créditos com categorização automática e rastreabilidade completa.

```python
class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('beer', 'Chope'),
        ('mate', 'Mate'),
        ('topup', 'Recarga'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_cents = models.IntegerField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    volume_ml = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ref_session = models.ForeignKey(
        TapSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(category__in=['beer', 'mate'], amount_cents__lt=0, volume_ml__gt=0) |
                    models.Q(category='topup', amount_cents__gt=0, volume_ml=0)
                ),
                name='valid_transaction_type'
            )
        ]
```

**Lógica de Negócio:**
- Transações de consumo: `amount_cents` negativo, `volume_ml` positivo
- Transações de recarga: `amount_cents` positivo, `volume_ml` zero
- Categorização automática baseada no tipo do tap
- Referência opcional ao token utilizado para rastreabilidade
- Método `get_amount_display()` para formatação monetária com sinal

**Auditoria e Compliance:**
- Imutabilidade após criação (sem update/delete)
- Timestamp automático para ordenação cronológica
- Descrição opcional para contexto adicional
- Relacionamento com TapSession para auditoria completa
- Índices otimizados para consultas de extrato por usuário e período

### Modelo TapValidationAudit (apps/taps/models.py)

O modelo TapValidationAudit implementa o sistema de auditoria completo para todas as tentativas de validação de tokens, fornecendo rastreabilidade total e dados para análise de segurança.

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
    
    class Meta:
        db_table = 'tap_validations_audit'
        indexes = [
            models.Index(fields=['device_id', '-created_at']),
            models.Index(fields=['token']),
            models.Index(fields=['result', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
```

**Funcionalidades de Auditoria:**
- Registro de todas as tentativas de validação (sucesso e falha)
- Captura de metadados de segurança (IP, User-Agent, Device ID)
- Relacionamentos opcionais para preservar dados mesmo após exclusões
- Método `get_success_rate()` para cálculo de métricas de confiabilidade
- Cleanup automático de registros antigos (>90 dias) via management command

**Análise de Segurança:**
- Detecção de padrões suspeitos por device_id
- Análise de tentativas de força bruta
- Métricas de taxa de erro por período
- Identificação de tokens comprometidos
- Relatórios de dispositivos com comportamento anômalo


## Especificação de APIs e Endpoints

### API de Validação de Tokens (Endpoint Crítico)

**Endpoint:** `POST /api/tap/validate/`  
**Propósito:** Validação de tokens QR por dispositivos leitores nos taps  
**Autenticação:** API Key por device_id (sem CSRF para dispositivos externos)  
**Rate Limiting:** 10 requisições por minuto por device_id  

**Contrato de Entrada:**
```json
{
    "token": "string (64 chars, required)",
    "device_id": "string (max 64 chars, required)"
}
```

**Contratos de Resposta:**

**Sucesso (HTTP 200):**
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

**Erros Específicos (HTTP 400):**
```json
{
    "ok": false,
    "error": "expired|used|insufficient|not_found|rate_limited|tap_inactive",
    "message": "Descrição detalhada do erro",
    "retry_after": 60  // apenas para rate_limited
}
```

**Implementação da View:**
```python
@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='header:X-Device-ID', rate='10/m', method='POST')
def validate_token(request):
    try:
        data = json.loads(request.body)
        token = data.get('token')
        device_id = data.get('device_id')
        
        # Validação de entrada
        if not token or not device_id:
            return JsonResponse({
                'ok': False,
                'error': 'invalid_request',
                'message': 'Token e device_id são obrigatórios'
            }, status=400)
        
        # Busca e validação do token
        with transaction.atomic():
            try:
                session = TapSession.objects.select_for_update().get(
                    token=token,
                    status='pending'
                )
            except TapSession.DoesNotExist:
                audit_result = 'not_found'
                return error_response('not_found', 'Token não encontrado')
            
            # Verificação de expiração
            if session.is_expired():
                session.status = 'expired'
                session.save()
                audit_result = 'expired'
                return error_response('expired', 'Token expirado')
            
            # Verificação de saldo
            wallet = session.user.wallet
            if not wallet.has_sufficient_balance(session.tap.price_cents):
                audit_result = 'insufficient'
                return error_response('insufficient', 'Saldo insuficiente')
            
            # Verificação de tap ativo
            if not session.tap.is_active:
                audit_result = 'tap_inactive'
                return error_response('tap_inactive', 'Tap temporariamente indisponível')
            
            # Processamento da transação
            wallet.debit(session.tap.price_cents)
            
            transaction_record = Transaction.objects.create(
                user=session.user,
                amount_cents=-session.tap.price_cents,
                category=session.tap.type,
                volume_ml=session.tap.dose_ml,
                ref_session=session
            )
            
            session.status = 'used'
            session.used_at = timezone.now()
            session.save()
            
            audit_result = 'ok'
            
            return JsonResponse({
                'ok': True,
                'dose_ml': session.tap.dose_ml,
                'user_name': session.user.get_full_name() or session.user.username,
                'tap_name': session.tap.name,
                'remaining_balance_cents': wallet.balance_cents,
                'transaction_id': transaction_record.id
            })
            
    except Exception as e:
        audit_result = 'error'
        logger.error(f"Erro na validação de token: {e}")
        return JsonResponse({
            'ok': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor'
        }, status=500)
    
    finally:
        # Auditoria obrigatória
        TapValidationAudit.objects.create(
            device_id=device_id,
            token=token,
            result=audit_result,
            user=getattr(session, 'user', None),
            tap=getattr(session, 'tap', None),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
```

### API de Status do Tap (Healthcheck)

**Endpoint:** `GET /api/tap/<int:tap_id>/status/`  
**Propósito:** Verificação de status operacional do tap  
**Autenticação:** API Key por device_id  

**Resposta:**
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

### APIs Web para Interface do Usuário

**Geração de Token QR:**
**Endpoint:** `POST /dashboard/generate-token/`  
**Autenticação:** Login obrigatório  
**CSRF:** Habilitado  

```python
@login_required
@require_http_methods(["POST"])
def generate_token(request):
    tap_id = request.POST.get('tap_id')
    
    try:
        tap = Tap.objects.get(id=tap_id, is_active=True)
    except Tap.DoesNotExist:
        return JsonResponse({'error': 'Tap não encontrado'}, status=404)
    
    # Verificação de saldo
    if not request.user.wallet.has_sufficient_balance(tap.price_cents):
        return JsonResponse({
            'error': 'Saldo insuficiente',
            'required': tap.price_cents,
            'available': request.user.wallet.balance_cents
        }, status=400)
    
    # Invalidar tokens pendentes anteriores do mesmo usuário/tap
    TapSession.objects.filter(
        user=request.user,
        tap=tap,
        status='pending'
    ).update(status='expired')
    
    # Criar novo token
    session = TapSession.objects.create(
        user=request.user,
        tap=tap,
        token=generate_secure_token(),
        expires_at=timezone.now() + timedelta(seconds=30)
    )
    
    return JsonResponse({
        'token': session.token,
        'expires_at': session.expires_at.isoformat(),
        'tap_name': tap.name,
        'dose_ml': tap.dose_ml,
        'price_cents': tap.price_cents
    })
```

## Especificação de Serviços de Negócio

### TokenService (apps/taps/services.py)

O TokenService centraliza toda a lógica relacionada à geração, validação e gerenciamento de tokens QR, implementando as regras de segurança e expiração.

```python
class TokenService:
    TOKEN_EXPIRY_SECONDS = 30
    
    @staticmethod
    def generate_secure_token():
        """Gera token criptograficamente seguro"""
        return secrets.token_urlsafe(32)
    
    @classmethod
    def create_session(cls, user, tap):
        """Cria nova sessão de token para usuário e tap"""
        # Invalidar sessões pendentes anteriores
        cls.invalidate_pending_sessions(user, tap)
        
        return TapSession.objects.create(
            user=user,
            tap=tap,
            token=cls.generate_secure_token(),
            expires_at=timezone.now() + timedelta(seconds=cls.TOKEN_EXPIRY_SECONDS)
        )
    
    @staticmethod
    def invalidate_pending_sessions(user, tap):
        """Invalida sessões pendentes do usuário para o tap específico"""
        TapSession.objects.filter(
            user=user,
            tap=tap,
            status='pending'
        ).update(status='expired')
    
    @staticmethod
    def cleanup_expired_sessions():
        """Remove sessões expiradas (management command)"""
        expired_count = TapSession.objects.filter(
            expires_at__lt=timezone.now(),
            status='pending'
        ).update(status='expired')
        
        return expired_count
    
    @staticmethod
    def get_session_stats(days=30):
        """Estatísticas de sessões para dashboard admin"""
        since = timezone.now() - timedelta(days=days)
        
        return {
            'total_generated': TapSession.objects.filter(created_at__gte=since).count(),
            'successful_uses': TapSession.objects.filter(
                created_at__gte=since,
                status='used'
            ).count(),
            'expired_unused': TapSession.objects.filter(
                created_at__gte=since,
                status='expired'
            ).count()
        }
```

### WalletService (apps/wallet/services.py)

O WalletService gerencia todas as operações financeiras, garantindo consistência transacional e auditoria completa.

```python
class WalletService:
    
    @staticmethod
    @transaction.atomic
    def process_consumption(user, tap, session):
        """Processa consumo: débito + transação + atualização de sessão"""
        wallet = user.wallet
        
        # Verificação de saldo com lock
        wallet = Wallet.objects.select_for_update().get(user=user)
        
        if wallet.balance_cents < tap.price_cents:
            raise InsufficientBalanceError(
                f"Saldo insuficiente: {wallet.balance_cents} < {tap.price_cents}"
            )
        
        # Débito atômico
        wallet.balance_cents -= tap.price_cents
        wallet.save()
        
        # Registro da transação
        transaction_record = Transaction.objects.create(
            user=user,
            amount_cents=-tap.price_cents,
            category=tap.type,
            volume_ml=tap.dose_ml,
            description=f"Consumo em {tap.name}",
            ref_session=session
        )
        
        # Atualização da sessão
        session.status = 'used'
        session.used_at = timezone.now()
        session.save()
        
        return transaction_record
    
    @staticmethod
    @transaction.atomic
    def add_credits(user, amount_cents, description="Recarga manual"):
        """Adiciona créditos à carteira do usuário"""
        if amount_cents <= 0:
            raise ValueError("Valor deve ser positivo")
        
        wallet = Wallet.objects.select_for_update().get(user=user)
        wallet.balance_cents += amount_cents
        wallet.save()
        
        return Transaction.objects.create(
            user=user,
            amount_cents=amount_cents,
            category='topup',
            volume_ml=0,
            description=description
        )
    
    @staticmethod
    def get_user_statement(user, days=30):
        """Extrato do usuário com paginação"""
        since = timezone.now() - timedelta(days=days)
        
        return Transaction.objects.filter(
            user=user,
            created_at__gte=since
        ).select_related('ref_session__tap').order_by('-created_at')
    
    @staticmethod
    def get_balance_summary(user):
        """Resumo financeiro do usuário"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_transactions = Transaction.objects.filter(
            user=user,
            created_at__gte=thirty_days_ago
        )
        
        consumed = recent_transactions.filter(
            amount_cents__lt=0
        ).aggregate(
            total=models.Sum('amount_cents'),
            volume=models.Sum('volume_ml')
        )
        
        topped_up = recent_transactions.filter(
            amount_cents__gt=0
        ).aggregate(total=models.Sum('amount_cents'))
        
        return {
            'current_balance': user.wallet.balance_cents,
            'consumed_30d': abs(consumed['total'] or 0),
            'volume_30d': consumed['volume'] or 0,
            'topped_up_30d': topped_up['total'] or 0,
            'transaction_count': recent_transactions.count()
        }
```

### MetricsService (apps/analytics/services.py)

O MetricsService fornece dados agregados para dashboards administrativos e relatórios de performance.

```python
class MetricsService:
    
    @staticmethod
    def get_daily_metrics(date=None):
        """Métricas do dia específico ou hoje"""
        if date is None:
            date = timezone.now().date()
        
        start_of_day = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        end_of_day = start_of_day + timedelta(days=1)
        
        transactions = Transaction.objects.filter(
            created_at__gte=start_of_day,
            created_at__lt=end_of_day,
            amount_cents__lt=0  # apenas consumos
        )
        
        return {
            'total_volume_ml': transactions.aggregate(
                total=models.Sum('volume_ml')
            )['total'] or 0,
            'total_transactions': transactions.count(),
            'total_revenue_cents': abs(transactions.aggregate(
                total=models.Sum('amount_cents')
            )['total'] or 0),
            'unique_users': transactions.values('user').distinct().count(),
            'by_category': transactions.values('category').annotate(
                volume=models.Sum('volume_ml'),
                count=models.Count('id'),
                revenue=models.Sum('amount_cents')
            )
        }
    
    @staticmethod
    def get_tap_performance(days=7):
        """Performance por tap nos últimos N dias"""
        since = timezone.now() - timedelta(days=days)
        
        return Transaction.objects.filter(
            created_at__gte=since,
            amount_cents__lt=0,
            ref_session__tap__isnull=False
        ).values(
            'ref_session__tap__name',
            'ref_session__tap__type'
        ).annotate(
            total_volume=models.Sum('volume_ml'),
            transaction_count=models.Count('id'),
            total_revenue=models.Sum('amount_cents'),
            unique_users=models.Count('user', distinct=True)
        ).order_by('-total_volume')
    
    @staticmethod
    def get_top_consumers(days=30, limit=10):
        """Top consumidores do período"""
        since = timezone.now() - timedelta(days=days)
        
        return Transaction.objects.filter(
            created_at__gte=since,
            amount_cents__lt=0
        ).values(
            'user__username',
            'user__first_name',
            'user__last_name'
        ).annotate(
            total_volume=models.Sum('volume_ml'),
            total_spent=models.Sum('amount_cents'),
            transaction_count=models.Count('id')
        ).order_by('-total_volume')[:limit]
    
    @staticmethod
    def get_error_rates(days=7):
        """Taxa de erro nas validações"""
        since = timezone.now() - timedelta(days=days)
        
        total_attempts = TapValidationAudit.objects.filter(
            created_at__gte=since
        ).count()
        
        if total_attempts == 0:
            return {'error_rate': 0, 'total_attempts': 0}
        
        errors_by_type = TapValidationAudit.objects.filter(
            created_at__gte=since
        ).values('result').annotate(
            count=models.Count('id')
        )
        
        success_count = next(
            (item['count'] for item in errors_by_type if item['result'] == 'ok'),
            0
        )
        
        return {
            'error_rate': ((total_attempts - success_count) / total_attempts) * 100,
            'total_attempts': total_attempts,
            'success_count': success_count,
            'errors_by_type': {
                item['result']: item['count'] 
                for item in errors_by_type 
                if item['result'] != 'ok'
            }
        }
```

### RateLimitService (apps/security/services.py)

O RateLimitService implementa controles de rate limiting específicos para dispositivos e IPs, prevenindo abuso e ataques.

```python
class RateLimitService:
    
    @staticmethod
    def check_device_rate_limit(device_id, window_minutes=1, max_requests=10):
        """Verifica rate limit por device_id"""
        window_start = timezone.now() - timedelta(minutes=window_minutes)
        
        recent_attempts = TapValidationAudit.objects.filter(
            device_id=device_id,
            created_at__gte=window_start
        ).count()
        
        return recent_attempts < max_requests
    
    @staticmethod
    def check_ip_rate_limit(ip_address, window_minutes=5, max_requests=50):
        """Verifica rate limit por IP"""
        window_start = timezone.now() - timedelta(minutes=window_minutes)
        
        recent_attempts = TapValidationAudit.objects.filter(
            ip_address=ip_address,
            created_at__gte=window_start
        ).count()
        
        return recent_attempts < max_requests
    
    @staticmethod
    def get_suspicious_devices(days=1, error_threshold=0.5):
        """Identifica dispositivos com alta taxa de erro"""
        since = timezone.now() - timedelta(days=days)
        
        device_stats = TapValidationAudit.objects.filter(
            created_at__gte=since
        ).values('device_id').annotate(
            total_attempts=models.Count('id'),
            error_count=models.Count(
                'id',
                filter=~models.Q(result='ok')
            )
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


## Especificação de Frontend e Templates

### Estrutura de Templates Django

**Template Base (templates/base.html):**
```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}LHC Tap System{% endblock %}</title>
    
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Custom CSS -->
    <link href="{% static 'css/main.css' %}" rel="stylesheet">
    
    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="{% static 'favicon.ico' %}">
    
    {% block extra_css %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{% url 'dashboard' %}">
                <i class="fas fa-beer"></i> LHC Tap
            </a>
            
            {% if user.is_authenticated %}
            <div class="navbar-nav ms-auto">
                <div class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                        {{ user.get_full_name|default:user.username }}
                        <span class="badge bg-success ms-1">
                            R$ {{ user.wallet.balance_cents|floatformat:2|div:100 }}
                        </span>
                    </a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="{% url 'profile' %}">Perfil</a></li>
                        <li><a class="dropdown-item" href="{% url 'statement' %}">Extrato</a></li>
                        {% if user.profile.is_admin %}
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="{% url 'admin_dashboard' %}">Admin</a></li>
                        {% endif %}
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="{% url 'logout' %}">Sair</a></li>
                    </ul>
                </div>
            </div>
            {% endif %}
        </div>
    </nav>
    
    <!-- Main Content -->
    <main class="container mt-4">
        {% if messages %}
        <div class="row">
            <div class="col-12">
                {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}
        
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    <footer class="bg-light mt-5 py-4">
        <div class="container text-center">
            <p class="mb-0">&copy; 2025 LHC Tap System. Todos os direitos reservados.</p>
        </div>
    </footer>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    
    <!-- Anime.js -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/animejs/3.2.1/anime.min.js"></script>
    
    <!-- QR Code Generator -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode/1.5.3/qrcode.min.js"></script>
    
    <!-- Custom JS -->
    <script src="{% static 'js/main.js' %}"></script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Dashboard do Membro (templates/dashboard/member.html)

```html
{% extends 'base.html' %}
{% load static %}

{% block title %}Dashboard - {{ user.get_full_name|default:user.username }}{% endblock %}

{% block content %}
<div class="row">
    <!-- Saldo Atual -->
    <div class="col-md-4 mb-4">
        <div class="card border-success">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0"><i class="fas fa-wallet"></i> Saldo Atual</h5>
            </div>
            <div class="card-body text-center">
                <h2 class="text-success mb-0" id="current-balance">
                    R$ {{ balance_summary.current_balance|floatformat:2|div:100 }}
                </h2>
                <small class="text-muted">Créditos disponíveis</small>
            </div>
        </div>
    </div>
    
    <!-- Consumo Mensal -->
    <div class="col-md-4 mb-4">
        <div class="card border-info">
            <div class="card-header bg-info text-white">
                <h5 class="mb-0"><i class="fas fa-chart-line"></i> Este Mês</h5>
            </div>
            <div class="card-body text-center">
                <h4 class="text-info mb-1">{{ balance_summary.volume_30d|floatformat:0 }}ml</h4>
                <small class="text-muted">
                    R$ {{ balance_summary.consumed_30d|floatformat:2|div:100 }} gastos
                </small>
            </div>
        </div>
    </div>
    
    <!-- Transações -->
    <div class="col-md-4 mb-4">
        <div class="card border-warning">
            <div class="card-header bg-warning text-dark">
                <h5 class="mb-0"><i class="fas fa-receipt"></i> Transações</h5>
            </div>
            <div class="card-body text-center">
                <h4 class="text-warning mb-1">{{ balance_summary.transaction_count }}</h4>
                <small class="text-muted">Últimos 30 dias</small>
            </div>
        </div>
    </div>
</div>

<!-- Taps Disponíveis -->
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-beer"></i> Taps Disponíveis</h5>
            </div>
            <div class="card-body">
                <div class="row" id="taps-container">
                    {% for tap in available_taps %}
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="card tap-card" data-tap-id="{{ tap.id }}">
                            <div class="card-body text-center">
                                <div class="tap-icon mb-3">
                                    {% if tap.type == 'beer' %}
                                    <i class="fas fa-beer fa-3x text-warning"></i>
                                    {% else %}
                                    <i class="fas fa-leaf fa-3x text-success"></i>
                                    {% endif %}
                                </div>
                                <h5 class="card-title">{{ tap.name }}</h5>
                                <p class="card-text">
                                    <strong>{{ tap.dose_ml }}ml</strong><br>
                                    <span class="text-success">R$ {{ tap.price_cents|floatformat:2|div:100 }}</span>
                                </p>
                                {% if user.wallet.balance_cents >= tap.price_cents %}
                                <button class="btn btn-primary generate-qr-btn" 
                                        data-tap-id="{{ tap.id }}"
                                        data-tap-name="{{ tap.name }}"
                                        data-price="{{ tap.price_cents }}">
                                    <i class="fas fa-qrcode"></i> Gerar QR
                                </button>
                                {% else %}
                                <button class="btn btn-secondary" disabled>
                                    <i class="fas fa-times"></i> Saldo Insuficiente
                                </button>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    {% empty %}
                    <div class="col-12">
                        <div class="alert alert-info text-center">
                            <i class="fas fa-info-circle"></i>
                            Nenhum tap disponível no momento.
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Últimas Transações -->
<div class="row mt-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h5 class="mb-0"><i class="fas fa-history"></i> Últimas Transações</h5>
                <a href="{% url 'statement' %}" class="btn btn-sm btn-outline-primary">
                    Ver Todas
                </a>
            </div>
            <div class="card-body">
                {% if recent_transactions %}
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Data</th>
                                <th>Descrição</th>
                                <th>Volume</th>
                                <th class="text-end">Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for transaction in recent_transactions %}
                            <tr>
                                <td>{{ transaction.created_at|date:"d/m H:i" }}</td>
                                <td>
                                    {% if transaction.category == 'topup' %}
                                    <i class="fas fa-plus-circle text-success"></i> Recarga
                                    {% elif transaction.category == 'beer' %}
                                    <i class="fas fa-beer text-warning"></i> 
                                    {{ transaction.ref_session.tap.name|default:"Chope" }}
                                    {% else %}
                                    <i class="fas fa-leaf text-success"></i>
                                    {{ transaction.ref_session.tap.name|default:"Mate" }}
                                    {% endif %}
                                </td>
                                <td>
                                    {% if transaction.volume_ml > 0 %}
                                    {{ transaction.volume_ml }}ml
                                    {% else %}
                                    -
                                    {% endif %}
                                </td>
                                <td class="text-end">
                                    {% if transaction.amount_cents > 0 %}
                                    <span class="text-success">
                                        +R$ {{ transaction.amount_cents|floatformat:2|div:100 }}
                                    </span>
                                    {% else %}
                                    <span class="text-danger">
                                        R$ {{ transaction.amount_cents|floatformat:2|div:100 }}
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <div class="text-center text-muted py-4">
                    <i class="fas fa-receipt fa-3x mb-3"></i>
                    <p>Nenhuma transação encontrada.</p>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<!-- Modal QR Code -->
<div class="modal fade" id="qrModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">QR Code - <span id="modal-tap-name"></span></h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
                <div id="qr-container" class="mb-3"></div>
                <div class="countdown-container">
                    <div class="progress mb-2">
                        <div class="progress-bar progress-bar-striped progress-bar-animated" 
                             id="countdown-progress" 
                             role="progressbar" 
                             style="width: 100%"></div>
                    </div>
                    <p class="mb-0">
                        Expira em: <strong id="countdown-timer">30</strong> segundos
                    </p>
                </div>
                <div class="alert alert-info mt-3">
                    <small>
                        <i class="fas fa-info-circle"></i>
                        Apresente este QR code no leitor do tap selecionado.
                    </small>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{% static 'js/dashboard.js' %}"></script>
{% endblock %}
```

### JavaScript para Interações (static/js/dashboard.js)

```javascript
class TapDashboard {
    constructor() {
        this.qrModal = new bootstrap.Modal(document.getElementById('qrModal'));
        this.countdownInterval = null;
        this.init();
    }
    
    init() {
        // Event listeners para botões de gerar QR
        document.querySelectorAll('.generate-qr-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tapId = e.target.dataset.tapId;
                const tapName = e.target.dataset.tapName;
                const price = e.target.dataset.price;
                this.generateQRCode(tapId, tapName, price);
            });
        });
        
        // Animações de entrada para cards
        this.animateCards();
        
        // Auto-refresh do saldo a cada 30 segundos
        setInterval(() => this.refreshBalance(), 30000);
    }
    
    async generateQRCode(tapId, tapName, price) {
        try {
            // Mostrar loading
            this.showQRLoading();
            
            const response = await fetch('/dashboard/generate-token/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: `tap_id=${tapId}`
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.displayQRCode(data.token, tapName, data.expires_at);
                this.startCountdown(data.expires_at);
            } else {
                this.showError(data.error || 'Erro ao gerar QR code');
            }
        } catch (error) {
            console.error('Erro:', error);
            this.showError('Erro de conexão. Tente novamente.');
        }
    }
    
    displayQRCode(token, tapName, expiresAt) {
        // Limpar container anterior
        const container = document.getElementById('qr-container');
        container.innerHTML = '';
        
        // Gerar QR code
        QRCode.toCanvas(container, token, {
            width: 200,
            height: 200,
            colorDark: '#000000',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M
        });
        
        // Atualizar título do modal
        document.getElementById('modal-tap-name').textContent = tapName;
        
        // Mostrar modal
        this.qrModal.show();
        
        // Animação de entrada do QR
        anime({
            targets: container.querySelector('canvas'),
            scale: [0, 1],
            rotate: [180, 0],
            duration: 600,
            easing: 'easeOutElastic(1, .8)'
        });
    }
    
    startCountdown(expiresAt) {
        const expirationTime = new Date(expiresAt).getTime();
        const totalDuration = 30000; // 30 segundos
        
        this.countdownInterval = setInterval(() => {
            const now = new Date().getTime();
            const timeLeft = expirationTime - now;
            
            if (timeLeft <= 0) {
                this.expireQRCode();
                return;
            }
            
            const secondsLeft = Math.ceil(timeLeft / 1000);
            const progressPercent = (timeLeft / totalDuration) * 100;
            
            // Atualizar timer
            document.getElementById('countdown-timer').textContent = secondsLeft;
            
            // Atualizar progress bar
            const progressBar = document.getElementById('countdown-progress');
            progressBar.style.width = `${progressPercent}%`;
            
            // Mudar cor quando restam poucos segundos
            if (secondsLeft <= 10) {
                progressBar.classList.remove('bg-success');
                progressBar.classList.add('bg-warning');
            }
            if (secondsLeft <= 5) {
                progressBar.classList.remove('bg-warning');
                progressBar.classList.add('bg-danger');
            }
        }, 100);
    }
    
    expireQRCode() {
        clearInterval(this.countdownInterval);
        
        // Animação de expiração
        anime({
            targets: '#qr-container canvas',
            opacity: [1, 0.3],
            scale: [1, 0.8],
            duration: 500
        });
        
        // Mostrar mensagem de expiração
        const container = document.getElementById('qr-container');
        const expiredMsg = document.createElement('div');
        expiredMsg.className = 'alert alert-danger mt-2';
        expiredMsg.innerHTML = '<i class="fas fa-clock"></i> QR Code expirado. Gere um novo.';
        container.appendChild(expiredMsg);
        
        // Desabilitar progress bar
        document.getElementById('countdown-progress').style.width = '0%';
        document.getElementById('countdown-timer').textContent = '0';
    }
    
    showQRLoading() {
        document.getElementById('modal-tap-name').textContent = 'Gerando...';
        document.getElementById('qr-container').innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
        `;
        this.qrModal.show();
    }
    
    showError(message) {
        const container = document.getElementById('qr-container');
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }
    
    animateCards() {
        // Animação de entrada para cards dos taps
        anime({
            targets: '.tap-card',
            translateY: [50, 0],
            opacity: [0, 1],
            delay: anime.stagger(100),
            duration: 600,
            easing: 'easeOutQuad'
        });
        
        // Hover effect para cards
        document.querySelectorAll('.tap-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                anime({
                    targets: card,
                    scale: 1.05,
                    duration: 200,
                    easing: 'easeOutQuad'
                });
            });
            
            card.addEventListener('mouseleave', () => {
                anime({
                    targets: card,
                    scale: 1,
                    duration: 200,
                    easing: 'easeOutQuad'
                });
            });
        });
    }
    
    async refreshBalance() {
        try {
            const response = await fetch('/api/user/balance/');
            const data = await response.json();
            
            if (response.ok) {
                const balanceElement = document.getElementById('current-balance');
                const newBalance = `R$ ${(data.balance_cents / 100).toFixed(2)}`;
                
                if (balanceElement.textContent !== newBalance) {
                    // Animação de atualização
                    anime({
                        targets: balanceElement,
                        scale: [1, 1.1, 1],
                        duration: 400,
                        complete: () => {
                            balanceElement.textContent = newBalance;
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Erro ao atualizar saldo:', error);
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new TapDashboard();
});
```

## Configuração de Deployment e Infraestrutura

### Settings de Produção (settings/production.py)

```python
from .base import *
import os
from urllib.parse import urlparse

# Security Settings
DEBUG = False
ALLOWED_HOSTS = ['*']  # Configurar domínios específicos em produção

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://casaos:casaos@192.168.0.48:32769/lhctap')
db_config = urlparse(DATABASE_URL)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_config.path[1:],
        'USER': db_config.username,
        'PASSWORD': db_config.password,
        'HOST': db_config.hostname,
        'PORT': db_config.port or 5432,
        'OPTIONS': {
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
    }
}

# Cache Configuration (Redis recomendado para produção)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'lhctap',
        'TIMEOUT': 300,
    }
}

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/lhctap/django.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/lhctap/security.log',
            'maxBytes': 1024*1024*15,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
        'lhctap': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

# Custom Settings
TOKEN_EXPIRY_SECONDS = 30
MAX_VALIDATIONS_PER_MINUTE = 10
MAX_VALIDATIONS_PER_IP_HOUR = 100
CLEANUP_EXPIRED_TOKENS_DAYS = 7
AUDIT_RETENTION_DAYS = 90
```

### Docker Configuration (Dockerfile)

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=lhctap.settings.production

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create log directory
RUN mkdir -p /var/log/lhctap

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app /var/log/lhctap
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "lhctap.wsgi:application"]
```

### Management Commands

**Cleanup Command (management/commands/cleanup_expired.py):**
```python
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.taps.models import TapSession, TapValidationAudit

class Command(BaseCommand):
    help = 'Limpa tokens expirados e logs antigos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Dias para manter tokens expirados (padrão: 7)'
        )
        parser.add_argument(
            '--audit-days',
            type=int,
            default=90,
            help='Dias para manter logs de auditoria (padrão: 90)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        audit_days = options['audit_days']
        
        # Limpar tokens expirados
        cutoff_date = timezone.now() - timedelta(days=days)
        expired_sessions = TapSession.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['expired', 'used']
        )
        
        sessions_count = expired_sessions.count()
        expired_sessions.delete()
        
        # Limpar logs de auditoria antigos
        audit_cutoff = timezone.now() - timedelta(days=audit_days)
        old_audits = TapValidationAudit.objects.filter(
            created_at__lt=audit_cutoff
        )
        
        audits_count = old_audits.count()
        old_audits.delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Limpeza concluída: {sessions_count} sessões e {audits_count} logs removidos'
            )
        )
```

### Monitoramento e Métricas

**Health Check View (apps/core/views.py):**
```python
from django.http import JsonResponse
from django.db import connection
from django.utils import timezone
from apps.taps.models import Tap

def health_check(request):
    """Endpoint de health check para monitoramento"""
    try:
        # Verificar conexão com banco
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Verificar se existem taps ativos
        active_taps = Tap.objects.filter(is_active=True).count()
        
        return JsonResponse({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'database': 'connected',
            'active_taps': active_taps,
            'version': '1.0.0'
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)
```

### Configuração de Backup Automático

**Script de Backup (scripts/backup.sh):**
```bash
#!/bin/bash

# Configurações
DB_HOST="192.168.0.48"
DB_PORT="32769"
DB_NAME="lhctap"
DB_USER="casaos"
BACKUP_DIR="/backups/lhctap"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Criar diretório se não existir
mkdir -p $BACKUP_DIR

# Backup do banco
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --no-password --verbose --clean --no-acl --no-owner \
    | gzip > $BACKUP_DIR/lhctap_$DATE.sql.gz

# Verificar se backup foi criado
if [ $? -eq 0 ]; then
    echo "Backup criado com sucesso: lhctap_$DATE.sql.gz"
    
    # Remover backups antigos
    find $BACKUP_DIR -name "lhctap_*.sql.gz" -mtime +$RETENTION_DAYS -delete
    echo "Backups antigos removidos (>$RETENTION_DAYS dias)"
else
    echo "Erro ao criar backup"
    exit 1
fi

# Backup de arquivos estáticos (opcional)
tar -czf $BACKUP_DIR/static_$DATE.tar.gz /app/staticfiles/

echo "Backup completo finalizado"
```

Esta especificação técnica refinada fornece uma base sólida e detalhada para implementação do sistema de controle de consumo em taps utilizando Django e PostgreSQL. O documento inclui especificações completas de modelos, APIs, frontend, segurança e deployment, permitindo que um LLM expert em código implemente o sistema de forma eficiente e seguindo as melhores práticas de desenvolvimento.


## Guia de Implementação para LLM Expert

### Estrutura de Projeto Django Recomendada

A implementação deve seguir a estrutura de projeto Django modular apresentada abaixo, organizando o código em aplicações específicas por domínio de negócio. Esta abordagem facilita a manutenção, testes e escalabilidade do sistema.

```
lhctap/
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── lhctap/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   ├── production.py
│   │   └── testing.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── __init__.py
│   ├── accounts/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── admin.py
│   │   └── migrations/
│   ├── wallet/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   ├── admin.py
│   │   └── migrations/
│   ├── taps/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── services.py
│   │   ├── admin.py
│   │   └── migrations/
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── services.py
│   │   ├── views.py
│   │   └── urls.py
│   └── core/
│       ├── __init__.py
│       ├── views.py
│       ├── middleware.py
│       ├── utils.py
│       └── exceptions.py
├── templates/
│   ├── base.html
│   ├── accounts/
│   ├── dashboard/
│   └── admin/
├── static/
│   ├── css/
│   ├── js/
│   ├── img/
│   └── favicon.ico
├── staticfiles/
├── media/
├── logs/
└── scripts/
    ├── backup.sh
    └── deploy.sh
```

### Sequência de Implementação Recomendada

**Fase 1: Configuração Base (Prioridade Máxima)**

Inicie pela configuração do ambiente Django com as seguintes etapas obrigatórias. Configure o projeto Django com estrutura modular de settings, separando configurações de desenvolvimento, teste e produção. Instale e configure PostgreSQL com a string de conexão fornecida: `postgresql://casaos:casaos@192.168.0.48:32769/lhctap`. Configure o sistema de autenticação nativo do Django, habilitando middleware de CSRF e sessões. Implemente logging estruturado com rotação de arquivos para auditoria e debugging. Configure arquivos estáticos e media files com servimento adequado para desenvolvimento e produção.

**Fase 2: Modelos e Migrações (Prioridade Máxima)**

Implemente todos os modelos Django na ordem específica apresentada na especificação técnica. Crie as migrações na sequência correta: UserProfile, Wallet, Tap, TapSession, Transaction, TapValidationAudit. Configure constraints de banco de dados, índices e relacionamentos conforme especificado. Implemente signals para criação automática de UserProfile e Wallet ao criar usuário. Configure o Django Admin para todos os modelos com interfaces adequadas para administração.

**Fase 3: Serviços de Negócio (Prioridade Alta)**

Implemente as classes de serviço TokenService, WalletService, MetricsService e RateLimitService conforme especificação detalhada. Garanta que todas as operações financeiras sejam atômicas usando `@transaction.atomic`. Implemente validações rigorosas de entrada e tratamento de exceções customizadas. Configure rate limiting usando django-ratelimit ou implementação customizada. Implemente auditoria completa de todas as operações críticas.

**Fase 4: APIs REST (Prioridade Máxima)**

Implemente o endpoint crítico `POST /api/tap/validate/` com todas as validações de segurança especificadas. Configure @csrf_exempt apenas para APIs de dispositivos externos com validação alternativa. Implemente rate limiting por device_id e IP address. Configure logging detalhado de todas as tentativas de validação. Implemente endpoints auxiliares para health check e status de taps.

**Fase 5: Interface Web (Prioridade Média)**

Implemente templates Django responsivos usando Bootstrap 5.x conforme especificação. Crie dashboard do membro com cards de saldo, taps disponíveis e histórico de transações. Implemente geração de QR code dinâmico com JavaScript e countdown timer. Configure animações com anime.js para feedback visual adequado. Implemente dashboard administrativo com métricas e KPIs especificados.

**Fase 6: Segurança e Performance (Prioridade Alta)**

Configure headers de segurança HTTP adequados para produção. Implemente validação rigorosa de entrada em todos os endpoints. Configure rate limiting e auditoria de tentativas suspeitas. Implemente cleanup automático de tokens expirados e logs antigos. Configure backup automático do banco de dados PostgreSQL.

### Checklist de Implementação Obrigatória

**Configuração Inicial:**
- [ ] Projeto Django criado com estrutura modular
- [ ] PostgreSQL configurado com string de conexão especificada
- [ ] Settings separados por ambiente (dev/test/prod)
- [ ] Logging configurado com rotação de arquivos
- [ ] Middleware de segurança habilitado (CSRF, XSS, etc.)
- [ ] Arquivos estáticos configurados adequadamente

**Modelos e Banco de Dados:**
- [ ] UserProfile implementado com relacionamento OneToOne
- [ ] Wallet implementado com constraints de saldo positivo
- [ ] Tap implementado com validações de dose e preço
- [ ] TapSession implementado com tokens únicos e expiração
- [ ] Transaction implementado com constraints de tipo
- [ ] TapValidationAudit implementado para auditoria completa
- [ ] Todas as migrações criadas na ordem correta
- [ ] Índices de performance configurados
- [ ] Django Admin configurado para todos os modelos

**Serviços de Negócio:**
- [ ] TokenService implementado com geração segura de tokens
- [ ] WalletService implementado com transações atômicas
- [ ] MetricsService implementado para dashboards administrativos
- [ ] RateLimitService implementado para prevenção de abuso
- [ ] Exceções customizadas definidas e tratadas adequadamente
- [ ] Validações de entrada rigorosas em todos os serviços

**APIs REST:**
- [ ] Endpoint /api/tap/validate/ implementado completamente
- [ ] Rate limiting configurado por device_id e IP
- [ ] Auditoria de todas as tentativas de validação
- [ ] Tratamento de erros específicos conforme especificação
- [ ] Health check endpoint implementado
- [ ] Documentação de API gerada (opcional: DRF + Swagger)

**Interface Web:**
- [ ] Template base responsivo com Bootstrap 5.x
- [ ] Dashboard do membro com todas as funcionalidades
- [ ] Geração de QR code com JavaScript
- [ ] Countdown timer para expiração de tokens
- [ ] Dashboard administrativo com métricas
- [ ] Animações com anime.js implementadas
- [ ] Formulários com validação client-side e server-side

**Segurança:**
- [ ] CSRF protection habilitado para views web
- [ ] Rate limiting implementado e testado
- [ ] Headers de segurança HTTP configurados
- [ ] Validação de entrada em todos os endpoints
- [ ] Auditoria completa de operações críticas
- [ ] Tokens criptograficamente seguros
- [ ] Sessões seguras configuradas

**Performance e Monitoramento:**
- [ ] Índices de banco otimizados para consultas frequentes
- [ ] Cache configurado (Redis recomendado)
- [ ] Queries otimizadas com select_related/prefetch_related
- [ ] Logging estruturado para debugging
- [ ] Health check para monitoramento
- [ ] Métricas de performance coletadas

**Deployment:**
- [ ] Dockerfile configurado adequadamente
- [ ] docker-compose.yml para desenvolvimento
- [ ] Scripts de backup automatizado
- [ ] Management commands para limpeza
- [ ] Configuração de produção testada
- [ ] Variáveis de ambiente documentadas

### Padrões de Código Obrigatórios

**Nomenclatura e Estrutura:**
Utilize nomenclatura em inglês para código (classes, métodos, variáveis) e português para interface do usuário (templates, mensagens). Siga PEP 8 rigorosamente para formatação de código Python. Use docstrings detalhadas em todas as classes e métodos públicos. Implemente type hints em todas as funções e métodos. Organize imports seguindo a ordem: standard library, third-party, local imports.

**Tratamento de Erros:**
Crie exceções customizadas para cada tipo de erro de negócio (InsufficientBalanceError, TokenExpiredError, etc.). Implemente logging detalhado de todas as exceções com contexto adequado. Use try/except específicos evitando bare except. Retorne respostas JSON estruturadas para APIs com códigos HTTP apropriados. Implemente fallbacks graceful para falhas não críticas.

**Transações e Consistência:**
Use `@transaction.atomic` para todas as operações que modificam múltiplas tabelas. Implemente `select_for_update()` para operações concorrentes críticas (débito de wallet). Valide dados de entrada antes de iniciar transações. Implemente rollback automático em caso de falhas. Use constraints de banco de dados como última linha de defesa.

**Segurança:**
Valide e sanitize todas as entradas do usuário. Use tokens criptograficamente seguros com `secrets.token_urlsafe()`. Implemente rate limiting em todos os endpoints públicos. Configure CORS adequadamente para APIs. Use HTTPS em produção com headers de segurança apropriados. Implemente auditoria de todas as operações sensíveis.

### Testes Obrigatórios

**Testes de Modelos:**
Teste todas as validações de modelo e constraints. Teste relacionamentos e cascatas de exclusão. Teste métodos customizados de modelo. Teste signals de criação automática. Teste edge cases de valores limites.

**Testes de Serviços:**
Teste cenários de sucesso e falha para cada método. Teste transações atômicas e rollbacks. Teste rate limiting e prevenção de abuso. Teste geração e validação de tokens. Teste cálculos de métricas e agregações.

**Testes de APIs:**
Teste endpoint de validação com todos os cenários de erro. Teste rate limiting por device_id e IP. Teste autenticação e autorização. Teste serialização de respostas JSON. Teste performance com carga simulada.

**Testes de Interface:**
Teste formulários com dados válidos e inválidos. Teste geração de QR code e countdown. Teste responsividade em diferentes dispositivos. Teste JavaScript e animações. Teste fluxos completos de usuário.

### Configurações de Produção Críticas

**Banco de Dados:**
Configure connection pooling adequado para PostgreSQL. Use CONN_MAX_AGE para reutilização de conexões. Configure timeouts apropriados para queries. Implemente backup automático com retenção de 30 dias. Configure monitoring de performance de queries.

**Cache e Performance:**
Configure Redis para cache de sessões e rate limiting. Use cache de template para páginas estáticas. Implemente cache de queries frequentes. Configure compressão de respostas HTTP. Use CDN para arquivos estáticos em produção.

**Monitoramento:**
Configure logging estruturado com níveis apropriados. Implemente health checks para todos os componentes críticos. Configure alertas para taxa de erro elevada. Monitore performance de APIs críticas. Implemente métricas de negócio (volume servido, receita, etc.).

**Segurança de Produção:**
Configure firewall para acesso restrito ao banco. Use secrets management para credenciais sensíveis. Configure rate limiting agressivo para IPs suspeitos. Implemente backup criptografado. Configure SSL/TLS com certificados válidos.

Esta estruturação detalhada fornece um roadmap completo para implementação do sistema, garantindo que todos os aspectos críticos sejam abordados de forma sistemática e seguindo as melhores práticas de desenvolvimento Django e segurança de aplicações web.


### Exemplos de Código Específicos para Implementação

**Requirements.txt Completo:**
```
Django==4.2.7
psycopg2-binary==2.9.7
django-ratelimit==4.1.0
django-redis==5.4.0
redis==5.0.1
gunicorn==21.2.0
whitenoise==6.6.0
python-decouple==3.8
Pillow==10.1.0
qrcode[pil]==7.4.2
celery==5.3.4
django-extensions==3.2.3
django-debug-toolbar==4.2.0
pytest-django==4.7.0
factory-boy==3.3.0
coverage==7.3.2
```

**Settings Base (lhctap/settings/base.py):**
```python
import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'django_ratelimit',
]

LOCAL_APPS = [
    'apps.accounts',
    'apps.wallet',
    'apps.taps',
    'apps.analytics',
    'apps.core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.AuditMiddleware',
]

ROOT_URLCONF = 'lhctap.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'lhctap.wsgi.application'

# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom settings
AUTH_USER_MODEL = 'auth.User'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Token settings
TOKEN_EXPIRY_SECONDS = config('TOKEN_EXPIRY_SECONDS', default=30, cast=int)
MAX_VALIDATIONS_PER_MINUTE = config('MAX_VALIDATIONS_PER_MINUTE', default=10, cast=int)
```

**URL Configuration Principal (lhctap/urls.py):**
```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('dashboard/', include('apps.wallet.urls')),
    path('api/', include('apps.taps.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('health/', health_check, name='health_check'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

**Middleware de Auditoria (apps/core/middleware.py):**
```python
import logging
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger('lhctap.audit')

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = timezone.now()
        
        response = self.get_response(request)
        
        # Log apenas requisições importantes
        if self.should_audit(request):
            duration = (timezone.now() - start_time).total_seconds()
            
            logger.info(
                f"Request: {request.method} {request.path} | "
                f"User: {getattr(request.user, 'username', 'anonymous')} | "
                f"IP: {self.get_client_ip(request)} | "
                f"Status: {response.status_code} | "
                f"Duration: {duration:.3f}s"
            )
        
        return response
    
    def should_audit(self, request):
        audit_paths = ['/api/', '/dashboard/', '/admin/']
        return any(request.path.startswith(path) for path in audit_paths)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
```

**Exceções Customizadas (apps/core/exceptions.py):**
```python
class LHCTapException(Exception):
    """Exceção base para o sistema LHC Tap"""
    pass

class InsufficientBalanceError(LHCTapException):
    """Saldo insuficiente para operação"""
    pass

class TokenExpiredError(LHCTapException):
    """Token expirado ou inválido"""
    pass

class TokenAlreadyUsedError(LHCTapException):
    """Token já foi utilizado"""
    pass

class RateLimitExceededError(LHCTapException):
    """Rate limit excedido"""
    pass

class TapInactiveError(LHCTapException):
    """Tap está inativo"""
    pass
```

**Utilitários Comuns (apps/core/utils.py):**
```python
import secrets
from django.utils import timezone
from datetime import timedelta

def generate_secure_token(length=32):
    """Gera token criptograficamente seguro"""
    return secrets.token_urlsafe(length)

def get_client_ip(request):
    """Extrai IP do cliente considerando proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def format_currency(cents):
    """Formata centavos para moeda brasileira"""
    return f"R$ {cents / 100:.2f}"

def is_token_expired(created_at, expiry_seconds=30):
    """Verifica se token está expirado"""
    expiry_time = created_at + timedelta(seconds=expiry_seconds)
    return timezone.now() > expiry_time

class TokenGenerator:
    """Gerador de tokens com configurações específicas"""
    
    @staticmethod
    def generate_tap_token():
        return generate_secure_token(32)
    
    @staticmethod
    def generate_api_key():
        return generate_secure_token(48)
```

### Comandos de Setup e Deployment

**Script de Inicialização (scripts/setup.sh):**
```bash
#!/bin/bash

echo "=== Configuração do Ambiente LHC Tap ==="

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variáveis de ambiente
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Arquivo .env criado. Configure as variáveis necessárias."
fi

# Configurar banco de dados
echo "Executando migrações..."
python manage.py makemigrations accounts
python manage.py makemigrations wallet
python manage.py makemigrations taps
python manage.py migrate

# Criar superusuário
echo "Criando superusuário..."
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Carregar dados iniciais
echo "Carregando dados iniciais..."
python manage.py loaddata fixtures/initial_data.json

echo "=== Setup concluído! ==="
echo "Execute: python manage.py runserver"
```

**Docker Compose para Desenvolvimento (docker-compose.yml):**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./logs:/var/log/lhctap
    environment:
      - DEBUG=True
      - DATABASE_URL=postgresql://casaos:casaos@192.168.0.48:32769/lhctap
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - redis
    command: python manage.py runserver 0.0.0.0:8000

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  celery:
    build: .
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://casaos:casaos@192.168.0.48:32769/lhctap
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - redis
    command: celery -A lhctap worker -l info

volumes:
  redis_data:
```

**Fixture de Dados Iniciais (fixtures/initial_data.json):**
```json
[
  {
    "model": "taps.tap",
    "pk": 1,
    "fields": {
      "name": "Chope 01",
      "type": "beer",
      "location": "Área Principal",
      "dose_ml": 300,
      "price_cents": 1000,
      "is_active": true
    }
  },
  {
    "model": "taps.tap",
    "pk": 2,
    "fields": {
      "name": "Mate 01",
      "type": "mate",
      "location": "Área Principal",
      "dose_ml": 200,
      "price_cents": 500,
      "is_active": true
    }
  },
  {
    "model": "taps.tap",
    "pk": 3,
    "fields": {
      "name": "Chope 02",
      "type": "beer",
      "location": "Área Secundária",
      "dose_ml": 300,
      "price_cents": 1000,
      "is_active": true
    }
  }
]
```

**Management Command para Dados de Teste (apps/core/management/commands/create_test_data.py):**
```python
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile
from apps.wallet.models import Wallet, Transaction
from apps.taps.models import Tap

class Command(BaseCommand):
    help = 'Cria dados de teste para desenvolvimento'
    
    def handle(self, *args, **options):
        # Criar usuários de teste
        users_data = [
            {'username': 'admin', 'email': 'admin@lhc.com', 'role': 'admin', 'balance': 5000},
            {'username': 'joao', 'email': 'joao@lhc.com', 'role': 'member', 'balance': 3000},
            {'username': 'maria', 'email': 'maria@lhc.com', 'role': 'member', 'balance': 2500},
            {'username': 'pedro', 'email': 'pedro@lhc.com', 'role': 'member', 'balance': 1500},
        ]
        
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
                
                # Criar profile
                profile = UserProfile.objects.create(
                    user=user,
                    role=user_data['role']
                )
                
                # Adicionar saldo inicial
                wallet = user.wallet
                wallet.balance_cents = user_data['balance']
                wallet.save()
                
                # Criar transação de recarga inicial
                Transaction.objects.create(
                    user=user,
                    amount_cents=user_data['balance'],
                    category='topup',
                    description='Saldo inicial de teste'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Usuário {user.username} criado com sucesso')
                )
        
        # Verificar se taps existem
        tap_count = Tap.objects.count()
        if tap_count == 0:
            self.stdout.write(
                self.style.WARNING('Nenhum tap encontrado. Execute: python manage.py loaddata fixtures/initial_data.json')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'{tap_count} taps encontrados')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Dados de teste criados com sucesso!')
        )
```

### Comandos de Execução

**Desenvolvimento Local:**
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar migrações
python manage.py migrate

# Criar dados de teste
python manage.py create_test_data

# Executar servidor de desenvolvimento
python manage.py runserver 0.0.0.0:8000

# Em outro terminal - executar Celery (se necessário)
celery -A lhctap worker -l info
```

**Produção com Docker:**
```bash
# Build da imagem
docker build -t lhctap:latest .

# Executar com docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Executar migrações em produção
docker-compose exec web python manage.py migrate

# Coletar arquivos estáticos
docker-compose exec web python manage.py collectstatic --noinput

# Criar superusuário
docker-compose exec web python manage.py createsuperuser
```

**Testes:**
```bash
# Executar todos os testes
python manage.py test

# Executar testes com coverage
coverage run --source='.' manage.py test
coverage report
coverage html

# Executar testes específicos
python manage.py test apps.taps.tests.test_api
python manage.py test apps.wallet.tests.test_services
```

Esta especificação técnica refinada fornece uma base completa e detalhada para implementação do sistema LHC Tap, incluindo todos os aspectos necessários para que um LLM expert em código possa desenvolver a solução de forma eficiente, seguindo as melhores práticas de desenvolvimento Django e garantindo segurança, performance e manutenibilidade do código.


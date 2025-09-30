# 📊 Modelos de Dados - LHC Tap System

## 🎯 Visão Geral

O sistema utiliza 6 modelos principais para gerenciar usuários, carteiras, taps, sessões e auditoria. Todos os modelos seguem as melhores práticas do Django com validações, índices otimizados e relacionamentos bem definidos.

## 👤 Gestão de Usuários

### UserProfile
**Localização:** `apps.accounts.models.UserProfile`

Extensão do modelo User padrão do Django para adicionar roles específicos do sistema.

```python
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('member', 'Membro'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Características:**
- Relacionamento 1:1 com User do Django
- Roles: `member` (padrão) e `admin`
- Índices otimizados para consultas por role
- Métodos auxiliares: `is_admin()`

**Relacionamentos:**
- `user` → `User` (OneToOne)

## 💰 Sistema de Carteira

### Wallet
**Localização:** `apps.wallet.models.Wallet`

Gerencia o saldo em centavos dos usuários com validações de integridade.

```python
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance_cents = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
```

**Características:**
- Saldo em centavos para precisão financeira
- Constraint de saldo não-negativo
- Métodos: `get_balance_display()`, `has_sufficient_balance()`, `debit()`, `credit()`
- Atualização automática de timestamp

**Relacionamentos:**
- `user` → `User` (OneToOne)

### Transaction
**Localização:** `apps.wallet.models.Transaction`

Registra todas as movimentações financeiras do sistema.

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
    ref_session = models.ForeignKey('taps.TapSession', on_delete=models.SET_NULL, null=True, blank=True)
```

**Características:**
- Valores negativos para débitos, positivos para créditos
- Categorias: `beer`, `mate`, `topup`
- Volume em ml para consumos
- Referência opcional à sessão do tap
- Constraint complexa para validar tipos de transação
- Índices otimizados para consultas por usuário e data

**Relacionamentos:**
- `user` → `User` (ForeignKey)
- `ref_session` → `TapSession` (ForeignKey, nullable)

## 🍺 Sistema de Taps

### Tap
**Localização:** `apps.taps.models.Tap`

Representa os pontos de consumo (taps de chope/mate).

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
```

**Características:**
- Nome único para identificação
- Tipos: `beer` (chope) e `mate`
- Dose padrão de 300ml
- Preço em centavos
- Status ativo/inativo
- Constraints para valores positivos
- Índices para consultas por tipo e status

**Relacionamentos:**
- `tapsession_set` → `TapSession` (Reverse ForeignKey)

### TapSession
**Localização:** `apps.taps.models.TapSession`

Gerencia sessões de tokens QR para consumo.

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
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
```

**Características:**
- Token único de 64 caracteres
- Status: `pending`, `used`, `expired`
- Expiração automática em 30 segundos
- Timestamp de uso para auditoria
- Índices otimizados para consultas por token e status
- Constraint para validar expiração

**Relacionamentos:**
- `user` → `User` (ForeignKey)
- `tap` → `Tap` (ForeignKey)
- `transaction_set` → `Transaction` (Reverse ForeignKey)

## 🔍 Sistema de Auditoria

### TapValidationAudit
**Localização:** `apps.taps.models.TapValidationAudit`

Registra todas as tentativas de validação para auditoria e segurança.

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

**Características:**
- Registro de todos os resultados de validação
- Informações de device_id e IP para rastreamento
- User agent para análise de dispositivos
- Relacionamentos nullable para casos de erro
- Índices para consultas por device, token e resultado
- Retenção configurável (padrão: 90 dias)

**Relacionamentos:**
- `user` → `User` (ForeignKey, nullable)
- `tap` → `Tap` (ForeignKey, nullable)

## 🔗 Diagrama de Relacionamentos

```
User (Django)
├── UserProfile (1:1)
├── Wallet (1:1)
├── Transaction (1:N)
├── TapSession (1:N)
└── TapValidationAudit (1:N)

Tap
├── TapSession (1:N)
└── TapValidationAudit (1:N)

TapSession
└── Transaction (1:N, nullable)
```

## 📊 Índices e Performance

### Índices Principais

**UserProfile:**
- `role` - Consultas por tipo de usuário

**Wallet:**
- Constraint `positive_balance` - Garantir saldo não-negativo

**Transaction:**
- `(user, -created_at)` - Extrato do usuário ordenado
- `(category, -created_at)` - Transações por categoria
- `-created_at` - Transações recentes
- Constraint `valid_transaction_type` - Validar tipos de transação

**Tap:**
- `(type, is_active)` - Taps disponíveis por tipo
- `location` - Consultas por localização

**TapSession:**
- `token` - Busca rápida por token
- `(user, tap)` - Sessões do usuário por tap
- `expires_at` - Limpeza de tokens expirados
- `pending_sessions_idx` - Sessões pendentes (parcial)

**TapValidationAudit:**
- `(device_id, -created_at)` - Histórico por dispositivo
- `token` - Busca por token específico
- `(result, -created_at)` - Análise de resultados
- `-created_at` - Auditoria recente

## 🛡️ Constraints e Validações

### Constraints de Banco
1. **positive_balance** - Saldo da carteira ≥ 0
2. **positive_dose** - Dose do tap > 0
3. **positive_price** - Preço do tap > 0
4. **valid_expiration** - Expiração > criação
5. **valid_transaction_type** - Regras de transação por categoria

### Validações de Aplicação
1. **Saldo suficiente** - Verificação antes de débito
2. **Token único** - Geração criptograficamente segura
3. **Expiração** - Validação de tempo de vida
4. **Status do tap** - Verificação de disponibilidade
5. **Rate limiting** - Controle de frequência de uso

## 🔄 Operações Atômicas

### Processamento de Consumo
```python
@transaction.atomic
def process_consumption(user, tap, session):
    # 1. Lock da carteira
    wallet = Wallet.objects.select_for_update().get(user=user)
    
    # 2. Verificação de saldo
    if wallet.balance_cents < tap.price_cents:
        raise InsufficientBalanceError()
    
    # 3. Débito atômico
    wallet.balance_cents -= tap.price_cents
    wallet.save()
    
    # 4. Registro da transação
    transaction = Transaction.objects.create(...)
    
    return transaction
```

### Geração de Token
```python
@transaction.atomic
def create_session(user, tap):
    # 1. Invalidar sessões pendentes
    invalidate_pending_sessions(user, tap)
    
    # 2. Criar nova sessão
    session = TapSession.objects.create(...)
    
    return session
```

## 📈 Métricas e Analytics

### Estatísticas de Sessão
- Total de tokens gerados
- Taxa de sucesso de uso
- Tokens expirados não utilizados
- Tempo médio de uso

### Estatísticas Financeiras
- Saldo total do sistema
- Volume de transações
- Receita por categoria
- Usuários mais ativos

### Estatísticas de Segurança
- Tentativas de fraude
- Dispositivos suspeitos
- Rate limits atingidos
- Padrões de uso anômalos

## 🧹 Limpeza e Manutenção

### Comandos de Limpeza
```bash
# Limpar tokens expirados
python manage.py cleanup_expired

# Limpar auditoria antiga
python manage.py cleanup_audit --days 90
```

### Retenção de Dados
- **Tokens expirados:** 7 dias (configurável)
- **Auditoria:** 90 dias (configurável)
- **Transações:** Permanente
- **Sessões utilizadas:** Permanente

## 🔧 Migrações e Evolução

### Estratégia de Migração
1. **Backward compatibility** - Manter compatibilidade com versões anteriores
2. **Data migration** - Migração segura de dados existentes
3. **Rollback plan** - Plano de reversão para cada migração
4. **Testing** - Testes em ambiente de staging

### Versionamento de Schema
- Versionamento semântico para mudanças de schema
- Documentação de breaking changes
- Scripts de migração automatizados
- Backup antes de migrações críticas

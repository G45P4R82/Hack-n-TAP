# 🍺 LHC Tap System

Sistema de controle de consumo em taps de chope e mate utilizando sistema de créditos e validação por QR dinâmico.

## 🚀 Stack Tecnológica

- **Backend:** Django 4.2+ com PostgreSQL
- **Frontend:** Bootstrap 5.x + anime.js
- **Banco de Dados:** PostgreSQL 14+
- **Cache:** Redis
- **Containerização:** Docker

## 📋 Funcionalidades

- ✅ Sistema de créditos com saldo em centavos
- ✅ Tokens QR dinâmicos com expiração de 30 segundos
- ✅ Validação em tempo real por dispositivos leitores
- ✅ Auditoria completa de todas as operações
- ✅ Rate limiting para prevenção de fraudes
- ✅ Dashboard responsivo com animações
- ✅ APIs REST para integração com hardware

## 🎯 Status do Projeto

**Progresso: 60% Concluído**

### ✅ Fases Concluídas:
- **FASE 1:** Configuração Base (100%)
- **FASE 2:** Modelos e Banco de Dados (100%)
- **FASE 3:** Serviços de Negócio (100%)
- **FASE 4:** APIs REST (100%)
- **FASE 5:** Interface Web (100%)

### ⏳ Fases Restantes:
- **FASE 6:** Segurança e Performance (0%)
- **FASE 7:** Deployment (0%)
- **FASE 8:** Testes (0%)
- **FASE 9:** Produção (0%)

## 🏗️ Estrutura do Projeto

```
lhctap/
├── manage.py
├── requirements.txt
├── lhctap/
│   ├── settings/          # Configurações por ambiente
│   ├── apps/              # Aplicações Django
│   │   ├── accounts/      # Usuários e perfis
│   │   ├── wallet/        # Carteira e transações
│   │   ├── taps/          # Taps e validação
│   │   ├── analytics/     # Métricas e relatórios
│   │   └── core/          # Utilitários e middleware
│   ├── templates/         # Templates Django
│   └── static/           # Arquivos estáticos
├── scripts/              # Scripts de setup e deploy
└── fixtures/             # Dados iniciais
```

## 🚀 Instalação e Configuração

### 📋 Pré-requisitos

- Python 3.11+
- PostgreSQL 14+
- Redis (opcional, para cache)
- Git

### 🛠️ Instalação Rápida (Recomendada)

#### 1. Clonar o repositório
```bash
git clone <repository-url>
cd Hack-n-TAP
```

#### 2. Executar setup automático
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

#### 3. Configurar variáveis de ambiente
```bash
cp env.example .env
# Editar .env com suas configurações (opcional)
```

#### 4. Testar conexão com banco
```bash
python test_db_connection.py
```

#### 5. Executar migrações
```bash
python run_migrations.py
```

#### 6. Carregar dados iniciais
```bash
python manage.py loaddata lhctap/fixtures/initial_data.json
```

#### 7. Criar dados de teste
```bash
python manage.py create_test_data
```

#### 8. Executar o servidor
```bash
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### 🔧 Configuração Manual (Passo a Passo)

#### 1. Ambiente Virtual
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Configurar Banco de Dados
```bash
# Testar conexão
python test_db_connection.py

# Criar migrações
python manage.py makemigrations accounts
python manage.py makemigrations wallet
python manage.py makemigrations taps

# Executar migrações
python manage.py migrate
```

#### 3. Carregar Dados Iniciais
```bash
# Carregar taps iniciais
python manage.py loaddata lhctap/fixtures/initial_data.json

# Criar usuários de teste
python manage.py create_test_data
```

#### 4. Criar Superusuário
```bash
python manage.py createsuperuser
```

#### 5. Coletar Arquivos Estáticos
```bash
python manage.py collectstatic --noinput
```

#### 6. Executar Servidor
```bash
python manage.py runserver 0.0.0.0:8000
```

### 🌐 Acessar o Sistema

- **Dashboard:** http://localhost:8000/dashboard/
- **Admin:** http://localhost:8000/admin/
- **Health Check:** http://localhost:8000/health/

### 👥 Usuários de Teste

O comando `create_test_data` cria os seguintes usuários:

| Usuário | Senha | Role | Saldo |
|---------|-------|------|-------|
| admin | 123456 | admin | R$ 50,00 |
| joao | 123456 | member | R$ 30,00 |
| maria | 123456 | member | R$ 25,00 |
| pedro | 123456 | member | R$ 15,00 |

## 🐳 Docker

### Desenvolvimento
```bash
docker-compose up -d
```

### Produção
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 🧪 Testes

```bash
# Executar todos os testes
python manage.py test

# Com coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📊 APIs REST

### 🔑 Validação de Token (Endpoint Crítico)
```http
POST /api/tap/validate/
Content-Type: application/json
X-Device-ID: device_001

{
    "token": "abc123...",
    "device_id": "device_001"
}
```

**Resposta de Sucesso:**
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

**Resposta de Erro:**
```json
{
    "ok": false,
    "error": "expired|used|insufficient|not_found|rate_limited|tap_inactive",
    "message": "Descrição do erro"
}
```

### 📊 Status do Tap
```http
GET /api/tap/1/status/
```

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

### 🎫 Geração de Token QR
```http
POST /dashboard/generate-token/
Content-Type: application/x-www-form-urlencoded
X-CSRFToken: csrf_token

tap_id=1
```

**Resposta:**
```json
{
    "token": "abc123...",
    "expires_at": "2025-09-06T14:30:30Z",
    "tap_name": "Chope 01",
    "dose_ml": 300,
    "price_cents": 1000
}
```

### 🏥 Health Check
```http
GET /health/
```

**Resposta:**
```json
{
    "status": "healthy",
    "timestamp": "2025-09-06T14:30:00Z",
    "database": "connected",
    "version": "1.0.0"
}
```

## 🎮 Como Usar o Sistema

### 1. **Login no Dashboard**
- Acesse: http://localhost:8000/dashboard/
- Use um dos usuários de teste (ex: joao/123456)

### 2. **Gerar QR Code**
- No dashboard, clique em "Gerar QR" em um tap disponível
- O QR code será exibido com countdown de 30 segundos

### 3. **Validar Token (Simulação)**
```bash
# Simular validação via API
curl -X POST http://localhost:8000/api/tap/validate/ \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: device_001" \
  -d '{"token": "SEU_TOKEN_AQUI", "device_id": "device_001"}'
```

### 4. **Administração**
- Acesse: http://localhost:8000/admin/
- Use admin/123456 para login
- Gerencie usuários, taps, transações e auditoria

## 🔧 Comandos Úteis

### Limpeza de Dados
```bash
# Limpar tokens expirados
python manage.py cleanup_expired

# Limpar com parâmetros customizados
python manage.py cleanup_expired --days 7 --audit-days 90
```

### Dados de Teste
```bash
# Criar usuários de teste
python manage.py create_test_data

# Recarregar taps iniciais
python manage.py loaddata lhctap/fixtures/initial_data.json
```

### Desenvolvimento
```bash
# Shell interativo do Django
python manage.py shell

# Verificar migrações pendentes
python manage.py showmigrations

# Coletar arquivos estáticos
python manage.py collectstatic --noinput
```

## 🔒 Segurança

- Tokens criptograficamente seguros (256 bits)
- Transações atômicas para operações financeiras
- Rate limiting por device_id e IP
- Headers de segurança HTTP
- Auditoria completa de tentativas de validação

## 🚨 Solução de Problemas

### Erro de Conexão com Banco
```bash
# Verificar se PostgreSQL está rodando
python test_db_connection.py

# Verificar configurações no .env
cat .env
```

### Erro de Migrações
```bash
# Verificar migrações pendentes
python manage.py showmigrations

# Aplicar migrações específicas
python manage.py migrate accounts
python manage.py migrate wallet
python manage.py migrate taps
```

### Erro de Dependências
```bash
# Reinstalar dependências
pip install -r requirements.txt --force-reinstall

# Verificar versão do Python
python --version
```

### Erro de Arquivos Estáticos
```bash
# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Verificar permissões
chmod -R 755 static/
```

## 📊 Monitoramento

### Logs
```bash
# Ver logs do Django
tail -f logs/django.log

# Ver logs de segurança
tail -f logs/security.log
```

### Métricas
- Acesse o Django Admin para ver métricas
- Use o endpoint `/health/` para health check
- Monitore logs de auditoria para tentativas suspeitas

## 🔄 Backup e Restore

### Backup do Banco
```bash
# Backup manual
pg_dump -h 192.168.0.48 -p 32769 -U casaos -d lhctap > backup.sql

# Restore
psql -h 192.168.0.48 -p 32769 -U casaos -d lhctap < backup.sql
```

### Backup de Dados
```bash
# Exportar dados
python manage.py dumpdata > data_backup.json

# Importar dados
python manage.py loaddata data_backup.json
```

## 📝 Licença

Este projeto é propriedade do LHC e está sob licença privada.

## 🤝 Contribuição

Para contribuir com o projeto, entre em contato com a equipe de desenvolvimento.

## 📞 Suporte

- **Documentação:** Consulte este README
- **Issues:** Reporte problemas via sistema de issues
- **Contato:** Equipe de desenvolvimento LHC

---

**Desenvolvido com ❤️ para o LHC**

**Versão:** 1.0.0  
**Última Atualização:** 06 de setembro de 2025
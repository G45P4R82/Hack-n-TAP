# 🚀 Deploy - LHC Tap System

## 🎯 Visão Geral

Este documento descreve o processo completo de deploy do LHC Tap System, desde a configuração do ambiente de desenvolvimento até a produção. O sistema suporta múltiplas estratégias de deploy incluindo Docker, servidores tradicionais e plataformas cloud.

## 📋 Pré-requisitos

### Requisitos do Sistema

**Servidor de Produção:**
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM:** Mínimo 2GB, Recomendado 4GB+
- **CPU:** 2 cores, Recomendado 4 cores+
- **Storage:** 20GB+ SSD
- **Python:** 3.11+
- **PostgreSQL:** 14+
- **Redis:** 6.0+ (opcional, para cache)

**Ferramentas Necessárias:**
- Git
- Docker & Docker Compose (opcional)
- Nginx (para produção)
- Certbot (para SSL)
- Supervisor (para gerenciamento de processos)

## 🛠️ Instalação Rápida

### Método 1: Script Automatizado (Recomendado)

```bash
# 1. Clonar repositório
git clone <repository-url>
cd Hack-n-TAP

# 2. Executar setup automático
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Configurar variáveis de ambiente
cp env.example .env
# Editar .env com suas configurações

# 4. Testar conexão com banco
python test_db_connection.py

# 5. Executar migrações
python run_migrations.py

# 6. Carregar dados iniciais
python manage.py loaddata lhctap/fixtures/initial_data.json

# 7. Criar dados de teste
python manage.py create_test_data

# 8. Executar servidor
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### Método 2: Docker (Desenvolvimento)

```bash
# 1. Clonar repositório
git clone <repository-url>
cd Hack-n-TAP

# 2. Configurar variáveis de ambiente
cp env.example .env

# 3. Executar com Docker Compose
docker-compose up -d

# 4. Executar migrações
docker-compose exec web python manage.py migrate

# 5. Carregar dados iniciais
docker-compose exec web python manage.py loaddata lhctap/fixtures/initial_data.json

# 6. Criar superusuário
docker-compose exec web python manage.py createsuperuser
```

## 🔧 Configuração Manual

### 1. Ambiente Virtual

```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Atualizar pip
pip install --upgrade pip

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configuração do Banco de Dados

#### PostgreSQL

```bash
# Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Criar usuário e banco
sudo -u postgres psql
CREATE USER lhctap_user WITH PASSWORD 'secure_password';
CREATE DATABASE lhctap OWNER lhctap_user;
GRANT ALL PRIVILEGES ON DATABASE lhctap TO lhctap_user;
\q
```

#### Configuração de Conexão

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

### 3. Configuração do Redis (Opcional)

```bash
# Instalar Redis
sudo apt install redis-server

# Configurar Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Testar conexão
redis-cli ping
```

### 4. Configuração de Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp env.example .env

# Editar configurações
nano .env
```

**Exemplo de .env:**
```bash
# Database
DB_NAME=lhctap
DB_USER=lhctap_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Security
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=lhctap.example.com,www.lhctap.example.com

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=lhctap@example.com
EMAIL_HOST_PASSWORD=email_password
DEFAULT_FROM_EMAIL=noreply@lhctap.com

# System
TOKEN_EXPIRY_SECONDS=30
MAX_VALIDATIONS_PER_MINUTE=10
MAX_VALIDATIONS_PER_IP_HOUR=100
```

### 5. Dados Iniciais

```bash
# Carregar taps iniciais
python manage.py loaddata lhctap/fixtures/initial_data.json

# Criar usuários de teste
python manage.py create_test_data

# Criar superusuário
python manage.py createsuperuser
```

### 6. Arquivos Estáticos

```bash
# Coletar arquivos estáticos
python manage.py collectstatic --noinput
```

## 🐳 Deploy com Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Definir variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash lhctap
USER lhctap

# Coletar arquivos estáticos
RUN python manage.py collectstatic --noinput

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Comando de inicialização
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lhctap.wsgi:application"]
```

### docker-compose.yml (Desenvolvimento)

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: lhctap
      POSTGRES_USER: lhctap_user
      POSTGRES_PASSWORD: lhctap_pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lhctap_user -d lhctap"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - DB_HOST=db
      - DB_NAME=lhctap
      - DB_USER=lhctap_user
      - DB_PASSWORD=lhctap_pass
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
    command: >
      sh -c "python manage.py migrate &&
             python manage.py loaddata lhctap/fixtures/initial_data.json &&
             python manage.py runserver 0.0.0.0:8000"

volumes:
  postgres_data:
```

### docker-compose.prod.yml (Produção)

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    environment:
      - DEBUG=False
      - DB_HOST=db
      - DB_NAME=${DB_NAME}
      - DB_USER=${DB_USER}
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_URL=redis://redis:6379/1
      - SECRET_KEY=${SECRET_KEY}
      - ALLOWED_HOSTS=${ALLOWED_HOSTS}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
      - ./staticfiles:/app/staticfiles
    restart: unless-stopped
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn --bind 0.0.0.0:8000 --workers 4 lhctap.wsgi:application"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./staticfiles:/var/www/static
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

## 🌐 Deploy em Produção

### 1. Configuração do Servidor

#### Ubuntu/Debian

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y python3.11 python3.11-venv python3.11-dev
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y redis-server nginx
sudo apt install -y git curl wget

# Instalar Docker (opcional)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### CentOS/RHEL

```bash
# Atualizar sistema
sudo yum update -y

# Instalar dependências
sudo yum install -y python3.11 python3.11-pip
sudo yum install -y postgresql-server postgresql-contrib
sudo yum install -y redis nginx
sudo yum install -y git curl wget

# Inicializar PostgreSQL
sudo postgresql-setup initdb
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2. Configuração do Banco de Dados

```bash
# Configurar PostgreSQL
sudo -u postgres psql

# Criar usuário e banco
CREATE USER lhctap_user WITH PASSWORD 'secure_password';
CREATE DATABASE lhctap OWNER lhctap_user;
GRANT ALL PRIVILEGES ON DATABASE lhctap TO lhctap_user;

# Configurar autenticação
\q
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Adicionar linha:
local   lhctap            lhctap_user                            md5

# Reiniciar PostgreSQL
sudo systemctl restart postgresql
```

### 3. Configuração da Aplicação

```bash
# Criar usuário para aplicação
sudo useradd -m -s /bin/bash lhctap
sudo usermod -aG www-data lhctap

# Criar diretórios
sudo mkdir -p /opt/lhctap
sudo mkdir -p /var/log/lhctap
sudo mkdir -p /var/www/lhctap/static
sudo mkdir -p /var/www/lhctap/media

# Definir permissões
sudo chown -R lhctap:lhctap /opt/lhctap
sudo chown -R lhctap:www-data /var/log/lhctap
sudo chown -R lhctap:www-data /var/www/lhctap

# Clonar repositório
sudo -u lhctap git clone <repository-url> /opt/lhctap
cd /opt/lhctap

# Configurar ambiente virtual
sudo -u lhctap python3.11 -m venv venv
sudo -u lhctap venv/bin/pip install --upgrade pip
sudo -u lhctap venv/bin/pip install -r requirements.txt

# Configurar variáveis de ambiente
sudo -u lhctap cp env.example .env
sudo -u lhctap nano .env
```

### 4. Configuração do Gunicorn

#### gunicorn.conf.py

```python
# gunicorn.conf.py
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeout
timeout = 30
keepalive = 2

# Logging
accesslog = "/var/log/lhctap/gunicorn_access.log"
errorlog = "/var/log/lhctap/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "lhctap"

# Server mechanics
daemon = False
pidfile = "/var/run/lhctap.pid"
user = "lhctap"
group = "lhctap"
tmp_upload_dir = None

# SSL (se necessário)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Preload app
preload_app = True
```

### 5. Configuração do Supervisor

#### /etc/supervisor/conf.d/lhctap.conf

```ini
[program:lhctap]
command=/opt/lhctap/venv/bin/gunicorn --config /opt/lhctap/gunicorn.conf.py lhctap.wsgi:application
directory=/opt/lhctap
user=lhctap
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/lhctap/supervisor.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/opt/lhctap/venv/bin"
```

```bash
# Recarregar configuração do Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start lhctap
```

### 6. Configuração do Nginx

#### /etc/nginx/sites-available/lhctap

```nginx
upstream lhctap {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name lhctap.example.com www.lhctap.example.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name lhctap.example.com www.lhctap.example.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/lhctap.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lhctap.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Static files
    location /static/ {
        alias /var/www/lhctap/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Media files
    location /media/ {
        alias /var/www/lhctap/media/;
        expires 1y;
        add_header Cache-Control "public";
        access_log off;
    }

    # Health check
    location /health/ {
        proxy_pass http://lhctap;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        access_log off;
    }

    # Main application
    location / {
        proxy_pass http://lhctap;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/lhctap /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Configuração SSL com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d lhctap.example.com -d www.lhctap.example.com

# Configurar renovação automática
sudo crontab -e
# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

### 8. Configuração de Firewall

```bash
# Configurar UFW
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Verificar status
sudo ufw status
```

## 🔄 Deploy Automatizado

### Script de Deploy

```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# Configurações
APP_DIR="/opt/lhctap"
REPO_URL="<repository-url>"
BRANCH="main"
VENV_DIR="$APP_DIR/venv"

echo "🚀 Iniciando deploy do LHC Tap System..."

# 1. Backup do banco de dados
echo "📦 Criando backup do banco de dados..."
sudo -u postgres pg_dump lhctap > /tmp/lhctap_backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Parar aplicação
echo "⏹️ Parando aplicação..."
sudo supervisorctl stop lhctap

# 3. Backup da aplicação atual
echo "📦 Criando backup da aplicação..."
sudo cp -r $APP_DIR $APP_DIR.backup.$(date +%Y%m%d_%H%M%S)

# 4. Atualizar código
echo "📥 Atualizando código..."
cd $APP_DIR
sudo -u lhctap git fetch origin
sudo -u lhctap git reset --hard origin/$BRANCH

# 5. Atualizar dependências
echo "📦 Atualizando dependências..."
sudo -u lhctap $VENV_DIR/bin/pip install --upgrade pip
sudo -u lhctap $VENV_DIR/bin/pip install -r requirements.txt

# 6. Executar migrações
echo "🗄️ Executando migrações..."
sudo -u lhctap $VENV_DIR/bin/python manage.py migrate

# 7. Coletar arquivos estáticos
echo "📁 Coletando arquivos estáticos..."
sudo -u lhctap $VENV_DIR/bin/python manage.py collectstatic --noinput

# 8. Limpar cache
echo "🧹 Limpando cache..."
sudo -u lhctap $VENV_DIR/bin/python manage.py clear_cache

# 9. Reiniciar aplicação
echo "🔄 Reiniciando aplicação..."
sudo supervisorctl start lhctap

# 10. Verificar saúde
echo "🏥 Verificando saúde da aplicação..."
sleep 5
curl -f http://localhost:8000/health/ || {
    echo "❌ Falha no health check!"
    echo "🔄 Restaurando backup..."
    sudo supervisorctl stop lhctap
    sudo rm -rf $APP_DIR
    sudo mv $APP_DIR.backup.$(date +%Y%m%d_%H%M%S) $APP_DIR
    sudo supervisorctl start lhctap
    exit 1
}

echo "✅ Deploy concluído com sucesso!"
```

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /opt/lhctap
          sudo -u lhctap git pull origin main
          sudo -u lhctap venv/bin/pip install -r requirements.txt
          sudo -u lhctap venv/bin/python manage.py migrate
          sudo -u lhctap venv/bin/python manage.py collectstatic --noinput
          sudo supervisorctl restart lhctap
```

## 📊 Monitoramento

### Health Checks

```bash
# Health check básico
curl -f http://localhost:8000/health/

# Health check detalhado
curl -f http://localhost:8000/health/ | jq

# Verificar logs
sudo tail -f /var/log/lhctap/gunicorn_error.log
sudo tail -f /var/log/lhctap/supervisor.log
```

### Métricas do Sistema

```bash
# Uso de CPU e memória
htop

# Uso de disco
df -h

# Conexões de rede
netstat -tulpn | grep :8000

# Status do banco
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE datname='lhctap';"
```

### Logs

```bash
# Logs da aplicação
sudo tail -f /var/log/lhctap/gunicorn_access.log
sudo tail -f /var/log/lhctap/gunicorn_error.log

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs do sistema
sudo journalctl -u nginx -f
sudo journalctl -u postgresql -f
```

## 🔧 Manutenção

### Comandos de Manutenção

```bash
# Limpar tokens expirados
sudo -u lhctap $VENV_DIR/bin/python manage.py cleanup_expired

# Limpar auditoria antiga
sudo -u lhctap $VENV_DIR/bin/bin/python manage.py cleanup_audit --days 90

# Backup do banco
sudo -u postgres pg_dump lhctap > backup_$(date +%Y%m%d).sql

# Restore do banco
sudo -u postgres psql lhctap < backup_20231201.sql

# Atualizar dependências
sudo -u lhctap $VENV_DIR/bin/pip install --upgrade -r requirements.txt

# Verificar configurações
sudo -u lhctap $VENV_DIR/bin/python manage.py check --deploy
```

### Rotação de Logs

```bash
# Configurar logrotate
sudo nano /etc/logrotate.d/lhctap
```

```bash
/var/log/lhctap/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 lhctap lhctap
    postrotate
        sudo supervisorctl restart lhctap
    endscript
}
```

## 🚨 Solução de Problemas

### Problemas Comuns

#### 1. Erro de Conexão com Banco

```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar configurações
sudo -u postgres psql -c "SHOW listen_addresses;"

# Testar conexão
python test_db_connection.py
```

#### 2. Erro de Permissões

```bash
# Verificar permissões
ls -la /opt/lhctap/
ls -la /var/log/lhctap/

# Corrigir permissões
sudo chown -R lhctap:lhctap /opt/lhctap
sudo chown -R lhctap:www-data /var/log/lhctap
```

#### 3. Erro de Arquivos Estáticos

```bash
# Coletar arquivos estáticos
sudo -u lhctap $VENV_DIR/bin/python manage.py collectstatic --noinput

# Verificar permissões
sudo chown -R lhctap:www-data /var/www/lhctap/static
```

#### 4. Erro de SSL

```bash
# Verificar certificado
sudo certbot certificates

# Renovar certificado
sudo certbot renew --dry-run
```

### Logs de Debug

```bash
# Ativar debug temporariamente
sudo -u lhctap nano /opt/lhctap/.env
# DEBUG=True

# Reiniciar aplicação
sudo supervisorctl restart lhctap

# Verificar logs
sudo tail -f /var/log/lhctap/gunicorn_error.log
```

## 📋 Checklist de Deploy

### Pré-Deploy

- [ ] Backup do banco de dados
- [ ] Backup da aplicação atual
- [ ] Verificar espaço em disco
- [ ] Verificar recursos do sistema
- [ ] Testar em ambiente de staging

### Deploy

- [ ] Parar aplicação
- [ ] Atualizar código
- [ ] Atualizar dependências
- [ ] Executar migrações
- [ ] Coletar arquivos estáticos
- [ ] Reiniciar aplicação
- [ ] Verificar health check

### Pós-Deploy

- [ ] Verificar logs de erro
- [ ] Testar funcionalidades principais
- [ ] Verificar métricas de performance
- [ ] Monitorar por 30 minutos
- [ ] Notificar equipe sobre sucesso/falha

## 🔄 Rollback

### Procedimento de Rollback

```bash
#!/bin/bash
# scripts/rollback.sh

set -e

echo "🔄 Iniciando rollback..."

# 1. Parar aplicação
sudo supervisorctl stop lhctap

# 2. Restaurar backup
BACKUP_DIR=$(ls -t $APP_DIR.backup.* | head -1)
sudo rm -rf $APP_DIR
sudo mv $BACKUP_DIR $APP_DIR

# 3. Restaurar banco (se necessário)
# sudo -u postgres psql lhctap < /tmp/lhctap_backup_*.sql

# 4. Reiniciar aplicação
sudo supervisorctl start lhctap

# 5. Verificar saúde
sleep 5
curl -f http://localhost:8000/health/

echo "✅ Rollback concluído com sucesso!"
```

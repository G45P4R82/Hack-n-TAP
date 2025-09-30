# ⚙️ Configuração - LHC Tap System

## 🎯 Visão Geral

O sistema LHC Tap utiliza uma arquitetura de configuração modular baseada em ambientes (development, production, testing) com suporte a variáveis de ambiente e configurações específicas por contexto.

## 🏗️ Estrutura de Configuração

### Organização de Settings

```
lhctap/settings/
├── __init__.py
├── base.py          # Configurações base compartilhadas
├── development.py   # Configurações de desenvolvimento
├── production.py    # Configurações de produção
└── testing.py       # Configurações de teste
```

### Herança de Configurações

```python
# settings/base.py
# Configurações base que são herdadas por todos os ambientes

# settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['lhctap.example.com']
```

## 🔧 Configurações Base

### Configurações de Aplicação

```python
# settings/base.py

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
```

### Middleware Stack

```python
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
```

### Configurações de Internacionalização

```python
# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Locale paths
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
```

### Configurações de Arquivos Estáticos

```python
# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
```

## 🗄️ Configurações de Banco de Dados

### Configuração Base

```python
# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='lhctap'),
        'USER': config('DB_USER', default='lhctap_user'),
        'PASSWORD': config('DB_PASSWORD', default='lhctap_pass'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        },
        'CONN_MAX_AGE': 600,  # 10 minutos
    }
}
```

### Configurações de Pool de Conexões

```python
# Connection pooling (para produção)
DATABASES['default']['OPTIONS'].update({
    'MAX_CONNS': 20,
    'MIN_CONNS': 5,
    'CONN_HEALTH_CHECKS': True,
})
```

### Configurações de Cache

```python
# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            }
        },
        'KEY_PREFIX': 'lhctap',
        'TIMEOUT': 300,  # 5 minutos
    }
}

# Session cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

## 🔐 Configurações de Segurança

### Configurações de Autenticação

```python
# Authentication
AUTH_USER_MODEL = 'auth.User'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Password validation
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
```

### Configurações de Sessão

```python
# Session configuration
SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_COOKIE_SECURE = True  # HTTPS apenas
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

### Headers de Segurança

```python
# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'
CSRF_TRUSTED_ORIGINS = [
    'https://lhctap.example.com',
]
```

## 🎫 Configurações do Sistema

### Configurações de Token

```python
# Token settings
TOKEN_EXPIRY_SECONDS = config('TOKEN_EXPIRY_SECONDS', default=30, cast=int)
MAX_VALIDATIONS_PER_MINUTE = config('MAX_VALIDATIONS_PER_MINUTE', default=10, cast=int)
MAX_VALIDATIONS_PER_IP_HOUR = config('MAX_VALIDATIONS_PER_IP_HOUR', default=100, cast=int)
```

### Configurações de Limpeza

```python
# Cleanup settings
CLEANUP_EXPIRED_TOKENS_DAYS = config('CLEANUP_EXPIRED_TOKENS_DAYS', default=7, cast=int)
AUDIT_RETENTION_DAYS = config('AUDIT_RETENTION_DAYS', default=90, cast=int)
```

### Configurações de Rate Limiting

```python
# Rate limiting
RATELIMIT_USE_CACHE = 'default'
RATELIMIT_VIEW = 'apps.core.views.rate_limit_exceeded'
RATELIMIT_ENABLE = True
```

## 📧 Configurações de Email

### Configuração Base

```python
# Email configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@lhctap.com')

# Security alert emails
SECURITY_ALERT_EMAILS = config('SECURITY_ALERT_EMAILS', default='admin@lhctap.com').split(',')
```

### Configurações de Produção

```python
# settings/production.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'lhctap@example.com'
EMAIL_HOST_PASSWORD = config('EMAIL_PASSWORD')
```

## 📊 Configurações de Logging

### Configuração Base

```python
# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'lhctap.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'lhctap.api': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Configurações de Produção

```python
# settings/production.py
LOGGING['handlers']['file']['filename'] = '/var/log/lhctap/django.log'
LOGGING['handlers']['security_file']['filename'] = '/var/log/lhctap/security.log'

# Adicionar handler de email para erros críticos
LOGGING['handlers']['mail_admins'] = {
    'level': 'ERROR',
    'class': 'django.utils.log.AdminEmailHandler',
    'formatter': 'verbose',
}

LOGGING['loggers']['django']['handlers'].append('mail_admins')
```

## 🌐 Configurações de Ambiente

### Desenvolvimento

```python
# settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database (SQLite para desenvolvimento)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Email (console para desenvolvimento)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Cache (local para desenvolvimento)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Debug toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### Produção

```python
# settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='lhctap.example.com').split(',')

# Database (PostgreSQL para produção)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c default_transaction_isolation=read_committed'
        },
        'CONN_MAX_AGE': 600,
    }
}

# Security
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
```

### Teste

```python
# settings/testing.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['testserver']

# Database (em memória para testes)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Cache (local para testes)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Email (console para testes)
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Password hashers (mais rápido para testes)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable migrations for tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()
```

## 🔧 Variáveis de Ambiente

### Arquivo .env

```bash
# Database
DB_NAME=lhctap
DB_USER=lhctap_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=lhctap@example.com
EMAIL_HOST_PASSWORD=email_password
DEFAULT_FROM_EMAIL=noreply@lhctap.com
SECURITY_ALERT_EMAILS=admin@lhctap.com,security@lhctap.com

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=lhctap.example.com,www.lhctap.example.com

# System
TOKEN_EXPIRY_SECONDS=30
MAX_VALIDATIONS_PER_MINUTE=10
MAX_VALIDATIONS_PER_IP_HOUR=100
CLEANUP_EXPIRED_TOKENS_DAYS=7
AUDIT_RETENTION_DAYS=90

# Debug (apenas desenvolvimento)
DEBUG=True
```

### Configuração com python-decouple

```python
from decouple import config

# Configurações com valores padrão
DEBUG = config('DEBUG', default=False, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-key')
DATABASE_URL = config('DATABASE_URL', default='sqlite:///db.sqlite3')

# Configurações obrigatórias em produção
if not DEBUG:
    SECRET_KEY = config('SECRET_KEY')  # Obrigatório
    DB_PASSWORD = config('DB_PASSWORD')  # Obrigatório
```

## 🐳 Configurações Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN useradd --create-home --shell /bin/bash lhctap
USER lhctap

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "lhctap.wsgi:application"]
```

### docker-compose.yml

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

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DB_HOST=db
      - DB_NAME=lhctap
      - DB_USER=lhctap_user
      - DB_PASSWORD=lhctap_pass
      - REDIS_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
```

## 📊 Configurações de Monitoramento

### Health Check

```python
# settings/base.py
HEALTH_CHECK_ENABLED = True
HEALTH_CHECK_ENDPOINT = '/health/'

# Configurações de health check
HEALTH_CHECK_DATABASE = True
HEALTH_CHECK_CACHE = True
HEALTH_CHECK_REDIS = True
```

### Métricas

```python
# Configurações de métricas
METRICS_ENABLED = True
METRICS_ENDPOINT = '/metrics/'
METRICS_BACKEND = 'prometheus'  # ou 'datadog', 'newrelic'
```

## 🔄 Configurações de Deploy

### Gunicorn

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

### Nginx

```nginx
# nginx.conf
upstream lhctap {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name lhctap.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lhctap.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://lhctap;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

## 🧪 Configurações de Teste

### pytest.ini

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = lhctap.settings.testing
python_files = tests.py test_*.py *_tests.py
addopts = --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### coverage.ini

```ini
[run]
source = .
omit = 
    */migrations/*
    */venv/*
    */env/*
    manage.py
    */settings/*
    */tests/*
    */test_*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## 🔧 Comandos de Configuração

### Scripts de Setup

```bash
#!/bin/bash
# scripts/setup.sh

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp env.example .env

# Executar migrações
python manage.py migrate

# Carregar dados iniciais
python manage.py loaddata lhctap/fixtures/initial_data.json

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

echo "Setup concluído! Execute: python manage.py runserver"
```

### Comandos de Manutenção

```bash
# Verificar configurações
python manage.py check --deploy

# Coletar arquivos estáticos
python manage.py collectstatic --noinput

# Executar migrações
python manage.py migrate

# Limpar cache
python manage.py clear_cache

# Health check
python manage.py health_check
```

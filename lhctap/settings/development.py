from .base import *
from decouple import config
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '*',  # Para desenvolvimento - REMOVER EM PRODUÇÃO
]

# Database Configuration
DATABASE_URL = config('DATABASE_URL', default='postgresql://casaos:casaos@192.168.0.48:32769/lhctap')

# Parse database URL
from urllib.parse import urlparse
db_config = urlparse(DATABASE_URL)

# Detectar o tipo de banco de dados baseado no scheme da URL
db_scheme = db_config.scheme.lower()

if db_scheme in ('mysql', 'mysql2'):
    # Configuração para MySQL/MariaDB
    ENGINE = 'django.db.backends.mysql'
    default_port = 3306
    # MySQL não precisa de connect_timeout nas OPTIONS dessa forma
    db_options = {
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'charset': 'utf8mb4',
    }
elif db_scheme == 'postgresql' or db_scheme.startswith('postgres'):
    # Configuração para PostgreSQL
    ENGINE = 'django.db.backends.postgresql'
    default_port = 5432
    db_options = {
        'connect_timeout': 10,
    }
else:
    # Fallback para SQLite se não for reconhecido
    ENGINE = 'django.db.backends.sqlite3'
    default_port = None
    db_options = {}

DATABASES = {
    'default': {
        'ENGINE': ENGINE,
        'NAME': db_config.path[1:] if db_config.path else ':memory:',
        'USER': db_config.username or '',
        'PASSWORD': db_config.password or '',
        'HOST': db_config.hostname or '',
        'PORT': db_config.port or (default_port if default_port else ''),
        'OPTIONS': db_options,
    }
}

# Se for SQLite, não usar HOST e PORT
if ENGINE == 'django.db.backends.sqlite3':
    DATABASES['default']['NAME'] = BASE_DIR / 'db.sqlite3'
    DATABASES['default'].pop('HOST', None)
    DATABASES['default'].pop('PORT', None)

# Cache Configuration (dummy cache - app simples, não precisa Redis/rate limiting)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Logging Configuration
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
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'lhctap': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Rate Limiting (desabilitado - app simples, não precisa)
RATELIMIT_ENABLE = False

# Development specific settings
if DEBUG:
    # Comentado temporariamente até instalar as dependências
    # INSTALLED_APPS += ['django_extensions', 'django_debug_toolbar']
    # MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    
    # Debug toolbar configuration
    INTERNAL_IPS = [
        '127.0.0.1',
        'localhost',
    ]
    
    # Email backend for development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

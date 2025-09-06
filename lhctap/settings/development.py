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
    }
}

# Cache Configuration (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'lhctap_dev',
        'TIMEOUT': 300,
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

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'

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

"""
Configuración de desarrollo.
Usa SQLite, DEBUG=True, y secretos de desarrollo.
"""
from .base import *  # noqa

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

SECRET_KEY = 'dev-secret-key-not-for-production'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Logging más verboso en dev
LOGGING['handlers']['console']['formatter'] = 'verbose'
LOGGING['root']['level'] = 'DEBUG'  # noqa
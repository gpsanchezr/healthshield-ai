"""
Configuración de producción.
Usa PostgreSQL, WhiteNoise, y variables de entorno obligatorias.
"""
from .base import *  # noqa
from decouple import config

DEBUG = config('DEBUG', default=False, cast=bool)

SECRET_KEY = config('SECRET_KEY')

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

# PostgreSQL — vía DATABASE_URL del twelve-factor
import dj_database_url
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL'),
        conn_max_age=600,
    )
}

# Whitenoise para servir staticfiles en producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging producción
LOGGING['handlers']['console']['formatter'] = 'verbose'
LOGGING['root']['level'] = 'INFO'  # noqa
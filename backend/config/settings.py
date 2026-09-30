import pymysql
import os

pymysql.install_as_MySQLdb()

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('PROPERTY_DJANGO_SECRET_KEY', 'property-management-local-dev-only')
DEBUG = os.environ.get('PROPERTY_DEBUG', 'true').lower() in ('1', 'true', 'yes', 'on')
ALLOWED_HOSTS = [host.strip() for host in os.environ.get(
    'PROPERTY_ALLOWED_HOSTS', '127.0.0.1,localhost'
).split(',') if host.strip()]

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'apps.core',
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': []},
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('PROPERTY_DB_NAME', 'property_management'),
        'USER': os.environ.get('PROPERTY_DB_USER', 'root'),
        'PASSWORD': os.environ.get('PROPERTY_DB_PASSWORD', ''),
        'HOST': os.environ.get('PROPERTY_DB_HOST', 'localhost'),
        'PORT': os.environ.get('PROPERTY_DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT 配置
JWT_SECRET = os.environ.get('PROPERTY_JWT_SECRET', 'property-management-jwt-local-dev-only')
JWT_EXPIRE_HOURS = int(os.environ.get('PROPERTY_JWT_EXPIRE_HOURS', '24'))

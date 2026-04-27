import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-your-secret-key-here'
DEBUG = True
ALLOWED_HOSTS = [
    'anatoliabox.store',
    'api.anatoliabox.store',
    'admin.anatoliabox.store',
    'localhost',
    '127.0.0.1',
]

# CSRF ve Güvenlik Yapılandırması
CSRF_TRUSTED_ORIGINS = [
    'https://admin.anatoliabox.store',
    'http://admin.anatoliabox.store',
    'https://api.anatoliabox.store',
    'http://api.anatoliabox.store',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

CORS_ALLOWED_ORIGINS = [
    'https://api.anatoliabox.store',
    'http://api.anatoliabox.store',
]

# Session ve Cookie izolasyonu/paylaşımı
# Tüm alt alan adlarında oturumun korunması için nokta ile başlar
SESSION_COOKIE_DOMAIN = '.anatoliabox.store'
CSRF_COOKIE_DOMAIN = '.anatoliabox.store'

# Nginx üzerinden gelen Header'ları tanıması için
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'django_hosts',
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    
    # Internal
    'pool',
]

MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',  # En üstte olmalı
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_hosts.middleware.HostsResponseMiddleware', # En altta olmalı
]

ROOT_HOSTCONF = 'config.hosts'
DEFAULT_HOST = 'api'

ROOT_URLCONF = 'config.urls'

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

AUTH_USER_MODEL = 'pool.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'kurye_db',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

WSGI_APPLICATION = 'config.wsgi.application'
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

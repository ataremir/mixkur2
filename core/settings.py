import os
from pathlib import Path
from datetime import timedelta

# .env dosyasını bağımlılık olmadan (pure python) yükleyen fonksiyon
def load_env_file(env_path):
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)

BASE_DIR = Path(__file__).resolve().parent.parent

# Ortam değişkenlerini yükle
load_env_file(os.path.join(BASE_DIR, '.env'))


# Güvenlik Ayarları (.env'den okunur)
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# Uygulama Tanımı
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
    'isletme_app',
    'telegram_bot',
    'analytics_app',
    'demo_app',
]

MIDDLEWARE = [
    'django_hosts.middleware.HostsRequestMiddleware',       # En üstte
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.AdminAccessMiddleware',
    'core.middleware.IsletmeAccessMiddleware',
    'core.middleware.APIAccessMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'analytics_app.middleware.IPLoggerMiddleware',           # IP Loglama
    'django_hosts.middleware.HostsResponseMiddleware',       # En altta
]

# Subdomain Yapılandırması
ROOT_HOSTCONF = 'core.hosts'
DEFAULT_HOST = 'www'
ROOT_URLCONF = 'core.urls'

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

# Custom User Model
AUTH_USER_MODEL = 'pool.User'

# Veritabanı Yapılandırması (.env'den okunur)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'sanal_kurye_db'),
        'USER': os.getenv('DB_USER', 'kurye_admin'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Şifre Doğrulama
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Dil ve Zaman Dilimi
LANGUAGE_CODE = 'tr-tr'
TIME_ZONE = 'Europe/Istanbul'
USE_I18N = True
USE_TZ = True

# Statik ve Medya Dosyaları
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CSRF ve Session Ayarları
CSRF_TRUSTED_ORIGINS = [url.strip() for url in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if url.strip()]
SESSION_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN', '.anatoliabox.store')
CSRF_COOKIE_DOMAIN = os.getenv('SESSION_COOKIE_DOMAIN', '.anatoliabox.store')

# Giriş/Çıkış Yönlendirmeleri
LOGIN_URL = '/giris/'
LOGIN_REDIRECT_URL = '/dashboard/'

# REST Framework
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

# ──────────────────────────────────────────────────
# Celery Yapılandırması (Redis Backend)
# ──────────────────────────────────────────────────
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Istanbul'

# ──────────────────────────────────────────────────
# Telegram Bot Ayarları
# ──────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_COURIER_GROUP_ID = os.getenv('TELEGRAM_COURIER_GROUP_ID', '')

# Sabit kurye ücreti (₺)
DEFAULT_DELIVERY_FEE = float(os.getenv('DEFAULT_DELIVERY_FEE', '50.00'))

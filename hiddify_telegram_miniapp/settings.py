import os
from pathlib import Path

# --- Configuration Section ---
# Replace the placeholder values below with your actual credentials.
# ---
# Django Settings
SECRET_KEY = "aa314c0bafe03f4f5408d8a77c53e413"
DEBUG = True

# PostgreSQL Database Settings
DB_NAME = "database"
DB_USER = "admin"
DB_PASSWORD = "admin1234"
DB_HOST = "localhost"
DB_PORT = "5432"

# Telegram Bot Settings
TELEGRAM_BOT_TOKEN = "8382768243:AAHv8Jj_8Z0D25h-AqaFIfoC9Zj54gka_C4"
BOT_USERNAME = "albaloovpnhidiffybot"  # without the @

# Admin & Site Settings
TELEGRAM_ADMIN_CHAT_ID = "6717722573"
SITE_URL = "albaloo.site"

# Bank Details for Payments
ADMIN_BANK_CARD = "6037-9977-0000-1111"
ADMIN_BANK_NAME = "نام صاحب حساب"
# --- End of Configuration Section ---


# --- Standard Django Settings ---
# (Usually no need to change the code below)
# ---
BASE_DIR = Path(__file__).resolve().parent.parent
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'shop.urls'

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
                'shop.context_processors.global_settings',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
    }
}

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = 'shop:home'
LOGOUT_REDIRECT_URL = 'shop:home'
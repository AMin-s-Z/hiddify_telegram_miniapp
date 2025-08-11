from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'rest_framework',
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

ROOT_URLCONF = 'hiddify_telegram_miniapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'hiddify_telegram_miniapp.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'database',          # نام دیتابیسی که ساختید
        'USER': 'admin',            # نام کاربری که ساختید
        'PASSWORD': 'admin1234',      # رمز عبوری که تعیین کردید
        'HOST': 'localhost',              # معمولاً همین localhost است
        'PORT': '5432',                   # پورت پیش‌فرض PostgreSQL
    }
}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# اطمینان از وجود پوشه media
if not os.path.exists(MEDIA_ROOT):
    os.makedirs(MEDIA_ROOT)

# اطمینان از وجود پوشه receipts
RECEIPTS_DIR = os.path.join(MEDIA_ROOT, 'receipts')
if not os.path.exists(RECEIPTS_DIR):
    os.makedirs(RECEIPTS_DIR)
    # تنظیم دسترسی برای پوشه جدید
    os.chmod(RECEIPTS_DIR, 0o777)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Telegram Settings
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
TELEGRAM_BOT_USERNAME = config('TELEGRAM_BOT_USERNAME')
ADMIN_TELEGRAM_ID = config('ADMIN_TELEGRAM_ID')

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'



# Bank Settings
BANK_CARD_NUMBER = config('BANK_CARD_NUMBER')

# برای آپلود فایل
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
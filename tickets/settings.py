"""
Django settings for tickets project.

Generated by 'django-admin startproject' using Django 4.1.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
from datetime import timedelta
from pathlib import Path
from environs import Env
import os
env = Env()
env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

PORTREDIS = env.str("PORTREDIS")
APP_NAME_CELERY = env.str("APP_NAME_CELERY")
SUPPORTBOT = env.str("SUPPORTBOT")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-@4sam!l!rt52jm_45govd0+rws#ieetc-0!fa$sy&&d5c8no_o'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
CHANNEL_REDIS_HOST = 6380
ALLOWED_HOSTS = ['*']
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# if DEBUG:
CORS_ALLOW_ALL_ORIGINS=True

CORS_ALLOW_HEADERS = [
    "*"
]
CSRF_TRUSTED_ORIGINS = ['pashtonp.space']
# if not DEBUG:
#     CSRF_TRUSTED_ORIGINS = ['https://pashtonp.space'] # FIX admin CSRF token issue


# Application definition

INSTALLED_APPS = [
    'sslserver',
    'channels',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'backend',
    'rest_framework_simplejwt.token_blacklist',
    # 'rest_framework',
    'django.contrib.staticfiles',
]

ASGI_APPLICATION = "tickets.asgi.application"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "corsheaders.middleware.CorsMiddleware",
]
DATA_UPLOAD_MAX_NUMBER_FIELDS = None
CELERY_BROKER_URL = PORTREDIS
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'


ROOT_URLCONF = 'tickets.urls'
AUTH_USER_MODEL = 'backend.User'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'tickets.wsgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6380)],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


import rsa

with open('Profiat-GramDesk-Pub.pem', 'r') as content_file:
    PROFIAT_PUBKEY = rsa.PublicKey.load_pkcs1_openssl_pem(content_file.read())

with open('Profiat-GramDesk-Priv.pem', 'r') as content_file:
    PEERXBOT_PUBKEY = content_file.read()


with open('privateKey_jwt.pem', 'r') as content_file:
    private_key_jwt = content_file.read()

with open('publicKey_jwt.pem', 'r') as content_file:
    pub_key_jwt = content_file.read()


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=2),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'RS512',
    'SIGNING_KEY': private_key_jwt,
    'VERIFYING_KEY': pub_key_jwt,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    "TOKEN_OBTAIN_SERIALIZER": "dispatcher.serializers.MyTokenObtainPairSerializer",

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    "TOKEN_REFRESH_SERIALIZER": "dispatcher.serializers.MyTokenRefreshSerializer",
    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(days=10000),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=10000),
}

# PROFIAT_PUBKEY=123


# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATIC_URL = 'static/'
import os
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

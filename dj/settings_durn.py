from django.core.management.utils import get_random_secret_key

from dj.settings import *

# ----------------------------------------------------------------------------------------------------------------------

# SECRET_KEY = "django-insecure-keurhx3%020a*z*%72!7_x@n)&k0hid-$e#4&-d&@*&g-k3%v-"
with open('/home/user/durn/django-key.txt') as f:
    SECRET_KEY = f.read().strip()

WSGI_APPLICATION = "dj.wsgi_durn.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'localhost',
        'NAME': 'durn',
        'USER': 'durnuser',
        'PASSWORD': 'x1941ab17v',
    }
}

# Главая папка Медиа
MEDIA_ROOT = '/home/user/durn/media/'

# Параметры сессии стандартной авторизации django
SESSION_EXPIREOD_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 600

# Параметры сессии jwt авторизации graphene django
GRAPHQL_JWT = {
    'JWT_VERIFY_EXPIRATION': True,
    'JWT_EXPIRATION_DELTA': timedelta(minutes=15),
    'JWT_REFRESH_EXPIRATION_DELTA': timedelta(days=1),
}

# Профилировщик silk - отключение перехвата запросов
SILKY_INTERCEPT_PERCENT = 0

DEBUG = False
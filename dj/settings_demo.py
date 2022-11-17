from dj.settings import *

# ----------------------------------------------------------------------------------------------------------------------

SECRET_KEY = "django-insecure-00qw+5p=v_kay7!4jdiverss=j6a)i%^z_b(2g%*%e9cm!&$p1"

WSGI_APPLICATION = "dj.wsgi_demo.application"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'HOST': 'localhost',
        'NAME': 'demo',
        'USER': 'demouser',
        'PASSWORD': '16384valpha',
    }
}

# Главая папка Медиа
MEDIA_ROOT = '/home/user/demo/media/'


# Параметры сессии стандартной авторизации django
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
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

#DEBUG = False
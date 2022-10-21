from django.contrib.auth import user_logged_in, user_login_failed, user_logged_out
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import models
import random


# ----------------------------------------------------------------------------------------------------------------------
# Расширенные атрибуты пользователей
# ----------------------------------------------------------------------------------------------------------------------

class UserAttr(models.Model):
    user = models.OneToOneField(User, verbose_name='Пользователь', on_delete=models.CASCADE, primary_key=True)
    color = models.CharField(verbose_name='Цвет', max_length=7, blank=False, null=False, default='#75dfff')
    openObjectsInNewWindow = models.BooleanField(verbose_name='Открывать объекты в новом окне', blank=False, null=False, default=False)

    class Meta:
        verbose_name = 'Атрибуты пользователей'
        verbose_name_plural = 'Атрибуты пользователей'

    def __str__(self):
        return f'Атрибуты для "{self.user.username}"'

# При сохранении объекта User - создаем его расширенные атрибуты
@receiver(post_save, sender=User)
def createUserAttr(sender, instance, **kwargs):
    if not hasattr(instance, 'userattr'):
        userAttr = UserAttr()
        userAttr.user = instance
        userAttr.color = '#' + '%06x' % random.randint(0, 0xFFFFFF)
        userAttr.save()


# ----------------------------------------------------------------------------------------------------------------------
# Журнал действий пользователей
# ----------------------------------------------------------------------------------------------------------------------

class UserAction(models.Model):
    moment = models.DateTimeField(verbose_name='Дата', default=timezone.now)
    user = models.ForeignKey(User, verbose_name='Пользователь', null=True, blank=True, on_delete=models.SET_NULL)
    object = models.CharField(verbose_name='Объект', max_length=255, blank=True, null=True)
    msg = models.CharField(verbose_name='Действие', max_length=255, blank=True, null=True)
    warnLvl = models.IntegerField(verbose_name='Важность', default=0)
    link = models.CharField(verbose_name='Ссылка', max_length=255, blank=True, null=True)
    diff = models.CharField(verbose_name='Изменение', max_length=1023, blank=True, null=True)


    def __str__(self):
        momentF = self.moment.strftime('%Y-%m-%d %H:%M:%S')
        return f'{momentF}|{self.user}|{self.warnLvl}|{self.object}|{self.msg}|{self.diff}'

    class Meta:
        verbose_name = 'Действие пользователя'
        verbose_name_plural = 'Действия пользователей'
        ordering = ['-moment']

# Запись действия пользователя
def logUserAction(user, obj, msg, wl=0, link=None, diff=None):
    from django.conf import settings
    # baseAddress = 'http://localhost:8080'
    baseAddress = settings.UA_BASEADDR
    ua = UserAction()
    ua.user = user
    ua.object = obj
    ua.msg = msg
    ua.warnLvl = wl
    # ua.link = link
    ua.link = f'{baseAddress}{link}'
    ua.diff = diff
    ua.save()
    print(f'{user}|{wl}|{obj}|{msg}|{link}|{diff}')

# Получить разницу в экземплярах модели
def modelDiff(old, new):
    if type(old) != type(new):
        return 'error - different types'
    res = ''
    for field in type(old)._meta.get_fields():
        if field.concrete:
            attr = field.name
            oldVal = getattr(old, attr)
            newVal = getattr(new, attr)
            if oldVal != newVal:
                res += f'{attr}: {oldVal} -> {newVal} | '
    return res[:-3]

# -----------------------------------------------------------------------------------------------------------------------
# Логинг событий
# -----------------------------------------------------------------------------------------------------------------------

# удачный вход пользователя
@receiver(user_logged_in)
def log_user_login(sender, user, **kwargs):
    logUserAction(user, 'auth', f'login ok')

# неудачный вход пользователя
@receiver(user_login_failed)
def log_user_login_failed(sender, user=None, **kwargs):
    logUserAction(user, 'auth', f'login failed', 10)

# выход пользователя
@receiver(user_logged_out)
def log_user_logout(sender, user, **kwargs):
    logUserAction(user, 'auth', f'logout')

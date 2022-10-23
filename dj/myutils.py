import json
import os
from datetime import *
from enum import Enum
from uuid import uuid4
from dateutil.relativedelta import relativedelta
import calendar
import decimal


# Форматировать сумму
def frmSum(number):
    return '{:,.0f}'.format(number).replace(',', ' ').replace('.', ',')


# Получить квартал
def get_quarter(_date):
    return (_date.month - 1) // 3 + 1


# Получить первый день квартала
def get_first_day_of_the_quarter(_date):
    return datetime(_date.year, 3 * ((_date.month - 1) // 3) + 1, 1)


# Получить последний день квартала
def get_last_day_of_the_quarter(_date):
    quarter = get_quarter(_date)
    return datetime(_date.year + 3 * quarter // 12, 3 * quarter % 12 + 1, 1)


# Интервалы - для журнала операций
class LogIntv(Enum):
    INF = -1
    DAY = 0
    WEEK = 1
    MONTH = 2
    QUART = 3
    YEAR = 4
    NDAYS = 5


# Получить временной интервал
def parseTsIntv(tsBegin, tsEnd, intv, intv_n):
    if tsBegin == -1:
        now = datetime.now()
        if intv == LogIntv.INF.value:
            tsBegin = datetime(1970, 1, 1)
            tsEnd = date(9999, 12, 31)
        elif intv == LogIntv.DAY.value:
            tsBegin = now - relativedelta(hour=0, minute=0, second=0)
            tsEnd = now + relativedelta(hour=23, minute=59, second=59)
        elif intv == LogIntv.WEEK.value:
            tsBegin = now - relativedelta(weeks=1, weekday=calendar.MONDAY, hour=0, minute=0, second=0)
            tsEnd = now + relativedelta(weeks=0, weekday=calendar.SUNDAY, hour=23, minute=59, second=59)
        elif intv == LogIntv.MONTH.value:
            tsBegin = now - relativedelta(day=1, hour=0, minute=0, second=0)
            tsEnd = now + relativedelta(day=31, hour=23, minute=59, second=59)
        elif intv == LogIntv.QUART.value:
            tsBegin = get_first_day_of_the_quarter(now)
            tsEnd = get_last_day_of_the_quarter(now) - relativedelta(days=1, hour=23, minute=59, second=59)
        elif intv == LogIntv.YEAR.value:
            tsBegin = now - relativedelta(month=1, day=1, hour=0, minute=0, second=0)
            tsEnd = now + relativedelta(month=12, day=31, hour=23, minute=59, second=59)
        elif intv == LogIntv.NDAYS.value:
            tsBegin = now - relativedelta(days=(intv_n - 1), hour=0, minute=0, second=0)
            tsEnd = now + relativedelta(hour=23, minute=59, second=59)
    else:
        tsBegin = datetime.fromtimestamp(int(tsBegin))
        tsEnd = datetime.fromtimestamp(int(tsEnd)) + relativedelta(hour=23, minute=59, second=59)
    return tsBegin, tsEnd


# Кастомная сериализация объекта по типам
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.timestamp()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, bool):
            return int(obj)
        return super(CustomJSONEncoder, self).default(obj)


# Сформировать случайное имя файла (для загрузки картинок)
def randomFileName(path):
    def wrapper(instance, filename):
        ext = filename.split('.')[-1]
        if instance.pk:
            filename = '{}.{}'.format(instance.pk, ext)
        else:
            filename = '{}.{}'.format(uuid4().hex, ext)
        return os.path.join(path, filename)

    return wrapper

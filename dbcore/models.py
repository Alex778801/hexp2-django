import os
import random

from django.contrib.auth.models import User
from django.db.models import ImageField
from django.utils import timezone

from django.conf import settings

from .models_base import *
from dj.myutils import LogIntv


# ----------------------------------------------------------------------------------------------------------------------
# Системные параметры
class SysParam(models.Model):
    name = models.CharField(verbose_name='Название', max_length=100)
    value = models.CharField(verbose_name='Значение', max_length=1000)


# ----------------------------------------------------------------------------------------------------------------------
# Проекты
class Project(HierarchyOrderModelExt, SecurityModelExt):
    name = models.CharField(verbose_name='Название', max_length=100, default='Новый проект')
    prefCostTypeGroup = models.ForeignKey('CostType', related_name='prefCostTypeGroup', verbose_name='Группа статей',
                                          null=True, blank=True,
                                          on_delete=models.SET_NULL)
    prefAgentGroup = models.ForeignKey('Agent', related_name='prefAgentGroup', verbose_name='Группа контрагентов',
                                       null=True, blank=True,
                                       on_delete=models.SET_NULL)
    prefFinOperLogIntv = models.IntegerField(verbose_name='Интервал журнала операций', default=-1)
    prefFinOperLogIntv_n = models.IntegerField(verbose_name='Параметр интервала журнала операций', default=1)
    info = models.TextField(verbose_name='Заметки', max_length=20000, null=True, blank=True, default='')

    class Ext:
        useHierarchy = True
        useOrder = True
        logIntv = [
            {'id': LogIntv.INF, 'fn': '∞'},
            {'id': LogIntv.DAY, 'fn': 'Сутки'},
            {'id': LogIntv.WEEK, 'fn': 'Неделя'},
            {'id': LogIntv.MONTH, 'fn': 'Месяц'},
            {'id': LogIntv.QUART, 'fn': 'Квартал'},
            {'id': LogIntv.YEAR, 'fn': 'Год'},
            {'id': LogIntv.NDAYS, 'fn': 'n дней'},
        ]

    def __str__(self):
        return str(self.name or '')

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['-isGrp', 'parent_id', 'order']


# ----------------------------------------------------------------------------------------------------------------------
# Статьи прихода/расхода
class CostType(HierarchyOrderModelExt, SecurityModelExt):
    name = models.CharField(verbose_name='Название', max_length=100, default='Новая статья')
    isOutcome = models.BooleanField(verbose_name='Расходная', default=True)
    color = models.CharField(verbose_name='Цвет', max_length=20, default='#AAAAAA')

    class Ext:
        useHierarchy = True
        useOrder = True

    def __str__(self):
        if self.isOutcome:
            return str(self.name or '')
        else:
            return "[+] " + str(self.name or '')

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-isGrp', 'parent_id', 'order']


# ----------------------------------------------------------------------------------------------------------------------
# Агенты
class Agent(HierarchyOrderModelExt, SecurityModelExt):
    name = models.CharField(verbose_name='Название', max_length=100, default='Новый контрагент')

    class Ext:
        useHierarchy = True
        useOrder = True

    def __str__(self):
        return str(self.name or '')

    class Meta:
        verbose_name = 'Агент'
        verbose_name_plural = 'Агенты'
        ordering = ['-isGrp', 'parent_id', 'order']


# ----------------------------------------------------------------------------------------------------------------------
# Финансовые операции
class FinOper(SecurityModelExt):
    project = models.ForeignKey(Project, verbose_name='Проект', on_delete=models.CASCADE)
    costType = models.ForeignKey(CostType, related_name='costType', verbose_name='Статья', null=True, blank=False,
                                 on_delete=models.SET_NULL)
    agentFrom = models.ForeignKey(Agent, related_name='agentFrom', verbose_name='Агент Откуда', null=True, blank=True,
                                  on_delete=models.SET_NULL)
    agentTo = models.ForeignKey(Agent, related_name='agentTo', verbose_name='Агент Куда', null=True, blank=True,
                                on_delete=models.SET_NULL)
    moment = models.DateTimeField(verbose_name='Дата', default=timezone.now)
    amount = models.DecimalField(verbose_name='Сумма', max_digits=16, decimal_places=0, default=0)
    notes = models.CharField(verbose_name='Примечание', max_length=2000, null=True, blank=True, default='')
    importTag = models.CharField(verbose_name='Метка импорта', max_length=50, null=True, blank=True, default='')

    def __str__(self):
        return str(self.project.pk or '') + ":" + str(self.project or '') + "|id:" + \
               str(self.pk) + "|" + str(self.costType or '') + "|" + str(self.notes or '') + " = " + str(
            self.amount or '')

    class Meta:
        verbose_name = 'Операция'
        verbose_name_plural = 'Операции'
        ordering = ['-moment']


# ----------------------------------------------------------------------------------------------------------------------
# Формирование имени файла фото
def getPhotoLocation(instance, filename):
    name, ext = os.path.splitext(filename)
    rand = random.randrange(100000000000, 900000000000, 1)
    newName = f'{instance.finOper.project_id}-{instance.finOper_id}-{rand}'
    return f'{settings.FINOPER_PHOTO_DIR}/{newName}{ext}'


# Фото финансовых операций
class Photo(models.Model):
    finOper = models.ForeignKey(FinOper, verbose_name='Операция', on_delete=models.CASCADE)
    image = ImageField(verbose_name='Фото', upload_to=getPhotoLocation)

    def __str__(self):
        return str(self.finOper.notes or '') + ' = ' + str(self.finOper.amount or '') + '; фото: ' + self.image.name

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'
        ordering = ['finOper']


# ----------------------------------------------------------------------------------------------------------------------
# Бюджеты проектов
class Budget(models.Model):
    project = models.ForeignKey(Project, verbose_name='Проект', on_delete=models.CASCADE)
    costType = models.ForeignKey(CostType, verbose_name='Статья', null=True, blank=False, on_delete=models.SET_NULL)
    order = models.IntegerField(verbose_name='Порядок', default=-1)
    amount = models.DecimalField(verbose_name='Сумма', max_digits=16, decimal_places=0, default=0)
    notes = models.CharField(verbose_name='Примечание', max_length=2000, null=True, blank=False, default='')

    def __str__(self):
        return str(self.notes or '') + ' = ' + str(self.amount or '')

    class Meta:
        verbose_name = 'Бюджет'
        verbose_name_plural = 'Бюджеты'
        ordering = ['costType', 'order']

    # Получить следующий порядок (для нового элемента)
    def getNextOrder(self):
        agg = self.__class__.objects.filter(project=self.project, costType=self.costType).aggregate(Max('order'))
        if agg['order__max'] is None:
            return 0
        else:
            return agg['order__max'] + 1

    # Перед сохранением - установим порядок элемента
    def save(self, *args, **kwargs):
        if self.order == -1:
            self.order = self.getNextOrder()
        super().save(*args, **kwargs)

    # После удаления - пересчитаем порядки элементов, следующих за удаляемым
    @receiver(pre_delete)
    def afterDelete(sender, instance, using, **kwargs):
        if sender != Budget:
            return
        recs = Budget.objects.filter(project=instance.project, costType=instance.costType, order__gt=instance.order)
        for r in recs:
            r.order -= 1
            r.save()

    # Сменить порядок элемента (переместить элемент)
    def changeOrder(self, toOrder):
        if toOrder < 0 or toOrder >= self.getNextOrder():
            # raise Exception(f'{self.__class__}', 'changeOrder', 'new order is out of range')
            return
        fromOrder = self.order
        if fromOrder > toOrder:
            recs = self.__class__.objects.filter(project=self.project, costType=self.costType, order__gte=toOrder,
                                                 order__lt=fromOrder)
            for r in recs:
                r.order += 1
                r.save()
        else:
            recs = self.__class__.objects.filter(project=self.project, costType=self.costType, order__gt=fromOrder,
                                                 order__lte=toOrder)
            for r in recs:
                r.order -= 1
                r.save()
        self.order = toOrder
        self.save()

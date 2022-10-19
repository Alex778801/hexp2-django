import json

from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Max
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from functools import reduce
from django.utils.translation import gettext as _
import re

# ----------------------------------------------------------------------------------------------------------------------
# Вспомогательные функции для обработки прав доступа

# Получить список пользователей из строки
def aclParseStr(_str):
    return re.split(";|,", _str.replace(' ', ''))

# Проверить корректность (существование) имен пользователей в списке доступа
def aclCheckUsers(users):
    for user in users:
        if user != '*' and user != '&':
            try:
                User.objects.get(username=user)
            except:
                raise Exception(f'СКД {users} содержит несуществующего пользователя "{user}"')


# Проверить существование пользователей в списоке контроля доступа
def aclUsersExist(aclStr):
    users = aclParseStr(aclStr)
    for user in users:
        if user != '*' and user != '&':
            try:
                User.objects.get(username=user)
            except:
                return False, user
    return True, None


# Запаковать списки доступа в словарь
def aclPack(readStr, omodStr, amodStr, reportStr):
    read = aclParseStr(readStr)
    aclCheckUsers(read)
    omod = aclParseStr(omodStr)
    aclCheckUsers(omod)
    amod = aclParseStr(amodStr)
    aclCheckUsers(amod)
    report = aclParseStr(reportStr)
    aclCheckUsers(report)
    return {'read': read, 'o_mod': omod,  'a_mod': amod, 'report': report}

# Распаковать список доступа из словаря по ключу-домену
def aclUnpack(domain):
    return reduce(lambda a, b: '' + a + '; ' + b, domain)

# Проверить административные привилегии пользователя
def isAdmin(user):
    # Администраторам - всегда разрешен
    adminsList = ('Admin', 'admin', 'Administrators', 'administrators')
    if user.username in adminsList:
        return True, 'By admin'
    # Членам групп администраторов - всегда разрешен
    adminsGrpList = ('Admin', 'admin', 'Administrators', 'administrators')
    if user.groups.filter(name__in=adminsGrpList).exists():
        return True, 'By admins group'
    return False

# Проверить ПРАВО
def aclCheckRights(model, user: User, domain):
    # Список доступа по домену
    acl = json.loads(model.acl)
    aclList =  aclParseStr(aclUnpack(acl[domain]))
    # ВСЕ *
    if '*' in aclList:
        return True, 'By * (all)'
    # ВЛАДЕЛЕЦ (создатель)
    if '&' in aclList and User == model.owner:
        return True, 'By & (owner)'
    # Конкретный пользователь
    if user.username in aclList:
        return True, 'By user name'
    # Админ
    return isAdmin(user)

# Проверить право на чтение
def aclCanRead(model, user: User):
    return aclCheckRights(model, user, 'read')

# Проверить право на изменение Владельцем
def aclCanOwnerMod(model, user):
    return aclCheckRights(model, user, 'o_mod')

# Проверить право на изменение ЛЮБЫМ
def aclCanAllMod(model, user):
    return aclCheckRights(model, user, 'a_mod')

# Проверить право на изменение - общий вид
def aclCanMod(model, user):
    if model.owner == user:
        return aclCanOwnerMod(model, user)
    else:
        return aclCanAllMod(model, user)

# Проверить право на построение отчетов
def aclCanReport(model, user):
    return aclCheckRights(model, user, 'report')


# ----------------------------------------------------------------------------------------------------------------------
# Базовый класс для организации прав доступа, аудита и безопаности
class SecurityModelExt(models.Model):
    owner = models.ForeignKey(User, verbose_name='Владелец', null=True, blank=True, on_delete=models.SET_NULL)
    acl = models.CharField(verbose_name='Права доступа', max_length=1000,
                           default='{"read": ["*"], "o_mod": ["*"], "a_mod": ["&"], "report": ["*"] }')
    #  ^  '*' все, '&' владелец

    class Meta:
        abstract = True


# ----------------------------------------------------------------------------------------------------------------------
# Базовый класс для организации иерархии объектов и порядка следования в списке
class HierarchyOrderModelExt(models.Model):
    parent = models.ForeignKey('self', related_name='children', verbose_name='Родитель', null=True, blank=True, on_delete=models.CASCADE)
    isGrp = models.BooleanField(verbose_name='Группа', default=False)
    order = models.IntegerField(verbose_name='Порядок', default=-1)

    class Ext:
        useHierarchy = False
        useOrder = False

    class Meta:
        abstract = True

    # Получить следующий порядок (для нового элемента)
    def getNextOrder(self):
        if not self.Ext.useOrder:
            return -1
        agg = self.__class__.objects.filter(parent=self.parent, isGrp=self.isGrp).aggregate(Max('order'))
        if agg['order__max'] is None:
            return 0
        else:
            return agg['order__max'] + 1

    # Перед сохранением - установим порядок элемента
    def save(self, *args, **kwargs):
        if not self.Ext.useOrder:
            return
        if self.order == -1:
            self.order = self.getNextOrder()
        super().save(*args, **kwargs)

    # После удаления - пересчитаем порядки элементов, следующих за удаляемым
    @receiver(pre_delete)
    def afterDelete(sender, instance, using, **kwargs):
        if not issubclass(sender, HierarchyOrderModelExt):
            return
        if sender.Ext.useOrder and sender.Ext.useHierarchy:
            recs = sender.objects.filter(parent=instance.parent, isGrp=instance.isGrp, order__gt=instance.order)
            for r in recs:
                r.order -= 1
                r.save()

    # Сменить порядок элемента (переместить элемент)
    def changeOrder(self, toOrder):
        if not self.Ext.useOrder:
            raise Exception(f'{self.__class__}', 'changeOrder', 'useOrder is not active')
        if toOrder < 0 or toOrder >= self.getNextOrder():
            raise Exception(f'{self.__class__}', 'changeOrder', 'new order is out of range')
        fromOrder = self.order
        if fromOrder > toOrder:
            recs = self.__class__.objects.filter(parent=self.parent, isGrp=self.isGrp, order__gte=toOrder,
                                                 order__lt=fromOrder)
            for r in recs:
                r.order += 1
                r.save()
        else:
            recs = self.__class__.objects.filter(parent=self.parent, isGrp=self.isGrp, order__gt=fromOrder,
                                                 order__lte=toOrder)
            for r in recs:
                r.order -= 1
                r.save()
        self.order = toOrder
        self.save()

    # Сменить родителя элемента - с учетом порядка
    def changeParent(self, newParent):
        if not self.Ext.useHierarchy:
            raise Exception(f'{self.__class__}', 'changeParent', 'hierarchyMode is not active')
        if self.Ext.useOrder:
            recs = self.__class__.objects.filter(parent=self.parent, isGrp=self.isGrp, order__gt=self.order)
            for r in recs:
                r.order -= 1
                r.save()
            self.parent = newParent
            self.order = self.getNextOrder()
        else:
            self.parent = newParent
        self.save()

    # Клонировать элемент
    def clone(self, newParent):
        if self.isGrp:
            raise Exception(f'{self.__class__}', 'clone', 'forbidden for group')
        new = self.__class__.objects.get(pk=self.pk)
        new.parent = newParent
        new.pk = None
        new.order = -1
        if hasattr(self, 'name'):
            setattr(new, 'name', '_' + str(self.name or ''))
        return new

    # Получить список предков элемента справочника
    def getParents(self):
        item = self
        res = []
        while item.parent is not None:
            res.insert(0, item.parent)
            item = item.parent
        res.insert(0, None)
        return res

    # Получить список предков элемента справочника оформленным путем
    def getParentsList(self):
        if self.parent is not None:
            parents = self.getParents()
            path = reduce(lambda a, b: a + b + '/', map(lambda i: str(i.name) if i is not None else '', parents))
        else:
            path = ''
        return path

    # Получить дерево групп - реркурсия
    @classmethod
    def getGroupsTreeRc(cls, tree, curParent, key):
        groups = cls.objects.filter(parent=curParent, isGrp=True).order_by('order')
        i = 0
        curKey = key
        key = key + str(i) + '-'
        for gr in groups:
            children = []
            cls.getGroupsTreeRc(children, gr, key)
            if len(children) > 0:
                tree.append({'key': curKey + str(i), 'data': gr.pk, 'label': gr.name, 'children': children})
            else:
                tree.append({'key': curKey + str(i), 'data': gr.pk, 'label': gr.name})
            i = i + 1
        return

    # Получить дерево групп
    @classmethod
    def getGroupsTree(cls):
        tree = []
        key = ''
        cls.getGroupsTreeRc(tree, None, key)
        return tree




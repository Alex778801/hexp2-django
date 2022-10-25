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

# # Получить список пользователей из строки
# def aclParseStr(_str):
#     return re.split(";|,", _str.replace(' ', ''))
#
# # Проверить корректность (существование) имен пользователей в списке доступа
# def aclCheckUsers(users):
#     for user in users:
#         if user != '*' and user != '&':
#             try:
#                 User.objects.get(username=user)
#             except:
#                 raise Exception(f'СКД {users} содержит несуществующего пользователя "{user}"')
#
#
# # Проверить существование пользователей в списоке контроля доступа
# def aclUsersExist(aclStr):
#     users = aclParseStr(aclStr)
#     for user in users:
#         if user != '*' and user != '&':
#             try:
#                 User.objects.get(username=user)
#             except:
#                 return False, user
#     return True, None
#
#
# # Запаковать списки доступа в словарь
# def aclPack(readStr, modStr, reportStr):
#     read = aclParseStr(readStr)
#     aclCheckUsers(read)
#     mod = aclParseStr(modStr)
#     aclCheckUsers(mod)
#     report = aclParseStr(reportStr)
#     aclCheckUsers(report)
#     return {'read': read, 'mod': mod, 'report': report}
#
# # Распаковать список доступа из словаря по ключу-домену
# def aclUnpack(domain):
#     return reduce(lambda a, b: '' + a + '; ' + b, domain, '')


def aclGetUsersList():
    list = [{'id': '*', 'label': 'Любой (*)'}, {'id': '&', 'label': 'Владелец (&)'}]
    userList = User.objects.all()
    for u in userList:
        list.append({'id': u.username, 'label': u.username})
    return list


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
    return False, ''


# Проверить ПРАВО
def aclCheckRights(model, acl, user: User, domain):
    # Список доступа по домену
    aclUnpack = json.loads(acl)
    if domain in aclUnpack:
        accessList = aclUnpack[domain]
    else:
        accessList = []
    if accessList is None:
        accessList = []
    # ВСЕ *
    if '*' in accessList:
        return True, 'By * (all)'
    # ВЛАДЕЛЕЦ (создатель)
    if '&' in accessList and user == model.owner:
        return True, 'By & (owner)'
    # Конкретный пользователь
    if user.username in accessList:
        return True, 'By user name'
    # Админ
    return isAdmin(user)


# Проверить право на чтение
def aclCanRead(model, acl, user: User):
    return aclCheckRights(model, acl, user, 'read')


# Проверить право на создание
def aclCanCrt(model, acl, user: User):
    return aclCheckRights(model, acl, user, 'crt')


# Проверить право на изменение
def aclCanMod(model, acl, user: User):
    return aclCheckRights(model, acl, user, 'mod')


# Проверить право на построение отчетов
def aclCanReport(model, acl, user: User):
    return aclCheckRights(model, acl, user, 'report')


# ----------------------------------------------------------------------------------------------------------------------
# Базовый класс для организации прав доступа, аудита и безопаности
class SecurityModelExt(models.Model):
    owner = models.ForeignKey(User, verbose_name='Владелец', null=True, blank=True, on_delete=models.SET_NULL)
    acl = models.CharField(verbose_name='Права доступа', max_length=1000,
                           default='{"read": ["*"], "crt": ["*"], "mod": ["&"], "report": ["*"] }')
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

    # Получить дерево групп - рекурсия
    @classmethod
    def __getGroupsTreeRc(cls, tree, curParent):
        groups = cls.objects.filter(parent=curParent, isGrp=True).order_by('order')
        for gr in groups:
            children = []
            cls.__getGroupsTreeRc(children, gr)
            if len(children) > 0:
                tree.append({'key': gr.pk, 'label': gr.name, 'children': children, 'icon': 'pi pi-fw pi-folder-open'})
            else:
                tree.append({'key': gr.pk, 'label': gr.name, 'icon': 'pi pi-fw pi-folder'})
        return

    # Получить дерево групп
    @classmethod
    def getGroupsTree(cls):
        tree = []
        cls.__getGroupsTreeRc(tree, None)
        return tree

    # Получить дерево групп и элементов - рекурсия
    @classmethod
    def __getGroupsElemsTreeRc(cls, tree, curParent):
        items = cls.objects.filter(parent=curParent).order_by('-isGrp', 'order')
        for item in items:
            children = []
            cls.__getGroupsElemsTreeRc(children, item)
            if len(children) > 0:
                tree.append({'key': item.pk, 'data': {'isGrp': item.isGrp}, 'label': item.name, 'children': children, 'icon': 'pi pi-fw pi-folder-open'})
            else:
                if item.isGrp:
                    tree.append({'key': item.pk, 'data': {'isGrp': item.isGrp}, 'label': item.name, 'icon': 'pi pi-fw pi-folder'})
                else:
                    tree.append({'key': item.pk, 'data': {'isGrp': item.isGrp}, 'label': item.name, 'icon': 'pi pi-fw pi-file'})
        return

    # Получить дерево групп и элементов
    @classmethod
    def getGroupsElemsTree(cls):
        tree = []
        cls.__getGroupsElemsTreeRc(tree, None)
        return tree


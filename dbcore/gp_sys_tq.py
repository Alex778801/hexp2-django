import json

import graphene
from django.contrib.auth.models import User
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from dbcore.models import Project, Agent, CostType, FinOper, SysParam
from dbcore.models_base import HierarchyOrderModelExt, aclGetUsersList, isAdmin


# ----------------------------------------------------------------------------------------------------------------------
# С И С Т Е М А
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# ТИПЫ
# ----------------------------------------------------------------------------------------------------------------------

# Пользователь
class UserType(DjangoObjectType):
    class Meta:
        model = User

    id = graphene.Int()
    color = graphene.String()

    # ИД пользователя
    def resolve_id(self: User, info):
        return int(self.pk)

    # Цвет оформления пользователя
    def resolve_color(self: User, info):
        return self.userattr.color if self is not None else None


# ----------------------------------------------------------------------------------------------------------------------
# ЗАПРОСЫ
# ----------------------------------------------------------------------------------------------------------------------


class SysQuery(graphene.ObjectType):
    sysParams = graphene.String()
    users = graphene.List(UserType)

    # Системные параметры
    @login_required
    def resolve_sysParams(self, info):
        tmp = {}
        for i in SysParam.objects.all().values('pk', 'name', 'value'):
            tmp[i['name']] = i['value']
        res = json.dumps(tmp, ensure_ascii=True, sort_keys=True, default=str)
        return res

    # Список пользователей
    @login_required
    def resolve_users(self, info):
        return User.objects.all()

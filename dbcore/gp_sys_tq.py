import json

import graphene
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


# ----------------------------------------------------------------------------------------------------------------------
# ЗАПРОСЫ
# ----------------------------------------------------------------------------------------------------------------------


class SysQuery(graphene.ObjectType):
    sysParams = graphene.String()

    # Системные параметры
    # @login_required
    def resolve_sysParams(self, info):
        tmp = {}
        for i in SysParam.objects.all().values('pk', 'name', 'value'):
            tmp[i['name']] = i['value']
        res = json.dumps(tmp, ensure_ascii=True, sort_keys=True, default=str)
        return res

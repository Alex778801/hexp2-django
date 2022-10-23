from enum import Enum

import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from dbcore.models import Project, Agent, CostType, FinOper
from dbcore.models_base import HierarchyOrderModelExt, aclGetUsersList, isAdmin

import json
import os
from datetime import *
from enum import Enum
from uuid import uuid4
from dateutil.relativedelta import relativedelta
import calendar
import decimal

from dj.myutils import parseTsIntv


# ----------------------------------------------------------------------------------------------------------------------
# Ф И Н А Н С О В Ы Е   О П Е Р А Ц И И
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# ТИПЫ
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# Финансовая операция
class FinOperType(DjangoObjectType):
    class Meta:
        model = FinOper

    ts = graphene.Int()
    user = graphene.String()
    ucol = graphene.String()
    pq = graphene.Int()

    # Метка времени операции в формате unix
    def resolve_ts(self: FinOper, info):
        return self.moment.timestamp()

    # Владелец операции
    def resolve_user(self: FinOper, info):
        return self.owner.username

    # Цвет владельца операции
    def resolve_ucol(self: FinOper, info):
        return self.owner.userattr.color

    # Колво фото у операции
    def resolve_pq(self: FinOper, info):
        return self.photo_set.all().count()


# ----------------------------------------------------------------------------------------------------------------------
# ЗАПРОСЫ
# ----------------------------------------------------------------------------------------------------------------------


class FinOpersQuery(graphene.ObjectType):
    finoper = graphene.Field(FinOperType, id=graphene.Int())
    finopers = graphene.List(FinOperType, projectId=graphene.Int(), tsBegin=graphene.Int(), tsEnd=graphene.Int())

    # Финансовая операция
    # @login_required
    def resolve_finoper(self, info, id):
        if id is not None:
            return FinOper.objects.get(pk=id)
        else:
            return None

    # Журнал фин операций проекта
    # @login_required
    def resolve_finopers(self, info, projectId, tsBegin, tsEnd):
        project = Project.objects.get(pk=projectId)
        tsBegin, tsEnd = parseTsIntv(tsBegin, tsEnd, project.prefFinOperLogIntv, project.prefFinOperLogIntv_n)
        return FinOper.objects.filter(project=project, moment__gte=tsBegin, moment__lte=tsEnd)

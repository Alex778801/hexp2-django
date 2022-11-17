from enum import Enum

import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from dbcore.gp_catalogs_tq import CostTypeType, AgentType, ProjectType
from dbcore.models import Project, Agent, CostType, FinOper, Photo, Budget
from dbcore.models_base import HierarchyOrderModelExt, aclGetUsersList, isAdmin, aclCanRead, aclCanMod

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
# Фото финансовой операции
class FinOperPhotoType(DjangoObjectType):

    class Meta:
        model = Photo


# Финансовая операция
class FinOperType(DjangoObjectType):
    class Meta:
        model = FinOper

    ts = graphene.Int()
    tsjs = graphene.DateTime()
    ctId = graphene.Int()
    agFromId = graphene.Int()
    agToId = graphene.Int()
    ownerId = graphene.Int()
    user = graphene.String()
    ucol = graphene.String()
    amount = graphene.Int()
    pq = graphene.Int()
    photoList = graphene.List(FinOperPhotoType)
    ctList = graphene.List(CostTypeType)
    agList = graphene.List(AgentType)
    aclList = graphene.String()
    readOnly = graphene.Boolean()

    # Метка времени операции в формате unix
    def resolve_ts(self: FinOper, info):
        return int(self.moment.timestamp())

    # Метка времени операции в формате js
    def resolve_tsjs(self: FinOper, info):
        return self.moment

    # Ид статьи
    def resolve_ctId(self: FinOper, info):
        return self.costType_id

    # Ид агента откуда
    def resolve_agFromId(self: FinOper, info):
        return self.agentFrom_id

    # Ид агента куда
    def resolve_agToId(self: FinOper, info):
        return self.agentTo_id

    # Ид владельца операции
    def resolve_ownerId(self: FinOper, info):
        return self.owner_id

    # Владелец операции
    def resolve_user(self: FinOper, info):
        return self.owner.username if self.owner is not None else None

    # Цвет владельца операции
    def resolve_ucol(self: FinOper, info):
        return self.owner.userattr.color if self.owner is not None else None

    # Сумма приведенная в инт. В оригинале десимал
    def resolve_amount(self: FinOper, info):
        return int(self.amount)

    # Список пользователей и служебных записей авторизации
    def resolve_aclList(self: FinOper, info):
        tmp = aclGetUsersList()
        res = json.dumps(tmp, ensure_ascii=True)
        return res

    # Разрешено только чтение
    def resolve_readOnly(self: FinOper, info):
        return not aclCanMod(self, self.project.acl, info.context.user)

    # Колво фото у операции
    def resolve_pq(self: FinOper, info):
        return self.photo_set.all().count()

    # Список фото
    def resolve_photoList(self: FinOper, info):
        return Photo.objects.filter(finOper=self).order_by('pk')

    # Список статей для выбора
    def resolve_ctList(self: FinOper, info):
        res = (CostType.objects.filter(parent=self.project.prefCostTypeGroup, isGrp=False)
              | CostType.objects.filter(parent=None, isGrp=False)).order_by('parent', 'order')
        # return CostType.objects.filter(parent=self.project.prefCostTypeGroup)
        return res

    # Список агентов для выбора
    def resolve_agList(self: FinOper, info):
        res = (Agent.objects.filter(parent=self.project.prefAgentGroup, isGrp=False)
              | Agent.objects.filter(parent=None, isGrp=False)).order_by('parent', 'order')
        # return Agent.objects.filter(parent=self.project.prefAgentGroup)
        return res


# Позиция бюджета
class BudgetLineType(DjangoObjectType):

    id = graphene.Int()
    amount = graphene.Int()

    class Meta:
        model = Budget

    def resolve_id(self: Budget, info):
        return int(self.pk) if self.pk is not None else None

    def resolve_amount(self: Budget, info):
        return int(self.amount) if self.amount is not None else None

    # ----------------------------------------------------------------------------------------------------------------------
# ЗАПРОСЫ
# ----------------------------------------------------------------------------------------------------------------------


class FinOpersQuery(graphene.ObjectType):
    finoper = graphene.Field(FinOperType, id=graphene.Int())
    finopers = graphene.List(FinOperType, projectId=graphene.Int(), tsBegin=graphene.Int(), tsEnd=graphene.Int())
    budget = graphene.List(BudgetLineType, projectId=graphene.Int())

    # Финансовая операция
    @login_required
    def resolve_finoper(self, info, id):
        oper = FinOper.objects.get(pk=id)
        # -- Безопасность ACL
        canRead = aclCanRead(oper.project, oper.project.acl, info.context.user)[0]
        if not canRead:
            raise Exception("У вас нет прав на просмотр данного объекта!")
        # --
        return oper


    # Журнал фин операций проекта
    @login_required
    def resolve_finopers(self, info, projectId, tsBegin, tsEnd):
        project = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canRead = aclCanRead(project, project.acl, info.context.user)[0]
        if not canRead:
            raise Exception("У вас нет прав на просмотр данного объекта!")
        # --
        tsBegin, tsEnd = parseTsIntv(tsBegin, tsEnd, project.prefFinOperLogIntv, project.prefFinOperLogIntv_n)
        return FinOper.objects.filter(project=project, moment__gte=tsBegin, moment__lte=tsEnd)

    # Бюджет проекта
    @login_required
    def resolve_budget(self, info, projectId):
        project = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canRead = aclCanRead(project, project.acl, info.context.user)[0]
        if not canRead:
            raise Exception("У вас нет прав на просмотр данного объекта!")
        # --
        return Budget.objects.filter(project=project)

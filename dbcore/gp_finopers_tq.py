from enum import Enum

import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required
from django.db import connection

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
    finopersSQL = graphene.String(projectId=graphene.Int(), tsBegin=graphene.Int(), tsEnd=graphene.Int())
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

    # Журнал фин операций проекта SQL
    @login_required
    def resolve_finopersSQL(self, info, projectId, tsBegin, tsEnd):
        project = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canRead = aclCanRead(project, project.acl, info.context.user)[0]
        if not canRead:
            raise Exception("У вас нет прав на просмотр данного объекта!")
        # --
        tsBegin, tsEnd = parseTsIntv(tsBegin, tsEnd, project.prefFinOperLogIntv, project.prefFinOperLogIntv_n)

        SQL = f'''
            select finopers.finopers, project.project, costTypes.costTypes, agents.agents, users.users
            from
            
            -- finopers
            (select json_agg(t) as finopers
            from (
            select
                finoper.id as id,
                extract(epoch from moment) as ts,
                "costType_id" as "ctId",
                "agentFrom_id" as "agFromId",
                "agentTo_id" as "agToId",
                owner_id as "ownerId",
                amount,
                notes,
                count(photo.id) as pq
            from dbcore_finoper as finoper
            left join dbcore_photo photo on finoper.id = photo."finOper_id"
            where project_id={projectId} and moment >= '{tsBegin}' and moment <= '{tsEnd}'
            group by finoper.id) t) finopers,
            
            -- project
            (select json_agg(t) as project
            from (
            select
                id,
                name
            from dbcore_project
            where id={projectId}) t) project,
            
            -- costTypes
            (select json_agg(t) as costTypes
            from (
            select
                id,
                coalesce(parent_id, -1) as pid,
                "order" as ord,
                name,
                "isOutcome" as out,
                color
            from dbcore_costtype) t) costTypes,
            
            -- agents
            (select json_agg(t) as agents
            from (
            select
                id,
                coalesce(parent_id, -1) as pid,
                "order" as ord,
                name
            from dbcore_agent) t) agents,
            
            -- users
            (select json_agg(t) as users
            from (
            select
                us.id as id,
                username,
                color
            from auth_user as us
            left join ua_userattr ua on us.id = ua.user_id) t) users
        '''
        with connection.cursor() as cursor:
            cursor.execute(SQL)
            row = cursor.fetchone()
        res = json.dumps({
            'finopers': row[0],
            'project': row[1],
            'costTypes': row[2],
            'agents': row[3],
            'users': row[4],
        }, ensure_ascii=True)
        return res

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

import json

import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from dbcore.models import Project, Agent, CostType, FinOper
from dbcore.models_base import HierarchyOrderModelExt, aclGetUsersList, isAdmin, aclCanRead, aclCanReport
from reports.report001 import report001
from reports.report002 import report002
from reports.search001 import search001


# ----------------------------------------------------------------------------------------------------------------------
# О Т Ч Е Т Ы
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# ТИПЫ
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# ЗАПРОСЫ
# ----------------------------------------------------------------------------------------------------------------------


class ReportsQuery(graphene.ObjectType):
    report001 = graphene.String(projectId=graphene.Int())
    report002 = graphene.String(projectId=graphene.Int(),
                                beginDate=graphene.Int(),
                                endDate=graphene.Int(),
                                costTypeId=graphene.Int(),
                                agentFromId=graphene.Int(),
                                agentToId=graphene.Int()
                                )
    search001 = graphene.String(findStr=graphene.String())

    # Отчет 001
    @login_required
    def resolve_report001(self, info, projectId):
        project = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canReport = aclCanReport(project, project.acl, info.context.user)[0]
        if not canReport:
            raise Exception("У вас нет прав на просмотр данного объекта!")
        # --
        tmp = report001(projectId)
        res = json.dumps(tmp, ensure_ascii=True, sort_keys=True, default=str)
        return res

    # Отчет 002
    @login_required
    def resolve_report002(self, info, projectId, beginDate=-1, endDate=-1, costTypeId=-1, agentFromId=-1, agentToId=-1):
        project = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canReport = aclCanReport(project, project.acl, info.context.user)[0]
        if not canReport:
            raise Exception("У вас нет прав на просмотр данного объекта!")
        # --
        tmp = report002(projectId, beginDate, endDate, costTypeId, agentFromId, agentToId)
        res = json.dumps(tmp, ensure_ascii=True, sort_keys=True, default=str)
        return res

    # Поиск 001
    @login_required
    def resolve_search001(self, info, findStr):
        tmp = search001(findStr, info.context.user)
        res = json.dumps(tmp, ensure_ascii=True, sort_keys=True, default=str)
        return res

import json

import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from dbcore.models import Project, Agent, CostType, FinOper
from dbcore.models_base import HierarchyOrderModelExt, aclGetUsersList, isAdmin, aclCanRead, aclCanReport
from reports.report001 import report001
from reports.report002 import report002


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
                                costType=graphene.Int(),
                                agentFrom=graphene.Int(),
                                agentTo=graphene.Int()
                                )

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
    def resolve_report002(self, info, projectId, beginDate=-1, endDate=-1, costType=-1, agentFrom=-1, agentTo=-1):
        project = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canReport = aclCanReport(project, project.acl, info.context.user)[0]
        if not canReport:
            raise Exception("У вас нет прав на просмотр данного объекта!")
        # --
        tmp = report002(projectId, beginDate, endDate, costType, agentFrom, agentTo)
        res = json.dumps(tmp, ensure_ascii=True, sort_keys=True, default=str)
        return res
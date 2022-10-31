import json

import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from dbcore.models import Project, Agent, CostType, FinOper
from dbcore.models_base import HierarchyOrderModelExt, aclGetUsersList, isAdmin, aclCanRead, aclCanReport
from reports.report001 import report001


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

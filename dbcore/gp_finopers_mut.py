import json
import graphene
from graphql_jwt.decorators import login_required

from django.contrib.auth.models import User
from dbcore.models import Project, Agent, CostType, FinOper
from dbcore.models_base import isAdmin, aclCanRead, aclCanMod
from ua.models import logUserAction, modelDiff


# ----------------------------------------------------------------------------------------------------------------------
# Ф И Н А Н С О В Ы Е   О П Е Р А Ц И И
# ----------------------------------------------------------------------------------------------------------------------


# Переместить фин операцию в другой проект
class MoveFinOper(graphene.Mutation):
    class Arguments:
        id = graphene.Int()
        projectId = graphene.Int()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, id, projectId):
        oper = FinOper.objects.get(pk=id)
        # -- Безопасность ACL
        canMod = aclCanMod(oper, oper.project.acl, info.context.user)[0]
        if not canMod:
            raise Exception("У вас нет прав на перемещение данного объекта!")
        # --
        oldProjectId = oper.project_id
        newProject = Project.objects.get(pk=projectId)
        oper.project = newProject
        oper.save();
        logUserAction(info.context.user, FinOper, f"change project id={id}", diff=f"projectId: {oldProjectId} -> {projectId}",
                          link=f"/finoper/{id}")
        # noinspection PyArgumentList
        return MoveFinOper(ok=True, result=f"Change project {FinOper}, id={id}")


# Копировать фин операцию (клонирование)
class CopyFinOper(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, id):
        oper = FinOper.objects.get(pk=id)
        # -- Безопасность ACL
        canMod = aclCanMod(oper, oper.project.acl, info.context.user)[0]
        if not canMod:
            raise Exception("У вас нет прав на копирование данного объекта!")
        # --
        copyOper = oper
        copyOper.pk = None
        copyOper.owner = info.context.user
        copyOper.notes = 'КОПИЯ ' + str(copyOper.notes or '')
        copyOper.save()
        logUserAction(info.context.user, FinOper,
                      f"clone '{copyOper.project.pk}:{copyOper.project.name}' ~ '{copyOper.pk} = {copyOper.amount}' from operId '{id}'",
                      link=f"/finoper/{copyOper.pk}")
        # noinspection PyArgumentList
        return CopyFinOper(ok=True, result=f"Copy (clone) {FinOper}, new id={copyOper.pk}")


class DeleteFinOper(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, id):
        oper = FinOper.objects.get(pk=id)
        # -- Безопасность ACL
        canMod = aclCanMod(oper, oper.project.acl, info.context.user)[0]
        if not canMod:
            raise Exception("У вас нет прав на удаление данного объекта!")
        # --
        operProjectPk = oper.project.pk
        operProjectName = oper.project.name
        operPk = oper.pk
        operAmount = oper.amount
        oper.delete()
        logUserAction(info.context.user, FinOper, f"delete '{operProjectPk}:{operProjectName}' ~ '{operPk} = {operAmount}'")
        # noinspection PyArgumentList
        return DeleteFinOper(ok=True, result=f"Delete {FinOper}, id={id}")

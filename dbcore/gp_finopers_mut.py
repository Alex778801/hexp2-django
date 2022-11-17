import json
import os
from datetime import datetime

import graphene
from graphql_jwt.decorators import login_required
import piexif

from django.conf import settings

from django.contrib.auth.models import User
from dbcore.models import Project, Agent, CostType, FinOper, Photo, getPhotoLocation, Budget
from dbcore.models_base import isAdmin, aclCanRead, aclCanMod, aclCanCrt
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
        oldProjectId = oper.project_id
        newProject = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canModSource = aclCanMod(oper, oper.project.acl, info.context.user)[0]
        canCrtTarget = aclCanCrt(newProject, newProject.acl, info.context.user)[0]
        if not canModSource or not canCrtTarget:
            raise Exception("У вас нет прав на перемещение данного объекта!")
        # --
        oper.project = newProject
        oper.save()
        logUserAction(info.context.user, FinOper, f"change project id={id}",
                      diff=f"projectId: {oldProjectId} -> {projectId}",
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
        canCrt = aclCanCrt(oper.project, oper.project.acl, info.context.user)[0]
        if not canMod or not canCrt:
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


# Удалить фин операцию
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


# Создать фин операцию
class CreateFinOper(graphene.Mutation):
    class Arguments:
        projectId = graphene.Int()

    ok = graphene.Boolean()
    result = graphene.String()
    newOperId = graphene.Int()

    @login_required
    def mutate(root, info, projectId):
        # Создаем новую фин операцию
        project = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canCrt = aclCanCrt(project, project.acl, info.context.user)[0]
        if not canCrt:
            raise Exception("У вас нет прав на создание данного объекта!")
        # --
        oper = FinOper()
        oper.project = project
        oper.owner = info.context.user
        oper.costType = CostType.objects.filter(parent=project.prefCostTypeGroup).order_by('order').first()
        # oper.agentFrom = Agent.objects.filter(parent=project.prefAgentGroup).order_by('order').first()
        # oper.agentTo = Agent.objects.filter(parent=project.prefAgentGroup).order_by('order').first()
        oper.save()
        # Журнал
        logUserAction(info.context.user, FinOper, f"create id={oper.pk}", diff=oper, link=f"/finoper/{oper.pk}")
        # noinspection PyArgumentList
        return CreateFinOper(ok=True, result=f"Create {FinOper}, id={oper.pk}", newOperId=oper.pk)


# Обновить фин операцию
class UpdateFinOper(graphene.Mutation):
    class Arguments:
        id = graphene.Int()
        ts = graphene.Int()
        costTypeId = graphene.Int()
        agentFromId = graphene.Int()
        agentToId = graphene.Int()
        amount = graphene.Int()
        notes = graphene.String()
        user = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, id, ts, costTypeId=None, agentFromId=None, agentToId=None, amount=0, notes=None, user=None):
        oper = FinOper.objects.get(pk=id)
        # -- Безопасность ACL
        canMod = aclCanMod(oper, oper.project.acl, info.context.user)[0]
        if not canMod:
            raise Exception("У вас нет прав на модификацию данного объекта!")
        # ---------
        oper.moment = datetime.fromtimestamp(ts)
        oper.costType_id = costTypeId
        oper.agentFrom_id = agentFromId
        oper.agentTo_id = agentToId
        oper.amount = amount
        oper.notes = notes
        oper.owner = User.objects.filter(username=user).first()
        # Журнал
        diff = modelDiff(FinOper.objects.get(pk=oper.pk), oper)
        oper.save()
        logUserAction(info.context.user, FinOper, f"update id={oper.pk}", diff=diff, link=f"/finoper/{oper.pk}")
        # noinspection PyArgumentList
        return UpdateFinOper(ok=True, result=f"Update {FinOper}, id={oper.pk}")


# Действия с фото фин операции
class PhotoAction(graphene.Mutation):
    class Arguments:
        id = graphene.Int()
        action = graphene.Int()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, id, action):
        # Операция с фото: 1 - удалить, 2 - вращать вправо, 3 - вращать влево
        actionsList = ['nothing', 'delete', 'rot right', 'rot left']
        photo = Photo.objects.get(pk=id)
        # -------------------------------------------------------------------
        # Удаление фото
        if action == 1:
            Photo.objects.get(pk=id).delete()
        # -------------------------------------------------------------------
        # Вращение фото
        if action == 2 or action == 3:
            try:
                # Когда есть exif инфо об ориентации
                exif_dict = piexif.load(photo.image.path)
                oldAngle = exif_dict['0th'][274]
                newAngle = 1
                # Вправо - по часовой
                if action == 2:
                    if oldAngle == 1:
                        newAngle = 8
                    elif oldAngle == 8:
                        newAngle = 3
                    elif oldAngle == 3:
                        newAngle = 6
                    elif oldAngle == 6:
                        newAngle = 1
                # Влево - против часовой
                elif action == 3:
                    if oldAngle == 1:
                        newAngle = 6
                    elif oldAngle == 6:
                        newAngle = 3
                    elif oldAngle == 3:
                        newAngle = 8
                    elif oldAngle == 8:
                        newAngle = 1
                exif_dict['0th'][274] = newAngle
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, photo.image.path)
            except:
                # Когда нет exif инфо
                newAngle = 1
                if action == 2:
                    newAngle = 8
                elif action == 3:
                    newAngle = 6
                exif_dict = {"0th": {274: newAngle}}
                # exif_dict['0th'][274] = newAngle
                exif_bytes = piexif.dump(exif_dict)
                piexif.insert(exif_bytes, photo.image.path)
            # Переименуем файл фото, чтобы не было проблем с кэшем браузеров
            oldName = f'{settings.MEDIA_ROOT}/{photo.image}'
            localName = getPhotoLocation(photo, oldName)
            newName = f'{settings.MEDIA_ROOT}/{localName}'
            os.rename(oldName, newName)
            photo.image = localName
            photo.save()
            # --
        logUserAction(info.context.user, Photo, f"photo {actionsList[action]}, id={id}", link=f"/finoper/{photo.finOper.project_id}")
        # noinspection PyArgumentList
        return PhotoAction(ok=True, result=f"photo action {actionsList[action]}, id={id}")


# Обновить бюджет проекта
class UpdateBudget(graphene.Mutation):
    class Arguments:
        projectId = graphene.Int()
        budgetPack = graphene.String()
        deletedPack = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, projectId, budgetPack, deletedPack):
        project = Project.objects.get(pk=projectId)
        # -- Безопасность ACL
        canMod = aclCanMod(project, project.acl, info.context.user)[0]
        if not canMod:
            raise Exception("У вас нет прав на модификацию данного объекта!")
        # Создадим новые и обновим существующие
        budgets = json.loads(budgetPack)
        for budgetLine in budgets:
            if budgetLine['id'] == -1:
                budget = Budget()
                budget.project = project
            else:
                budget = Budget.objects.get(pk=budgetLine['id'])
            budget.costType_id = budgetLine['costType']['id']
            budget.order = budgetLine['order']
            budget.amount = budgetLine['amount']
            budget.notes = budgetLine['notes']
            # Журнал - обновление
            if budgetLine['id'] != -1:
                diff = modelDiff(Budget.objects.get(pk=budget.pk), budget)
                if diff != '':
                    logUserAction(info.context.user, Budget, f"update budget, id={budget.pk}", diff=diff, link=f"/budget/{projectId}")
            budget.save()
            # Журнал - новый
            if budgetLine['id'] == -1:
                logUserAction(info.context.user, Budget, f"new budget, id={budget.pk}", diff=budget, link=f"/budget/{projectId}")
        # Удалим помеченные на удаление
        deletes = json.loads(deletedPack)
        for delete in deletes:
            budget = Budget.objects.get(pk=delete)
            logUserAction(info.context.user, Budget, f"delete budget, id={budget.pk}", diff=budget, link=f"/budget/{projectId}")
            budget.delete()
        # noinspection PyArgumentList
        return UpdateBudget(ok=True, result=f"Update {Budget}, projectd id={projectId}")

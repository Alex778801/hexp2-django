import json

import graphene
from django.core import serializers

from dbcore.models import Project, Agent, CostType
from dj.myutils import CustomJSONEncoder
from ua.models import logUserAction


def getObjectModel(model):
    pModel = model.lower()
    objectModel = None
    if pModel == 'project':
        objectModel = Project
    elif pModel == 'agent':
        objectModel = Agent
    elif pModel == 'costtypes':
        objectModel = CostType
    return objectModel


# Создание объекта справочника
class CreateCatObject(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        pid = graphene.Int()
        isGrp = graphene.Boolean()
        name = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

    def mutate(root, info, model, pid, isGrp, name):
        objectModel = getObjectModel(model)
        newObject = objectModel()
        if pid != -1:
            newObject.parent = Project.objects.get(pk=pid)
        newObject.isGrp = isGrp
        newObject.name = name
        newObject.save()
        logUserAction(info.context.user, objectModel,
                      f"new object {'group' if isGrp else 'element'} '{newObject.pk}:{newObject.name}'")
        return CreateCatObject(ok=True, result=f'Created in {objectModel}, id={newObject.pk}')


# Удаление объектов справочника
class DeleteCatObjects(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        ids = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

    def mutate(root, info, model, ids):
        objectModel = getObjectModel(model)
        itemsId = json.loads(ids)
        for itemId in itemsId:
            item = objectModel.objects.get(pk=itemId)
            itemName = item.name
            # Проверка наличия ссылок на удаляемый объект
            refTotal = 0
            # ------------------------------------------------------
            # Группы
            if item.isGrp:
                refTotal = objectModel.objects.filter(parent=item).count()
            # ------------------------------------------------------
            # Элементы
            else:
                # Агенты
                if objectModel == Agent:
                    refProjectsQnty = item.prefAgentGroup.all().count()
                    refFinOpersAgentFromQ = item.agentFrom.all().count()
                    refFinOpersAgentToQ = item.agentTo.all().count()
                    refTotal = refProjectsQnty + refFinOpersAgentFromQ + refFinOpersAgentToQ
                #  Статьи расхода
                elif objectModel == CostType:
                    refProjectsQnty = item.prefCostTypeGroup.all().count()
                    refFinOpersQnty = item.costType.all().count()
                    refTotal = refProjectsQnty + refFinOpersQnty
            # ------------------------------------------------------
            # нет зависимостей - удаляем
            if refTotal == 0:
                item.delete()
                logUserAction(info.context.user, objectModel, f"delete '{itemId}:{itemName}'")
            # есть зависимости - переносим в папку _DELREF
            else:
                delRefGroup = objectModel.objects.get(isGrp=True, name='_DELREF')
                item.changeParent(delRefGroup)
                logUserAction(info.context.user, objectModel, f"move to _DELREF folder '{itemId}:{itemName}'")
        return DeleteCatObjects(ok=True, result=f'Deleted in {objectModel}, ids={ids}')

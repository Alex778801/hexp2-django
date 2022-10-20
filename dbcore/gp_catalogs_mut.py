import json
import graphene
from graphql_jwt.decorators import login_required

from django.contrib.auth.models import User
from dbcore.models import Project, Agent, CostType
from dbcore.models_base import isAdmin
from ua.models import logUserAction, modelDiff


# ----------------------------------------------------------------------------------------------------------------------
# М У Т А Ц И И
# ----------------------------------------------------------------------------------------------------------------------


# Вспомогательная - получить модель данных по ее строковому представлению
def getItemModel(model):
    pModel = model.lower()
    itemModel = None
    if pModel == 'project':
        itemModel = Project
    elif pModel == 'agent':
        itemModel = Agent
    elif pModel == 'costtype':
        itemModel = CostType
    return itemModel

# Создание объекта справочника
class CreateCatObject(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        pid = graphene.Int()
        isGrp = graphene.Boolean()
        name = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, model, pid, isGrp, name):
        itemModel = getItemModel(model)
        newItem = itemModel()
        if pid != -1:
            newItem.parent = itemModel.objects.get(pk=pid)
        newItem.isGrp = isGrp
        newItem.name = name
        newItem.owner = info.context.user
        newItem.save()
        logUserAction(info.context.user, itemModel, f"new {'group' if isGrp else 'element'} '{newItem.pk}:{newItem.name}'",
                      link=f"/{model}/{newItem.pk}")
        # noinspection PyArgumentList
        return CreateCatObject(ok=True, result=f'Create in {itemModel}, id={newItem.pk}')


# Удаление объектов справочника
class DeleteCatObjects(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        ids = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, model, ids):
        itemModel = getItemModel(model)
        itemsId = json.loads(ids)
        for itemId in itemsId:
            item = itemModel.objects.get(pk=itemId)
            itemName = item.name
            # Проверка наличия ссылок на удаляемый объект
            refTotal = 0
            # ------------------------------------------------------
            # Группы
            if item.isGrp:
                refTotal = itemModel.objects.filter(parent=item).count()
            # ------------------------------------------------------
            # Элементы
            else:
                # Агенты
                if itemModel == Agent:
                    refProjectsQnty = item.prefAgentGroup.all().count()
                    refFinOpersAgentFromQ = item.agentFrom.all().count()
                    refFinOpersAgentToQ = item.agentTo.all().count()
                    refTotal = refProjectsQnty + refFinOpersAgentFromQ + refFinOpersAgentToQ
                #  Статьи расхода
                elif itemModel == CostType:
                    refProjectsQnty = item.prefCostTypeGroup.all().count()
                    refFinOpersQnty = item.costType.all().count()
                    refTotal = refProjectsQnty + refFinOpersQnty
            # ------------------------------------------------------
            # нет зависимостей - удаляем
            if refTotal == 0:
                logUserAction(info.context.user, itemModel, f"delete '{id}:{item.name}'")
                item.delete()
            # есть зависимости - переносим в папку _DELREF
            else:
                delRefGroup = itemModel.objects.get(isGrp=True, name='_DELREF')
                item.changeParent(delRefGroup)
                logUserAction(info.context.user, itemModel, f"move _DELREF, '{id}:{item.name}'")
        # noinspection PyArgumentList
        return DeleteCatObjects(ok=True, result=f'Delete in {itemModel}, ids={ids}')


# Переименование объекта справочника
class RenameCatObject(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        id = graphene.Int()
        name = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, model, id, name):
        itemModel = getItemModel(model)
        item = itemModel.objects.get(pk=id)
        oldName = item.name
        item.name = name
        item.save()
        logUserAction(info.context.user, itemModel, f"rename '{id}:{name}'", diff=f"name: {oldName} -> {name}",
                      link=f"/{model}/{item.pk}")
        # noinspection PyArgumentList
        return CreateCatObject(ok=True, result=f"Rename in {itemModel}, id={id}")


# Изменение порядка объекта справочника
class ChangeOrderCatObject(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        id = graphene.Int()
        order = graphene.Int()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, model, id, order):
        itemModel = getItemModel(model)
        item = itemModel.objects.get(pk=id)
        oldOrder = item.order
        item.changeOrder(order)
        logUserAction(info.context.user, itemModel, f"change order '{item.pk}:{item.name}'", diff=f"order: {oldOrder} -> {order}",
                      link=f"/{model}/{item.pk}")
        # noinspection PyArgumentList
        return ChangeOrderCatObject(ok=True, result=f"Change order in {itemModel}, id={id}")


# Изменить родителя объектов справочника
class ChangeParentCatObjects(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        ids = graphene.String()
        pid = graphene.Int()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, model, ids, pid):
        itemModel = getItemModel(model)
        itemsId = json.loads(ids)
        if pid != -1:
            newParent = itemModel.objects.get(pk=pid)
        else:
            newParent = None
        for itemId in itemsId:
            item = itemModel.objects.get(pk=itemId)
            oldPid = item.parent.pk if item.parent is not None else -1
            item.changeParent(newParent)
            logUserAction(info.context.user, itemModel, f"change parent '{item.pk}:{item.name}'", diff=f"pid: {oldPid} -> {pid}",
                          link=f"/{model}/{item.pk}")
        # noinspection PyArgumentList
        return ChangeParentCatObjects(ok=True, result=f"Change parent in {itemModel}, ids={ids}")


# Копировать (клонировать) объекты справочника
class CopyCatObjects(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        ids = graphene.String()
        pid = graphene.Int()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, model, ids, pid):
        itemModel = getItemModel(model)
        itemsId = json.loads(ids)
        if pid != -1:
            parent = itemModel.objects.get(pk=pid)
        else:
            parent = None
        for itemId in itemsId:
            item = itemModel.objects.get(pk=itemId)
            clonedItem = item.clone(parent)
            clonedItem.owner = info.context.user
            clonedItem.save()
            logUserAction(info.context.user, itemModel, f"clone to '{clonedItem.pk}:{clonedItem.name}' from '{item.pk}:{item.name}'",
                          link=f"/{model}/{clonedItem.pk}")
        # noinspection PyArgumentList
        return CopyCatObjects(ok=True, result=f"Clone in {itemModel}, ids={ids}")

# ----------------------------------------------------------------------------------------------------------------------
# Обновление элемента справочника
class UpdateProject(graphene.Mutation):
    class Arguments:
        id = graphene.Int()
        name = graphene.String()
        prefCostTypeGroup = graphene.Int()
        prefAgentGroup = graphene.Int()
        prefFinOperLogIntv = graphene.Int()
        prefFinOperLogIntvN = graphene.Int()
        owner = graphene.String()
        acl = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

    @login_required
    def mutate(root, info, id, name, prefCostTypeGroup, prefAgentGroup,
               prefFinOperLogIntv, prefFinOperLogIntvN, owner, acl):

        project = Project.objects.get(pk=id)
        # Изменять может только админ или владелец!
        if isAdmin(info.context.user) or info.context.user == project.owner:
            raise Exception("У вас нет прав на изменение данного объекта!")
        # --
        project.name = name
        project.prefCostTypeGroup = CostType.objects.get(pk=prefCostTypeGroup)
        project.prefAgentGroup = Agent.objects.get(pk=prefAgentGroup)
        project.prefFinOperLogIntv = prefFinOperLogIntv
        project.prefFinOperLogIntv_n = prefFinOperLogIntvN
        project.acl = acl
        project.owner = User.objects.get(username=owner)
        # --
        diff = modelDiff(Project.objects.get(pk=project.pk), project)
        project.save()
        logUserAction(info.context.user, Project, f"save '{project.pk}:{project.name}'", link=f"/project/{project.pk}", diff=diff)
        # noinspection PyArgumentList
        return CopyCatObjects(ok=True, result=f"Update in {Project}, id={project.pk}")



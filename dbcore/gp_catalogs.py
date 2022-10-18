import json
import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required


from dbcore.models import Project, Agent, CostType
from ua.models import logUserAction


# ----------------------------------------------------------------------------------------------------------------------
# - Т И П Ы
# ----------------------------------------------------------------------------------------------------------------------


class CustomCat:
    id = graphene.Int()
    pid = graphene.Int()
    grp = graphene.Boolean()
    ord = graphene.Int()

    def resolve_id(self, info):
        if self is not None:
            return self.id
        else:
            return -1

    def resolve_pid(self: Project, info):
        if self.parent_id is not None:
            return self.parent_id
        else:
            return -1

    def resolve_grp(self: Project, info):
        return self.isGrp

    def resolve_ord(self: Project, info):
        return self.order


class ProjectType(DjangoObjectType, CustomCat):
    class Meta:
        model = Project


# ----------------------------------------------------------------------------------------------------------------------
# - З А П Р О С Ы
# ----------------------------------------------------------------------------------------------------------------------


class Query(graphene.ObjectType):
    project = graphene.Field(ProjectType, id=graphene.Int())
    projects = graphene.List(ProjectType)

    @login_required
    def resolve_project(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return Project.objects.get(pk=id)
        return None

    @login_required
    def resolve_projects(self, info, **kwargs):
        return Project.objects.all()


# Вспомогательная - получить модель данных по ее строковому представлению
def getItemModel(model):
    pModel = model.lower()
    itemModel = None
    if pModel == 'projects':
        itemModel = Project
    elif pModel == 'agents':
        itemModel = Agent
    elif pModel == 'costtypes':
        itemModel = CostType
    return itemModel


# ----------------------------------------------------------------------------------------------------------------------
# - М У Т А Ц И И
# ----------------------------------------------------------------------------------------------------------------------


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
        itemModel = getItemModel(model)
        newItem = itemModel()
        if pid != -1:
            newItem.parent = Project.objects.get(pk=pid)
        newItem.isGrp = isGrp
        newItem.name = name
        newItem.save()
        # TODO: link=makeLinkForModel(item)
        logUserAction(info.context.user, itemModel, f"new {'group' if isGrp else 'element'} '{newItem.pk}:{newItem.name}'")
        # noinspection PyArgumentList
        return CreateCatObject(ok=True, result=f'Create in {itemModel}, id={newItem.pk}')


# Удаление объектов справочника
class DeleteCatObjects(graphene.Mutation):
    class Arguments:
        model = graphene.String()
        ids = graphene.String()

    ok = graphene.Boolean()
    result = graphene.String()

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
                # TODO: link=makeLinkForModel(item)
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

    def mutate(root, info, model, id, name):
        itemModel = getItemModel(model)
        item = itemModel.objects.get(pk=id)
        oldName = item.name
        item.name = name
        item.save()
        # TODO: link=makeLinkForModel(item)
        logUserAction(info.context.user, itemModel, f"rename '{id}:{name}'", diff=f"name: {oldName} -> {name}")
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

    def mutate(root, info, model, id, order):
        itemModel = getItemModel(model)
        item = itemModel.objects.get(pk=id)
        oldOrder = item.order
        item.changeOrder(order)
        # TODO: link=makeLinkForModel(item)
        logUserAction(info.context.user, itemModel, f"change order '{item.pk}:{item.name}'", diff=f"order: {oldOrder} -> {order}")
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
            # TODO: link=makeLinkForModel(item)
            logUserAction(info.context.user, itemModel, f"change parent '{item.pk}:{item.name}'", diff=f"pid: {oldPid} -> {pid}")
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
            # TODO: link=makeLinkForModel(item)
            logUserAction(info.context.user, itemModel, f"clone to '{clonedItem.pk}:{clonedItem.name}' from '{item.pk}:{item.name}'")
        # noinspection PyArgumentList
        return CopyCatObjects(ok=True, result=f"Clone in {itemModel}, ids={ids}")

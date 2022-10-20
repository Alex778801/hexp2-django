import json

import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required


from dbcore.models import Project, Agent, CostType
from dbcore.models_base import HierarchyOrderModelExt, aclGetUsersList
from dj.myutils import CustomJSONEncoder


# ----------------------------------------------------------------------------------------------------------------------
# - Т И П Ы
# ----------------------------------------------------------------------------------------------------------------------


# Базовый класс каталога
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

    def resolve_pid(self: HierarchyOrderModelExt, info):
        if self.parent_id is not None:
            return self.parent_id
        else:
            return -1

    def resolve_grp(self: HierarchyOrderModelExt, info):
        return self.isGrp

    def resolve_ord(self: HierarchyOrderModelExt, info):
        return self.order


# Проекты
class ProjectType(DjangoObjectType, CustomCat):
    class Meta:
        model = Project

    path = graphene.String()
    prefCostTypeGroupTree = graphene.String()
    prefAgentGroupTree = graphene.String()
    logIntervalList = graphene.String()
    owner = graphene.String()
    aclList = graphene.String()

    # Путь к проекту
    def resolve_path(self: Project, info):
        return self.getParentsList()

    # Дерево групп Статей
    def resolve_prefCostTypeGroupTree(self: Project, info):
        tmp = CostType.getGroupsTree()
        res = json.dumps(tmp, ensure_ascii=True)
        return res

    # Дерево групп Агентов
    def resolve_prefAgentGroupTree(self: Project, info):
        tmp = Agent.getGroupsTree()
        res = json.dumps(tmp, ensure_ascii=True)
        return res

    # Интервалы журнала
    def resolve_logIntervalList(self: Project, info):
        tmp = list(map(lambda i: {'id': i['id'].value, 'label': i['fn']}, Project.Ext.logIntv))
        res = json.dumps(tmp, ensure_ascii=True)
        return res

    # Владелец
    def resolve_owner(self: Project, info):
        return self.owner.username

    # Список пользователей и служебных записей авторизации
    def resolve_aclList(self: Project, info):
        tmp = aclGetUsersList()
        res = json.dumps(tmp, ensure_ascii=True)
        return res


# Агенты
class AgentType(DjangoObjectType, CustomCat):
    class Meta:
        model = Agent


# Статьи
class CostTypeType(DjangoObjectType, CustomCat):
    class Meta:
        model = CostType

    out = graphene.Boolean()

    def resolve_out(self: CostType, info):
        return self.isOutcome


# ----------------------------------------------------------------------------------------------------------------------
# З А П Р О С Ы
# ----------------------------------------------------------------------------------------------------------------------


class CatalogsQuery(graphene.ObjectType):
    # Проекты
    project = graphene.Field(ProjectType, id=graphene.Int())
    projects = graphene.List(ProjectType)
    # Агенты
    agent = graphene.Field(AgentType, id=graphene.Int())
    agents = graphene.List(AgentType)
    # Статьи
    costtype = graphene.Field(CostTypeType, id=graphene.Int())
    costtypes = graphene.List(CostTypeType)

    # -------------
    # Проект
    @login_required
    def resolve_project(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return Project.objects.get(pk=id)
        return None

    # ПроектЫ
    @login_required
    def resolve_projects(self, info, **kwargs):
        return Project.objects.all()

    # -------------
    # Агент
    @login_required
    def resolve_agent(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return Agent.objects.get(pk=id)
        return None

    # АгентЫ
    @login_required
    def resolve_agents(self, info, **kwargs):
        return Agent.objects.all()

    # -------------
    # Статья
    @login_required
    def resolve_costtype(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return CostType.objects.get(pk=id)
        return None

    # Статьи
    @login_required
    def resolve_costtypes(self, info, **kwargs):
        return CostType.objects.all()
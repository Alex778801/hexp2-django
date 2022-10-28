import json

import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from dbcore.models import Project, Agent, CostType, FinOper
from dbcore.models_base import HierarchyOrderModelExt, aclGetUsersList, isAdmin


# ----------------------------------------------------------------------------------------------------------------------
# К А Т А Л О Г И
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# ТИПЫ
# ----------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# Базовый класс каталога
class CustomCat:
    id = graphene.Int()
    pid = graphene.Int()
    grp = graphene.Boolean()
    ord = graphene.Int()

    def resolve_id(self, info):
        return self.id

    def resolve_pid(self: HierarchyOrderModelExt, info):
        if self.parent_id is not None:
            return self.parent_id
        else:
            return -1

    def resolve_grp(self: HierarchyOrderModelExt, info):
        return self.isGrp

    def resolve_ord(self: HierarchyOrderModelExt, info):
        return self.order


# ----------------------------------------------------------------------------------------------------------------------
# Проект
class ProjectType(DjangoObjectType, CustomCat):
    class Meta:
        model = Project

    path = graphene.String()
    prefCostTypeGroupTree = graphene.String()
    prefAgentGroupTree = graphene.String()
    tree = graphene.String()
    logIntervalList = graphene.String()
    user = graphene.String()
    aclList = graphene.String()
    readOnly = graphene.Boolean()

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

    # Владелец - текстовое представление объекта owner
    def resolve_user(self: Project, info):
        return self.owner.username


    # Список пользователей и служебных записей авторизации
    def resolve_aclList(self: Project, info):
        tmp = aclGetUsersList()
        res = json.dumps(tmp, ensure_ascii=True)
        return res

    # Разрешено только чтение
    def resolve_readOnly(self: Project, info):
        return not isAdmin(info.context.user)[0] and not self.owner == info.context.user and self.owner is not None


# ----------------------------------------------------------------------------------------------------------------------
# Статья
class CostTypeType(DjangoObjectType, CustomCat):
    class Meta:
        model = CostType

    path = graphene.String()
    out = graphene.Boolean()
    user = graphene.String()
    aclList = graphene.String()
    readOnly = graphene.Boolean()

    # Путь к проекту
    def resolve_path(self: CostType, info):
        return self.getParentsList()

    # Сокращение для isOutcome
    def resolve_out(self: CostType, info):
        return self.isOutcome

    # Владелец - текстовое представление объекта owner
    def resolve_user(self: Project, info):
        return self.owner.username

    # Список пользователей и служебных записей авторизации
    def resolve_aclList(self: CostType, info):
        tmp = aclGetUsersList()
        res = json.dumps(tmp, ensure_ascii=True)
        return res

    # Разрешено только чтение
    def resolve_readOnly(self: CostType, info):
        return not isAdmin(info.context.user)[0] and not self.owner == info.context.user and self.owner is not None


# ----------------------------------------------------------------------------------------------------------------------
# Агент
class AgentType(DjangoObjectType, CustomCat):
    class Meta:
        model = Agent

    path = graphene.String()
    user = graphene.String()
    aclList = graphene.String()
    readOnly = graphene.Boolean()

    # Путь к проекту
    def resolve_path(self: Agent, info):
        return self.getParentsList()

    # Владелец - текстовое представление объекта owner
    def resolve_user(self: Project, info):
        return self.owner.username

    # Список пользователей и служебных записей авторизации
    def resolve_aclList(self: Agent, info):
        tmp = aclGetUsersList()
        res = json.dumps(tmp, ensure_ascii=True)
        return res

    # Разрешено только чтение
    def resolve_readOnly(self: Agent, info):
        return not isAdmin(info.context.user)[0] and not self.owner == info.context.user and self.owner is not None


# ----------------------------------------------------------------------------------------------------------------------
# ЗАПРОСЫ
# ----------------------------------------------------------------------------------------------------------------------


class CatalogsQuery(graphene.ObjectType):
    # Проекты
    project = graphene.Field(ProjectType, id=graphene.Int())
    projects = graphene.List(ProjectType)
    # Агенты
    agent = graphene.Field(AgentType, id=graphene.Int())
    agents = graphene.List(AgentType)
    # Статьи
    costType = graphene.Field(CostTypeType, id=graphene.Int())
    costTypes = graphene.List(CostTypeType, pid=graphene.Int())
    # Дерево проектов
    projectsTree = graphene.String()

    # Проект
    @login_required
    def resolve_project(self, info, id):
        return Project.objects.get(pk=id)

    # ПроектЫ
    @login_required
    def resolve_projects(self, info):
        return Project.objects.all()

    # Агент
    @login_required
    def resolve_agent(self, info, id):
        return Agent.objects.get(pk=id)

    # АгентЫ
    @login_required
    def resolve_agents(self, info):
        return Agent.objects.all()

    # Статья
    @login_required
    def resolve_costType(self, info, id):
        return CostType.objects.get(pk=id)

    # СтатьИ
    @login_required
    def resolve_costTypes(self, info, pid=-1):
        if pid == -1:
            return CostType.objects.all()
        else:
            return CostType.objects.filter(parent_id=pid)

    # Дерево групп и элементов Проектов
    def resolve_projectsTree(self, info):
        tmp = Project.getGroupsElemsTree()
        res = json.dumps(tmp, ensure_ascii=True)
        return res

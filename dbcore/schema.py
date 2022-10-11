from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from .models import Project
import graphene


class CustomCat:

    id = graphene.Int()
    pid = graphene.Int()
    g = graphene.Boolean()
    o = graphene.Int()

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

    def resolve_g(self: Project, info):
        return self.isGrp

    def resolve_o(self: Project, info):
        return self.order


class ProjectType(DjangoObjectType, CustomCat):
    class Meta:
        model = Project


class Query(graphene.ObjectType):
    project = graphene.Field(ProjectType, id=graphene.Int())
    projects = graphene.List(ProjectType)

    def resolve_project(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return Project.objects.get(pk=id)
        return None

    def resolve_projects(self, info, **kwargs):
        return Project.objects.all()


schema = graphene.Schema(query=Query)

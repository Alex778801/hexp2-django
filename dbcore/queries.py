import graphene
from graphql_jwt.decorators import login_required

from .models import Project
from .types import ProjectType


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

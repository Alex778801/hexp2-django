import graphene
from graphene_django import DjangoObjectType
from ua import models
from .models import Project


class UserType(DjangoObjectType):
    class Meta:
        model = models.User


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

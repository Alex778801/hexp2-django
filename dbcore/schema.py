import graphene
import graphql_jwt
from graphene_django import DjangoObjectType

from dbcore import models
from dbcore.gp_catalog_tq import CatalogsQuery
from dbcore.gp_catalogs_mut import CreateCatObject, DeleteCatObjects, RenameCatObject, ChangeOrderCatObject, \
    ChangeParentCatObjects, CopyCatObjects, UpdateProject


# ----------------------------------------------------------------------------------------------------------------------
# З А П Р О С Ы
# ----------------------------------------------------------------------------------------------------------------------

class Query(
    CatalogsQuery,
    graphene.ObjectType
): pass


# ----------------------------------------------------------------------------------------------------------------------
# М У Т А Ц И И
# ----------------------------------------------------------------------------------------------------------------------


class UserType(DjangoObjectType):
    class Meta:
        model = models.User


class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        # noinspection PyArgumentList
        return cls(user=info.context.user)


class Mutation(graphene.ObjectType):
    # -----------------------------------------------------
    # АВТОРИЗАЦИЯ
    # token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    token_auth = ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    # -----------------------------------------------------
    # КАТАЛОГИ
    # Создание объекта справочника
    create_cat_object = CreateCatObject.Field()
    # Удаление объектов справочника
    delete_cat_objects = DeleteCatObjects.Field()
    # Переименование объекта справочника
    rename_cat_object = RenameCatObject.Field()
    # Изменение порядка объекта справочника
    change_order_cat_object = ChangeOrderCatObject.Field()
    # Изменить родителя объектов справочника
    change_parent_cat_objects = ChangeParentCatObjects.Field()
    # Копировать (клонировать) объекты справочника
    copy_cat_objects = CopyCatObjects.Field()
    # Обновить проект
    update_project = UpdateProject.Field()
    # -----------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------
# С Х Е М А
# ----------------------------------------------------------------------------------------------------------------------


schema = graphene.Schema(query=Query, mutation=Mutation)

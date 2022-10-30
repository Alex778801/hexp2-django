import graphene
import graphql_jwt
from graphene_django import DjangoObjectType

from dbcore import models
from dbcore.gp_catalogs_tq import CatalogsQuery
from dbcore.gp_catalogs_mut import CreateCatObject, DeleteCatObjects, RenameCatObject, ChangeOrderCatObject, \
    ChangeParentCatObjects, CopyCatObjects, UpdateProject, UpdateCostType, UpdateAgent, UpdateProjectInfo
from dbcore.gp_finopers_tq import FinOpersQuery
from dbcore.gp_finopers_mut import MoveFinOper, CopyFinOper, DeleteFinOper, UpdateFinOper, PhotoAction, CreateFinOper, \
    UpdateBudget


# ----------------------------------------------------------------------------------------------------------------------
# З А П Р О С Ы
# ----------------------------------------------------------------------------------------------------------------------

class Query(
    CatalogsQuery,
    FinOpersQuery,
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
    # Обновить Заметки проекта
    update_project_info = UpdateProjectInfo.Field()
    # Обновить статью
    update_costtype = UpdateCostType.Field()
    # Обновить агента
    update_agent = UpdateAgent.Field()
    # -----------------------------------------------------
    # ФИНАНСОВЫЕ ОПЕРАЦИИ
    # Создать фин операцию
    create_finoper =CreateFinOper.Field()
    # Обновить фин операцию
    update_finoper = UpdateFinOper.Field()
    # Переместить фин операцию в другой проект
    move_finoper = MoveFinOper.Field()
    # Копировать (клонировать) фин операцию
    copy_finoper = CopyFinOper.Field()
    # Удалить фин операцию
    delete_finoper = DeleteFinOper.Field()
    # Действия с фото фин операции
    photo_action = PhotoAction.Field()
    # Обновить бюджет проекта
    update_budget = UpdateBudget.Field()


# ----------------------------------------------------------------------------------------------------------------------
# С Х Е М А
# ----------------------------------------------------------------------------------------------------------------------


schema = graphene.Schema(query=Query, mutation=Mutation)

import graphene


from dbcore.gp_catalogs import CatalogsQuery


class Query(
    CatalogsQuery,
    graphene.ObjectType
): pass

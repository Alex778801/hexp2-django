import json
import graphene
from graphql_jwt.decorators import login_required

from django.contrib.auth.models import User
from dbcore.models import Project, Agent, CostType
from dbcore.models_base import isAdmin
from ua.models import logUserAction, modelDiff


# ----------------------------------------------------------------------------------------------------------------------
# Ф И Н А Н С О В Ы Е   О П Е Р А Ц И И
# ----------------------------------------------------------------------------------------------------------------------






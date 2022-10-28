import os
import random

import graphql_jwt
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.http import HttpResponse
import requests
import json

from dbcore.models import Photo, FinOper, Project
from dbcore.models_base import aclCanMod
from dj import settings

# Проверить валидность токена авторизации
def checkJwtToken(token):
    query = "mutation VerifyToken($token: String!) { verifyToken(token: $token) { payload } }"
    url = f'{settings.BACKEND_ADDR}/gp/'
    res = requests.post(url, json={'query': query, 'variables': {'token': token}}).text
    return 'error' not in res and 'payload' in res

# Загрузить фото фин операции
def uploadFinOperPhoto(request):
    token = request.POST['token']
    ownerId = int(request.POST['ownerId'])
    operId = int(request.POST['operId'])
    # --
    owner = User.objects.get(pk=ownerId)
    oper = FinOper.objects.get(pk=operId)
    # -- Безопасность токена JWT
    if not checkJwtToken(token):
        raise Exception("Токен авторизации не действителен!")
    # -- Безопасность ACL
    canMod = aclCanMod(oper, oper.project.acl, owner)[0]
    if not canMod:
        raise Exception("У вас нет прав на модификацию данного объекта!")
    # --
    newPhoto = Photo()
    newPhoto.finOper = oper
    newPhoto.image = request.FILES['file']
    newPhoto.save()
    return HttpResponse('ok', content_type="text/plain", status=200)


def uploadProjectInfo(request):
    token = request.POST['token']
    projectId = int(request.POST['projectId'])
    # -- Безопасность токена JWT
    if not checkJwtToken(token):
        raise Exception("Токен авторизации не действителен!")
    # --
    file = request.FILES['file']
    name, ext = os.path.splitext(file.name)
    rand = random.randrange(100000000000, 900000000000, 1)
    newName = f'{projectId}-{rand}'
    fileName = default_storage.save(f'{settings.PROJECT_INFO_DIR}/{newName}{ext}', file)
    # resFileName = settings.BACKEND_ADDR + str(settings.MEDIA_URL) + fileName
    resFileName = fileName
    response = {'url': resFileName}
    return HttpResponse(json.dumps(response), content_type="json", status=200)

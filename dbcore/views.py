import os
import random

import graphql_jwt
import jwt
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.http import HttpResponse
import requests
import json

from graphql_jwt.settings import jwt_settings

from dbcore.models import Photo, FinOper, Project
from dbcore.models_base import aclCanMod

from django.conf import settings


# Проверить валидность токена авторизации
def checkJwtToken(token):
    try:
        res = jwt.decode(
            token,
            jwt_settings.JWT_PUBLIC_KEY or jwt_settings.JWT_SECRET_KEY,
            options={
                "verify_exp": jwt_settings.JWT_VERIFY_EXPIRATION,
                "verify_aud": jwt_settings.JWT_AUDIENCE is not None,
                "verify_signature": jwt_settings.JWT_VERIFY,
            },
            leeway=jwt_settings.JWT_LEEWAY,
            audience=jwt_settings.JWT_AUDIENCE,
            issuer=jwt_settings.JWT_ISSUER,
            algorithms=[jwt_settings.JWT_ALGORITHM],
        )
        user = User.objects.get(username=res['username'])
    except:
        return False, None
    return True, user
    # query = "mutation VerifyToken($token: String!) { verifyToken(token: $token) { payload } }"
    # url = f'{settings.BACKEND_ADDR}/gp/'
    # res = requests.post(url, json={'query': query, 'variables': {'token': token}}).text
    # return 'error' not in res and 'payload' in res


# Загрузить фото фин операции
def uploadFinOperPhoto(request):
    token = request.POST['token']
    operId = int(request.POST['operId'])
    # --
    oper = FinOper.objects.get(pk=operId)
    # -- Безопасность токена JWT
    tokenCheck, user = checkJwtToken(token)
    if not tokenCheck:
        raise Exception("Токен авторизации не действителен!")
    # -- Безопасность ACL
    canMod = aclCanMod(oper, oper.project.acl, user)[0]
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
    tokenCheck, user = checkJwtToken(token)
    if not tokenCheck:
        raise Exception("Токен авторизации не действителен!")
    # --
    file = request.FILES['file']
    name, ext = os.path.splitext(file.name)
    rand = random.randrange(100000000000, 900000000000, 1)
    newName = f'{projectId}-{rand}'
    fileName = default_storage.save(f'{settings.PROJECT_INFO_DIR}/{newName}{ext}', file)
    # resFileName = settings.BACKEND_ADDR + str(settings.MEDIA_URL) + fileName
    resFileName = str(settings.MEDIA_URL) + fileName
    response = {'url': resFileName}
    return HttpResponse(json.dumps(response), content_type="json", status=200)

# def convertMedia(request):
#     buf = ''
#     workDir = '/Users/alexeysorokin/Desktop/hexp2/media/'
#     workDir = '/home/user/hexp2/media/'
#     photo = Photo.objects.all()
#     for ph in photo:
#         # Старое имя
#         oldFn = str(ph.image)
#         # Новое имя
#         name, ext = os.path.splitext(oldFn)
#         rand = random.randrange(100000000000, 900000000000, 1)
#         newName = f'{ph.finOper.project_id}-{ph.finOper_id}-{rand}'
#         newFn = f'{settings.FINOPER_PHOTO_DIR}/{newName}{ext}'
#         # Переименование
#         renOld = workDir + oldFn
#         renNew = workDir + newFn
#         os.rename(renOld, renNew)
#         ph.image = newFn
#         ph.save()
#         # Инфо
#         tmp = f'{renOld} -> {renNew}\n'
#         print(tmp)
#         buf += tmp
#     return HttpResponse(buf, content_type="text", status=200)

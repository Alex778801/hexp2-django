import graphql_jwt
from django.contrib.auth.models import User
from django.http import HttpResponse
import requests
import json

from dbcore.models import Photo, FinOper
from dbcore.models_base import aclCanMod

# Загрузить фото фин операции
def uploadFinOperPhoto(request):
    token = request.POST['token']
    ownerId = int(request.POST['ownerId'])
    operId = int(request.POST['operId'])
    # --
    owner = User.objects.get(pk=ownerId)
    oper = FinOper.objects.get(pk=operId)
    # -- Безопасность токена JWT
    query = "mutation VerifyToken($token: String!) { verifyToken(token: $token) { payload } }"
    url = 'http://127.0.0.1:8000/gp/'
    res = requests.post(url, json={'query': query, 'variables': {'token': token}}).text
    if 'error' in res or 'payload' not in res:
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
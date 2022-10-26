import graphql_jwt
from django.contrib.auth.models import User
from django.http import HttpResponse
from graphql_jwt.decorators import ensure_token

from dbcore.models import Photo, FinOper
from dbcore.models_base import aclCanMod

def uploadFinOperPhoto(request):
    token = request.POST['token']
    ownerId = int(request.POST['ownerId'])
    operId = int(request.POST['operId'])
    # --
    owner = User.objects.get(pk=ownerId)
    oper = FinOper.objects.get(pk=operId)
    # -- Безопасность токена JWT



    # -- Безопасность ACL
    canMod = aclCanMod(oper, oper.project.acl, owner)[0]
    if not canMod:
        raise Exception("У вас нет прав на модификацию данного объекта!")
    # --


    newPhoto = Photo()
    newPhoto.finOper = oper
    newPhoto.image = request.FILES['file']
    newPhoto.save()
    return HttpResponse('ok', content_type="text/plain", status=200) #400


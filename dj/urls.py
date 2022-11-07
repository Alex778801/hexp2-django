"""dj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.template.defaulttags import url
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView

from dbcore.views import uploadFinOperPhoto, uploadProjectInfo
from dj import settings
from reports import report001, report002

urlpatterns = [
    # Интерфейс администратора
    path('admin/', admin.site.urls),
    # Отладочный интерфей graphql
    path('gp/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    # Загрузить фото фин операции
    path('uploads/uploadFinOperPhoto/', csrf_exempt(uploadFinOperPhoto)),
    # Загрузить объекты текстового редактора CKE из заметок проекта Project.info
    path('uploads/uploadProjectInfo/', csrf_exempt(uploadProjectInfo)),
]

# Для доступа к медиа файлам в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
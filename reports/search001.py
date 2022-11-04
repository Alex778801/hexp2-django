from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render
import re

from dbcore.models import Project, FinOper
from dbcore.models_base import aclCanRead


def search001(findStr, user):
    # -----------------------------------------------------------------------------------------------------------
    # Операции
    operList = list(
        FinOper.objects.filter(notes__icontains=findStr)
            .annotate(proj=F('project__name'), projId=F('project__id'), operId=F('pk'), ct=F('costType__name'), agF=F('agentFrom__name'), agT=F('agentTo__name'))
            # .filter(lambda i: aclCanRead(i, i.acl, user)[0])
            .values('proj', 'projId', 'operId', 'moment', 'notes', 'ct', 'agF', 'agT', 'amount')
            .order_by('project__parent', 'project__order', '-moment')
    )
    for i in operList:
        # оформить доступ к объектам
        oper = FinOper.objects.get(pk=i['operId'])
        i['canRead'] = aclCanRead(oper.project, oper.project.acl, user)[0]
        # подсветка поиска
        i['notes'] = re.sub(F'(?i){findStr}', F'<span>{findStr}</span>', i['notes'])
    # Удалим объекты к которым нет права доступа
    operList = [oper for oper in operList if oper['canRead']]
    # -----------------------------------------------------------------------------------------------------------
    # Проекты
    projList = list(
        Project.objects.filter(info__icontains=findStr)
            .values('id', 'parent', 'order', 'name', 'info')
            .order_by('parent', 'order')
    )
    for i in projList:
        # оформить доступ к проектам
        proj = Project.objects.get(pk=i['id'])
        i['canRead'] = aclCanRead(proj, proj.acl, user)[0]
        # подсветка поиска
        i['info'] = re.sub(F'(?i){findStr}', F'<span>{findStr}</span>', i['info'])
    # Удалим объекты к кторым нет права доступа
    projList = [proj for proj in projList if proj['canRead']]
    # --
    return {'searchStr': findStr, 'operL': operList, 'projL': projList}

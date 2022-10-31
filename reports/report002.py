from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Min, Max, Avg, Func
from django.shortcuts import render, get_object_or_404
from django.db.models import F
from django.utils.timezone import now
from django.db.models.functions import TruncMonth

from dbcore.models import Project, FinOper, Budget, CostType, Agent
from dbcore.models_base import aclCanReport

from reports.froms import Report_2_Form
from reports.report001 import aggCtSum


# ----------------------------------------------------------------------------------------------------------
# ОТЧЕТ 2
# ----------------------------------------------------------------------------------------------------------


# Поиск в списке словарей по ключу
def listSearch(sList, name, value):
    return [element for element in sList if element[name] == value]

# Движения по статьям - вспомогательная
def moveOnCtH(proj, beginDate, endDate, costType, agentFrom, agentTo):
    filters = {'project': proj, 'moment__gte': beginDate, 'moment__lte': endDate}
    if costType is not None:
        filters['costType'] = costType
    if agentFrom is not None:
        filters['agentFrom'] = agentFrom
    if agentTo is not None:
        filters['agentTo'] = agentTo
    res = list(
        FinOper.objects.filter(**filters)
            .annotate(ct=F('costType__name'), ctId=F('costType__pk'), isOut=F('costType__isOutcome'))
            .values('ct', 'ctId', 'isOut')
            .annotate(qnty=Count('pk'), summ=Sum('amount'))
            .order_by('costType__parent', 'costType__order')
            # .order_by('-summ')
    )
    totalSumm = sum(i['summ'] for i in res)
    totalQnty = sum(i['qnty'] for i in res)
    res = list(map(lambda i: {**i, 'pr': i['summ'] / totalSumm * 100 if totalSumm > 0 else ''}, res))
    res_ = {'ct': 'Итого', 'summ': totalSumm, 'qnty': totalQnty}
    return res, res_

# Обороты по статьям
def report_2_moveOnCt(proj, beginDate, endDate, costType, agentFrom, agentTo):
    res = []
    beginYear = endDate - relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    endYear = endDate + relativedelta(month=12, day=31, hour=23, minute=59, second=59, microsecond=0)
    per, per_ = moveOnCtH(proj, beginDate, endDate, costType, agentFrom, agentTo)
    year, year_ = moveOnCtH(proj, beginYear, endYear, costType, agentFrom, agentTo)
    for y in year:
        yPart = {'ct': y['ct'], 'ctId': y['ctId'], 'isOut': y['isOut'], 'Ysum': y['summ'], 'Yqnty': y['qnty'], 'Ypr': y['pr']}
        pList = listSearch(per, 'ctId', y['ctId'])
        if len(pList) > 0:
            p = pList[0]
            pPart = {'Psum': p['summ'], 'Pqnty': p['qnty'], 'Ppr': p['pr']}
        else:
            pPart = {'Psum': '0'}
        res.append({**yPart, **pPart})
    res_ = { 'ct': year_['ct'], 'Ysum': year_['summ'], 'Yqnty': year_['qnty'],
             'Psum': per_['summ'], 'Pqnty': per_['qnty'] }
    return res, res_

# Движения по агентам - вспомогательная
def moveOnAgH(proj, beginDate, endDate, costType, agentFrom, agentTo, agentMode):
    filters = {'project': proj, 'moment__gte': beginDate, 'moment__lte': endDate}
    if costType is not None:
        filters['costType'] = costType
    if agentFrom is not None:
        filters['agentFrom'] = agentFrom
    if agentTo is not None:
        filters['agentTo'] = agentTo
    res = list(
        FinOper.objects.filter(**filters)
            .annotate(ag=F(agentMode + '__name'), agId=F(agentMode + '__pk'))
            .values('ag', 'agId')
            .annotate(qnty=Count('pk'), summ=Sum('amount'))
            .order_by(agentMode + '__parent', agentMode + '__order')
            # .order_by('-summ')
    )
    totalSumm = sum(i['summ'] for i in res)
    totalQnty = sum(i['qnty'] for i in res)
    res = list(map(lambda i: {**i, 'pr': i['summ'] / totalSumm * 100 if totalSumm > 0 else ''}, res))
    res_ = {'ag': 'Итого', 'summ': totalSumm, 'qnty': totalQnty}
    return res, res_

# Обороты по агентам
def report_2_moveOnAg(proj, beginDate, endDate, costType, agentFrom, agentTo, agentMode):
    res = []
    beginYear = endDate - relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    endYear = endDate + relativedelta(month=12, day=31, hour=23, minute=59, second=59, microsecond=0)
    per, per_ = moveOnAgH(proj, beginDate, endDate, costType, agentFrom, agentTo, agentMode)
    year, year_ = moveOnAgH(proj, beginYear, endYear, costType, agentFrom, agentTo, agentMode)
    for y in year:
        yPart = {'ag': y['ag'], 'agId': y['agId'], 'Ysum': y['summ'], 'Yqnty': y['qnty'], 'Ypr': y['pr']}
        pList = listSearch(per, 'agId', y['agId'])
        if len(pList) > 0:
            p = pList[0]
            pPart = {'Psum': p['summ'], 'Pqnty': p['qnty'], 'Ppr': p['pr']}
        else:
            pPart = {'Psum': '0'}
        res.append({**yPart, **pPart})
    res_ = { 'ag': year_['ag'], 'Ysum': year_['summ'], 'Yqnty': year_['qnty'],
             'Psum': per_['summ'], 'Pqnty': per_['qnty'] }
    return res, res_

# Детализация по статьям
def report_2_detailOnCt(proj, beginDate, endDate, costType, agentFrom, agentTo):
    res = []
    filters = {'project': proj, 'moment__gte': beginDate, 'moment__lte': endDate}
    if costType is not None:
        filters['costType'] = costType
    if agentFrom is not None:
        filters['agentFrom'] = agentFrom
    if agentTo is not None:
        filters['agentTo'] = agentTo
    operList = list(
        FinOper.objects.filter(**filters)
            .annotate(ct=F('costType__name'), ctId=F('costType__id'), isOut=F('costType__isOutcome'),
                      agF=F('agentFrom__name'), agT=F('agentTo__name'), summ=F('amount'), user=F('owner__username'), userColor=F('owner__userattr__color'))
            .values('pk', 'moment', 'ctId', 'ct', 'isOut', 'agF', 'agT', 'notes', 'summ', 'user', 'userColor')
            .order_by('costType__parent', 'costType__order', 'moment')
    )
    aggCtSum(operList, res)
    return res

# Вычислить сумму с группировкой по агентам
def aggAgSum(source, target):
    _gid = None
    _pos = None
    _sum = 0
    for c in source:
        # Добавим группу
        if _gid != c['agId']:
            target.append({'grp': True, **c})
            if _gid is not None:
                _pos['summ'] = _sum
            _gid = c['agId']
            _pos = target[-1]
            _sum = 0
        # Добавим элемент
        target.append(
            {'grp': False, **c})
        _sum += c['summ']
    # --
    if _gid is not None:
        _pos['summ'] = _sum

# Детализация по агентам
def report_2_detailOnAg(proj, beginDate, endDate, costType, agentFrom, agentTo, agentMode):
    res = []
    filters = {'project': proj, 'moment__gte': beginDate, 'moment__lte': endDate}
    if costType is not None:
        filters['costType'] = costType
    if agentFrom is not None:
        filters['agentFrom'] = agentFrom
    if agentTo is not None:
        filters['agentTo'] = agentTo
    operList = list(
        FinOper.objects.filter(**filters) #.exclude(agentFrom=None).exclude(agentTo=None)
            .annotate(ag=F(agentMode + '__name'), agId=F(agentMode + '__id'), ct=F('costType__name'), user=F('owner__username'), summ=F('amount'), userColor=F('owner__userattr__color'))
            .values('pk', 'moment', 'agId', 'ag', 'ct', 'notes', 'summ', agentMode + '__order', 'user', 'userColor')
            .order_by('-' + agentMode + '__parent', agentMode + '__order', 'moment', 'userColor')
    )
    aggAgSum(operList, res)
    return res

# Движения по месяцам за год
def report_2_months(proj, beginDate, endDate, costType, agentFrom, agentTo):
    beginYear = endDate - relativedelta(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    endYear = endDate + relativedelta(month=12, day=31, hour=23, minute=59, second=59, microsecond=0)
    filters = {'project': proj, 'moment__gte': beginYear, 'moment__lte': endYear}
    if costType is not None:
        filters['costType'] = costType
    if agentFrom is not None:
        filters['agentFrom'] = agentFrom
    if agentTo is not None:
        filters['agentTo'] = agentTo
    res = list(
        FinOper.objects.filter(**filters)
            .annotate(month=TruncMonth('moment'))
            .values('month')
            .annotate(summ=Sum('amount'))
            .order_by('month')
    )
    totalSumm = sum(i['summ'] for i in res)
    res = list(map(lambda i: {**i, 'pr': i['summ'] / totalSumm * 100 if totalSumm > 0 else ''}, res))
    res_ = {'month': 'Итого', 'summ': totalSumm}
    return res, res_

# Отчет №2
@login_required()
def reports_2_View(request, projId):
    try:
        proj = get_object_or_404(Project, pk=projId)
        if proj.isGrp:
            raise Exception('Project is NOT an Element')
        # Контроль доступа ACL!
        if not aclCanReport(proj, request.user):
            raise Exception('Доступ к отчету запрещен!')
        # Значения по умолчанию - до создания формы
        endDate = now() + relativedelta(months=0, day=0, hour=23, minute=59, second=59, microsecond=0)
        beginDate = endDate - relativedelta(months=0, day=1, hour=0, minute=0, second=0, microsecond=0)
        costType = None
        agentFrom = None
        agentTo = None
        # Создаем пустую форму
        if request.method == 'GET':
            form = Report_2_Form()
            form.fields['beginDate'].initial = beginDate
            form.fields['endDate'].initial = endDate
            form.fields['period'].initial = endDate
        # Получем форму из ввода пользователя, обрабатываем действия пользователя
        else:
            form = Report_2_Form(request.POST)
            if form.is_valid():
                beginDate = form.cleaned_data['beginDate']
                endDate = form.cleaned_data['endDate'] + relativedelta(months=0, day=0, hour=23, minute=59, second=59, microsecond=0)
                costType = form.cleaned_data['costType']
                agentFrom = form.cleaned_data['agentFrom']
                agentTo = form.cleaned_data['agentTo']
        # Рендер формы
        # ---
        # Строим отчет
        # Обороты по статьям
        moveOnCt, moveOnCt_ = report_2_moveOnCt(proj, beginDate, endDate, costType, agentFrom, agentTo)
        # Обороты по агентам
        moveOnAgFrom, moveOnAgFrom_ = report_2_moveOnAg(proj, beginDate, endDate, costType, agentFrom, agentTo, 'agentFrom')
        moveOnAgTo, moveOnAgTo_ = report_2_moveOnAg(proj, beginDate, endDate, costType, agentFrom, agentTo, 'agentTo')
        moveOnAg = [{'ag': 'О Т К У Д А  → → →', 'hdr': True}] + moveOnAgFrom + [{'ag': '→ → → К У Д А', 'hdr': True}] + moveOnAgTo
        # Детализация по статьям
        detct = report_2_detailOnCt(proj, beginDate, endDate, costType, agentFrom, agentTo)
        # Детализация по агентам
        detagFrom = report_2_detailOnAg(proj, beginDate, endDate, costType, agentFrom, agentTo, 'agentFrom')
        detagTo = report_2_detailOnAg(proj, beginDate, endDate, costType, agentFrom, agentTo, 'agentTo')
        detag = [{'ag': 'О Т К У Д А  → → →', 'hdr': True}] + detagFrom + [{'ag': '→ → → К У Д А', 'hdr': True}] + detagTo
        # Обороты по месяцам
        months, months_ = report_2_months(proj, beginDate, endDate, costType, agentFrom, agentTo)
        # ---
        # Значения по умолчанию - после создания формы
        form.fields['costType'].queryset = (CostType.objects.filter(parent=proj.prefCostTypeGroup, isGrp=False)
                                           | CostType.objects.filter(parent=None, isGrp=False)).order_by('parent', 'order')
        form.fields['agentFrom'].queryset = (Agent.objects.filter(parent=proj.prefAgentGroup, isGrp=False)
                                             | Agent.objects.filter(parent=None, isGrp=False)).order_by('parent', 'order')
        form.fields['agentTo'].queryset = form.fields['agentFrom'].queryset
        return render(request, 'reports/report_02.html', {'proj': proj,
                                                         'form': form,
                                                         'moveOnCt': moveOnCt,
                                                         'moveOnCt_': moveOnCt_,
                                                         'moveOnAg': moveOnAg,
                                                         'moveOnAgFrom_': moveOnAgFrom_,
                                                         'moveOnAgTo_': moveOnAgTo_,
                                                         'detct': detct,
                                                         'detag': detag,
                                                         'months': months,
                                                         'months_': months_,
                                                         })
    # Непредвиденные ошибки
    except Exception as e:
        return render(request, 'info_msg.html', {'state': 'danger', 'text': 'Ошибка: ' + str(e)})
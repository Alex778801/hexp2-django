from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Min, Max, Avg, Func
from django.shortcuts import render, get_object_or_404
from django.db.models import F
from django.utils.timezone import now

from dbcore.models import Project, FinOper, Budget, CostType, Agent
from dbcore.models_base import aclCanReport
from dj.myutils import frmSum


# ----------------------------------------------------------------------------------------------------------
# ОТЧЕТ 1
# ----------------------------------------------------------------------------------------------------------


# Отчет 1 Заголовок
def report_1_header(proj):
    res = []
    beginDate = FinOper.objects.filter(project=proj).aggregate(beginDate=Min('moment'))['beginDate']
    endDate = FinOper.objects.filter(project=proj).aggregate(endDate=Max('moment'))['endDate']
    beginDate = now() if beginDate is None else beginDate
    endDate = now() if endDate is None else endDate
    daysDiff = abs((endDate - beginDate).days)
    res.append({'param': 'Путь', 'value': proj.getParentsList()})
    res.append({'param': 'Дата начала', 'value': beginDate})
    res.append({'param': 'Дата конца', 'value': endDate})
    res.append({'param': 'Продолжительность', 'value': str(daysDiff) + ' дн.'})
    prihSumm = FinOper.objects.filter(project=proj, costType__isOutcome=False) \
        .aggregate(summ=Sum('amount'))['summ']
    prihQnty = FinOper.objects.filter(project=proj, costType__isOutcome=False) \
        .aggregate(summ=Count('amount'))['summ']
    rashSumm = FinOper.objects.filter(project=proj, costType__isOutcome=True) \
        .aggregate(summ=Sum('amount'))['summ']
    rashQnty = FinOper.objects.filter(project=proj, costType__isOutcome=True) \
        .aggregate(summ=Count('amount'))['summ']
    prihSumm = prihSumm if prihSumm is not None else 0
    rashSumm = rashSumm if rashSumm is not None else 0
    sumDiff = prihSumm - rashSumm
    res.append({'param': 'Приход', 'value': frmSum(prihSumm) + ' (' + str(prihQnty) + ')'})
    res.append({'param': 'Раход', 'value': frmSum(rashSumm) + ' (' + str(rashQnty) + ')'})
    res.append({'param': 'Остаток', 'value': frmSum(sumDiff)})
    return res

# Приход/расход по статьям
def report_1_moveOnCt(proj, isOutcome):
    res = list(
        FinOper.objects.filter(project=proj, costType__isOutcome=isOutcome).annotate(ct=F('costType__name'), ctId=F('costType__pk'))
            .values('ct', 'ctId').annotate(qnty=Count('pk'), summ=Sum('amount'))
            .order_by('costType__parent', 'costType__Order')
            # .order_by('-summ')
    )
    totalSumm = sum(i['summ'] for i in res)
    totalQnty = sum(i['qnty'] for i in res)
    res = list(map(lambda i: {**i, 'pr': i['summ'] / totalSumm * 100 if totalSumm > 0 else ''}, res))
    res_ = {'ct': 'Итого', 'summ': totalSumm, 'qnty': totalQnty}
    return res, res_

# Обороты контрагентов
def report_1_agMove(proj):
    res1 = [{'ag': 'Откуда →'}] + \
           list(
                FinOper.objects.filter(project=proj).annotate(ag=F('agentFrom__name'), isOut=F('costType__isOutcome'))
                .values('ag', 'isOut').annotate(qnty=Count('pk'), summ=Sum('amount'))
                .order_by('agentFrom__parent', 'agentFrom__order')
                # .order_by('-summ')
            )
    res2 = [{'ag': '→ Куда'}] + \
           list(
                FinOper.objects.filter(project=proj).annotate(ag=F('agentTo__name'), isOut=F('costType__isOutcome'))
                .values('ag', 'isOut').annotate(qnty=Count('pk'), summ=Sum('amount'))
                .order_by('agentTo__parent', 'agentTo__order')
                # .order_by('-summ')
            )

    res = res1 + res2
    return res

# Вычислить сумму с группировкой по статье
def aggCtSum(source, target):
    _gid = None
    _pos = None
    _sum = 0
    for c in source:
        # Добавим группу
        if _gid != c['ctId']:
            ctName = c['ct'] if c['isOut'] else ('[+] ' + c['ct'])
            target.append({'grp': True, **c, 'ct': ctName})
            if _gid is not None:
                _pos['summ'] = _sum
            _gid = c['ctId']
            _pos = target[-1]
            _sum = 0
        # Добавим элемент
        target.append(
            {'grp': False, **c})
        _sum += c['summ']
    # --
    if _gid is not None:
        _pos['summ'] = _sum


# Детализация по статьям
def report_1_detailOnCt(proj):
    res = []
    operList = list(
        FinOper.objects.filter(project=proj)
            .annotate(ct=F('costType__name'), ctId=F('costType__id'), isOut=F('costType__isOutcome'),
                      agF=F('agentFrom__name'), agT=F('agentTo__name'), summ=F('amount'), user=F('owner__username'),  userColor=F('owner__userattr__color'))
            .values('pk', 'moment', 'ctId', 'ct', 'isOut', 'agF', 'agT', 'notes', 'summ', 'user', 'userColor')
            .order_by('costType__parent', 'costType__order', 'moment')
    )
    aggCtSum(operList, res)
    return res

# Бюджет
def report_1_budget(proj):
    res = []
    # Запланированный бюджет
    budListQ = list(
        Budget.objects.filter(project=proj)
            .annotate(ct=F('costType__name'), ctId=F('costType__id'), isOut=F('costType__isOutcome'), summ=F('amount'))
            .values('ct', 'ctId', 'isOut', 'notes', 'summ')
            .order_by('costType__parent', 'costType__order', 'order')
    )
    budList = []
    aggCtSum(budListQ, budList)
    # Фин операции
    operListQ = list(
        FinOper.objects.filter(project=proj)
            .annotate(ct=F('costType__name'), ctId=F('costType__id'), isOut=F('costType__isOutcome'), summ=F('amount'))
            .values('ctId', 'ct', 'isOut', 'notes', 'summ', 'pk', 'moment', )
            .order_by('costType__parent', 'costType__order', 'moment')
    )
    operList = []
    aggCtSum(operListQ, operList)
    # Слияние
    _ctId = None
    __ctId = None
    for budIt in budList:
        if budIt['grp']:
            if __ctId is not None:
                # Строки операций
                for operIt in operList:
                    if operIt['ctId'] == __ctId and not operIt['grp']:
                        res.append({'type': 'oper', **operIt})
            # Группа
            _ctId = budIt['ctId']
            __ctId = _ctId
            hasEqOper = False
            for operIt in operList:
                if operIt['ctId'] == budIt['ctId']:
                    sumdiff = budIt['summ'] - operIt['summ']
                    res.append({**budIt, 'sumb': budIt['summ'], 'sumo': operIt['summ'], 'sumdiff': sumdiff})
                    hasEqOper = True
                    break
            if not hasEqOper:
                res.append({**budIt, 'sumb': budIt['summ'], 'sumo': '---', 'sumdiff':  budIt['summ']})
            continue
        # Строки бюджета
        else:
            if _ctId == budIt['ctId']:
                res.append({'type': 'bud', **budIt})
                continue
    return res

# Отчет №1
def report001(projId):
    proj = get_object_or_404(Project, pk=projId)
    if proj.isGrp:
        raise Exception('Project is NOT an Element')
    # Строим отчет
    # Заголовок
    head = report_1_header(proj)
    # Приход по статьям
    prihps, prihps_ = report_1_moveOnCt(proj, False)
    # Расход по статьям
    rashps, rashps_ = report_1_moveOnCt(proj, True)
    # Обороты агентов
    obk = report_1_agMove(proj)
    # Детализация по статьям
    detct = report_1_detailOnCt(proj)
    # Бюджет
    budget = report_1_budget(proj)
    # ---
    # Итоговый результат
    return {
            'proj': proj,
            'head': head,
            'prihps': prihps,
            'prihps_': prihps_,
            'rashps': rashps,
            'rashps_': rashps_,
            'obk': obk,
            'detct': detct,
            'budget': budget,
           }

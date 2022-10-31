from django.forms import Form, DateField, ModelChoiceField, DateTimeInput
from dbcore.models import CostType, Agent


class Report_2_Form(Form):
    beginDate = DateField(label='Дата начала', widget=DateTimeInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    endDate = DateField(label='Дата конца',  widget=DateTimeInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    period = DateField(label='Месяц/год',  widget=DateTimeInput(attrs={'type': 'month'}, format='%Y-%m'), input_formats=['%Y-%m'])
    costType = ModelChoiceField(label='Статья', empty_label='< все >', required=False, blank=True, queryset=CostType.objects.all())
    agentFrom = ModelChoiceField(label='Агент Откуда', empty_label='< все >', required=False, blank=True, queryset=Agent.objects.all())
    agentTo = ModelChoiceField(label='Агент Куда', empty_label='< все >', required=False, blank=True, queryset=Agent.objects.all())

    class Meta:
        pass







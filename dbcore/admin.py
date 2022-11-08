from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from .models import Project, CostType, Agent, FinOper, Photo, Budget, SysParam


# -----------------------------------------------------------------
# Системные параметры
@admin.register(SysParam)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'value')
    ordering = ['name']
    search_fields = ('name', 'value')


# -----------------------------------------------------------------
# Статьи

@admin.register(CostType)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'parent', 'isGrp', 'order', 'name', 'isOutcome', 'color')
    ordering = ('parent', '-isGrp', 'order')
    search_fields = ('pk', 'name__icontains')


# -----------------------------------------------------------------
# Агенты

@admin.register(Agent)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'parent', 'isGrp', 'order', 'name')
    ordering = ('parent', '-isGrp', 'order')
    search_fields = ('pk', 'name__icontains')


# -----------------------------------------------------------------
# Проекты = мастер - детализация для: проект - фин операции

# class FinOperInline(admin.TabularInline):
#     model = FinOper
#     extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('pk', 'parent', 'isGrp', 'order', 'name')
    ordering = ('parent', '-isGrp', 'order')
    search_fields = ('pk', 'name__icontains')

    # inlines = [FinOperInline]

    class Meta:
        model = Project


# -----------------------------------------------------------------
# Фин операции = мастер - детализация для: фин-операция - фотки

class PhotoInline(admin.TabularInline):
    model = Photo
    extra = 1


@admin.register(FinOper)
class FinoperAdmin(admin.ModelAdmin):
    list_display = ('pk', 'dt', 'project', 'costType', 'agentFrom', 'agentTo', 'notes', 'amount')
    ordering = ('-moment', )
    list_filter = ('moment', ('moment', DateRangeFilter), 'project')
    search_fields = ('pk', 'notes__icontains')

    def dt(self, obj):
        return obj.moment.strftime('%Y-%m-%d %H:%M:%S')

    dt.short_description = 'Дата'

    inlines = [PhotoInline]

    class Meta:
        model = FinOper


# -----------------------------------------------------------------
# Бюджеты

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('pk', 'project', 'costType', 'order', 'notes', 'amount')
    ordering = ('project', 'costType', 'order')
    list_filter = ('project', )
    search_fields = ('pk', 'notes__icontains')


# -----------------------------------------------------------------
# Фото

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('pk', 'finOper', 'image')
    ordering = ('finOper', )
    search_fields = ('pk', )

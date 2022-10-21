from django.contrib import admin
from django.contrib.auth.models import Permission
from django.forms import ModelForm, TextInput
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from rangefilter.filters import DateRangeFilter

from ua.models import UserAction, UserAttr

admin.site.register(Permission)


# -----------------------------------------------------------------
# Атрибуты пользователей

class UserAttrForm(ModelForm):
    class Meta:
        model = UserAttr
        fields = '__all__'
        widgets = {
            'color': TextInput(attrs={'type': 'color'}),
        }


@admin.register(UserAttr)
class UserAttrAdmin(admin.ModelAdmin):
    list_display = ('pk', 'user', 'color', 'color2', 'openObjectsInNewWindow')
    ordering = ('user', )
    list_filter = ('user', )
    search_fields = ('user__icontains', )

    def color2(self, obj):
        return mark_safe(
            f'<div style="color: {obj.color}; height: 2.2em; line-height: 2.2em; text-align: center">Образец цвета <strong> Образец цвета </strong></div>'
            f'<div style="color: {obj.color}; background-color: white; height: 2.2em; line-height: 2.2em; text-align: center"> Образец цвета <strong> Образец цвета </strong> </div>')

    color2.short_description = "Образец цвета"

    form = UserAttrForm


# -----------------------------------------------------------------
# Журнал действий пользователей в приложении

@admin.display(description='link')
@admin.register(UserAction)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ('dt', 'warnLvl', 'user', 'object', 'msg', 'diff', 'http')
    ordering = ('-moment', )
    list_filter = ('user', 'warnLvl', 'object', 'moment', ('moment', DateRangeFilter))
    search_fields = ('msg__icontains', )

    def dt(self, obj):
        return obj.moment.strftime('%Y-%m-%d %H:%M:%S')

    dt.short_description = 'Дата'

    def http(self, obj):
        from django.conf import settings
        baseAddress = settings.UA_BASEADDR
        if obj.link is not None:
            # return format_html('<a href="{url}">{url}</a>', url=obj.link)
            return format_html('<a href="{url}">{url}</a>', url=f'{baseAddress}{obj.link}')
        else:
            return ''

    http.short_description = 'Ссылка'

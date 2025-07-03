from django.contrib import admin
from .models import TablePermission, PvoRegistro


admin.site.register(TablePermission)


@admin.register(PvoRegistro)
class PvoRegistroAdmin(admin.ModelAdmin):
    list_display = ['pid', 'fecha_full', 'fecha_flp', 'fecha_fef', 'creado_por', 'fecha_creacion']

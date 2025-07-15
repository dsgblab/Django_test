from django.contrib import admin
from .models import TablePermission, PvoRegistro, HistoricalPvoRegistro
from simple_history.admin import SimpleHistoryAdmin

@admin.register(TablePermission)
class TablePermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'table', 'can_read', 'can_write', 'can_delete', 'can_edit', 'can_edit_full', 'can_edit_flp', 'can_edit_fef', 'can_view_history')
    list_filter = ('table',)
    search_fields = ('user__username',)


@admin.register(PvoRegistro)
class PvoRegistroAdmin(admin.ModelAdmin):
    list_display = ['pid', 'fecha_full', 'fecha_flp', 'fecha_fef', 'creado_por', 'fecha_creacion']


@admin.register(HistoricalPvoRegistro)
class HistoricalPvoRegistroAdmin(SimpleHistoryAdmin):
    list_display = ['pid', 'fecha_full', 'fecha_flp', 'fecha_fef', 'creado_por', 'fecha_creacion']

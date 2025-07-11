from django.contrib import admin
from .models import TablePermission, PvoRegistro, HistoricalPvoRegistro
from simple_history.admin import SimpleHistoryAdmin


@admin.register(TablePermission)
class TablePermissionAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'table', 'can_read', 'can_write', 'can_delete', 'can_edit',
        'can_edit_full', 'can_edit_flp', 'can_edit_fef', 'can_view_history'
    )
    list_filter = ('table',)
    search_fields = ('user__username',)


@admin.register(PvoRegistro)
class PvoRegistroAdmin(admin.ModelAdmin):
    list_display = [
        'pid', 'fecha_full', 'fecha_flp', 'fecha_fef',
        'creado_por', 'fecha_creacion'
    ]


@admin.register(HistoricalPvoRegistro)
class HistoricalPvoRegistro(SimpleHistoryAdmin):
    list_display = [
        'pid', 'fecha_full', 'fecha_flp', 'fecha_fef',
        'creado_por', 'fecha_creacion', 'get_changed_fields'
    ]
    history_list_display = ['history_date', 'history_change_reason', 'history_type']
    search_fields = ['pid']
    list_filter = ['history_date', 'history_type']

    def get_changed_fields(self, obj):
        try:
            previous = obj.prev_record
            if not previous:
                return "-"
            changed_fields = []
            for field in obj._meta.fields:
                field_name = field.name
                if field_name in [
                    'history_id', 'history_date', 'history_user',
                    'history_type', 'history_change_reason', 'id'
                ]:
                    continue  # skip metadata fields
                old = getattr(previous, field_name, None)
                new = getattr(obj, field_name, None)
                if old != new:
                    changed_fields.append(field_name)
            return ", ".join(changed_fields) if changed_fields else "-"
        except Exception as e:
            return f"Error: {e}"

    get_changed_fields.short_description = "Changed Fields"

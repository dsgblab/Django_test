# tableapp/admin.py
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .models import (
    TablePermission,
    PvoRegistro,
    FPConfig,
    FPCatalogo,
)

# ---------------------------
# Permisos por tabla
# ---------------------------
@admin.register(TablePermission)
class TablePermissionAdmin(admin.ModelAdmin):
    list_display = (
        "user", "table",
        "can_read", "can_write", "can_delete", "can_edit",
        "can_edit_full", "can_edit_flp", "can_edit_fif", "can_edit_fef",
        "can_view_history",
    )
    list_filter = ("table",)
    search_fields = ("user__username",)


# ---------------------------
# PVO principal (con historial embebido)
# ---------------------------
@admin.register(PvoRegistro)
class PvoRegistroAdmin(SimpleHistoryAdmin):
    list_display = (
        "pid",
        "fecha_full", "fecha_flp", "fecha_fif", "fecha_fef",
        "obs_full", "obs_flp", "obs_fef",  # <<< NUEVO
        "batch", "planta", "tamano_lote", "familia", "tipo",
        "creado_por", "fecha_creacion",
    )
    search_fields = ("pid",)
    list_filter = ("familia", "tipo", "planta")


# ---------------------------
# Modelos de soporte para combos / config
# ---------------------------
@admin.register(FPCatalogo)
class FPCatalogoAdmin(admin.ModelAdmin):
    list_display = ("grupo", "valor")
    list_filter = ("grupo",)
    search_fields = ("valor",)


@admin.register(FPConfig)
class FPConfigAdmin(admin.ModelAdmin):
    list_display = (
        "codigo_producto", "estado_fp", "tiempo_fp_horas",
        "familia", "tipo", "batch", "planta", "tamano_lote", "personal_fase",
        "updated_at",
    )
    search_fields = ("codigo_producto",)
    list_filter = ("estado_fp", "familia", "tipo", "planta")


# ---------------------------
# Registro del modelo histórico dinámico
# (Simple History crea una clase en runtime)
# ---------------------------
PvoHistModel = PvoRegistro.history.model  # <- modelo histórico real

@admin.register(PvoHistModel)
class PvoRegistroHistoryAdmin(admin.ModelAdmin):
    date_hierarchy = "history_date"
    list_display = (
        "pid",
        "history_date", "history_type", "history_user",
        "fecha_full", "fecha_flp", "fecha_fif", "fecha_fef",
    )
    list_filter = ("history_type",)
    search_fields = ("pid",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("history_user")

    # (Opcional) ver campos cambiados en cada entrada histórica
    def changed_fields(self, obj):
        prev = getattr(obj, "prev_record", None)
        if not prev:
            return "—"
        changed = []
        for f in obj._meta.fields:
            name = f.name
            if name in {
                "id", "history_id", "history_date", "history_user",
                "history_type", "history_change_reason",
            }:
                continue
            if getattr(prev, name, None) != getattr(obj, name, None):
                changed.append(name)
        return ", ".join(changed) if changed else "—"

    changed_fields.short_description = "Changed fields"

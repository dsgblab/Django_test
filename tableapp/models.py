from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords


# ---------------------------
# Permisos por tabla
# ---------------------------
class TablePermission(models.Model):
    TABLE_CHOICES = (
        ("report", "Report"),
        ("edit_dates", "Edit Dates"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.CharField(choices=TABLE_CHOICES, max_length=20)

    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)

    can_edit_full = models.BooleanField(default=False)
    can_edit_flp  = models.BooleanField(default=False)
    can_edit_fif  = models.BooleanField(default=False)
    can_edit_fef  = models.BooleanField(default=False)

    can_view_history = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "table")

    def __str__(self):
        return f"{self.user.username} - {self.table}"


# ---------------------------
# PVO + campos de análisis
# ---------------------------
class PvoRegistro(models.Model):
    pid = models.CharField(max_length=20, unique=True)

    # Fechas “clásicas” del tablero
    fecha_full = models.DateField(null=True, blank=True)
    fecha_flp  = models.DateField(null=True, blank=True)
    fecha_fif  = models.DateField(null=True, blank=True)
    fecha_fef  = models.DateField(null=True, blank=True)

    # >>> NUEVO: observaciones por fecha <<<
    obs_full = models.TextField(null=True, blank=True)
    obs_flp  = models.TextField(null=True, blank=True)
    obs_fef  = models.TextField(null=True, blank=True)

    # Datos globales
    pt          = models.CharField(max_length=50, null=True, blank=True, db_column="PT")
    batch       = models.IntegerField(null=True, blank=True, db_column="BATCH")
    planta      = models.CharField(max_length=50, null=True, blank=True, db_column="PLANTA")
    tamano_lote = models.IntegerField(null=True, blank=True, db_column="TAMANO_LOTE")
    familia     = models.CharField(max_length=50, null=True, blank=True, db_column="FAMILIA")
    tipo        = models.CharField(max_length=50, null=True, blank=True, db_column="TIPO")

    # ===== FASES =====
    # Nota: por requerimiento, F_* guarda el **nombre de la fase** (texto),
    # T_* el tiempo (decimal) y P_* el personal (entero).

    # DISPENSACION
    f_dispensacion = models.CharField(max_length=50, null=True, blank=True, db_column="F_DISPENSACION")
    t_dispensacion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="T_DISPENSACION")
    p_dispensacion = models.IntegerField(null=True, blank=True, db_column="P_DISPENSACION")

    # PESAJE
    f_pesaje = models.CharField(max_length=50, null=True, blank=True, db_column="F_PESAJE")
    t_pesaje = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="T_PESAJE")
    p_pesaje = models.IntegerField(null=True, blank=True, db_column="P_PESAJE")

    # FABRICACION
    f_fabricacion = models.CharField(max_length=50, null=True, blank=True, db_column="F_FABRICACION")
    t_fabricacion = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="T_FABRICACION")
    p_fabricacion = models.IntegerField(null=True, blank=True, db_column="P_FABRICACION")

    # ENFRIAMIENTO
    f_enfriamiento = models.CharField(max_length=50, null=True, blank=True, db_column="F_ENFRIAMIENTO")
    t_enfriamiento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="T_ENFRIAMIENTO")
    p_enfriamiento = models.IntegerField(null=True, blank=True, db_column="P_ENFRIAMIENTO")

    # ENVASADO
    f_envasado = models.CharField(max_length=50, null=True, blank=True, db_column="F_ENVASADO")
    t_envasado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="T_ENVASADO")
    p_envasado = models.IntegerField(null=True, blank=True, db_column="P_ENVASADO")

    # ACONDICIONAMIENTO
    f_acondicionamiento = models.CharField(max_length=50, null=True, blank=True, db_column="F_ACONDICIONAMIENTO")
    t_acondicionamiento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="T_ACONDICIONAMIENTO")
    p_acondicionamiento = models.IntegerField(null=True, blank=True, db_column="P_ACONDICIONAMIENTO")

    # EMBALAJE
    f_embalaje = models.CharField(max_length=50, null=True, blank=True, db_column="F_EMBALAJE")
    t_embalaje = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="T_EMBALAJE")
    p_embalaje = models.IntegerField(null=True, blank=True, db_column="P_EMBALAJE")

    # DESPACHO
    f_despacho = models.CharField(max_length=50, null=True, blank=True, db_column="F_DESPACHO")
    t_despacho = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_column="T_DESPACHO")
    p_despacho = models.IntegerField(null=True, blank=True, db_column="P_DESPACHO")

    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        managed = True
        db_table = "tableapp_pvoregistro"

    def __str__(self):
        return self.pid


# ---------------------------
# Catálogo para combos
# ---------------------------
class FPCatalogo(models.Model):
    grupo = models.CharField(max_length=30)   # p.ej. ESTADO FP, FAMILIA, TIPO, PLANTA
    valor = models.CharField(max_length=50)   # p.ej. ENVASADO, FRIO, CREMA, P1

    class Meta:
        db_table = "tableapp_fpcatalogo"

    def __str__(self):
        return f"{self.grupo}: {self.valor}"


# ---------------------------
# Config por código de producto
# ---------------------------
class FPConfig(models.Model):
    codigo_producto = models.CharField(max_length=50, primary_key=True)
    estado_fp       = models.CharField(max_length=50, null=True, blank=True)
    tiempo_fp_horas = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    familia         = models.CharField(max_length=50, null=True, blank=True)
    tipo            = models.CharField(max_length=50, null=True, blank=True)
    batch           = models.CharField(max_length=50, null=True, blank=True)
    planta          = models.CharField(max_length=50, null=True, blank=True)
    tamano_lote     = models.CharField(max_length=50, null=True, blank=True)
    personal_fase   = models.IntegerField(null=True, blank=True)
    capacidad       = models.IntegerField(null=True, blank=True)  # gramaje/capacidad en la unidad que uses
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tableapp_fpconfig"

    def __str__(self):
        return self.codigo_producto

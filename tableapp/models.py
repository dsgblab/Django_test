from django.db import models
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords

class TablePermission(models.Model):
    TABLE_CHOICES = (
        ('report', 'Report'),
        ('edit_dates', 'Edit Dates'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    table = models.CharField(choices=TABLE_CHOICES, max_length=20)
    can_read = models.BooleanField(default=False)
    can_write = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)

    # Permisos adicionales
    can_edit_full = models.BooleanField(default=False)
    can_edit_flp = models.BooleanField(default=False)
    can_edit_fef = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'table')

    def __str__(self):
        return f"{self.user.username} - {self.table}"


class PvoRegistro(models.Model):
    pid = models.CharField(max_length=20, unique=True)

    # Fechas
    fecha_full = models.DateField(null=True, blank=True)
    fecha_flp = models.DateField(null=True, blank=True)
    fecha_fef = models.DateField(null=True, blank=True)

    # Auditoría
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()
    
    class Meta:
        managed = True
        db_table = 'tableapp_pvoregistro'

    def __str__(self):
        return self.pid

    @property
    def guid(self):
        return self.pid

    @property
    def updated_by(self):
        return self.creado_por.username if self.creado_por else "N/A"

    @property
    def updated_at(self):
        return self.fecha_creacion

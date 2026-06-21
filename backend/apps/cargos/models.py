from django.db import models

from apps.core.models import ActiveModel, IglesiaScopedModel, TimeStampedModel


class Cargo(TimeStampedModel, ActiveModel):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    es_nacional = models.BooleanField(default=False)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "cargo"
        verbose_name_plural = "cargos"

    def __str__(self):
        return self.nombre


class AsignacionCargo(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        VIGENTE = "VIGENTE", "Vigente"
        FINALIZADO = "FINALIZADO", "Finalizado"
        ANULADO = "ANULADO", "Anulado"

    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="asignaciones")
    miembro = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, null=True, blank=True, related_name="cargos")
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, null=True, blank=True, related_name="cargos")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.VIGENTE)
    documento = models.FileField(upload_to="cargos/documentos/", blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-fecha_inicio",)
        verbose_name = "asignacion de cargo"
        verbose_name_plural = "asignaciones de cargos"

    def __str__(self):
        asignado = self.miembro or self.usuario
        return f"{self.cargo} - {asignado}"

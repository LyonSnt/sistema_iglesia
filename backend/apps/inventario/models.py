from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import IglesiaScopedModel, TimeStampedModel


class ActivoInventario(TimeStampedModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        ASIGNADO = "ASIGNADO", "Asignado"
        EN_REPARACION = "EN_REPARACION", "En reparacion"
        DADO_DE_BAJA = "DADO_DE_BAJA", "Dado de baja"

    codigo = models.CharField(max_length=40)
    nombre = models.CharField(max_length=160)
    categoria = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    ubicacion_actual = models.CharField(max_length=160)
    responsable_actual = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="activos_inventario_responsable",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.DISPONIBLE)
    fecha_adquisicion = models.DateField(null=True, blank=True)
    valor_referencial = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ("iglesia__nombre", "codigo")
        unique_together = ("iglesia", "codigo")
        verbose_name = "activo de inventario"
        verbose_name_plural = "activos de inventario"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def clean(self):
        errors = {}
        if (
            self.responsable_actual_id
            and self.iglesia_id
            and self.responsable_actual.iglesia_id != self.iglesia_id
        ):
            errors["responsable_actual"] = "El responsable debe pertenecer a la misma iglesia."
        if self.valor_referencial is not None and self.valor_referencial < 0:
            errors["valor_referencial"] = "El valor referencial no puede ser negativo."
        if errors:
            raise ValidationError(errors)


class MovimientoInventario(TimeStampedModel, IglesiaScopedModel):
    class Tipo(models.TextChoices):
        UBICACION = "UBICACION", "Cambio de ubicacion"
        RESPONSABLE = "RESPONSABLE", "Cambio de responsable"
        REPARACION = "REPARACION", "Reparacion o mantenimiento"
        BAJA = "BAJA", "Baja"

    activo = models.ForeignKey(
        ActivoInventario,
        on_delete=models.PROTECT,
        related_name="movimientos",
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    fecha = models.DateField()
    ubicacion_anterior = models.CharField(max_length=160, blank=True)
    ubicacion_nueva = models.CharField(max_length=160, blank=True)
    responsable_anterior = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_inventario_responsable_anterior",
    )
    responsable_nuevo = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_inventario_responsable_nuevo",
    )
    detalle = models.TextField()
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="movimientos_inventario_registrados",
    )

    class Meta:
        ordering = ("-fecha", "-creado_en")
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.activo}"

    def clean(self):
        errors = {}
        if self.activo_id and self.iglesia_id and self.activo.iglesia_id != self.iglesia_id:
            errors["activo"] = "El activo debe pertenecer a la misma iglesia."
        for campo in ("responsable_anterior", "responsable_nuevo"):
            usuario = getattr(self, campo)
            if usuario is not None and self.iglesia_id and usuario.iglesia_id != self.iglesia_id:
                errors[campo] = "El responsable debe pertenecer a la misma iglesia."
        if errors:
            raise ValidationError(errors)

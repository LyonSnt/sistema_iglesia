from django.db import models
from django.core.exceptions import ValidationError

from apps.core.models import ActiveModel, IglesiaScopedModel, TimeStampedModel


class Ministerio(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    class Tipo(models.TextChoices):
        DEPARTAMENTO = "DEPARTAMENTO", "Departamento"
        MINISTERIO = "MINISTERIO", "Ministerio"
        EQUIPO = "EQUIPO", "Equipo"
        GRUPO = "GRUPO", "Grupo"

    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.MINISTERIO)
    descripcion = models.TextField(blank=True)
    responsable = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, null=True, blank=True)
    lider = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="ministerios_liderados",
    )

    class Meta:
        unique_together = ("iglesia", "nombre")
        ordering = ("nombre",)
        verbose_name = "ministerio"
        verbose_name_plural = "ministerios"

    def __str__(self):
        return self.nombre

    def clean(self):
        super().clean()
        errors = {}
        if self.responsable_id and self.iglesia_id and self.responsable.iglesia_id != self.iglesia_id:
            errors["responsable"] = "El responsable debe pertenecer a la misma iglesia."
        if self.lider_id and self.iglesia_id and self.lider.iglesia_id != self.iglesia_id:
            errors["lider"] = "El lider debe pertenecer a la misma iglesia."
        if errors:
            raise ValidationError(errors)


class ParticipacionMinisterio(TimeStampedModel, ActiveModel):
    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"
        FINALIZADO = "FINALIZADO", "Finalizado"

    ministerio = models.ForeignKey(Ministerio, on_delete=models.PROTECT, related_name="participaciones")
    miembro = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, related_name="ministerios")
    cargo = models.CharField(max_length=120, blank=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    motivo_salida = models.TextField(blank=True)

    class Meta:
        ordering = ("-fecha_inicio",)
        verbose_name = "participacion ministerial"
        verbose_name_plural = "participaciones ministeriales"

    def __str__(self):
        return f"{self.miembro} - {self.ministerio}"

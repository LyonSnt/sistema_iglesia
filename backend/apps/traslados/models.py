from django.db import models

from apps.core.models import IglesiaScopedModel, TimeStampedModel


class Traslado(TimeStampedModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        SOLICITADO = "SOLICITADO", "Solicitado"
        APROBADO = "APROBADO", "Aprobado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        CANCELADO = "CANCELADO", "Cancelado"

    miembro = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, related_name="traslados")
    iglesia_destino = models.ForeignKey(
        "iglesias.Iglesia",
        on_delete=models.PROTECT,
        related_name="traslados_recibidos",
    )
    solicitado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="traslados_solicitados",
    )
    respondido_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="traslados_respondidos",
    )
    fecha_solicitud = models.DateField()
    fecha_respuesta = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.SOLICITADO)
    motivo = models.TextField(blank=True)
    observacion_respuesta = models.TextField(blank=True)

    class Meta:
        ordering = ("-fecha_solicitud", "-creado_en")
        verbose_name = "traslado"
        verbose_name_plural = "traslados"

    def __str__(self):
        return f"{self.miembro} de {self.iglesia} a {self.iglesia_destino}"

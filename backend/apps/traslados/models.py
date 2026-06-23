from django.db import models

from apps.core.models import TimeStampedModel


class TrasladoMiembro(TimeStampedModel):
    class Estado(models.TextChoices):
        SOLICITADO = "SOLICITADO", "Solicitado"
        ACEPTADO = "ACEPTADO", "Aceptado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        ANULADO = "ANULADO", "Anulado"

    miembro = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, related_name="traslados")
    iglesia_origen = models.ForeignKey(
        "iglesias.Iglesia",
        on_delete=models.PROTECT,
        related_name="traslados_origen",
    )
    iglesia_destino = models.ForeignKey(
        "iglesias.Iglesia",
        on_delete=models.PROTECT,
        related_name="traslados_destino",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.SOLICITADO)
    motivo = models.TextField()
    observacion_respuesta = models.TextField(blank=True)
    solicitado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="traslados_solicitados",
    )
    respondido_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="traslados_respondidos",
        null=True,
        blank=True,
    )
    respondido_en = models.DateTimeField(null=True, blank=True)
    completado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "traslado de miembro"
        verbose_name_plural = "traslados de miembros"

    def __str__(self):
        return f"{self.miembro} de {self.iglesia_origen.codigo} a {self.iglesia_destino.codigo}"

    @property
    def pendiente(self):
        return self.estado == self.Estado.SOLICITADO

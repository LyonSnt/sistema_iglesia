from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import IglesiaScopedModel, TimeStampedModel


class CertificadoEscuelaDominical(TimeStampedModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        EMITIDO = "EMITIDO", "Emitido"
        ANULADO = "ANULADO", "Anulado"

    resultado_promocion = models.OneToOneField(
        "escuela_dominical.ResultadoPromocionEscuelaDominical",
        on_delete=models.PROTECT,
        related_name="certificado",
    )
    numero = models.CharField(max_length=40, unique=True)
    fecha_emision = models.DateField()
    fecha_graduacion = models.DateField()
    nombre_alumno = models.CharField(max_length=250)
    nivel_cursado = models.CharField(max_length=120)
    periodo_lectivo = models.CharField(max_length=80)
    nombre_pastor = models.CharField(max_length=180)
    nombre_director = models.CharField(max_length=180)
    emitido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="certificados_escuela_emitidos",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.EMITIDO)
    anulado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="certificados_escuela_anulados",
    )
    anulado_en = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-fecha_emision", "-numero")
        verbose_name = "certificado de Escuela Dominical"
        verbose_name_plural = "certificados de Escuela Dominical"

    def clean(self):
        super().clean()
        if (
            self.resultado_promocion_id
            and self.resultado_promocion.proceso.iglesia_id != self.iglesia_id
        ):
            raise ValidationError(
                {"resultado_promocion": "La promocion debe pertenecer a la misma iglesia."}
            )

    def __str__(self):
        return f"{self.numero} - {self.nombre_alumno}"

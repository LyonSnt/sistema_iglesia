from django.db import models

from apps.core.models import IglesiaScopedModel, TimeStampedModel


class AporteNacional(TimeStampedModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADO = "PAGADO", "Pagado"
        ANULADO = "ANULADO", "Anulado"

    cierre = models.OneToOneField(
        "finanzas.CierreMensualFinanciero",
        on_delete=models.PROTECT,
        related_name="aporte_nacional",
    )
    anio = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
    monto_base = models.DecimalField(max_digits=12, decimal_places=2)
    monto_aporte = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    generado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="aportes_nacionales_generados",
    )
    fecha_pago = models.DateField(null=True, blank=True)
    referencia_pago = models.CharField(max_length=120, blank=True)
    numero_recibo = models.CharField(max_length=40, unique=True, null=True, blank=True)
    registrado_pago_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="pagos_aportes_nacionales_registrados",
    )
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-anio", "-mes", "iglesia__nombre")
        unique_together = ("iglesia", "anio", "mes")
        verbose_name = "aporte nacional"
        verbose_name_plural = "aportes nacionales"

    def __str__(self):
        return f"{self.iglesia} - {self.anio}-{self.mes:02d}"

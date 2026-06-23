from django.db import models

from apps.core.models import ActiveModel, IglesiaScopedModel, TimeStampedModel


class TipoMovimiento(models.TextChoices):
    INGRESO = "INGRESO", "Ingreso"
    EGRESO = "EGRESO", "Egreso"


class ConceptoFinanciero(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    nombre = models.CharField(max_length=140)
    tipo = models.CharField(max_length=20, choices=TipoMovimiento.choices)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ("tipo", "nombre")
        unique_together = ("iglesia", "tipo", "nombre")
        verbose_name = "concepto financiero"
        verbose_name_plural = "conceptos financieros"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nombre}"


class MovimientoFinanciero(TimeStampedModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        REGISTRADO = "REGISTRADO", "Registrado"
        ANULADO = "ANULADO", "Anulado"

    concepto = models.ForeignKey(ConceptoFinanciero, on_delete=models.PROTECT, related_name="movimientos")
    tipo = models.CharField(max_length=20, choices=TipoMovimiento.choices)
    fecha = models.DateField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.CharField(max_length=255)
    numero_comprobante = models.CharField(max_length=80, blank=True)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="movimientos_financieros_registrados",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.REGISTRADO)
    fecha_anulacion = models.DateField(null=True, blank=True)
    motivo_anulacion = models.TextField(blank=True)
    anulado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="movimientos_financieros_anulados",
    )

    class Meta:
        ordering = ("-fecha", "-creado_en")
        verbose_name = "movimiento financiero"
        verbose_name_plural = "movimientos financieros"

    def __str__(self):
        return f"{self.get_tipo_display()} {self.monto} - {self.descripcion}"


class CierreMensualFinanciero(TimeStampedModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        CERRADO = "CERRADO", "Cerrado"
        ANULADO = "ANULADO", "Anulado"

    anio = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    total_ingresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_egresos = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    saldo = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.CERRADO)
    cerrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="cierres_financieros",
    )
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-anio", "-mes", "iglesia__nombre")
        unique_together = ("iglesia", "anio", "mes")
        verbose_name = "cierre mensual financiero"
        verbose_name_plural = "cierres mensuales financieros"

    def __str__(self):
        return f"{self.iglesia} - {self.anio}-{self.mes:02d}"

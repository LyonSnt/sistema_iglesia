from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

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
    fecha_vencimiento = models.DateField(null=True, blank=True)
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
    anulado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="aportes_nacionales_anulados",
    )
    anulado_en = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.TextField(blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-anio", "-mes", "iglesia__nombre")
        unique_together = ("iglesia", "anio", "mes")
        verbose_name = "aporte nacional"
        verbose_name_plural = "aportes nacionales"

    def __str__(self):
        return f"{self.iglesia} - {self.anio}-{self.mes:02d}"

    @property
    def total_pagos(self):
        total = self.pagos.aggregate(total=Sum("monto"))["total"] or Decimal("0.00")
        if total == 0 and self.estado == self.Estado.PAGADO:
            return self.monto_aporte
        return total

    @property
    def total_cargos(self):
        return self.ajustes.filter(tipo=AjusteAporteNacional.Tipo.CARGO).aggregate(total=Sum("monto"))[
            "total"
        ] or Decimal("0.00")

    @property
    def total_abonos(self):
        return self.ajustes.filter(tipo=AjusteAporteNacional.Tipo.ABONO).aggregate(total=Sum("monto"))[
            "total"
        ] or Decimal("0.00")

    @property
    def total_deuda(self):
        return self.monto_aporte + self.total_cargos - self.total_abonos

    @property
    def saldo_pendiente(self):
        saldo = self.total_deuda - self.total_pagos
        if saldo < 0:
            return Decimal("0.00")
        return saldo


class AjusteAporteNacional(TimeStampedModel, IglesiaScopedModel):
    class Tipo(models.TextChoices):
        CARGO = "CARGO", "Cargo"
        ABONO = "ABONO", "Abono"

    aporte = models.ForeignKey(
        AporteNacional,
        on_delete=models.PROTECT,
        related_name="ajustes",
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    motivo = models.TextField()
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="ajustes_aportes_nacionales_registrados",
    )
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "ajuste de aporte nacional"
        verbose_name_plural = "ajustes de aportes nacionales"

    def clean(self):
        super().clean()
        errors = {}
        if self.monto is not None and self.monto <= 0:
            errors["monto"] = "El monto del ajuste debe ser mayor a cero."
        if self.aporte_id:
            if self.iglesia_id and self.aporte.iglesia_id != self.iglesia_id:
                errors["iglesia"] = "El ajuste debe pertenecer a la misma iglesia del aporte."
            if self.aporte.estado != AporteNacional.Estado.PAGADO:
                errors["aporte"] = "Solo se pueden ajustar aportes pagados con recibo."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.get_tipo_display()} {self.monto} - {self.aporte}"


class PagoAporteNacional(TimeStampedModel, IglesiaScopedModel):
    aporte = models.ForeignKey(
        AporteNacional,
        on_delete=models.PROTECT,
        related_name="pagos",
    )
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    fecha_pago = models.DateField()
    referencia_pago = models.CharField(max_length=120)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="pagos_aportes_nacionales_detallados",
    )
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("fecha_pago", "creado_en")
        verbose_name = "pago de aporte nacional"
        verbose_name_plural = "pagos de aportes nacionales"

    def clean(self):
        super().clean()
        errors = {}
        if self.monto is not None and self.monto <= 0:
            errors["monto"] = "El monto del pago debe ser mayor a cero."
        if self.aporte_id:
            if self.iglesia_id and self.aporte.iglesia_id != self.iglesia_id:
                errors["iglesia"] = "El pago debe pertenecer a la misma iglesia del aporte."
            if self.aporte.estado == AporteNacional.Estado.ANULADO:
                errors["aporte"] = "No se pueden registrar pagos sobre aportes anulados."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Pago {self.monto} - {self.aporte}"


class AcuerdoPagoAporteNacional(TimeStampedModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        VIGENTE = "VIGENTE", "Vigente"
        CUMPLIDO = "CUMPLIDO", "Cumplido"
        ANULADO = "ANULADO", "Anulado"

    aporte = models.ForeignKey(
        AporteNacional,
        on_delete=models.PROTECT,
        related_name="acuerdos",
    )
    fecha_compromiso = models.DateField()
    monto_comprometido = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.VIGENTE)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="acuerdos_aportes_nacionales_registrados",
    )
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("fecha_compromiso",)
        verbose_name = "acuerdo de pago de aporte nacional"
        verbose_name_plural = "acuerdos de pago de aportes nacionales"

    def clean(self):
        super().clean()
        errors = {}
        if self.monto_comprometido is not None and self.monto_comprometido <= 0:
            errors["monto_comprometido"] = "El monto comprometido debe ser mayor a cero."
        if self.aporte_id:
            if self.iglesia_id and self.aporte.iglesia_id != self.iglesia_id:
                errors["iglesia"] = "El acuerdo debe pertenecer a la misma iglesia del aporte."
            if self.aporte.estado != AporteNacional.Estado.PENDIENTE:
                errors["aporte"] = "Solo se pueden acordar pagos de aportes pendientes."
            acuerdo_vigente = AcuerdoPagoAporteNacional.objects.filter(
                aporte=self.aporte,
                estado=self.Estado.VIGENTE,
            ).exclude(pk=self.pk)
            if self.estado == self.Estado.VIGENTE and acuerdo_vigente.exists():
                errors["aporte"] = "El aporte ya tiene un acuerdo de pago vigente."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Acuerdo {self.monto_comprometido} - {self.aporte}"

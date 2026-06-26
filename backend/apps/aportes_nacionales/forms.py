from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone

from apps.finanzas.models import CierreMensualFinanciero
from apps.parametros.models import ParametroGeneral

from .models import AcuerdoPagoAporteNacional, AjusteAporteNacional, AporteNacional


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class AporteNacionalForm(forms.ModelForm):
    class Meta:
        model = AporteNacional
        fields = ("cierre", "porcentaje", "fecha_vencimiento", "observacion")
        widgets = {
            "fecha_vencimiento": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["porcentaje"].initial = obtener_porcentaje_default()
        self.fields["cierre"].queryset = (
            CierreMensualFinanciero.objects.filter(estado=CierreMensualFinanciero.Estado.CERRADO)
            .filter(Q(aporte_nacional__isnull=True) | Q(aporte_nacional__estado=AporteNacional.Estado.ANULADO))
            .select_related("iglesia")
            .order_by("-anio", "-mes", "iglesia__nombre")
        )
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean_porcentaje(self):
        porcentaje = self.cleaned_data["porcentaje"]
        if porcentaje <= 0:
            raise ValidationError("El porcentaje debe ser mayor a cero.")
        if porcentaje > 100:
            raise ValidationError("El porcentaje no puede ser mayor a 100.")
        return porcentaje

    def validate_unique(self):
        return None

    def save(self, commit=True):
        cierre = self.cleaned_data["cierre"]
        porcentaje = self.cleaned_data["porcentaje"]
        aporte_existente = AporteNacional.objects.filter(
            cierre=cierre,
            estado=AporteNacional.Estado.ANULADO,
        ).first()
        if aporte_existente is not None:
            instance = aporte_existente
            instance.observacion = self.cleaned_data.get("observacion", "")
        else:
            instance = super().save(commit=False)
        instance.iglesia = cierre.iglesia
        instance.cierre = cierre
        instance.anio = cierre.anio
        instance.mes = cierre.mes
        instance.porcentaje = porcentaje
        instance.monto_base = cierre.total_ingresos
        instance.monto_aporte = calcular_aporte(cierre.total_ingresos, porcentaje)
        instance.fecha_vencimiento = self.cleaned_data.get("fecha_vencimiento")
        instance.estado = AporteNacional.Estado.PENDIENTE
        instance.fecha_pago = None
        instance.referencia_pago = ""
        instance.numero_recibo = None
        instance.registrado_pago_por = None
        instance.anulado_por = None
        instance.anulado_en = None
        instance.motivo_anulacion = ""
        if commit:
            instance.save()
            self.save_m2m()
        return instance


def obtener_porcentaje_default():
    parametro = ParametroGeneral.objects.filter(clave="APORTE_NACIONAL_PORCENTAJE", activo=True).first()
    if parametro is None:
        return Decimal("10.00")
    try:
        return Decimal(parametro.valor)
    except Exception:
        return Decimal("10.00")


def calcular_aporte(monto_base, porcentaje):
    return (monto_base * porcentaje / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class RegistrarPagoAporteForm(forms.Form):
    fecha_pago = forms.DateField(
        label="Fecha de pago",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    monto = forms.DecimalField(
        label="Monto",
        required=False,
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": FIELD_CLASS, "step": "0.01", "min": "0.01"}),
    )
    referencia_pago = forms.CharField(
        label="Referencia",
        max_length=120,
        widget=forms.TextInput(attrs={"class": FIELD_CLASS}),
    )
    observacion = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )

    def __init__(self, *args, aporte=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.aporte = aporte

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if monto is None:
            return monto
        if monto <= 0:
            raise ValidationError("El monto del pago debe ser mayor a cero.")
        if self.aporte is not None and monto > self.aporte.saldo_pendiente:
            raise ValidationError("El monto del pago no puede superar el saldo pendiente.")
        return monto


class AnularAporteNacionalForm(forms.Form):
    motivo_anulacion = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )


class AjusteAporteNacionalForm(forms.ModelForm):
    class Meta:
        model = AjusteAporteNacional
        fields = ("tipo", "monto", "motivo", "observacion")
        widgets = {
            "motivo": forms.Textarea(attrs={"rows": 4}),
            "observacion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto <= 0:
            raise ValidationError("El monto del ajuste debe ser mayor a cero.")
        return monto


class AcuerdoPagoAporteNacionalForm(forms.ModelForm):
    class Meta:
        model = AcuerdoPagoAporteNacional
        fields = ("fecha_compromiso", "monto_comprometido", "observacion")
        widgets = {
            "fecha_compromiso": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, aporte=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.aporte = aporte
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean_monto_comprometido(self):
        monto = self.cleaned_data["monto_comprometido"]
        if monto <= 0:
            raise ValidationError("El monto comprometido debe ser mayor a cero.")
        return monto

    def clean(self):
        cleaned_data = super().clean()
        if (
            self.aporte is not None
            and AcuerdoPagoAporteNacional.objects.filter(
                aporte=self.aporte,
                estado=AcuerdoPagoAporteNacional.Estado.VIGENTE,
            ).exists()
        ):
            raise ValidationError("El aporte ya tiene un acuerdo de pago vigente.")
        return cleaned_data

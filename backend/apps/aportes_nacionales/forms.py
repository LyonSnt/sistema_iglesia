from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.finanzas.models import CierreMensualFinanciero
from apps.parametros.models import ParametroGeneral

from .models import AporteNacional


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class AporteNacionalForm(forms.ModelForm):
    class Meta:
        model = AporteNacional
        fields = ("cierre", "porcentaje", "observacion")
        widgets = {"observacion": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["porcentaje"].initial = obtener_porcentaje_default()
        self.fields["cierre"].queryset = (
            CierreMensualFinanciero.objects.filter(estado=CierreMensualFinanciero.Estado.CERRADO)
            .exclude(aporte_nacional__isnull=False)
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

    def save(self, commit=True):
        instance = super().save(commit=False)
        cierre = self.cleaned_data["cierre"]
        porcentaje = self.cleaned_data["porcentaje"]
        instance.iglesia = cierre.iglesia
        instance.anio = cierre.anio
        instance.mes = cierre.mes
        instance.monto_base = cierre.total_ingresos
        instance.monto_aporte = calcular_aporte(cierre.total_ingresos, porcentaje)
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

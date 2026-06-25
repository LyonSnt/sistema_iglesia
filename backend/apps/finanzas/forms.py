from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia

from .models import CierreMensualFinanciero, ConceptoFinanciero, MovimientoFinanciero


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class ConceptoFinancieroForm(forms.ModelForm):
    class Meta:
        model = ConceptoFinanciero
        fields = ("iglesia", "nombre", "tipo", "descripcion", "activo")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        iglesias = Iglesia.objects.filter(activo=True, tipo=Iglesia.Tipo.FILIAL).order_by("nombre")
        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        self.fields["iglesia"].queryset = iglesias
        aplicar_estilos(self.fields.values())

    def clean(self):
        cleaned_data = super().clean()
        if self.user is not None and not usuario_es_nacional(self.user):
            cleaned_data["iglesia"] = self.user.iglesia
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class MovimientoFinancieroForm(forms.ModelForm):
    class Meta:
        model = MovimientoFinanciero
        fields = ("iglesia", "concepto", "tipo", "fecha", "monto", "descripcion", "numero_comprobante")
        widgets = {"fecha": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if not self.initial.get("fecha") and not self.instance.pk:
            self.initial["fecha"] = timezone.localdate()

        iglesias = Iglesia.objects.filter(activo=True, tipo=Iglesia.Tipo.FILIAL).order_by("nombre")
        conceptos = ConceptoFinanciero.objects.filter(activo=True).select_related("iglesia").order_by("tipo", "nombre")

        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            conceptos = conceptos.filter(iglesia=user.iglesia)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True

        self.fields["iglesia"].queryset = iglesias
        self.fields["concepto"].queryset = conceptos
        aplicar_estilos(self.fields.values())

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto <= 0:
            raise ValidationError("El monto debe ser mayor a cero.")
        return monto

    def clean(self):
        cleaned_data = super().clean()
        iglesia = cleaned_data.get("iglesia")
        concepto = cleaned_data.get("concepto")
        tipo = cleaned_data.get("tipo")

        if self.user is not None and not usuario_es_nacional(self.user):
            iglesia = self.user.iglesia
            cleaned_data["iglesia"] = iglesia

        if iglesia is not None and concepto is not None and concepto.iglesia_id != iglesia.id:
            raise ValidationError("El concepto debe pertenecer a la misma iglesia.")
        if concepto is not None and tipo and concepto.tipo != tipo:
            raise ValidationError("El tipo del movimiento debe coincidir con el tipo del concepto.")
        fecha = cleaned_data.get("fecha")
        if iglesia is not None and fecha is not None and mes_esta_cerrado(iglesia, fecha.year, fecha.month):
            raise ValidationError("No se pueden registrar movimientos en un mes cerrado.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if self.user is not None and not instance.registrado_por_id:
            instance.registrado_por = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class AnularMovimientoForm(forms.Form):
    fecha_anulacion = forms.DateField(
        label="Fecha de anulacion",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    motivo_anulacion = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )


class AnularCierreMensualForm(forms.Form):
    motivo_anulacion = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )


class CierreMensualFinancieroForm(forms.ModelForm):
    class Meta:
        model = CierreMensualFinanciero
        fields = ("iglesia", "anio", "mes", "observacion")
        widgets = {"observacion": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        anio_actual = timezone.localdate().year
        self.fields["anio"].initial = anio_actual
        self.fields["mes"].widget = forms.Select(choices=[(numero, f"{numero:02d}") for numero in range(1, 13)])
        iglesias = Iglesia.objects.filter(activo=True, tipo=Iglesia.Tipo.FILIAL).order_by("nombre")
        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        self.fields["iglesia"].queryset = iglesias
        aplicar_estilos(self.fields.values())

    def clean_anio(self):
        anio = self.cleaned_data["anio"]
        if anio < 2000 or anio > 2100:
            raise ValidationError("El anio debe estar entre 2000 y 2100.")
        return anio

    def clean_mes(self):
        mes = self.cleaned_data["mes"]
        if mes < 1 or mes > 12:
            raise ValidationError("El mes debe estar entre 1 y 12.")
        return mes

    def clean(self):
        cleaned_data = super().clean()
        iglesia = cleaned_data.get("iglesia")
        anio = cleaned_data.get("anio")
        mes = cleaned_data.get("mes")
        if self.user is not None and not usuario_es_nacional(self.user):
            iglesia = self.user.iglesia
            cleaned_data["iglesia"] = iglesia
        if iglesia is not None and anio is not None and mes is not None and mes_esta_cerrado(iglesia, anio, mes):
            raise ValidationError("Ya existe un cierre para este mes.")
        return cleaned_data


def aplicar_estilos(fields):
    for field in fields:
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300 text-slate-950")
        elif not isinstance(field.widget, forms.HiddenInput):
            field.widget.attrs.setdefault("class", FIELD_CLASS)


def mes_esta_cerrado(iglesia, anio, mes):
    return CierreMensualFinanciero.objects.filter(
        iglesia=iglesia,
        anio=anio,
        mes=mes,
        estado=CierreMensualFinanciero.Estado.CERRADO,
    ).exists()

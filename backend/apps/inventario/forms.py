from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario

from .models import ActivoInventario, MovimientoInventario


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class ActivoInventarioForm(forms.ModelForm):
    class Meta:
        model = ActivoInventario
        fields = (
            "iglesia",
            "codigo",
            "nombre",
            "categoria",
            "descripcion",
            "ubicacion_actual",
            "responsable_actual",
            "estado",
            "fecha_adquisicion",
            "valor_referencial",
            "activo",
        )
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "fecha_adquisicion": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        iglesias = Iglesia.objects.filter(activo=True, tipo=Iglesia.Tipo.FILIAL).order_by("nombre")
        responsables = Usuario.objects.filter(is_active=True).select_related("iglesia").order_by("iglesia__nombre", "username")
        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            responsables = responsables.filter(iglesia=user.iglesia)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        elif self.instance.pk and self.instance.iglesia_id:
            responsables = responsables.filter(iglesia=self.instance.iglesia)
        self.fields["iglesia"].queryset = iglesias
        self.fields["responsable_actual"].queryset = responsables
        aplicar_estilos(self.fields.values())

    def clean(self):
        cleaned_data = super().clean()
        iglesia = cleaned_data.get("iglesia")
        responsable = cleaned_data.get("responsable_actual")
        if self.user is not None and not usuario_es_nacional(self.user):
            iglesia = self.user.iglesia
            cleaned_data["iglesia"] = iglesia
        if iglesia is not None and responsable is not None and responsable.iglesia_id != iglesia.id:
            raise ValidationError("El responsable debe pertenecer a la misma iglesia.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if commit:
            instance.full_clean()
            instance.save()
            self.save_m2m()
        return instance


class MovimientoInventarioForm(forms.Form):
    tipo = forms.ChoiceField(label="Tipo de movimiento", choices=MovimientoInventario.Tipo.choices)
    fecha = forms.DateField(
        label="Fecha",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    ubicacion_nueva = forms.CharField(label="Nueva ubicacion", max_length=160, required=False)
    responsable_nuevo = forms.ModelChoiceField(
        label="Nuevo responsable",
        queryset=Usuario.objects.none(),
        required=False,
    )
    detalle = forms.CharField(label="Detalle", widget=forms.Textarea(attrs={"rows": 4}))

    def __init__(self, *args, activo=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.activo = activo
        self.user = user
        responsables = Usuario.objects.filter(is_active=True).select_related("iglesia").order_by("username")
        if activo is not None:
            responsables = responsables.filter(iglesia=activo.iglesia)
        self.fields["responsable_nuevo"].queryset = responsables
        aplicar_estilos(self.fields.values())

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        ubicacion_nueva = cleaned_data.get("ubicacion_nueva")
        responsable_nuevo = cleaned_data.get("responsable_nuevo")
        if tipo == MovimientoInventario.Tipo.UBICACION and not ubicacion_nueva:
            raise ValidationError("Debe indicar la nueva ubicacion.")
        if tipo == MovimientoInventario.Tipo.RESPONSABLE and responsable_nuevo is None:
            raise ValidationError("Debe seleccionar el nuevo responsable.")
        if tipo == MovimientoInventario.Tipo.REPARACION and not ubicacion_nueva:
            cleaned_data["ubicacion_nueva"] = self.activo.ubicacion_actual
        if responsable_nuevo is not None and responsable_nuevo.iglesia_id != self.activo.iglesia_id:
            raise ValidationError("El responsable debe pertenecer a la misma iglesia.")
        return cleaned_data

    def save(self):
        tipo = self.cleaned_data["tipo"]
        movimiento = MovimientoInventario(
            iglesia=self.activo.iglesia,
            activo=self.activo,
            tipo=tipo,
            fecha=self.cleaned_data["fecha"],
            ubicacion_anterior=self.activo.ubicacion_actual,
            ubicacion_nueva=self.cleaned_data.get("ubicacion_nueva") or self.activo.ubicacion_actual,
            responsable_anterior=self.activo.responsable_actual,
            responsable_nuevo=self.cleaned_data.get("responsable_nuevo") or self.activo.responsable_actual,
            detalle=self.cleaned_data["detalle"],
            registrado_por=self.user,
        )
        movimiento.full_clean()
        movimiento.save()
        if tipo in {MovimientoInventario.Tipo.UBICACION, MovimientoInventario.Tipo.REPARACION}:
            self.activo.ubicacion_actual = movimiento.ubicacion_nueva
        if tipo == MovimientoInventario.Tipo.RESPONSABLE:
            self.activo.responsable_actual = movimiento.responsable_nuevo
            self.activo.estado = ActivoInventario.Estado.ASIGNADO
        if tipo == MovimientoInventario.Tipo.REPARACION:
            self.activo.estado = ActivoInventario.Estado.EN_REPARACION
        self.activo.save(update_fields=["ubicacion_actual", "responsable_actual", "estado", "actualizado_en"])
        return movimiento


class BajaInventarioForm(forms.Form):
    fecha = forms.DateField(
        label="Fecha de baja",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    motivo = forms.CharField(label="Motivo", widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}))


def aplicar_estilos(fields):
    for field in fields:
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300 text-slate-950")
        elif not isinstance(field.widget, forms.HiddenInput):
            field.widget.attrs.setdefault("class", FIELD_CLASS)

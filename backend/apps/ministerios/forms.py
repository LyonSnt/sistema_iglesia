from django import forms
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro

from .models import Ministerio, ParticipacionMinisterio


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class MinisterioForm(forms.ModelForm):
    class Meta:
        model = Ministerio
        fields = ("iglesia", "nombre", "tipo", "descripcion", "responsable", "activo")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        iglesias = Iglesia.objects.filter(activo=True).order_by("nombre")
        miembros = Miembro.objects.filter(activo=True).select_related("iglesia").order_by("apellidos", "nombres")

        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            miembros = miembros.filter(iglesia=user.iglesia)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        elif self.instance and self.instance.pk and self.instance.iglesia_id:
            miembros = miembros.filter(iglesia=self.instance.iglesia)

        self.fields["iglesia"].queryset = iglesias
        self.fields["responsable"].queryset = miembros

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300 text-slate-950")
            elif not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        iglesia = cleaned_data.get("iglesia")
        responsable = cleaned_data.get("responsable")

        if self.user is not None and not usuario_es_nacional(self.user):
            iglesia = self.user.iglesia
            cleaned_data["iglesia"] = iglesia

        if iglesia is not None and responsable is not None and responsable.iglesia_id != iglesia.id:
            raise ValidationError("El responsable debe pertenecer a la misma iglesia del ministerio.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ParticipacionMinisterioForm(forms.ModelForm):
    class Meta:
        model = ParticipacionMinisterio
        fields = ("miembro", "cargo", "fecha_inicio", "fecha_fin", "estado", "motivo_salida", "activo")
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
            "motivo_salida": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, ministerio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ministerio = ministerio
        if ministerio is not None:
            self.fields["miembro"].queryset = Miembro.objects.filter(
                iglesia=ministerio.iglesia,
                activo=True,
            ).order_by("apellidos", "nombres")

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300 text-slate-950")
            else:
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        miembro = cleaned_data.get("miembro")
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")

        if self.ministerio is not None and miembro is not None and miembro.iglesia_id != self.ministerio.iglesia_id:
            raise ValidationError("El miembro debe pertenecer a la misma iglesia del ministerio.")
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")

        return cleaned_data


class FinalizarParticipacionMinisterioForm(forms.Form):
    fecha_fin = forms.DateField(
        label="Fecha de fin",
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    motivo_salida = forms.CharField(
        label="Motivo de salida",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )

    def __init__(self, *args, participacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.participacion = participacion

    def clean_fecha_fin(self):
        fecha_fin = self.cleaned_data["fecha_fin"]
        if self.participacion is not None and fecha_fin < self.participacion.fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")
        return fecha_fin

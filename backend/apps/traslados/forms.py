from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro

from .models import Traslado


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class TrasladoForm(forms.ModelForm):
    class Meta:
        model = Traslado
        fields = ("iglesia", "miembro", "iglesia_destino", "fecha_solicitud", "motivo")
        widgets = {
            "fecha_solicitud": forms.DateInput(attrs={"type": "date"}),
            "motivo": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if not self.initial.get("fecha_solicitud") and not self.instance.pk:
            self.initial["fecha_solicitud"] = timezone.localdate()

        iglesias = Iglesia.objects.filter(activo=True, tipo=Iglesia.Tipo.FILIAL).order_by("nombre")
        miembros = Miembro.objects.filter(activo=True).select_related("iglesia").order_by("apellidos", "nombres")

        if user is not None and not usuario_es_nacional(user):
            iglesias_origen = iglesias.filter(pk=user.iglesia_id)
            miembros = miembros.filter(iglesia=user.iglesia).exclude(estado=Miembro.Estado.FALLECIDO)
            iglesias_destino = iglesias.exclude(pk=user.iglesia_id)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        else:
            iglesias_origen = iglesias
            iglesias_destino = iglesias

        self.fields["iglesia"].queryset = iglesias_origen
        self.fields["miembro"].queryset = miembros
        self.fields["iglesia_destino"].queryset = iglesias_destino

        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        iglesia = cleaned_data.get("iglesia")
        miembro = cleaned_data.get("miembro")
        iglesia_destino = cleaned_data.get("iglesia_destino")

        if self.user is not None and not usuario_es_nacional(self.user):
            iglesia = self.user.iglesia
            cleaned_data["iglesia"] = iglesia

        if iglesia is not None and iglesia.tipo != Iglesia.Tipo.FILIAL:
            raise ValidationError("La iglesia origen debe ser una filial.")
        if iglesia_destino is not None and iglesia_destino.tipo != Iglesia.Tipo.FILIAL:
            raise ValidationError("La iglesia destino debe ser una filial.")
        if iglesia is not None and iglesia_destino is not None and iglesia.id == iglesia_destino.id:
            raise ValidationError("La iglesia destino debe ser diferente a la iglesia origen.")
        if iglesia is not None and miembro is not None and miembro.iglesia_id != iglesia.id:
            raise ValidationError("El miembro debe pertenecer a la iglesia origen.")
        if miembro is not None and miembro.estado == Miembro.Estado.FALLECIDO:
            raise ValidationError("No se puede trasladar un miembro fallecido.")
        if miembro is not None:
            existe_pendiente = Traslado.objects.filter(miembro=miembro, estado=Traslado.Estado.SOLICITADO)
            if self.instance.pk:
                existe_pendiente = existe_pendiente.exclude(pk=self.instance.pk)
            if existe_pendiente.exists():
                raise ValidationError("El miembro ya tiene un traslado solicitado.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if self.user is not None and not instance.solicitado_por_id:
            instance.solicitado_por = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ResponderTrasladoForm(forms.Form):
    fecha_respuesta = forms.DateField(
        label="Fecha de respuesta",
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    observacion_respuesta = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )

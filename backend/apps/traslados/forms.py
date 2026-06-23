from django import forms
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro

from .models import TrasladoMiembro


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class TrasladoMiembroForm(forms.ModelForm):
    class Meta:
        model = TrasladoMiembro
        fields = ("miembro", "iglesia_destino", "motivo")
        widgets = {
            "motivo": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        miembros = Miembro.objects.filter(activo=True, estado=Miembro.Estado.ACTIVO).select_related("iglesia")
        iglesias_destino = Iglesia.objects.filter(activo=True, estado=Iglesia.Estado.ACTIVA, tipo=Iglesia.Tipo.FILIAL)

        if user is not None and not usuario_es_nacional(user):
            miembros = miembros.filter(iglesia=user.iglesia)
            iglesias_destino = iglesias_destino.exclude(pk=user.iglesia_id)

        self.fields["miembro"].queryset = miembros.order_by("apellidos", "nombres")
        self.fields["iglesia_destino"].queryset = iglesias_destino.order_by("nombre")

        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        miembro = cleaned_data.get("miembro")
        iglesia_destino = cleaned_data.get("iglesia_destino")

        if self.user is not None and not usuario_es_nacional(self.user):
            if miembro is not None and miembro.iglesia_id != self.user.iglesia_id:
                raise ValidationError("Solo puede solicitar traslados de miembros de su iglesia.")

        if miembro is not None and iglesia_destino is not None:
            if miembro.iglesia_id == iglesia_destino.id:
                raise ValidationError("La iglesia destino debe ser distinta de la iglesia origen.")
            existe_pendiente = TrasladoMiembro.objects.filter(
                miembro=miembro,
                estado=TrasladoMiembro.Estado.SOLICITADO,
            ).exists()
            if existe_pendiente:
                raise ValidationError("El miembro ya tiene un traslado pendiente.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.miembro_id:
            instance.iglesia_origen = instance.miembro.iglesia
        if self.user is not None:
            instance.solicitado_por = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class ResponderTrasladoForm(forms.Form):
    observacion = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )

    def __init__(self, *args, traslado=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.traslado = traslado

    def clean(self):
        cleaned_data = super().clean()
        if self.traslado is not None and not self.traslado.pendiente:
            raise ValidationError("Solo se pueden responder traslados pendientes.")
        return cleaned_data

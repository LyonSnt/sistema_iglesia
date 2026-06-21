from django import forms
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro

from .models import Familia, MiembroFamilia


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class FamiliaForm(forms.ModelForm):
    class Meta:
        model = Familia
        fields = ("iglesia", "nombre", "jefe_hogar", "direccion", "telefono", "activo")

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
        self.fields["jefe_hogar"].queryset = miembros

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300 text-slate-950")
            elif not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        iglesia = cleaned_data.get("iglesia")
        jefe_hogar = cleaned_data.get("jefe_hogar")

        if self.user is not None and not usuario_es_nacional(self.user):
            iglesia = self.user.iglesia
            cleaned_data["iglesia"] = iglesia

        if iglesia is not None and jefe_hogar is not None and jefe_hogar.iglesia_id != iglesia.id:
            raise ValidationError("El jefe de hogar debe pertenecer a la misma iglesia de la familia.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if commit:
            instance.save()
            relacion, _ = MiembroFamilia.objects.get_or_create(
                familia=instance,
                miembro=instance.jefe_hogar,
                relacion=MiembroFamilia.Relacion.REPRESENTANTE,
            )
            if not relacion.activo:
                relacion.activo = True
                relacion.save(update_fields=["activo"])
            self.save_m2m()
        return instance


class AgregarIntegranteFamiliaForm(forms.Form):
    miembro = forms.ModelChoiceField(
        label="Miembro",
        queryset=Miembro.objects.none(),
        widget=forms.Select(attrs={"class": FIELD_CLASS}),
    )
    relacion = forms.ChoiceField(
        label="Relacion",
        choices=MiembroFamilia.Relacion.choices,
        widget=forms.Select(attrs={"class": FIELD_CLASS}),
    )

    def __init__(self, *args, familia=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.familia = familia
        if familia is not None:
            self.fields["miembro"].queryset = Miembro.objects.filter(
                iglesia=familia.iglesia,
                activo=True,
            ).order_by("apellidos", "nombres")

    def clean(self):
        cleaned_data = super().clean()
        miembro = cleaned_data.get("miembro")
        relacion = cleaned_data.get("relacion")

        if self.familia is not None and miembro is not None and miembro.iglesia_id != self.familia.iglesia_id:
            raise ValidationError("El miembro debe pertenecer a la misma iglesia de la familia.")

        if self.familia is not None and miembro is not None and relacion:
            existe = MiembroFamilia.objects.filter(
                familia=self.familia,
                miembro=miembro,
                relacion=relacion,
                activo=True,
            ).exists()
            if existe:
                raise ValidationError("El integrante ya tiene esa relacion en esta familia.")

        return cleaned_data

from django import forms
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.familias.models import Familia, Matrimonio, MiembroFamilia
from apps.iglesias.models import Iglesia

from .models import Miembro


class MiembroForm(forms.ModelForm):
    class Meta:
        model = Miembro
        fields = (
            "iglesia",
            "nombres",
            "apellidos",
            "cedula",
            "fecha_nacimiento",
            "sexo",
            "estado_civil",
            "telefono",
            "direccion",
            "fecha_conversion",
            "fecha_bautismo",
            "fecha_membresia",
            "estado",
            "fecha_fallecimiento",
            "observacion",
            "activo",
        )
        widgets = {
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date"}),
            "fecha_conversion": forms.DateInput(attrs={"type": "date"}),
            "fecha_bautismo": forms.DateInput(attrs={"type": "date"}),
            "fecha_membresia": forms.DateInput(attrs={"type": "date"}),
            "fecha_fallecimiento": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["iglesia"].queryset = Iglesia.objects.filter(activo=True).order_by("nombre")

        if user is not None and not usuario_es_nacional(user):
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300 text-slate-950")
                continue
            if isinstance(field.widget, forms.HiddenInput):
                continue
            field.widget.attrs.setdefault(
                "class",
                "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class FechaPastoralForm(forms.Form):
    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )


class BautismoForm(FechaPastoralForm):
    fecha = forms.DateField(
        label="Fecha de bautismo",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )


class MembresiaForm(FechaPastoralForm):
    fecha = forms.DateField(
        label="Fecha de membresia",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )


class FallecimientoForm(FechaPastoralForm):
    fecha = forms.DateField(
        label="Fecha de fallecimiento",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )


class MatrimonioForm(forms.Form):
    conyuge = forms.ModelChoiceField(
        label="Conyuge",
        queryset=Miembro.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )
    fecha_matrimonio = forms.DateField(
        label="Fecha de matrimonio",
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )
    familia = forms.ModelChoiceField(
        label="Familia",
        queryset=Familia.objects.none(),
        required=False,
        help_text="Opcional. Si se selecciona, ambos quedaran vinculados como conyuges.",
        widget=forms.Select(
            attrs={
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )
    observacion = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )

    def __init__(self, *args, miembro=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.miembro = miembro
        if miembro is not None:
            self.fields["conyuge"].queryset = Miembro.objects.filter(
                iglesia=miembro.iglesia,
                activo=True,
            ).exclude(pk=miembro.pk).order_by("apellidos", "nombres")
            self.fields["familia"].queryset = Familia.objects.filter(
                iglesia=miembro.iglesia,
                activo=True,
            ).order_by("nombre")

    def clean(self):
        cleaned_data = super().clean()
        conyuge = cleaned_data.get("conyuge")
        familia = cleaned_data.get("familia")

        if self.miembro is not None and conyuge is not None and conyuge.iglesia_id != self.miembro.iglesia_id:
            raise ValidationError("El conyuge debe pertenecer a la misma iglesia.")

        if self.miembro is not None and familia is not None and familia.iglesia_id != self.miembro.iglesia_id:
            raise ValidationError("La familia debe pertenecer a la misma iglesia.")

        if self.miembro is not None and conyuge is not None:
            existe = Matrimonio.objects.filter(
                activo=True,
                conyuge_1=self.miembro,
                conyuge_2=conyuge,
            ).exists() or Matrimonio.objects.filter(
                activo=True,
                conyuge_1=conyuge,
                conyuge_2=self.miembro,
            ).exists()
            if existe:
                raise ValidationError("Ya existe un matrimonio activo entre estos miembros.")

        return cleaned_data


class CrearFamiliaMiembroForm(forms.Form):
    nombre = forms.CharField(
        label="Nombre de la familia",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )
    relacion = forms.ChoiceField(
        label="Relacion del miembro",
        choices=MiembroFamilia.Relacion.choices,
        initial=MiembroFamilia.Relacion.REPRESENTANTE,
        widget=forms.Select(
            attrs={
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )
    direccion = forms.CharField(
        label="Direccion",
        max_length=255,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )
    telefono = forms.CharField(
        label="Telefono",
        max_length=30,
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )


class VincularFamiliaMiembroForm(forms.Form):
    familia = forms.ModelChoiceField(
        label="Familia",
        queryset=Familia.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )
    relacion = forms.ChoiceField(
        label="Relacion",
        choices=MiembroFamilia.Relacion.choices,
        widget=forms.Select(
            attrs={
                "class": "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200",
            }
        ),
    )

    def __init__(self, *args, miembro=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.miembro = miembro
        if miembro is not None:
            self.fields["familia"].queryset = Familia.objects.filter(
                iglesia=miembro.iglesia,
                activo=True,
            ).order_by("nombre")

    def clean(self):
        cleaned_data = super().clean()
        familia = cleaned_data.get("familia")
        relacion = cleaned_data.get("relacion")

        if self.miembro is not None and familia is not None and familia.iglesia_id != self.miembro.iglesia_id:
            raise ValidationError("La familia debe pertenecer a la misma iglesia del miembro.")

        if self.miembro is not None and familia is not None and relacion:
            existe = MiembroFamilia.objects.filter(
                familia=familia,
                miembro=self.miembro,
                relacion=relacion,
            ).exists()
            if existe:
                raise ValidationError("El miembro ya tiene esa relacion en la familia seleccionada.")

        return cleaned_data

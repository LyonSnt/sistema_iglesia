from django import forms
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.usuarios.models import Usuario

from .models import AsignacionCargo, Cargo


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class AsignacionCargoForm(forms.ModelForm):
    class Meta:
        model = AsignacionCargo
        fields = (
            "iglesia",
            "cargo",
            "miembro",
            "usuario",
            "tipo_asignacion",
            "fecha_inicio",
            "fecha_fin",
            "estado",
            "observacion",
            "activo",
        )
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        iglesias = Iglesia.objects.filter(activo=True).order_by("nombre")
        cargos = Cargo.objects.filter(activo=True).order_by("nombre")
        miembros = Miembro.objects.filter(activo=True).select_related("iglesia").order_by("apellidos", "nombres")
        usuarios = Usuario.objects.filter(is_active=True).select_related("iglesia").order_by("username")

        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            cargos = cargos.filter(es_nacional=False)
            miembros = miembros.filter(iglesia=user.iglesia)
            usuarios = usuarios.filter(iglesia=user.iglesia)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        elif self.instance and self.instance.pk and self.instance.iglesia_id:
            miembros = miembros.filter(iglesia=self.instance.iglesia)
            usuarios = usuarios.filter(iglesia=self.instance.iglesia)

        self.fields["iglesia"].queryset = iglesias
        self.fields["cargo"].queryset = cargos
        self.fields["miembro"].queryset = miembros
        self.fields["usuario"].queryset = usuarios

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300 text-slate-950")
            elif not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        iglesia = cleaned_data.get("iglesia")
        cargo = cleaned_data.get("cargo")
        miembro = cleaned_data.get("miembro")
        usuario = cleaned_data.get("usuario")
        fecha_inicio = cleaned_data.get("fecha_inicio")
        fecha_fin = cleaned_data.get("fecha_fin")
        estado = cleaned_data.get("estado")

        if self.user is not None and not usuario_es_nacional(self.user):
            iglesia = self.user.iglesia
            cleaned_data["iglesia"] = iglesia

        if miembro is None and usuario is None:
            raise ValidationError("Debe seleccionar un miembro o un usuario.")
        if miembro is not None and usuario is not None:
            raise ValidationError("Seleccione solo un miembro o solo un usuario.")

        if iglesia is not None and miembro is not None and miembro.iglesia_id != iglesia.id:
            raise ValidationError("El miembro debe pertenecer a la misma iglesia de la asignacion.")
        if iglesia is not None and usuario is not None and usuario.iglesia_id != iglesia.id:
            raise ValidationError("El usuario debe pertenecer a la misma iglesia de la asignacion.")
        if self.user is not None and not usuario_es_nacional(self.user) and cargo is not None and cargo.es_nacional:
            raise ValidationError("Una filial no puede asignar cargos nacionales.")
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")
        if iglesia and cargo and cargo.es_sensible and estado in {
            AsignacionCargo.Estado.NOMBRADO,
            AsignacionCargo.Estado.VIGENTE,
        }:
            solapada = AsignacionCargo.objects.filter(
                iglesia=iglesia,
                cargo=cargo,
                estado__in=[AsignacionCargo.Estado.NOMBRADO, AsignacionCargo.Estado.VIGENTE],
            )
            if self.instance.pk:
                solapada = solapada.exclude(pk=self.instance.pk)
            if fecha_inicio:
                solapada = solapada.filter(fecha_fin__isnull=True) | solapada.filter(fecha_fin__gte=fecha_inicio)
            if solapada.exists():
                raise ValidationError("Ya existe una asignacion sensible nombrada o vigente para ese cargo.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class FinalizarAsignacionCargoForm(forms.Form):
    fecha_fin = forms.DateField(
        label="Fecha de fin",
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    observacion = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )

    def __init__(self, *args, asignacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.asignacion = asignacion

    def clean_fecha_fin(self):
        fecha_fin = self.cleaned_data["fecha_fin"]
        if self.asignacion is not None and fecha_fin < self.asignacion.fecha_inicio:
            raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")
        return fecha_fin


class AccionFormalCargoForm(forms.Form):
    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    motivo = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )

    def __init__(self, *args, asignacion=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.asignacion = asignacion

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if self.asignacion is not None and fecha < self.asignacion.fecha_inicio:
            raise ValidationError("La fecha no puede ser anterior a la fecha de inicio.")
        return fecha


class ReemplazarAsignacionCargoForm(AccionFormalCargoForm):
    nueva_asignacion = forms.ModelChoiceField(
        label="Nueva asignacion",
        queryset=AsignacionCargo.objects.none(),
        widget=forms.Select(attrs={"class": FIELD_CLASS}),
    )

    def __init__(self, *args, asignacion=None, **kwargs):
        super().__init__(*args, asignacion=asignacion, **kwargs)
        if asignacion is not None:
            self.fields["nueva_asignacion"].queryset = AsignacionCargo.objects.filter(
                iglesia=asignacion.iglesia,
                cargo=asignacion.cargo,
                estado=AsignacionCargo.Estado.NOMBRADO,
                activo=True,
            ).exclude(pk=asignacion.pk).select_related("miembro", "usuario").order_by("-fecha_inicio")

    def clean(self):
        cleaned_data = super().clean()
        nueva = cleaned_data.get("nueva_asignacion")
        if self.asignacion is not None and nueva is not None:
            if nueva.iglesia_id != self.asignacion.iglesia_id or nueva.cargo_id != self.asignacion.cargo_id:
                raise ValidationError("La nueva asignacion debe pertenecer al mismo cargo e iglesia.")
        return cleaned_data

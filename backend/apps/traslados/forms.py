from django import forms
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.escuela_dominical.models import ClaseEscuelaDominical, MatriculaEscuelaDominical
from apps.familias.models import Familia, MiembroFamilia
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


class ConfirmarRecepcionTrasladoForm(forms.Form):
    observacion_recepcion = forms.CharField(
        label="Observacion de recepcion pastoral",
        required=False,
        widget=forms.Textarea(attrs={"rows": 5, "class": FIELD_CLASS}),
        help_text="Registre acuerdos, pendientes o datos importantes para la integracion en la iglesia destino.",
    )

    def __init__(self, *args, traslado=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.traslado = traslado

    def clean(self):
        cleaned_data = super().clean()
        if self.traslado is not None and not self.traslado.pendiente_recepcion:
            raise ValidationError("Solo se puede confirmar la recepcion de traslados aceptados pendientes de recepcion.")
        return cleaned_data


class RevisionIntegracionDestinoForm(forms.Form):
    observacion = forms.CharField(
        label="Observacion de revision",
        required=False,
        widget=forms.Textarea(attrs={"rows": 4, "class": FIELD_CLASS}),
    )

    def __init__(self, *args, traslado=None, tipo="", **kwargs):
        super().__init__(*args, **kwargs)
        self.traslado = traslado
        self.tipo = tipo

    def clean(self):
        cleaned_data = super().clean()
        if self.traslado is None:
            return cleaned_data
        if self.tipo == "familia" and not self.traslado.integracion_familiar_pendiente:
            raise ValidationError("La revision familiar no esta pendiente para este traslado.")
        if self.tipo == "escuela" and not self.traslado.revision_escuela_dominical_pendiente:
            raise ValidationError("La revision de Escuela Dominical no esta pendiente para este traslado.")
        return cleaned_data


class VincularFamiliaDestinoForm(forms.Form):
    familia = forms.ModelChoiceField(
        label="Familia destino",
        queryset=Familia.objects.none(),
        widget=forms.Select(attrs={"class": FIELD_CLASS}),
    )
    relacion = forms.ChoiceField(
        label="Relacion",
        choices=MiembroFamilia.Relacion.choices,
        widget=forms.Select(attrs={"class": FIELD_CLASS}),
    )
    observacion = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": FIELD_CLASS}),
    )

    def __init__(self, *args, traslado=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.traslado = traslado
        if traslado is not None:
            self.fields["familia"].queryset = Familia.objects.filter(
                iglesia=traslado.iglesia_destino,
                activo=True,
            ).order_by("nombre")

    def clean(self):
        cleaned_data = super().clean()
        familia = cleaned_data.get("familia")
        if self.traslado is None:
            return cleaned_data
        if not self.traslado.integracion_familiar_pendiente:
            raise ValidationError("La integracion familiar no esta pendiente para este traslado.")
        if familia is not None and familia.iglesia_id != self.traslado.iglesia_destino_id:
            raise ValidationError("La familia debe pertenecer a la iglesia destino.")
        return cleaned_data


class MatricularEscuelaDestinoForm(forms.Form):
    clase = forms.ModelChoiceField(
        label="Clase destino",
        queryset=ClaseEscuelaDominical.objects.none(),
        widget=forms.Select(attrs={"class": FIELD_CLASS}),
    )
    fecha_inscripcion = forms.DateField(
        label="Fecha de inscripcion",
        widget=forms.DateInput(attrs={"type": "date", "class": FIELD_CLASS}),
    )
    observacion = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": FIELD_CLASS}),
    )

    def __init__(self, *args, traslado=None, fecha_inicial=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.traslado = traslado
        if fecha_inicial is not None:
            self.fields["fecha_inscripcion"].initial = fecha_inicial
        if traslado is not None:
            self.fields["clase"].queryset = ClaseEscuelaDominical.objects.filter(
                iglesia=traslado.iglesia_destino,
                activo=True,
            ).select_related("nivel", "periodo").order_by("-periodo__fecha_inicio", "nivel__orden", "nombre")

    def clean(self):
        cleaned_data = super().clean()
        clase = cleaned_data.get("clase")
        fecha_inscripcion = cleaned_data.get("fecha_inscripcion")
        if self.traslado is None:
            return cleaned_data
        if not self.traslado.revision_escuela_dominical_pendiente:
            raise ValidationError("La integracion con Escuela Dominical no esta pendiente para este traslado.")
        if clase is not None and clase.iglesia_id != self.traslado.iglesia_destino_id:
            raise ValidationError("La clase debe pertenecer a la iglesia destino.")
        if clase is not None and fecha_inscripcion is not None:
            if fecha_inscripcion < clase.periodo.fecha_inicio or fecha_inscripcion > clase.periodo.fecha_fin:
                raise ValidationError("La fecha de inscripcion debe estar dentro del periodo de la clase.")
            if clase.cupo is not None and clase.matriculas.filter(activo=True).count() >= clase.cupo:
                raise ValidationError("La clase alcanzo el cupo configurado.")
            existe = MatriculaEscuelaDominical.objects.filter(
                clase=clase,
                alumno=self.traslado.miembro,
                activo=True,
            ).exists()
            if existe:
                raise ValidationError("El miembro ya tiene matricula activa en esa clase.")
        return cleaned_data

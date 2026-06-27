from django import forms
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.escuela_dominical.models import ClaseEscuelaDominical, MatriculaEscuelaDominical
from apps.familias.models import Familia, MiembroFamilia
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro

from .models import TareaPastoralTraslado, TrasladoFamiliarIntegrante, TrasladoMiembro


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class TrasladoMiembroForm(forms.ModelForm):
    integrantes_familiares = forms.ModelMultipleChoiceField(
        label="Integrantes adicionales",
        queryset=Miembro.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Seleccione otros integrantes de la misma familia que se trasladaran junto al miembro principal.",
    )

    class Meta:
        model = TrasladoMiembro
        fields = ("miembro", "iglesia_destino", "es_familiar", "familia_origen", "integrantes_familiares", "motivo")
        widgets = {
            "es_familiar": forms.CheckboxInput(),
            "motivo": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "es_familiar": "Traslado familiar",
            "familia_origen": "Familia de origen",
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
        familias_origen = Familia.objects.filter(activo=True)
        if user is not None and not usuario_es_nacional(user):
            familias_origen = familias_origen.filter(iglesia=user.iglesia)
        self.fields["familia_origen"].queryset = familias_origen.order_by("nombre")

        miembro_id = self.data.get(self.add_prefix("miembro")) if self.is_bound else self.initial.get("miembro")
        if miembro_id:
            self.fields["familia_origen"].queryset = Familia.objects.filter(
                integrantes__miembro_id=miembro_id,
                integrantes__activo=True,
                activo=True,
            ).distinct().order_by("nombre")

        familia_id = self.data.get(self.add_prefix("familia_origen")) if self.is_bound else self.initial.get("familia_origen")
        if familia_id:
            self.fields["integrantes_familiares"].queryset = Miembro.objects.filter(
                familias__familia_id=familia_id,
                familias__activo=True,
                activo=True,
                estado=Miembro.Estado.ACTIVO,
            ).exclude(pk=miembro_id).distinct().order_by("apellidos", "nombres")

        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", FIELD_CLASS)

    def clean(self):
        cleaned_data = super().clean()
        miembro = cleaned_data.get("miembro")
        iglesia_destino = cleaned_data.get("iglesia_destino")
        es_familiar = cleaned_data.get("es_familiar")
        familia_origen = cleaned_data.get("familia_origen")
        integrantes_familiares = cleaned_data.get("integrantes_familiares")

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

        if es_familiar:
            if familia_origen is None:
                raise ValidationError("Seleccione la familia de origen para el traslado familiar.")
            if miembro is not None:
                if familia_origen.iglesia_id != miembro.iglesia_id:
                    raise ValidationError("La familia de origen debe pertenecer a la iglesia del miembro.")
                miembro_en_familia = MiembroFamilia.objects.filter(
                    familia=familia_origen,
                    miembro=miembro,
                    activo=True,
                ).exists()
                if not miembro_en_familia:
                    raise ValidationError("El miembro principal debe pertenecer activamente a la familia seleccionada.")
            if not integrantes_familiares:
                raise ValidationError("Seleccione al menos un integrante adicional para el traslado familiar.")
            for integrante in integrantes_familiares:
                if miembro is not None and integrante.pk == miembro.pk:
                    raise ValidationError("El miembro principal no debe repetirse como integrante adicional.")
                if iglesia_destino is not None and integrante.iglesia_id == iglesia_destino.id:
                    raise ValidationError("Los integrantes adicionales ya no deben pertenecer a la iglesia destino.")
                if miembro is not None and integrante.iglesia_id != miembro.iglesia_id:
                    raise ValidationError("Todos los integrantes adicionales deben pertenecer a la iglesia origen.")
                existe_pendiente = TrasladoMiembro.objects.filter(
                    miembro=integrante,
                    estado=TrasladoMiembro.Estado.SOLICITADO,
                ).exists()
                existe_como_integrante = TrasladoFamiliarIntegrante.objects.filter(
                    miembro=integrante,
                    traslado__estado=TrasladoMiembro.Estado.SOLICITADO,
                ).exists()
                if existe_pendiente or existe_como_integrante:
                    raise ValidationError(f"{integrante} ya tiene un traslado pendiente.")
        else:
            cleaned_data["familia_origen"] = None

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.miembro_id:
            instance.iglesia_origen = instance.miembro.iglesia
        if self.user is not None:
            instance.solicitado_por = self.user
        if commit:
            instance.save()
            self._guardar_integrantes_familiares(instance)
        return instance

    def _guardar_integrantes_familiares(self, instance):
        instance.integrantes_familiares.all().delete()
        if not instance.es_familiar:
            return
        familia = self.cleaned_data.get("familia_origen")
        for miembro in self.cleaned_data.get("integrantes_familiares", []):
            relacion = (
                MiembroFamilia.objects.filter(familia=familia, miembro=miembro, activo=True)
                .values_list("relacion", flat=True)
                .first()
                or ""
            )
            TrasladoFamiliarIntegrante.objects.create(
                traslado=instance,
                miembro=miembro,
                relacion=relacion,
            )


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


class TareaPastoralTrasladoForm(forms.ModelForm):
    class Meta:
        model = TareaPastoralTraslado
        fields = ("descripcion",)
        widgets = {
            "descripcion": forms.TextInput(attrs={"class": FIELD_CLASS}),
        }

    def __init__(self, *args, traslado=None, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.traslado = traslado
        self.user = user

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.traslado is not None:
            instance.traslado = self.traslado
        if self.user is not None:
            instance.creada_por = self.user
        if commit:
            instance.save()
        return instance


class CompletarTareaPastoralTrasladoForm(forms.Form):
    observacion = forms.CharField(
        label="Observacion",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": FIELD_CLASS}),
    )

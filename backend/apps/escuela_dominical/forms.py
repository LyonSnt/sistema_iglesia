from django import forms
from django.core.exceptions import ValidationError

from apps.core.iglesias import usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.parametros.models import Periodo
from apps.usuarios.models import Usuario

from .models import (
    AsistenciaEscuelaDominical,
    ClaseEscuelaDominical,
    MatriculaEscuelaDominical,
    NivelEscuelaDominical,
    SesionEscuelaDominical,
    ProcesoPromocionEscuelaDominical,
    ResultadoPromocionEscuelaDominical,
)


FIELD_CLASS = (
    "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-950 "
    "shadow-sm focus:border-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-200"
)


class FormularioEscuelaMixin:
    def aplicar_estilos(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "h-4 w-4 rounded border-slate-300 text-slate-950")
            elif not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.setdefault("class", FIELD_CLASS)


class NivelEscuelaDominicalForm(FormularioEscuelaMixin, forms.ModelForm):
    class Meta:
        model = NivelEscuelaDominical
        fields = ("iglesia", "nombre", "edad_minima", "edad_maxima", "orden", "descripcion", "activo")
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        iglesias = Iglesia.objects.filter(activo=True).order_by("nombre")
        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        self.fields["iglesia"].queryset = iglesias
        self.aplicar_estilos()

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
        return instance


class ClaseEscuelaDominicalForm(FormularioEscuelaMixin, forms.ModelForm):
    class Meta:
        model = ClaseEscuelaDominical
        fields = (
            "iglesia",
            "nombre",
            "nivel",
            "periodo",
            "maestro",
            "aula",
            "horario",
            "cupo",
            "descripcion",
            "activo",
        )
        widgets = {"descripcion": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        iglesias = Iglesia.objects.filter(activo=True).order_by("nombre")
        niveles = NivelEscuelaDominical.objects.filter(activo=True).select_related("iglesia")
        maestros = Usuario.objects.filter(is_active=True).select_related("iglesia")

        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            niveles = niveles.filter(iglesia=user.iglesia)
            maestros = maestros.filter(iglesia=user.iglesia)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        elif self.instance and self.instance.pk:
            niveles = niveles.filter(iglesia=self.instance.iglesia)
            maestros = maestros.filter(iglesia=self.instance.iglesia)

        self.fields["iglesia"].queryset = iglesias
        self.fields["nivel"].queryset = niveles.order_by("iglesia__nombre", "orden", "nombre")
        self.fields["periodo"].queryset = Periodo.objects.filter(activo=True).order_by("-fecha_inicio")
        self.fields["maestro"].queryset = maestros.order_by("iglesia__nombre", "username")
        self.aplicar_estilos()

    def clean(self):
        cleaned_data = super().clean()
        iglesia = cleaned_data.get("iglesia")
        if self.user is not None and not usuario_es_nacional(self.user):
            iglesia = self.user.iglesia
            cleaned_data["iglesia"] = iglesia

        nivel = cleaned_data.get("nivel")
        maestro = cleaned_data.get("maestro")
        if iglesia and nivel and nivel.iglesia_id != iglesia.id:
            raise ValidationError("El nivel debe pertenecer a la misma iglesia de la clase.")
        if iglesia and maestro and maestro.iglesia_id != iglesia.id:
            raise ValidationError("El maestro debe pertenecer a la misma iglesia de la clase.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user is not None and not usuario_es_nacional(self.user):
            instance.iglesia = self.user.iglesia
        if commit:
            instance.save()
        return instance


class MatriculaEscuelaDominicalForm(FormularioEscuelaMixin, forms.ModelForm):
    class Meta:
        model = MatriculaEscuelaDominical
        fields = ("alumno", "fecha_inscripcion", "estado", "fecha_salida", "observacion", "activo")
        widgets = {
            "fecha_inscripcion": forms.DateInput(attrs={"type": "date"}),
            "fecha_salida": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, clase=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.clase = clase
        alumnos = Miembro.objects.filter(activo=True)
        if clase is not None:
            alumnos_matriculados = clase.matriculas.exclude(pk=self.instance.pk).values("alumno_id")
            alumnos = alumnos.filter(iglesia=clase.iglesia).exclude(pk__in=alumnos_matriculados)
        self.fields["alumno"].queryset = alumnos.order_by("apellidos", "nombres")
        self.aplicar_estilos()

    def clean(self):
        cleaned_data = super().clean()
        alumno = cleaned_data.get("alumno")
        if self.clase and alumno and alumno.iglesia_id != self.clase.iglesia_id:
            raise ValidationError("El alumno debe pertenecer a la misma iglesia de la clase.")
        if (
            self.clase
            and not self.instance.pk
            and self.clase.cupo is not None
            and self.clase.matriculas.filter(activo=True).count() >= self.clase.cupo
        ):
            raise ValidationError("La clase alcanzo el cupo configurado.")
        return cleaned_data


class SesionEscuelaDominicalForm(FormularioEscuelaMixin, forms.ModelForm):
    class Meta:
        model = SesionEscuelaDominical
        fields = ("fecha", "tema", "observacion")
        widgets = {
            "fecha": forms.DateInput(attrs={"type": "date"}),
            "observacion": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, clase=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.clase = clase
        self.aplicar_estilos()

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if self.clase and not (
            self.clase.periodo.fecha_inicio <= fecha <= self.clase.periodo.fecha_fin
        ):
            raise ValidationError("La fecha debe estar dentro del periodo de la clase.")
        return fecha


class TomaAsistenciaForm(forms.Form):
    cerrar_sesion = forms.BooleanField(label="Cerrar sesion al guardar", required=False)

    def __init__(self, *args, sesion=None, matriculas=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.sesion = sesion
        self.matriculas = list(matriculas)
        existentes = {
            asistencia.matricula_id: asistencia
            for asistencia in sesion.asistencias.all()
        } if sesion else {}

        for matricula in self.matriculas:
            asistencia = existentes.get(matricula.pk)
            self.fields[f"estado_{matricula.pk}"] = forms.ChoiceField(
                label=str(matricula.alumno),
                choices=AsistenciaEscuelaDominical.Estado.choices,
                initial=asistencia.estado if asistencia else AsistenciaEscuelaDominical.Estado.PRESENTE,
                widget=forms.Select(attrs={"class": FIELD_CLASS}),
            )
            self.fields[f"observacion_{matricula.pk}"] = forms.CharField(
                required=False,
                initial=asistencia.observacion if asistencia else "",
                widget=forms.TextInput(attrs={"class": FIELD_CLASS, "placeholder": "Observacion opcional"}),
            )

        self.fields["cerrar_sesion"].widget.attrs.setdefault(
            "class", "h-4 w-4 rounded border-slate-300"
        )

    def datos_asistencia(self):
        for matricula in self.matriculas:
            yield (
                matricula,
                self.cleaned_data[f"estado_{matricula.pk}"],
                self.cleaned_data[f"observacion_{matricula.pk}"],
            )


class ProcesoPromocionForm(FormularioEscuelaMixin, forms.ModelForm):
    class Meta:
        model = ProcesoPromocionEscuelaDominical
        fields = ("iglesia", "periodo_origen", "periodo_destino", "fecha_corte")
        widgets = {"fecha_corte": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        iglesias = Iglesia.objects.filter(activo=True).order_by("nombre")
        if user is not None and not usuario_es_nacional(user):
            iglesias = iglesias.filter(pk=user.iglesia_id)
            self.fields["iglesia"].required = False
            self.fields["iglesia"].widget = forms.HiddenInput()
            self.fields["iglesia"].disabled = True
        self.fields["iglesia"].queryset = iglesias
        self.fields["periodo_origen"].queryset = Periodo.objects.order_by("-fecha_inicio")
        self.fields["periodo_destino"].queryset = Periodo.objects.order_by("-fecha_inicio")
        self.aplicar_estilos()

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
            instance.full_clean()
            instance.save()
        return instance


class ConfirmarPromocionForm(forms.Form):
    confirmar = forms.BooleanField(label="Confirmo el cierre y la promocion de estos alumnos")

    def __init__(self, *args, proceso=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.proceso = proceso
        resultados = proceso.resultados.select_related("nivel_destino")
        for resultado in resultados:
            if resultado.destino != ResultadoPromocionEscuelaDominical.Destino.NIVEL_SIGUIENTE:
                continue
            self.fields[f"clase_{resultado.pk}"] = forms.ModelChoiceField(
                label=f"Clase destino de {resultado.matricula_origen.alumno}",
                queryset=ClaseEscuelaDominical.objects.filter(
                    iglesia=proceso.iglesia,
                    periodo=proceso.periodo_destino,
                    nivel=resultado.nivel_destino,
                    activo=True,
                ).order_by("nombre"),
                initial=resultado.clase_destino_id,
                widget=forms.Select(attrs={"class": FIELD_CLASS}),
            )
        self.fields["confirmar"].widget.attrs["class"] = "h-4 w-4 rounded border-slate-300"

    def guardar_destinos(self):
        for resultado in self.proceso.resultados.all():
            campo = f"clase_{resultado.pk}"
            if campo in self.cleaned_data:
                resultado.clase_destino = self.cleaned_data[campo]
                resultado.full_clean()
                resultado.save(update_fields=["clase_destino", "actualizado_en"])

from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

from apps.core.models import ActiveModel, IglesiaScopedModel, TimeStampedModel


class NivelEscuelaDominical(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    nombre = models.CharField(max_length=120)
    edad_minima = models.PositiveSmallIntegerField(null=True, blank=True)
    edad_maxima = models.PositiveSmallIntegerField(null=True, blank=True)
    orden = models.PositiveSmallIntegerField(default=1)
    descripcion = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("iglesia", "nombre"),
                name="escuela_nivel_nombre_unico_por_iglesia",
            )
        ]
        ordering = ("orden", "nombre")
        verbose_name = "nivel de Escuela Dominical"
        verbose_name_plural = "niveles de Escuela Dominical"

    def clean(self):
        super().clean()
        if (
            self.edad_minima is not None
            and self.edad_maxima is not None
            and self.edad_maxima < self.edad_minima
        ):
            raise ValidationError({"edad_maxima": "La edad maxima no puede ser menor que la edad minima."})

    def __str__(self):
        return self.nombre


class ClaseEscuelaDominical(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    nombre = models.CharField(max_length=150)
    nivel = models.ForeignKey(
        NivelEscuelaDominical,
        on_delete=models.PROTECT,
        related_name="clases",
    )
    periodo = models.ForeignKey(
        "parametros.Periodo",
        on_delete=models.PROTECT,
        related_name="clases_escuela_dominical",
    )
    maestro = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="clases_escuela_dominical",
    )
    aula = models.CharField(max_length=100, blank=True)
    horario = models.CharField(max_length=120, blank=True)
    cupo = models.PositiveSmallIntegerField(null=True, blank=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("iglesia", "periodo", "nombre"),
                name="escuela_clase_nombre_unico_por_periodo",
            )
        ]
        ordering = ("nivel__orden", "nombre")
        verbose_name = "clase de Escuela Dominical"
        verbose_name_plural = "clases de Escuela Dominical"

    def clean(self):
        super().clean()
        errors = {}
        if self.nivel_id and self.iglesia_id and self.nivel.iglesia_id != self.iglesia_id:
            errors["nivel"] = "El nivel debe pertenecer a la misma iglesia de la clase."
        if self.maestro_id and self.iglesia_id and self.maestro.iglesia_id != self.iglesia_id:
            errors["maestro"] = "El maestro debe pertenecer a la misma iglesia de la clase."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.nombre} - {self.periodo}"


class MatriculaEscuelaDominical(TimeStampedModel, ActiveModel):
    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        RETIRADA = "RETIRADA", "Retirada"
        PROMOVIDA = "PROMOVIDA", "Promovida"

    clase = models.ForeignKey(
        ClaseEscuelaDominical,
        on_delete=models.PROTECT,
        related_name="matriculas",
    )
    alumno = models.ForeignKey(
        "miembros.Miembro",
        on_delete=models.PROTECT,
        related_name="matriculas_escuela_dominical",
    )
    fecha_inscripcion = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    fecha_salida = models.DateField(null=True, blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("clase", "alumno"),
                name="escuela_matricula_unica_por_clase",
            )
        ]
        ordering = ("alumno__apellidos", "alumno__nombres")
        verbose_name = "matricula de Escuela Dominical"
        verbose_name_plural = "matriculas de Escuela Dominical"

    def clean(self):
        super().clean()
        errors = {}
        if self.clase_id and self.alumno_id and self.clase.iglesia_id != self.alumno.iglesia_id:
            errors["alumno"] = "El alumno debe pertenecer a la misma iglesia de la clase."
        if self.clase_id and self.alumno_id and self.estado == self.Estado.ACTIVA and self.activo:
            matricula_activa = MatriculaEscuelaDominical.objects.filter(
                alumno=self.alumno,
                clase__iglesia=self.clase.iglesia,
                clase__periodo=self.clase.periodo,
                estado=self.Estado.ACTIVA,
                activo=True,
            ).exclude(pk=self.pk)
            if matricula_activa.exists():
                errors["alumno"] = "El alumno ya tiene una matricula activa en este periodo."
        if self.fecha_salida and self.fecha_inscripcion and self.fecha_salida < self.fecha_inscripcion:
            errors["fecha_salida"] = "La fecha de salida no puede ser anterior a la inscripcion."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.alumno} - {self.clase}"


class SesionEscuelaDominical(TimeStampedModel):
    clase = models.ForeignKey(
        ClaseEscuelaDominical,
        on_delete=models.PROTECT,
        related_name="sesiones",
    )
    fecha = models.DateField()
    tema = models.CharField(max_length=180, blank=True)
    observacion = models.TextField(blank=True)
    cerrada = models.BooleanField(default=False)
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="sesiones_escuela_dominical_registradas",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("clase", "fecha"),
                name="escuela_sesion_unica_por_clase_fecha",
            )
        ]
        ordering = ("-fecha",)
        verbose_name = "sesion de Escuela Dominical"
        verbose_name_plural = "sesiones de Escuela Dominical"

    def clean(self):
        super().clean()
        if self.clase_id and self.fecha:
            if self.fecha < self.clase.periodo.fecha_inicio or self.fecha > self.clase.periodo.fecha_fin:
                raise ValidationError({"fecha": "La fecha debe estar dentro del periodo de la clase."})
        if (
            self.clase_id
            and self.registrado_por_id
            and self.registrado_por.iglesia_id != self.clase.iglesia_id
        ):
            raise ValidationError(
                {"registrado_por": "El usuario debe pertenecer a la misma iglesia de la clase."}
            )

    @property
    def iglesia(self):
        return self.clase.iglesia

    def __str__(self):
        return f"{self.clase.nombre} - {self.fecha}"


class AsistenciaEscuelaDominical(TimeStampedModel):
    class Estado(models.TextChoices):
        PRESENTE = "PRESENTE", "Presente"
        AUSENTE = "AUSENTE", "Ausente"
        JUSTIFICADO = "JUSTIFICADO", "Justificado"

    sesion = models.ForeignKey(
        SesionEscuelaDominical,
        on_delete=models.PROTECT,
        related_name="asistencias",
    )
    matricula = models.ForeignKey(
        MatriculaEscuelaDominical,
        on_delete=models.PROTECT,
        related_name="asistencias",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices)
    observacion = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("sesion", "matricula"),
                name="escuela_asistencia_unica_por_sesion_matricula",
            )
        ]
        ordering = ("matricula__alumno__apellidos", "matricula__alumno__nombres")
        verbose_name = "asistencia de Escuela Dominical"
        verbose_name_plural = "asistencias de Escuela Dominical"

    def clean(self):
        super().clean()
        if self.sesion_id and self.matricula_id and self.sesion.clase_id != self.matricula.clase_id:
            raise ValidationError({"matricula": "La matricula debe pertenecer a la clase de la sesion."})

    @property
    def iglesia(self):
        return self.sesion.clase.iglesia

    def __str__(self):
        return f"{self.matricula.alumno} - {self.sesion.fecha}: {self.get_estado_display()}"


class ProcesoPromocionEscuelaDominical(TimeStampedModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        BORRADOR = "BORRADOR", "Borrador"
        CONFIRMADO = "CONFIRMADO", "Confirmado"

    periodo_origen = models.ForeignKey(
        "parametros.Periodo", on_delete=models.PROTECT, related_name="promociones_escuela_origen"
    )
    periodo_destino = models.ForeignKey(
        "parametros.Periodo", on_delete=models.PROTECT, related_name="promociones_escuela_destino"
    )
    fecha_corte = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.BORRADOR)
    confirmado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="promociones_escuela_confirmadas",
    )
    confirmado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("iglesia", "periodo_origen", "periodo_destino"),
                name="escuela_promocion_unica_por_periodos",
            )
        ]
        ordering = ("-fecha_corte", "iglesia__nombre")
        verbose_name = "proceso de promocion de Escuela Dominical"
        verbose_name_plural = "procesos de promocion de Escuela Dominical"

    def clean(self):
        super().clean()
        errors = {}
        if self.fecha_corte and self.fecha_corte.month != 1:
            errors["fecha_corte"] = "La graduacion de Escuela Dominical debe tener corte en enero."
        if self.periodo_origen_id and self.periodo_destino_id:
            if self.periodo_origen_id == self.periodo_destino_id:
                errors["periodo_destino"] = "El periodo destino debe ser diferente al periodo origen."
            elif self.periodo_destino.fecha_inicio <= self.periodo_origen.fecha_inicio:
                errors["periodo_destino"] = "El periodo destino debe ser posterior al periodo origen."
            if self.fecha_corte and not (
                self.periodo_destino.fecha_inicio <= self.fecha_corte <= self.periodo_destino.fecha_fin
            ):
                errors["fecha_corte"] = "La fecha de corte debe pertenecer al periodo destino."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.iglesia} - {self.periodo_origen} a {self.periodo_destino}"


class ResultadoPromocionEscuelaDominical(TimeStampedModel):
    class Destino(models.TextChoices):
        NIVEL_SIGUIENTE = "NIVEL_SIGUIENTE", "Nivel siguiente"
        JOVENES = "JOVENES", "Jovenes"

    proceso = models.ForeignKey(
        ProcesoPromocionEscuelaDominical, on_delete=models.PROTECT, related_name="resultados"
    )
    matricula_origen = models.ForeignKey(
        MatriculaEscuelaDominical, on_delete=models.PROTECT, related_name="resultados_promocion"
    )
    edad_al_corte = models.PositiveSmallIntegerField()
    destino = models.CharField(max_length=20, choices=Destino.choices)
    nivel_destino = models.ForeignKey(
        NivelEscuelaDominical,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resultados_promocion_destino",
    )
    clase_destino = models.ForeignKey(
        ClaseEscuelaDominical,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resultados_promocion_destino",
    )
    matricula_destino = models.OneToOneField(
        MatriculaEscuelaDominical,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resultado_promocion_origen",
    )
    sesiones_consideradas = models.PositiveSmallIntegerField(default=0)
    presentes = models.PositiveSmallIntegerField(default=0)
    ausentes = models.PositiveSmallIntegerField(default=0)
    justificados = models.PositiveSmallIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("proceso", "matricula_origen"),
                name="escuela_resultado_unico_por_proceso_matricula",
            )
        ]
        ordering = ("matricula_origen__alumno__apellidos", "matricula_origen__alumno__nombres")
        verbose_name = "resultado de promocion de Escuela Dominical"
        verbose_name_plural = "resultados de promocion de Escuela Dominical"

    @property
    def porcentaje_asistencia(self):
        if not self.sesiones_consideradas:
            return None
        return round(self.presentes * 100 / self.sesiones_consideradas, 1)

    @property
    def iglesia(self):
        return self.proceso.iglesia

    def clean(self):
        super().clean()
        errors = {}
        if self.proceso_id and self.matricula_origen_id:
            if self.matricula_origen.clase.iglesia_id != self.proceso.iglesia_id:
                errors["matricula_origen"] = "La matricula debe pertenecer a la iglesia del proceso."
            if self.matricula_origen.clase.periodo_id != self.proceso.periodo_origen_id:
                errors["matricula_origen"] = "La matricula debe pertenecer al periodo origen."
        if self.destino == self.Destino.JOVENES:
            if self.nivel_destino_id or self.clase_destino_id:
                errors["clase_destino"] = "El egreso a Jovenes no crea una matricula destino."
        elif self.destino == self.Destino.NIVEL_SIGUIENTE:
            if not self.nivel_destino_id:
                errors["nivel_destino"] = "Indique el nivel siguiente."
            if self.clase_destino_id:
                if self.clase_destino.nivel_id != self.nivel_destino_id:
                    errors["clase_destino"] = "La clase debe corresponder al nivel destino."
                elif self.clase_destino.periodo_id != self.proceso.periodo_destino_id:
                    errors["clase_destino"] = "La clase debe pertenecer al periodo destino."
                elif self.clase_destino.iglesia_id != self.proceso.iglesia_id:
                    errors["clase_destino"] = "La clase debe pertenecer a la iglesia del proceso."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.matricula_origen.alumno} - {self.get_destino_display()}"

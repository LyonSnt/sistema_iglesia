from django.db import models

from apps.core.models import ActiveModel, IglesiaScopedModel, TimeStampedModel


class Cargo(TimeStampedModel, ActiveModel):
    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.TextField(blank=True)
    es_nacional = models.BooleanField(default=False)
    es_sensible = models.BooleanField(default=False)
    requiere_documento_posesion = models.BooleanField(default=False)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "cargo"
        verbose_name_plural = "cargos"

    def __str__(self):
        return self.nombre


class AsignacionCargo(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    class Estado(models.TextChoices):
        NOMBRADO = "NOMBRADO", "Nombrado"
        VIGENTE = "VIGENTE", "Vigente"
        FINALIZADO = "FINALIZADO", "Finalizado"
        ANULADO = "ANULADO", "Anulado"

    class TipoAsignacion(models.TextChoices):
        TITULAR = "TITULAR", "Titular"
        INTERINO = "INTERINO", "Interino"
        SUPLENTE = "SUPLENTE", "Suplente"

    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="asignaciones")
    miembro = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, null=True, blank=True, related_name="cargos")
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, null=True, blank=True, related_name="cargos")
    tipo_asignacion = models.CharField(
        max_length=20,
        choices=TipoAsignacion.choices,
        default=TipoAsignacion.TITULAR,
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.VIGENTE)
    asignacion_reemplazada = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="reemplazos",
        null=True,
        blank=True,
    )
    documento = models.FileField(upload_to="cargos/documentos/", blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-fecha_inicio",)
        verbose_name = "asignacion de cargo"
        verbose_name_plural = "asignaciones de cargos"

    def __str__(self):
        asignado = self.miembro or self.usuario
        return f"{self.cargo} - {asignado}"


class HistorialAsignacionCargo(TimeStampedModel):
    class Tipo(models.TextChoices):
        NOMBRAMIENTO = "NOMBRAMIENTO", "Nombramiento"
        POSESION = "POSESION", "Posesion"
        RENUNCIA = "RENUNCIA", "Renuncia"
        REEMPLAZO = "REEMPLAZO", "Reemplazo"

    asignacion = models.ForeignKey(
        AsignacionCargo,
        on_delete=models.PROTECT,
        related_name="historial_formal",
    )
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    fecha = models.DateField()
    motivo = models.TextField()
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="historial_cargos_registrado",
    )
    estado_anterior = models.CharField(max_length=20, blank=True)
    estado_nuevo = models.CharField(max_length=20, blank=True)
    asignacion_relacionada = models.ForeignKey(
        AsignacionCargo,
        on_delete=models.PROTECT,
        related_name="historial_relacionado",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-fecha", "-creado_en")
        verbose_name = "historial formal de cargo"
        verbose_name_plural = "historial formal de cargos"

    def __str__(self):
        return f"{self.asignacion} - {self.get_tipo_display()}"

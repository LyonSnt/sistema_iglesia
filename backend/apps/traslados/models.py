from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel


class TrasladoMiembro(TimeStampedModel):
    class Estado(models.TextChoices):
        SOLICITADO = "SOLICITADO", "Solicitado"
        ACEPTADO = "ACEPTADO", "Aceptado"
        RECHAZADO = "RECHAZADO", "Rechazado"
        ANULADO = "ANULADO", "Anulado"

    miembro = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, related_name="traslados")
    iglesia_origen = models.ForeignKey(
        "iglesias.Iglesia",
        on_delete=models.PROTECT,
        related_name="traslados_origen",
    )
    iglesia_destino = models.ForeignKey(
        "iglesias.Iglesia",
        on_delete=models.PROTECT,
        related_name="traslados_destino",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.SOLICITADO)
    motivo = models.TextField()
    observacion_respuesta = models.TextField(blank=True)
    solicitado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="traslados_solicitados",
    )
    respondido_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="traslados_respondidos",
        null=True,
        blank=True,
    )
    respondido_en = models.DateTimeField(null=True, blank=True)
    completado_en = models.DateTimeField(null=True, blank=True)
    recepcion_confirmada_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="traslados_recepciones_confirmadas",
        null=True,
        blank=True,
    )
    recepcion_confirmada_en = models.DateTimeField(null=True, blank=True)
    observacion_recepcion = models.TextField(blank=True)
    familia_destino_revisada_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="traslados_familia_destino_revisados",
        null=True,
        blank=True,
    )
    familia_destino_revisada_en = models.DateTimeField(null=True, blank=True)
    observacion_familia_destino = models.TextField(blank=True)
    escuela_dominical_destino_revisada_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="traslados_escuela_destino_revisados",
        null=True,
        blank=True,
    )
    escuela_dominical_destino_revisada_en = models.DateTimeField(null=True, blank=True)
    observacion_escuela_dominical_destino = models.TextField(blank=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "traslado de miembro"
        verbose_name_plural = "traslados de miembros"

    def __str__(self):
        return f"{self.miembro} de {self.iglesia_origen.codigo} a {self.iglesia_destino.codigo}"

    @property
    def pendiente(self):
        return self.estado == self.Estado.SOLICITADO

    @property
    def pendiente_recepcion(self):
        return self.estado == self.Estado.ACEPTADO and self.recepcion_confirmada_en is None

    @property
    def recepcion_confirmada(self):
        return self.recepcion_confirmada_en is not None

    @property
    def tiene_familia_activa_destino(self):
        if not self.miembro_id or not self.iglesia_destino_id:
            return False
        from apps.familias.models import MiembroFamilia

        return MiembroFamilia.objects.filter(
            miembro_id=self.miembro_id,
            activo=True,
            familia__activo=True,
            familia__iglesia_id=self.iglesia_destino_id,
        ).exists()

    @property
    def integracion_familiar_pendiente(self):
        return (
            self.recepcion_confirmada
            and self.familia_destino_revisada_en is None
            and not self.tiene_familia_activa_destino
        )

    @property
    def edad_actual_miembro(self):
        if not self.miembro_id or not self.miembro.fecha_nacimiento:
            return None
        hoy = timezone.localdate()
        fecha = self.miembro.fecha_nacimiento
        return hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))

    @property
    def aplica_revision_escuela_dominical(self):
        edad = self.edad_actual_miembro
        return edad is not None and edad < 18

    @property
    def tiene_matricula_activa_destino(self):
        if not self.miembro_id or not self.iglesia_destino_id:
            return False
        from apps.escuela_dominical.models import MatriculaEscuelaDominical

        return MatriculaEscuelaDominical.objects.filter(
            alumno_id=self.miembro_id,
            activo=True,
            estado=MatriculaEscuelaDominical.Estado.ACTIVA,
            clase__iglesia_id=self.iglesia_destino_id,
        ).exists()

    @property
    def revision_escuela_dominical_pendiente(self):
        return (
            self.recepcion_confirmada
            and self.aplica_revision_escuela_dominical
            and self.escuela_dominical_destino_revisada_en is None
            and not self.tiene_matricula_activa_destino
        )

    @property
    def integracion_destino_pendiente(self):
        return self.integracion_familiar_pendiente or self.revision_escuela_dominical_pendiente

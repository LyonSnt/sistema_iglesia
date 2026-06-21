from django.db import models

from apps.core.models import TimeStampedModel


class RegistroAuditoria(TimeStampedModel):
    usuario = models.ForeignKey("usuarios.Usuario", on_delete=models.PROTECT, null=True, blank=True)
    accion = models.CharField(max_length=80)
    modulo = models.CharField(max_length=80)
    registro_afectado = models.CharField(max_length=120, blank=True)
    valor_anterior = models.JSONField(null=True, blank=True)
    valor_nuevo = models.JSONField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    iglesia = models.ForeignKey("iglesias.Iglesia", on_delete=models.PROTECT, null=True, blank=True)
    motivo = models.TextField(blank=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "registro de auditoria"
        verbose_name_plural = "registros de auditoria"

    def __str__(self):
        return f"{self.modulo} - {self.accion}"

from pathlib import Path

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import IglesiaScopedModel, TimeStampedModel


EXTENSIONES_PERMITIDAS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx"}
TAMANO_MAXIMO_MB = 10


def documento_upload_to(instance, filename):
    return f"documentos/{instance.iglesia.codigo.lower()}/{timezone.now():%Y/%m}/{filename}"


def validar_archivo_adjunto(archivo):
    extension = Path(archivo.name).suffix.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValidationError("Tipo de archivo no permitido.")
    limite = getattr(settings, "DOCUMENTO_ADJUNTO_MAX_MB", TAMANO_MAXIMO_MB) * 1024 * 1024
    if archivo.size > limite:
        raise ValidationError("El archivo excede el tamano maximo permitido.")


class DocumentoAdjunto(TimeStampedModel, IglesiaScopedModel):
    class Tipo(models.TextChoices):
        FACTURA = "FACTURA", "Factura"
        FOTO = "FOTO", "Foto"
        GARANTIA = "GARANTIA", "Garantia"
        ACTA = "ACTA", "Acta"
        COMPROBANTE = "COMPROBANTE", "Comprobante"
        OTRO = "OTRO", "Otro"

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        ANULADO = "ANULADO", "Anulado"

    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    archivo = models.FileField(upload_to=documento_upload_to, validators=[validar_archivo_adjunto])
    nombre = models.CharField(max_length=160)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.OTRO)
    descripcion = models.TextField(blank=True)
    subido_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="documentos_adjuntos_subidos",
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    anulado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="documentos_adjuntos_anulados",
    )
    anulado_en = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-creado_en",)
        verbose_name = "documento adjunto"
        verbose_name_plural = "documentos adjuntos"

    def __str__(self):
        return f"{self.nombre} - {self.iglesia.codigo}"

    def clean(self):
        errors = {}
        objeto = self.content_object
        if objeto is not None and hasattr(objeto, "iglesia_id") and objeto.iglesia_id != self.iglesia_id:
            errors["iglesia"] = "El documento debe pertenecer a la misma iglesia del registro asociado."
        if self.estado == self.Estado.ANULADO and not self.motivo_anulacion:
            errors["motivo_anulacion"] = "Debe indicar el motivo de anulacion."
        if errors:
            raise ValidationError(errors)

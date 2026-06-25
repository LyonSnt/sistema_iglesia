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
        tipos_permitidos = tipos_documento_permitidos(objeto)
        if tipos_permitidos and self.tipo not in tipos_permitidos:
            errors["tipo"] = "Tipo de documento no permitido para este modulo."
        if self.estado == self.Estado.ANULADO and not self.motivo_anulacion:
            errors["motivo_anulacion"] = "Debe indicar el motivo de anulacion."
        if errors:
            raise ValidationError(errors)


TIPOS_DOCUMENTO_POR_MODELO = {
    ("cargos", "asignacioncargo"): (
        DocumentoAdjunto.Tipo.ACTA,
        DocumentoAdjunto.Tipo.OTRO,
    ),
    ("traslados", "trasladomiembro"): (
        DocumentoAdjunto.Tipo.ACTA,
        DocumentoAdjunto.Tipo.OTRO,
    ),
    ("finanzas", "movimientofinanciero"): (
        DocumentoAdjunto.Tipo.COMPROBANTE,
        DocumentoAdjunto.Tipo.FACTURA,
        DocumentoAdjunto.Tipo.OTRO,
    ),
    ("inventario", "activoinventario"): (
        DocumentoAdjunto.Tipo.FACTURA,
        DocumentoAdjunto.Tipo.FOTO,
        DocumentoAdjunto.Tipo.GARANTIA,
        DocumentoAdjunto.Tipo.ACTA,
        DocumentoAdjunto.Tipo.COMPROBANTE,
        DocumentoAdjunto.Tipo.OTRO,
    ),
}


def clave_modelo_documento(objeto):
    if objeto is None:
        return None
    content_type = ContentType.objects.get_for_model(objeto, for_concrete_model=False)
    return (content_type.app_label, content_type.model)


def tipos_documento_permitidos(objeto):
    clave = clave_modelo_documento(objeto)
    if clave is None:
        return ()
    return TIPOS_DOCUMENTO_POR_MODELO.get(clave, ())


def choices_tipos_documento_permitidos(objeto):
    tipos = tipos_documento_permitidos(objeto)
    if not tipos:
        return DocumentoAdjunto.Tipo.choices
    return [(valor, etiqueta) for valor, etiqueta in DocumentoAdjunto.Tipo.choices if valor in tipos]

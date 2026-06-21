from django.db import models

from apps.core.models import ActiveModel, TimeStampedModel


class Periodo(TimeStampedModel, ActiveModel):
    nombre = models.CharField(max_length=80)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    cerrado = models.BooleanField(default=False)

    class Meta:
        ordering = ("-fecha_inicio",)
        verbose_name = "periodo"
        verbose_name_plural = "periodos"

    def __str__(self):
        return self.nombre


class ParametroGeneral(TimeStampedModel, ActiveModel):
    class TipoDato(models.TextChoices):
        TEXTO = "TEXTO", "Texto"
        ENTERO = "ENTERO", "Entero"
        DECIMAL = "DECIMAL", "Decimal"
        BOOLEANO = "BOOLEANO", "Booleano"
        FECHA = "FECHA", "Fecha"

    clave = models.CharField(max_length=100, unique=True)
    nombre = models.CharField(max_length=150)
    valor = models.CharField(max_length=255)
    tipo_dato = models.CharField(max_length=20, choices=TipoDato.choices, default=TipoDato.TEXTO)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ("clave",)
        verbose_name = "parametro general"
        verbose_name_plural = "parametros generales"

    def __str__(self):
        return self.clave

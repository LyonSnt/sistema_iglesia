from django.db import models

from apps.core.models import ActiveModel, TimeStampedModel


class Zona(TimeStampedModel, ActiveModel):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "zona"
        verbose_name_plural = "zonas"

    def __str__(self):
        return self.nombre

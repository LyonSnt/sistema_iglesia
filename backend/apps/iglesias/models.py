from django.db import models

from apps.core.models import ActiveModel, TimeStampedModel


class Iglesia(TimeStampedModel, ActiveModel):
    class Tipo(models.TextChoices):
        NACIONAL = "NACIONAL", "Nacional"
        FILIAL = "FILIAL", "Filial"

    class Estado(models.TextChoices):
        ACTIVA = "ACTIVA", "Activa"
        INACTIVA = "INACTIVA", "Inactiva"
        EN_REVISION = "EN_REVISION", "En revision"

    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=180)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.FILIAL)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    zona = models.ForeignKey("zonas.Zona", on_delete=models.PROTECT, null=True, blank=True)
    iglesia_matriz = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    responsable_principal = models.CharField(max_length=180, blank=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "iglesia"
        verbose_name_plural = "iglesias"

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def es_nacional(self):
        return self.tipo == self.Tipo.NACIONAL

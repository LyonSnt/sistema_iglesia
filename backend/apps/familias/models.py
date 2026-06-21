from django.db import models

from apps.core.models import ActiveModel, IglesiaScopedModel, TimeStampedModel


class Familia(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    nombre = models.CharField(max_length=150)
    jefe_hogar = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, related_name="familias_jefatura")
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ("nombre",)
        verbose_name = "familia"
        verbose_name_plural = "familias"

    def __str__(self):
        return self.nombre


class MiembroFamilia(TimeStampedModel, ActiveModel):
    class Relacion(models.TextChoices):
        PADRE = "PADRE", "Padre"
        MADRE = "MADRE", "Madre"
        CONYUGE = "CONYUGE", "Conyuge"
        HIJO = "HIJO", "Hijo"
        REPRESENTANTE = "REPRESENTANTE", "Representante"
        OTRO = "OTRO", "Otro"

    familia = models.ForeignKey(Familia, on_delete=models.PROTECT, related_name="integrantes")
    miembro = models.ForeignKey("miembros.Miembro", on_delete=models.PROTECT, related_name="familias")
    relacion = models.CharField(max_length=20, choices=Relacion.choices)

    class Meta:
        unique_together = ("familia", "miembro", "relacion")
        verbose_name = "miembro de familia"
        verbose_name_plural = "miembros de familias"

    def __str__(self):
        return f"{self.miembro} - {self.relacion}"


class Matrimonio(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    conyuge_1 = models.ForeignKey(
        "miembros.Miembro",
        on_delete=models.PROTECT,
        related_name="matrimonios_como_conyuge_1",
    )
    conyuge_2 = models.ForeignKey(
        "miembros.Miembro",
        on_delete=models.PROTECT,
        related_name="matrimonios_como_conyuge_2",
    )
    fecha_matrimonio = models.DateField()
    familia = models.ForeignKey(Familia, on_delete=models.PROTECT, related_name="matrimonios", null=True, blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("-fecha_matrimonio", "conyuge_1__apellidos", "conyuge_2__apellidos")
        verbose_name = "matrimonio"
        verbose_name_plural = "matrimonios"

    def __str__(self):
        return f"{self.conyuge_1} y {self.conyuge_2}"

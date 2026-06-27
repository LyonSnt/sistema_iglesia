from django.db import models

from apps.core.models import ActiveModel, IglesiaScopedModel, TimeStampedModel


class Miembro(TimeStampedModel, ActiveModel, IglesiaScopedModel):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    class EstadoCivil(models.TextChoices):
        SOLTERO = "SOLTERO", "Soltero"
        CASADO = "CASADO", "Casado"
        VIUDO = "VIUDO", "Viudo"
        DIVORCIADO = "DIVORCIADO", "Divorciado"
        UNION_LIBRE = "UNION_LIBRE", "Union libre"

    class Estado(models.TextChoices):
        ACTIVO = "ACTIVO", "Activo"
        INACTIVO = "INACTIVO", "Inactivo"
        SUSPENDIDO = "SUSPENDIDO", "Suspendido"
        DISCIPLINA = "DISCIPLINA", "En disciplina"
        TRASLADADO = "TRASLADADO", "Trasladado"
        FALLECIDO = "FALLECIDO", "Fallecido"

    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    cedula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    estado_civil = models.CharField(max_length=20, choices=EstadoCivil.choices, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    fotografia = models.ImageField(upload_to="miembros/fotografias/", blank=True)
    fecha_conversion = models.DateField(null=True, blank=True)
    fecha_bautismo = models.DateField(null=True, blank=True)
    fecha_membresia = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    fecha_fallecimiento = models.DateField(null=True, blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        ordering = ("apellidos", "nombres")
        verbose_name = "miembro"
        verbose_name_plural = "miembros"

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"


class HistorialPastoralMiembro(TimeStampedModel):
    class Tipo(models.TextChoices):
        BAUTISMO = "BAUTISMO", "Bautismo"
        ADMISION = "ADMISION", "Admision formal"
        BAJA_VOLUNTARIA = "BAJA_VOLUNTARIA", "Baja voluntaria"
        RESTAURACION = "RESTAURACION", "Restauracion"
        DISCIPLINA = "DISCIPLINA", "Disciplina"
        SUSPENSION = "SUSPENSION", "Suspension"
        FALLECIMIENTO = "FALLECIMIENTO", "Fallecimiento"

    miembro = models.ForeignKey(Miembro, on_delete=models.PROTECT, related_name="historial_pastoral")
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    fecha = models.DateField()
    motivo = models.TextField()
    registrado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.PROTECT,
        related_name="historial_pastoral_registrado",
    )
    estado_anterior = models.CharField(max_length=20, blank=True)
    estado_nuevo = models.CharField(max_length=20, blank=True)
    activo_anterior = models.BooleanField(default=True)
    activo_nuevo = models.BooleanField(default=True)
    resumen_cierre = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ("-fecha", "-creado_en")
        verbose_name = "historial pastoral de miembro"
        verbose_name_plural = "historial pastoral de miembros"

    def __str__(self):
        return f"{self.miembro} - {self.get_tipo_display()}"

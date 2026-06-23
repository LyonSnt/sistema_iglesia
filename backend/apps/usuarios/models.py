from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Superadmin"
        ADMIN_NACIONAL = "ADMIN_NACIONAL", "Admin nacional"
        PASTOR_FILIAL = "PASTOR_FILIAL", "Pastor filial"
        ENCARGADO_FILIAL = "ENCARGADO_FILIAL", "Encargado filial"
        SECRETARIO_FILIAL = "SECRETARIO_FILIAL", "Secretario filial"
        TESORERO_FILIAL = "TESORERO_FILIAL", "Tesorero filial"
        SOLO_LECTURA = "SOLO_LECTURA", "Solo lectura"

    iglesia = models.ForeignKey(
        "iglesias.Iglesia",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="usuarios",
    )
    rol = models.CharField(max_length=40, choices=Rol.choices, default=Rol.SOLO_LECTURA)
    cedula = models.CharField(max_length=20, blank=True, unique=True, null=True)
    telefono = models.CharField(max_length=30, blank=True)
    debe_cambiar_password = models.BooleanField(default=False)

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    @property
    def es_usuario_nacional(self):
        return self.is_superuser or self.rol in {
            self.Rol.SUPERADMIN,
            self.Rol.ADMIN_NACIONAL,
        }

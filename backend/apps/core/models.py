from django.db import models


class TimeStampedModel(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveModel(models.Model):
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True


class IglesiaScopedModel(models.Model):
    iglesia = models.ForeignKey(
        "iglesias.Iglesia",
        on_delete=models.PROTECT,
        related_name="%(app_label)s_%(class)s_items",
    )

    class Meta:
        abstract = True

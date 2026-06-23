from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import Traslado


@admin.register(Traslado)
class TrasladoAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("miembro", "iglesia", "iglesia_destino", "estado", "fecha_solicitud", "fecha_respuesta")
    list_filter = ("estado", "iglesia", "iglesia_destino")
    search_fields = ("miembro__nombres", "miembro__apellidos", "iglesia__nombre", "iglesia_destino__nombre")
    readonly_fields = ("creado_en", "actualizado_en")

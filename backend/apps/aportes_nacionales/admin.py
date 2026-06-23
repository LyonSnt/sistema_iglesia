from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import AporteNacional


@admin.register(AporteNacional)
class AporteNacionalAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("iglesia", "anio", "mes", "porcentaje", "monto_base", "monto_aporte", "estado", "numero_recibo")
    list_filter = ("estado", "anio", "mes", "iglesia")
    search_fields = ("iglesia__nombre", "iglesia__codigo", "referencia_pago", "numero_recibo")
    readonly_fields = ("creado_en", "actualizado_en")

from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import AcuerdoPagoAporteNacional, AjusteAporteNacional, AporteNacional, PagoAporteNacional


@admin.register(AporteNacional)
class AporteNacionalAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("iglesia", "anio", "mes", "porcentaje", "monto_base", "monto_aporte", "estado", "numero_recibo")
    list_filter = ("estado", "anio", "mes", "iglesia")
    search_fields = ("iglesia__nombre", "iglesia__codigo", "referencia_pago", "numero_recibo")
    readonly_fields = ("creado_en", "actualizado_en")


@admin.register(AjusteAporteNacional)
class AjusteAporteNacionalAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("iglesia", "aporte", "tipo", "monto", "registrado_por", "creado_en")
    list_filter = ("tipo", "iglesia")
    search_fields = ("iglesia__nombre", "iglesia__codigo", "motivo", "aporte__numero_recibo")
    readonly_fields = ("creado_en", "actualizado_en")


@admin.register(PagoAporteNacional)
class PagoAporteNacionalAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("iglesia", "aporte", "monto", "fecha_pago", "referencia_pago", "registrado_por")
    list_filter = ("fecha_pago", "iglesia")
    search_fields = ("iglesia__nombre", "iglesia__codigo", "referencia_pago", "aporte__numero_recibo")
    readonly_fields = ("creado_en", "actualizado_en")


@admin.register(AcuerdoPagoAporteNacional)
class AcuerdoPagoAporteNacionalAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("iglesia", "aporte", "fecha_compromiso", "monto_comprometido", "estado", "registrado_por")
    list_filter = ("estado", "fecha_compromiso", "iglesia")
    search_fields = ("iglesia__nombre", "iglesia__codigo", "aporte__numero_recibo", "observacion")
    readonly_fields = ("creado_en", "actualizado_en")

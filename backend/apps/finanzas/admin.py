from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import CierreMensualFinanciero, ConceptoFinanciero, MovimientoFinanciero


@admin.register(ConceptoFinanciero)
class ConceptoFinancieroAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "tipo", "iglesia", "activo")
    list_filter = ("tipo", "activo", "iglesia")
    search_fields = ("nombre", "descripcion", "iglesia__nombre", "iglesia__codigo")


@admin.register(MovimientoFinanciero)
class MovimientoFinancieroAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("fecha", "tipo", "concepto", "monto", "iglesia", "estado")
    list_filter = ("tipo", "estado", "iglesia")
    search_fields = ("descripcion", "numero_comprobante", "concepto__nombre", "iglesia__nombre", "iglesia__codigo")
    readonly_fields = ("creado_en", "actualizado_en")


@admin.register(CierreMensualFinanciero)
class CierreMensualFinancieroAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("iglesia", "anio", "mes", "total_ingresos", "total_egresos", "saldo", "estado")
    list_filter = ("estado", "anio", "mes", "iglesia")
    search_fields = ("iglesia__nombre", "iglesia__codigo", "observacion")
    readonly_fields = ("creado_en", "actualizado_en")

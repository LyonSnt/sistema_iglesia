from django.contrib import admin

from .models import TareaPastoralTraslado, TrasladoFamiliarIntegrante, TrasladoMiembro


@admin.register(TrasladoMiembro)
class TrasladoMiembroAdmin(admin.ModelAdmin):
    list_display = (
        "miembro",
        "iglesia_origen",
        "iglesia_destino",
        "es_familiar",
        "estado",
        "recepcion_confirmada_en",
        "familia_destino_revisada_en",
        "escuela_dominical_destino_revisada_en",
        "creado_en",
    )
    list_filter = ("estado", "es_familiar", "iglesia_origen", "iglesia_destino")
    search_fields = ("miembro__nombres", "miembro__apellidos", "motivo")
    readonly_fields = (
        "creado_en",
        "actualizado_en",
        "respondido_en",
        "completado_en",
        "recepcion_confirmada_en",
        "familia_destino_revisada_en",
        "escuela_dominical_destino_revisada_en",
    )


@admin.register(TrasladoFamiliarIntegrante)
class TrasladoFamiliarIntegranteAdmin(admin.ModelAdmin):
    list_display = ("traslado", "miembro", "relacion")
    search_fields = ("miembro__nombres", "miembro__apellidos", "traslado__motivo")


@admin.register(TareaPastoralTraslado)
class TareaPastoralTrasladoAdmin(admin.ModelAdmin):
    list_display = ("traslado", "descripcion", "estado", "creada_por", "completada_por", "completada_en")
    list_filter = ("estado",)
    search_fields = ("descripcion", "traslado__miembro__nombres", "traslado__miembro__apellidos")

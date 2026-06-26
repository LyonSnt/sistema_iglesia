from django.contrib import admin

from .models import TrasladoMiembro


@admin.register(TrasladoMiembro)
class TrasladoMiembroAdmin(admin.ModelAdmin):
    list_display = (
        "miembro",
        "iglesia_origen",
        "iglesia_destino",
        "estado",
        "recepcion_confirmada_en",
        "familia_destino_revisada_en",
        "escuela_dominical_destino_revisada_en",
        "creado_en",
    )
    list_filter = ("estado", "iglesia_origen", "iglesia_destino")
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

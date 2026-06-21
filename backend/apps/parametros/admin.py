from django.contrib import admin

from .models import ParametroGeneral, Periodo


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "fecha_inicio", "fecha_fin", "cerrado", "activo")
    list_filter = ("cerrado", "activo")
    search_fields = ("nombre",)


@admin.register(ParametroGeneral)
class ParametroGeneralAdmin(admin.ModelAdmin):
    list_display = ("clave", "nombre", "valor", "tipo_dato", "activo")
    list_filter = ("tipo_dato", "activo")
    search_fields = ("clave", "nombre")

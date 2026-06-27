from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import AsignacionCargo, Cargo, HistorialAsignacionCargo


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "es_nacional", "es_sensible", "requiere_documento_posesion", "activo")
    list_filter = ("es_nacional", "es_sensible", "requiere_documento_posesion", "activo")
    search_fields = ("nombre",)


@admin.register(AsignacionCargo)
class AsignacionCargoAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("cargo", "miembro", "usuario", "iglesia", "tipo_asignacion", "fecha_inicio", "fecha_fin", "estado", "activo")
    list_filter = ("iglesia", "cargo", "tipo_asignacion", "estado", "activo")
    search_fields = ("cargo__nombre", "miembro__nombres", "miembro__apellidos", "usuario__username")


@admin.register(HistorialAsignacionCargo)
class HistorialAsignacionCargoAdmin(admin.ModelAdmin):
    list_display = ("asignacion", "tipo", "fecha", "registrado_por", "estado_anterior", "estado_nuevo")
    list_filter = ("tipo", "fecha", "asignacion__iglesia")
    search_fields = ("asignacion__cargo__nombre", "motivo")

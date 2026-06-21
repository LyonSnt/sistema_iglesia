from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import AsignacionCargo, Cargo


@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "es_nacional", "activo")
    list_filter = ("es_nacional", "activo")
    search_fields = ("nombre",)


@admin.register(AsignacionCargo)
class AsignacionCargoAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("cargo", "miembro", "usuario", "iglesia", "fecha_inicio", "fecha_fin", "estado", "activo")
    list_filter = ("iglesia", "cargo", "estado", "activo")
    search_fields = ("cargo__nombre", "miembro__nombres", "miembro__apellidos", "usuario__username")

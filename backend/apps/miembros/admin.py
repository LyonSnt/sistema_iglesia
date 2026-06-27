from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import HistorialPastoralMiembro, Miembro


@admin.register(Miembro)
class MiembroAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("apellidos", "nombres", "cedula", "iglesia", "estado", "activo")
    list_filter = ("iglesia", "estado", "sexo", "activo")
    search_fields = ("nombres", "apellidos", "cedula", "telefono")


@admin.register(HistorialPastoralMiembro)
class HistorialPastoralMiembroAdmin(admin.ModelAdmin):
    list_display = ("miembro", "tipo", "fecha", "registrado_por", "estado_anterior", "estado_nuevo")
    list_filter = ("tipo", "fecha", "miembro__iglesia")
    search_fields = ("miembro__nombres", "miembro__apellidos", "motivo")
    readonly_fields = ("creado_en", "actualizado_en")

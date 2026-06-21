from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import Miembro


@admin.register(Miembro)
class MiembroAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("apellidos", "nombres", "cedula", "iglesia", "estado", "activo")
    list_filter = ("iglesia", "estado", "sexo", "activo")
    search_fields = ("nombres", "apellidos", "cedula", "telefono")

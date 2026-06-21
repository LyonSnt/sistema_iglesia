from django.contrib import admin

from .models import Iglesia


@admin.register(Iglesia)
class IglesiaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "tipo", "zona", "estado", "activo")
    list_filter = ("tipo", "zona", "estado", "activo")
    search_fields = ("codigo", "nombre", "responsable_principal")

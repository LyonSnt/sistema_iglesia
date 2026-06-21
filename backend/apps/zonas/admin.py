from django.contrib import admin

from .models import Zona


@admin.register(Zona)
class ZonaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "codigo", "activo")
    list_filter = ("activo",)
    search_fields = ("nombre", "codigo")

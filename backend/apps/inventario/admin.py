from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import ActivoInventario, MovimientoInventario


@admin.register(ActivoInventario)
class ActivoInventarioAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("codigo", "nombre", "categoria", "iglesia", "ubicacion_actual", "estado", "activo")
    list_filter = ("estado", "categoria", "iglesia", "activo")
    search_fields = ("codigo", "nombre", "categoria", "ubicacion_actual")


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("activo", "tipo", "fecha", "iglesia", "registrado_por")
    list_filter = ("tipo", "fecha", "iglesia")
    search_fields = ("activo__codigo", "activo__nombre", "detalle")

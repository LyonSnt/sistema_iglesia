from django.contrib import admin

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "usuario", "accion", "modulo", "registro_afectado", "iglesia", "ip")
    list_filter = ("accion", "modulo", "iglesia")
    search_fields = ("usuario__username", "accion", "modulo", "registro_afectado", "motivo")
    readonly_fields = ("creado_en", "actualizado_en")

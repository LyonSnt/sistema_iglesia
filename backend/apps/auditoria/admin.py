from django.contrib import admin

from apps.core.permisos import ACCION_VER, MODULO_AUDITORIA, usuario_puede

from .models import RegistroAuditoria


@admin.register(RegistroAuditoria)
class RegistroAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("creado_en", "usuario", "accion", "modulo", "registro_afectado", "iglesia", "ip")
    list_filter = ("accion", "modulo", "iglesia")
    search_fields = ("usuario__username", "accion", "modulo", "registro_afectado", "motivo")
    readonly_fields = (
        "usuario",
        "accion",
        "modulo",
        "registro_afectado",
        "valor_anterior",
        "valor_nuevo",
        "ip",
        "iglesia",
        "motivo",
        "creado_en",
        "actualizado_en",
    )

    def has_view_permission(self, request, obj=None):
        return usuario_puede(request.user, MODULO_AUDITORIA, ACCION_VER)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

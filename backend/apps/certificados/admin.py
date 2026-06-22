from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import CertificadoEscuelaDominical


@admin.register(CertificadoEscuelaDominical)
class CertificadoEscuelaDominicalAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = (
        "numero",
        "nombre_alumno",
        "nivel_cursado",
        "iglesia",
        "fecha_emision",
        "estado",
    )
    list_filter = ("iglesia", "estado", "fecha_emision")
    search_fields = ("numero", "nombre_alumno")
    readonly_fields = (
        "iglesia",
        "resultado_promocion",
        "numero",
        "fecha_emision",
        "fecha_graduacion",
        "nombre_alumno",
        "nivel_cursado",
        "periodo_lectivo",
        "nombre_pastor",
        "nombre_director",
        "emitido_por",
        "estado",
        "anulado_por",
        "anulado_en",
        "motivo_anulacion",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

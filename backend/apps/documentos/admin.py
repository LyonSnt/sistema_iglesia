from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import DocumentoAdjunto


@admin.register(DocumentoAdjunto)
class DocumentoAdjuntoAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "tipo", "iglesia", "estado", "subido_por", "creado_en")
    list_filter = ("tipo", "estado", "iglesia")
    search_fields = ("nombre", "descripcion", "archivo")
    readonly_fields = ("content_type", "object_id", "subido_por", "anulado_por", "anulado_en")

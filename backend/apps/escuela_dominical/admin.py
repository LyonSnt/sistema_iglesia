from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin
from apps.core.iglesias import filtrar_queryset_por_iglesia, usuario_es_nacional
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.usuarios.models import Usuario

from .models import (
    AsistenciaEscuelaDominical,
    ClaseEscuelaDominical,
    MatriculaEscuelaDominical,
    NivelEscuelaDominical,
    SesionEscuelaDominical,
    ProcesoPromocionEscuelaDominical,
    ResultadoPromocionEscuelaDominical,
)


class EscuelaDominicalAdminScopeMixin:
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not usuario_es_nacional(request.user):
            if db_field.name == "iglesia":
                kwargs["queryset"] = Iglesia.objects.filter(pk=request.user.iglesia_id)
            elif db_field.name == "nivel":
                kwargs["queryset"] = NivelEscuelaDominical.objects.filter(
                    iglesia_id=request.user.iglesia_id
                )
            elif db_field.name == "maestro":
                kwargs["queryset"] = Usuario.objects.filter(
                    iglesia_id=request.user.iglesia_id,
                    is_active=True,
                )
            elif db_field.name == "clase":
                kwargs["queryset"] = ClaseEscuelaDominical.objects.filter(
                    iglesia_id=request.user.iglesia_id
                )
            elif db_field.name == "sesion":
                kwargs["queryset"] = SesionEscuelaDominical.objects.filter(
                    clase__iglesia_id=request.user.iglesia_id
                )
            elif db_field.name == "matricula":
                kwargs["queryset"] = MatriculaEscuelaDominical.objects.filter(
                    clase__iglesia_id=request.user.iglesia_id
                )
            elif db_field.name == "registrado_por":
                kwargs["queryset"] = Usuario.objects.filter(
                    iglesia_id=request.user.iglesia_id,
                    is_active=True,
                )
            elif db_field.name == "alumno":
                kwargs["queryset"] = Miembro.objects.filter(
                    iglesia_id=request.user.iglesia_id,
                    activo=True,
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(NivelEscuelaDominical)
class NivelEscuelaDominicalAdmin(
    EscuelaDominicalAdminScopeMixin,
    IglesiaScopedAdminMixin,
    admin.ModelAdmin,
):
    list_display = ("nombre", "iglesia", "edad_minima", "edad_maxima", "orden", "activo")
    list_filter = ("iglesia", "activo")
    search_fields = ("nombre",)


class MatriculaEscuelaDominicalInline(admin.TabularInline):
    model = MatriculaEscuelaDominical
    extra = 0


@admin.register(ClaseEscuelaDominical)
class ClaseEscuelaDominicalAdmin(
    EscuelaDominicalAdminScopeMixin,
    IglesiaScopedAdminMixin,
    admin.ModelAdmin,
):
    list_display = ("nombre", "nivel", "periodo", "maestro", "iglesia", "activo")
    list_filter = ("iglesia", "periodo", "nivel", "activo")
    search_fields = ("nombre", "maestro__username", "maestro__first_name", "maestro__last_name")
    inlines = (MatriculaEscuelaDominicalInline,)


@admin.register(MatriculaEscuelaDominical)
class MatriculaEscuelaDominicalAdmin(EscuelaDominicalAdminScopeMixin, admin.ModelAdmin):
    list_display = ("alumno", "clase", "fecha_inscripcion", "estado", "activo")
    list_filter = ("clase__iglesia", "clase", "estado", "activo")
    search_fields = ("alumno__nombres", "alumno__apellidos", "clase__nombre")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filtrar_queryset_por_iglesia(
            queryset,
            request.user,
            campo_iglesia="clase__iglesia",
        )


class AsistenciaEscuelaDominicalInline(admin.TabularInline):
    model = AsistenciaEscuelaDominical
    extra = 0


@admin.register(SesionEscuelaDominical)
class SesionEscuelaDominicalAdmin(EscuelaDominicalAdminScopeMixin, admin.ModelAdmin):
    list_display = ("fecha", "clase", "tema", "cerrada", "registrado_por")
    list_filter = ("clase__iglesia", "cerrada", "fecha")
    search_fields = ("clase__nombre", "tema")
    inlines = (AsistenciaEscuelaDominicalInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filtrar_queryset_por_iglesia(
            queryset,
            request.user,
            campo_iglesia="clase__iglesia",
        )


@admin.register(AsistenciaEscuelaDominical)
class AsistenciaEscuelaDominicalAdmin(EscuelaDominicalAdminScopeMixin, admin.ModelAdmin):
    list_display = ("sesion", "matricula", "estado", "observacion")
    list_filter = ("sesion__clase__iglesia", "estado")
    search_fields = ("matricula__alumno__nombres", "matricula__alumno__apellidos")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filtrar_queryset_por_iglesia(
            queryset,
            request.user,
            campo_iglesia="sesion__clase__iglesia",
        )


class ResultadoPromocionInline(admin.TabularInline):
    model = ResultadoPromocionEscuelaDominical
    extra = 0
    readonly_fields = (
        "matricula_origen",
        "edad_al_corte",
        "destino",
        "nivel_destino",
        "clase_destino",
        "matricula_destino",
        "sesiones_consideradas",
        "presentes",
        "ausentes",
        "justificados",
    )
    can_delete = False


@admin.register(ProcesoPromocionEscuelaDominical)
class ProcesoPromocionAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = (
        "fecha_corte",
        "iglesia",
        "periodo_origen",
        "periodo_destino",
        "estado",
        "confirmado_por",
    )
    list_filter = ("iglesia", "estado", "fecha_corte")
    readonly_fields = ("estado", "confirmado_por", "confirmado_en")
    inlines = (ResultadoPromocionInline,)

from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin
from apps.core.iglesias import usuario_es_nacional
from apps.miembros.models import Miembro
from apps.usuarios.models import Usuario

from .models import Ministerio, ParticipacionMinisterio


class ParticipacionMinisterioInline(admin.TabularInline):
    model = ParticipacionMinisterio
    extra = 0


@admin.register(Ministerio)
class MinisterioAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "tipo", "iglesia", "responsable", "lider", "activo")
    list_filter = ("iglesia", "tipo", "activo")
    search_fields = ("nombre", "responsable__nombres", "responsable__apellidos", "lider__username")
    inlines = (ParticipacionMinisterioInline,)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not usuario_es_nacional(request.user):
            if db_field.name == "responsable":
                kwargs["queryset"] = Miembro.objects.filter(
                    iglesia_id=request.user.iglesia_id,
                    activo=True,
                )
            elif db_field.name == "lider":
                kwargs["queryset"] = Usuario.objects.filter(
                    iglesia_id=request.user.iglesia_id,
                    is_active=True,
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ParticipacionMinisterio)
class ParticipacionMinisterioAdmin(admin.ModelAdmin):
    list_display = ("ministerio", "miembro", "cargo", "fecha_inicio", "fecha_fin", "estado", "activo")
    list_filter = ("ministerio__iglesia", "ministerio", "estado", "activo")
    search_fields = ("miembro__nombres", "miembro__apellidos", "ministerio__nombre", "cargo")

from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import Ministerio, ParticipacionMinisterio


class ParticipacionMinisterioInline(admin.TabularInline):
    model = ParticipacionMinisterio
    extra = 0


@admin.register(Ministerio)
class MinisterioAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "tipo", "iglesia", "responsable", "activo")
    list_filter = ("iglesia", "tipo", "activo")
    search_fields = ("nombre", "responsable__nombres", "responsable__apellidos")
    inlines = (ParticipacionMinisterioInline,)


@admin.register(ParticipacionMinisterio)
class ParticipacionMinisterioAdmin(admin.ModelAdmin):
    list_display = ("ministerio", "miembro", "cargo", "fecha_inicio", "fecha_fin", "estado", "activo")
    list_filter = ("ministerio__iglesia", "ministerio", "estado", "activo")
    search_fields = ("miembro__nombres", "miembro__apellidos", "ministerio__nombre", "cargo")

from django.contrib import admin

from apps.core.admin import IglesiaScopedAdminMixin

from .models import Familia, Matrimonio, MiembroFamilia


class MiembroFamiliaInline(admin.TabularInline):
    model = MiembroFamilia
    extra = 0


@admin.register(Familia)
class FamiliaAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "iglesia", "jefe_hogar", "activo")
    list_filter = ("iglesia", "activo")
    search_fields = ("nombre", "jefe_hogar__nombres", "jefe_hogar__apellidos")
    inlines = (MiembroFamiliaInline,)


@admin.register(MiembroFamilia)
class MiembroFamiliaAdmin(admin.ModelAdmin):
    list_display = ("familia", "miembro", "relacion", "activo")
    list_filter = ("relacion", "activo", "familia__iglesia")
    search_fields = ("familia__nombre", "miembro__nombres", "miembro__apellidos")


@admin.register(Matrimonio)
class MatrimonioAdmin(IglesiaScopedAdminMixin, admin.ModelAdmin):
    list_display = ("conyuge_1", "conyuge_2", "fecha_matrimonio", "iglesia", "familia", "activo")
    list_filter = ("iglesia", "activo", "fecha_matrimonio")
    search_fields = (
        "conyuge_1__nombres",
        "conyuge_1__apellidos",
        "conyuge_2__nombres",
        "conyuge_2__apellidos",
        "familia__nombre",
    )

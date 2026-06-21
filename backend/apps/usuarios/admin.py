from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Datos eclesiales", {"fields": ("iglesia", "rol", "cedula", "telefono", "debe_cambiar_password")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Datos eclesiales", {"fields": ("iglesia", "rol", "cedula", "telefono")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "iglesia", "rol", "is_active")
    list_filter = UserAdmin.list_filter + ("rol", "iglesia")
    search_fields = UserAdmin.search_fields + ("cedula", "telefono")

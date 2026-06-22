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

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return request.user.is_superuser and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser and super().has_delete_permission(request, obj)

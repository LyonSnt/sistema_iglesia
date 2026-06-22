from django.contrib import admin

from .models import Iglesia


@admin.register(Iglesia)
class IglesiaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "tipo", "zona", "estado", "activo")
    list_filter = ("tipo", "zona", "estado", "activo")
    search_fields = ("codigo", "nombre", "responsable_principal")

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

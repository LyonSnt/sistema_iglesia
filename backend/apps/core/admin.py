from django.contrib import admin

from .iglesias import filtrar_queryset_por_iglesia

class IglesiaScopedAdminMixin:
    list_filter = ("iglesia", "activo")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return filtrar_queryset_por_iglesia(queryset, request.user)

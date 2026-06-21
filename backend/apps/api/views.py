from django.db.models import Q

from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.views import APIView

from apps.cargos.models import AsignacionCargo, Cargo
from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import ACCION_VER, MODULO_CARGOS, MODULO_MIEMBROS, PermisoModuloDRF
from apps.familias.models import Familia, Matrimonio
from apps.miembros.models import Miembro

from .serializers import AsignacionCargoSerializer, CargoSerializer, FamiliaSerializer, MatrimonioSerializer, MiembroSerializer


class HealthCheckAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "service": "Ecclesia"})


class ModuloMiembrosAPIMixin:
    permission_classes = [PermisoModuloDRF]
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_VER


class ModuloCargosAPIMixin:
    permission_classes = [PermisoModuloDRF]
    modulo_permiso = MODULO_CARGOS
    accion_permiso = ACCION_VER


class MiembroListAPIView(ModuloMiembrosAPIMixin, ListAPIView):
    serializer_class = MiembroSerializer

    def get_queryset(self):
        queryset = Miembro.objects.select_related("iglesia")
        queryset = filtrar_queryset_por_iglesia(queryset, self.request.user)

        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombres__icontains=query)
                | Q(apellidos__icontains=query)
                | Q(cedula__icontains=query)
                | Q(telefono__icontains=query)
            )

        estado = self.request.query_params.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset


class MiembroRetrieveAPIView(ModuloMiembrosAPIMixin, RetrieveAPIView):
    serializer_class = MiembroSerializer

    def get_queryset(self):
        queryset = Miembro.objects.select_related("iglesia")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class FamiliaListAPIView(ModuloMiembrosAPIMixin, ListAPIView):
    serializer_class = FamiliaSerializer

    def get_queryset(self):
        queryset = Familia.objects.select_related("iglesia", "jefe_hogar").prefetch_related(
            "integrantes__miembro"
        )
        queryset = filtrar_queryset_por_iglesia(queryset, self.request.user)

        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(jefe_hogar__nombres__icontains=query)
                | Q(jefe_hogar__apellidos__icontains=query)
                | Q(telefono__icontains=query)
            )

        return queryset


class FamiliaRetrieveAPIView(ModuloMiembrosAPIMixin, RetrieveAPIView):
    serializer_class = FamiliaSerializer

    def get_queryset(self):
        queryset = Familia.objects.select_related("iglesia", "jefe_hogar").prefetch_related(
            "integrantes__miembro"
        )
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class MatrimonioListAPIView(ModuloMiembrosAPIMixin, ListAPIView):
    serializer_class = MatrimonioSerializer

    def get_queryset(self):
        queryset = Matrimonio.objects.select_related("iglesia", "conyuge_1", "conyuge_2", "familia")
        queryset = filtrar_queryset_por_iglesia(queryset, self.request.user)

        miembro_id = self.request.query_params.get("miembro", "").strip()
        if miembro_id:
            queryset = queryset.filter(Q(conyuge_1_id=miembro_id) | Q(conyuge_2_id=miembro_id))

        return queryset


class CargoListAPIView(ModuloCargosAPIMixin, ListAPIView):
    serializer_class = CargoSerializer

    def get_queryset(self):
        queryset = Cargo.objects.filter(activo=True).order_by("nombre")
        if not getattr(self.request.user, "es_usuario_nacional", False) and not getattr(
            self.request.user,
            "is_superuser",
            False,
        ):
            queryset = queryset.filter(es_nacional=False)
        return queryset


class AsignacionCargoListAPIView(ModuloCargosAPIMixin, ListAPIView):
    serializer_class = AsignacionCargoSerializer

    def get_queryset(self):
        queryset = AsignacionCargo.objects.select_related("iglesia", "cargo", "miembro", "usuario")
        queryset = filtrar_queryset_por_iglesia(queryset, self.request.user)

        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(cargo__nombre__icontains=query)
                | Q(miembro__nombres__icontains=query)
                | Q(miembro__apellidos__icontains=query)
                | Q(usuario__username__icontains=query)
            )

        estado = self.request.query_params.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset


class AsignacionCargoRetrieveAPIView(ModuloCargosAPIMixin, RetrieveAPIView):
    serializer_class = AsignacionCargoSerializer

    def get_queryset(self):
        queryset = AsignacionCargo.objects.select_related("iglesia", "cargo", "miembro", "usuario")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)

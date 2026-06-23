from django.db.models import Q

from rest_framework.response import Response
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.cargos.models import AsignacionCargo, Cargo
from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import (
    ACCION_VER,
    MODULO_CARGOS,
    MODULO_MIEMBROS,
    MODULO_MINISTERIOS,
    MODULO_TRASLADOS,
    PermisoModuloDRF,
    usuario_puede,
)
from apps.familias.models import Familia, Matrimonio
from apps.miembros.models import Miembro
from apps.ministerios.models import Ministerio, ParticipacionMinisterio
from apps.ministerios.alcance import filtrar_ministerios_por_usuario, filtrar_participaciones_por_usuario
from apps.traslados.models import TrasladoMiembro
from apps.usuarios.models import Usuario

from .serializers import (
    AsignacionCargoSerializer,
    CargoSerializer,
    FamiliaSerializer,
    MatrimonioSerializer,
    MiembroSerializer,
    MinisterioSerializer,
    ParticipacionMinisterioSerializer,
    TrasladoMiembroSerializer,
)


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


class ModuloMinisteriosAPIMixin:
    permission_classes = [PermisoModuloDRF]
    modulo_permiso = MODULO_MINISTERIOS
    accion_permiso = ACCION_VER


class PermisoConsultaTrasladosAPI(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        if getattr(user, "is_superuser", False) or getattr(user, "rol", None) == Usuario.Rol.ADMIN_NACIONAL:
            return True
        return usuario_puede(user, MODULO_TRASLADOS, ACCION_VER)


class ModuloTrasladosAPIMixin:
    permission_classes = [PermisoConsultaTrasladosAPI]


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


class MinisterioListAPIView(ModuloMinisteriosAPIMixin, ListAPIView):
    serializer_class = MinisterioSerializer

    def get_queryset(self):
        queryset = Ministerio.objects.select_related("iglesia", "responsable").prefetch_related(
            "participaciones__miembro"
        )
        queryset = filtrar_ministerios_por_usuario(queryset, self.request.user)

        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(descripcion__icontains=query)
                | Q(responsable__nombres__icontains=query)
                | Q(responsable__apellidos__icontains=query)
            )

        tipo = self.request.query_params.get("tipo", "").strip()
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        return queryset


class MinisterioRetrieveAPIView(ModuloMinisteriosAPIMixin, RetrieveAPIView):
    serializer_class = MinisterioSerializer

    def get_queryset(self):
        queryset = Ministerio.objects.select_related("iglesia", "responsable").prefetch_related(
            "participaciones__miembro"
        )
        return filtrar_ministerios_por_usuario(queryset, self.request.user)


class ParticipacionMinisterioListAPIView(ModuloMinisteriosAPIMixin, ListAPIView):
    serializer_class = ParticipacionMinisterioSerializer

    def get_queryset(self):
        queryset = ParticipacionMinisterio.objects.select_related("ministerio", "miembro")
        queryset = filtrar_participaciones_por_usuario(queryset, self.request.user)

        ministerio_id = self.request.query_params.get("ministerio", "").strip()
        if ministerio_id:
            queryset = queryset.filter(ministerio_id=ministerio_id)

        miembro_id = self.request.query_params.get("miembro", "").strip()
        if miembro_id:
            queryset = queryset.filter(miembro_id=miembro_id)

        estado = self.request.query_params.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset


class ParticipacionMinisterioRetrieveAPIView(ModuloMinisteriosAPIMixin, RetrieveAPIView):
    serializer_class = ParticipacionMinisterioSerializer

    def get_queryset(self):
        queryset = ParticipacionMinisterio.objects.select_related("ministerio", "miembro")
        return filtrar_participaciones_por_usuario(queryset, self.request.user)


class TrasladoMiembroQuerysetAPIMixin:
    def get_queryset(self):
        queryset = TrasladoMiembro.objects.select_related(
            "miembro",
            "iglesia_origen",
            "iglesia_destino",
            "solicitado_por",
            "respondido_por",
        )
        user = self.request.user
        if not (getattr(user, "is_superuser", False) or getattr(user, "rol", None) == Usuario.Rol.ADMIN_NACIONAL):
            queryset = queryset.filter(Q(iglesia_origen=user.iglesia) | Q(iglesia_destino=user.iglesia))

        estado = self.request.query_params.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        origen = self.request.query_params.get("iglesia_origen", "").strip()
        if origen:
            queryset = queryset.filter(iglesia_origen_id=origen)

        destino = self.request.query_params.get("iglesia_destino", "").strip()
        if destino:
            queryset = queryset.filter(iglesia_destino_id=destino)

        miembro = self.request.query_params.get("miembro", "").strip()
        if miembro:
            queryset = queryset.filter(miembro_id=miembro)

        desde = self.request.query_params.get("desde", "").strip()
        if desde:
            queryset = queryset.filter(creado_en__date__gte=desde)

        hasta = self.request.query_params.get("hasta", "").strip()
        if hasta:
            queryset = queryset.filter(creado_en__date__lte=hasta)

        query = self.request.query_params.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(miembro__nombres__icontains=query)
                | Q(miembro__apellidos__icontains=query)
                | Q(iglesia_origen__codigo__icontains=query)
                | Q(iglesia_origen__nombre__icontains=query)
                | Q(iglesia_destino__codigo__icontains=query)
                | Q(iglesia_destino__nombre__icontains=query)
            )

        return queryset


class TrasladoMiembroListAPIView(ModuloTrasladosAPIMixin, TrasladoMiembroQuerysetAPIMixin, ListAPIView):
    serializer_class = TrasladoMiembroSerializer


class TrasladoMiembroRetrieveAPIView(ModuloTrasladosAPIMixin, TrasladoMiembroQuerysetAPIMixin, RetrieveAPIView):
    serializer_class = TrasladoMiembroSerializer

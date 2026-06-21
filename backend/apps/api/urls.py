from django.urls import path

from .views import (
    AsignacionCargoListAPIView,
    AsignacionCargoRetrieveAPIView,
    CargoListAPIView,
    FamiliaListAPIView,
    FamiliaRetrieveAPIView,
    HealthCheckAPIView,
    MatrimonioListAPIView,
    MiembroListAPIView,
    MiembroRetrieveAPIView,
)

app_name = "api"

urlpatterns = [
    path("health/", HealthCheckAPIView.as_view(), name="health"),
    path("miembros/", MiembroListAPIView.as_view(), name="miembro-list"),
    path("miembros/<int:pk>/", MiembroRetrieveAPIView.as_view(), name="miembro-detail"),
    path("familias/", FamiliaListAPIView.as_view(), name="familia-list"),
    path("familias/<int:pk>/", FamiliaRetrieveAPIView.as_view(), name="familia-detail"),
    path("matrimonios/", MatrimonioListAPIView.as_view(), name="matrimonio-list"),
    path("cargos/", CargoListAPIView.as_view(), name="cargo-list"),
    path("asignaciones-cargos/", AsignacionCargoListAPIView.as_view(), name="asignacion-cargo-list"),
    path("asignaciones-cargos/<int:pk>/", AsignacionCargoRetrieveAPIView.as_view(), name="asignacion-cargo-detail"),
]

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
    MinisterioListAPIView,
    MinisterioRetrieveAPIView,
    ParticipacionMinisterioListAPIView,
    ParticipacionMinisterioRetrieveAPIView,
    TrasladoMiembroListAPIView,
    TrasladoMiembroRetrieveAPIView,
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
    path("ministerios/", MinisterioListAPIView.as_view(), name="ministerio-list"),
    path("ministerios/<int:pk>/", MinisterioRetrieveAPIView.as_view(), name="ministerio-detail"),
    path(
        "participaciones-ministerios/",
        ParticipacionMinisterioListAPIView.as_view(),
        name="participacion-ministerio-list",
    ),
    path(
        "participaciones-ministerios/<int:pk>/",
        ParticipacionMinisterioRetrieveAPIView.as_view(),
        name="participacion-ministerio-detail",
    ),
    path("traslados/", TrasladoMiembroListAPIView.as_view(), name="traslado-list"),
    path("traslados/<int:pk>/", TrasladoMiembroRetrieveAPIView.as_view(), name="traslado-detail"),
]

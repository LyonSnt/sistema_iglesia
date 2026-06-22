from django.urls import path

from .views import (
    ClaseCreateView,
    ClaseDetailView,
    ClaseListView,
    ClaseUpdateView,
    MatriculaCreateView,
    MatriculaUpdateView,
    NivelCreateView,
    NivelListView,
    NivelUpdateView,
    SesionCreateView,
    SesionDetailView,
    TomaAsistenciaView,
    PromocionCreateView,
    PromocionDetailView,
    PromocionListView,
)

app_name = "escuela_dominical"

urlpatterns = [
    path("", ClaseListView.as_view(), name="list"),
    path("crear/", ClaseCreateView.as_view(), name="create"),
    path("niveles/", NivelListView.as_view(), name="nivel-list"),
    path("niveles/crear/", NivelCreateView.as_view(), name="nivel-create"),
    path("niveles/<int:pk>/editar/", NivelUpdateView.as_view(), name="nivel-update"),
    path("promociones/", PromocionListView.as_view(), name="promocion-list"),
    path("promociones/crear/", PromocionCreateView.as_view(), name="promocion-create"),
    path("promociones/<int:pk>/", PromocionDetailView.as_view(), name="promocion-detail"),
    path("<int:pk>/", ClaseDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", ClaseUpdateView.as_view(), name="update"),
    path("<int:pk>/matriculas/agregar/", MatriculaCreateView.as_view(), name="matricula-add"),
    path("<int:pk>/sesiones/crear/", SesionCreateView.as_view(), name="sesion-create"),
    path(
        "<int:pk>/sesiones/<int:sesion_pk>/",
        SesionDetailView.as_view(),
        name="sesion-detail",
    ),
    path(
        "<int:pk>/sesiones/<int:sesion_pk>/asistencia/",
        TomaAsistenciaView.as_view(),
        name="asistencia",
    ),
    path(
        "<int:pk>/matriculas/<int:matricula_pk>/editar/",
        MatriculaUpdateView.as_view(),
        name="matricula-update",
    ),
]

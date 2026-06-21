from django.urls import path

from .views import (
    MiembroCreateView,
    MiembroDetailView,
    MiembroListView,
    MiembroUpdateView,
    CrearFamiliaMiembroView,
    RegistrarBautismoView,
    RegistrarFallecimientoView,
    RegistrarMatrimonioView,
    RegistrarMembresiaView,
    VincularFamiliaMiembroView,
)

app_name = "miembros"

urlpatterns = [
    path("", MiembroListView.as_view(), name="list"),
    path("crear/", MiembroCreateView.as_view(), name="create"),
    path("<int:pk>/", MiembroDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", MiembroUpdateView.as_view(), name="update"),
    path("<int:pk>/bautismo/", RegistrarBautismoView.as_view(), name="bautismo"),
    path("<int:pk>/membresia/", RegistrarMembresiaView.as_view(), name="membresia"),
    path("<int:pk>/fallecimiento/", RegistrarFallecimientoView.as_view(), name="fallecimiento"),
    path("<int:pk>/matrimonio/", RegistrarMatrimonioView.as_view(), name="matrimonio"),
    path("<int:pk>/familias/crear/", CrearFamiliaMiembroView.as_view(), name="familia_create"),
    path("<int:pk>/familias/vincular/", VincularFamiliaMiembroView.as_view(), name="familia_link"),
]

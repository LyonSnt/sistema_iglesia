from django.urls import path

from .views import (
    AgregarIntegranteFamiliaView,
    DesactivarIntegranteFamiliaView,
    FamiliaCreateView,
    FamiliaDetailView,
    FamiliaListView,
    FamiliaUpdateView,
)

app_name = "familias"

urlpatterns = [
    path("", FamiliaListView.as_view(), name="list"),
    path("crear/", FamiliaCreateView.as_view(), name="create"),
    path("<int:pk>/", FamiliaDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", FamiliaUpdateView.as_view(), name="update"),
    path("<int:pk>/integrantes/agregar/", AgregarIntegranteFamiliaView.as_view(), name="integrante_add"),
    path(
        "<int:pk>/integrantes/<int:integrante_pk>/desactivar/",
        DesactivarIntegranteFamiliaView.as_view(),
        name="integrante_deactivate",
    ),
]

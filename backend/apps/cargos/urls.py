from django.urls import path

from .views import (
    AsignacionCargoCreateView,
    AsignacionCargoDetailView,
    AsignacionCargoListView,
    AsignacionCargoUpdateView,
    AdjuntarDocumentoCargoView,
    AnularDocumentoCargoView,
    DescargarDocumentoCargoView,
    FinalizarAsignacionCargoView,
    RegistrarNombramientoCargoView,
    RegistrarPosesionCargoView,
    RegistrarReemplazoCargoView,
    RegistrarRenunciaCargoView,
)

app_name = "cargos"

urlpatterns = [
    path("", AsignacionCargoListView.as_view(), name="list"),
    path("crear/", AsignacionCargoCreateView.as_view(), name="create"),
    path("<int:pk>/", AsignacionCargoDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", AsignacionCargoUpdateView.as_view(), name="update"),
    path("<int:pk>/finalizar/", FinalizarAsignacionCargoView.as_view(), name="finalize"),
    path("<int:pk>/nombramiento/", RegistrarNombramientoCargoView.as_view(), name="nombramiento"),
    path("<int:pk>/posesion/", RegistrarPosesionCargoView.as_view(), name="posesion"),
    path("<int:pk>/renuncia/", RegistrarRenunciaCargoView.as_view(), name="renuncia"),
    path("<int:pk>/reemplazo/", RegistrarReemplazoCargoView.as_view(), name="reemplazo"),
    path("<int:pk>/documentos/subir/", AdjuntarDocumentoCargoView.as_view(), name="document-create"),
    path("<int:pk>/documentos/<int:documento_pk>/", DescargarDocumentoCargoView.as_view(), name="document-download"),
    path("<int:pk>/documentos/<int:documento_pk>/anular/", AnularDocumentoCargoView.as_view(), name="document-deactivate"),
]

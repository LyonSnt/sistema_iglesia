from django.urls import path

from .views import (
    ActivoInventarioCreateView,
    ActivoInventarioDetailView,
    ActivoInventarioListView,
    ActivoInventarioUpdateView,
    AdjuntarDocumentoInventarioView,
    AnularDocumentoInventarioView,
    BajaInventarioView,
    DescargarDocumentoInventarioView,
    MovimientoInventarioCreateView,
)

app_name = "inventario"

urlpatterns = [
    path("", ActivoInventarioListView.as_view(), name="list"),
    path("crear/", ActivoInventarioCreateView.as_view(), name="create"),
    path("<int:pk>/", ActivoInventarioDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", ActivoInventarioUpdateView.as_view(), name="update"),
    path("<int:pk>/movimiento/", MovimientoInventarioCreateView.as_view(), name="movement"),
    path("<int:pk>/baja/", BajaInventarioView.as_view(), name="deactivate"),
    path("<int:pk>/documentos/subir/", AdjuntarDocumentoInventarioView.as_view(), name="document-create"),
    path("<int:pk>/documentos/<int:documento_pk>/", DescargarDocumentoInventarioView.as_view(), name="document-download"),
    path("<int:pk>/documentos/<int:documento_pk>/anular/", AnularDocumentoInventarioView.as_view(), name="document-deactivate"),
]

from django.urls import path

from .views import (
    AnularMovimientoView,
    AdjuntarDocumentoFinanzasView,
    AnularDocumentoFinanzasView,
    CierreMensualCreateView,
    CierreMensualListView,
    ConceptoCreateView,
    DescargarDocumentoFinanzasView,
    MovimientoCreateView,
    MovimientoDetailView,
    MovimientoListView,
)

app_name = "finanzas"

urlpatterns = [
    path("", MovimientoListView.as_view(), name="list"),
    path("crear/", MovimientoCreateView.as_view(), name="create"),
    path("conceptos/crear/", ConceptoCreateView.as_view(), name="concept-create"),
    path("cierres/", CierreMensualListView.as_view(), name="cierre-list"),
    path("cierres/crear/", CierreMensualCreateView.as_view(), name="cierre-create"),
    path("<int:pk>/", MovimientoDetailView.as_view(), name="detail"),
    path("<int:pk>/anular/", AnularMovimientoView.as_view(), name="annul"),
    path("<int:pk>/documentos/subir/", AdjuntarDocumentoFinanzasView.as_view(), name="document-create"),
    path("<int:pk>/documentos/<int:documento_pk>/", DescargarDocumentoFinanzasView.as_view(), name="document-download"),
    path("<int:pk>/documentos/<int:documento_pk>/anular/", AnularDocumentoFinanzasView.as_view(), name="document-deactivate"),
]

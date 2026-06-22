from django.urls import path

from .views import (
    AnularCertificadoView,
    CertificadoListView,
    CertificadoPDFView,
    EmitirCertificadoView,
    EmitirLoteCertificadosView,
)

app_name = "certificados"

urlpatterns = [
    path("", CertificadoListView.as_view(), name="list"),
    path("emitir/<int:pk>/", EmitirCertificadoView.as_view(), name="emitir"),
    path("emitir-lote/<int:pk>/", EmitirLoteCertificadosView.as_view(), name="emitir-lote"),
    path("<int:pk>/pdf/", CertificadoPDFView.as_view(), name="pdf"),
    path("<int:pk>/anular/", AnularCertificadoView.as_view(), name="anular"),
]

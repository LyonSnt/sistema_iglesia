from django.urls import path

from .views import (
    AporteNacionalCreateView,
    AporteNacionalDetailView,
    AporteNacionalListView,
    CuentaCorrienteAportesView,
    ReciboAportePDFView,
    RegistrarPagoAporteView,
)

app_name = "aportes_nacionales"

urlpatterns = [
    path("", AporteNacionalListView.as_view(), name="list"),
    path("cuenta-corriente/", CuentaCorrienteAportesView.as_view(), name="account"),
    path("generar/", AporteNacionalCreateView.as_view(), name="create"),
    path("<int:pk>/", AporteNacionalDetailView.as_view(), name="detail"),
    path("<int:pk>/registrar-pago/", RegistrarPagoAporteView.as_view(), name="payment"),
    path("<int:pk>/recibo.pdf", ReciboAportePDFView.as_view(), name="receipt-pdf"),
]

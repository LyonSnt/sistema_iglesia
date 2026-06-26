from django.urls import path

from .views import (
    AcuerdoPagoAporteNacionalCreateView,
    AjusteAporteNacionalCreateView,
    AnularAporteNacionalView,
    AporteNacionalCreateView,
    AporteNacionalDetailView,
    AporteNacionalListView,
    CuentaCorrienteAportesView,
    ReciboAportePDFView,
    RegistrarPagoAporteView,
    TableroMorosidadAportesView,
)

app_name = "aportes_nacionales"

urlpatterns = [
    path("", AporteNacionalListView.as_view(), name="list"),
    path("tablero-morosidad/", TableroMorosidadAportesView.as_view(), name="arrears-dashboard"),
    path("cuenta-corriente/", CuentaCorrienteAportesView.as_view(), name="account"),
    path("generar/", AporteNacionalCreateView.as_view(), name="create"),
    path("<int:pk>/", AporteNacionalDetailView.as_view(), name="detail"),
    path("<int:pk>/anular/", AnularAporteNacionalView.as_view(), name="annul"),
    path("<int:pk>/ajustes/crear/", AjusteAporteNacionalCreateView.as_view(), name="adjustment-create"),
    path("<int:pk>/acuerdos/crear/", AcuerdoPagoAporteNacionalCreateView.as_view(), name="agreement-create"),
    path("<int:pk>/registrar-pago/", RegistrarPagoAporteView.as_view(), name="payment"),
    path("<int:pk>/recibo.pdf", ReciboAportePDFView.as_view(), name="receipt-pdf"),
]

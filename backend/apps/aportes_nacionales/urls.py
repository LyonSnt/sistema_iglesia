from django.urls import path

from .views import AporteNacionalCreateView, AporteNacionalDetailView, AporteNacionalListView, RegistrarPagoAporteView

app_name = "aportes_nacionales"

urlpatterns = [
    path("", AporteNacionalListView.as_view(), name="list"),
    path("generar/", AporteNacionalCreateView.as_view(), name="create"),
    path("<int:pk>/", AporteNacionalDetailView.as_view(), name="detail"),
    path("<int:pk>/registrar-pago/", RegistrarPagoAporteView.as_view(), name="payment"),
]

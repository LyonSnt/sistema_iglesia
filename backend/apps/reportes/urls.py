from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "reportes"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="reportes:finanzas", permanent=False), name="index"),
    path("traslados/", views.ReporteTrasladosView.as_view(), name="traslados"),
    path("finanzas/", views.ReporteFinanzasView.as_view(), name="finanzas"),
]

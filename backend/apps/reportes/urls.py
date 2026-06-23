from django.urls import path

from . import views

app_name = "reportes"

urlpatterns = [
    path("traslados/", views.ReporteTrasladosView.as_view(), name="traslados"),
]

from django.urls import path

from .views import (
    AprobarTrasladoView,
    CancelarTrasladoView,
    RechazarTrasladoView,
    TrasladoCreateView,
    TrasladoDetailView,
    TrasladoListView,
)

app_name = "traslados"

urlpatterns = [
    path("", TrasladoListView.as_view(), name="list"),
    path("crear/", TrasladoCreateView.as_view(), name="create"),
    path("<int:pk>/", TrasladoDetailView.as_view(), name="detail"),
    path("<int:pk>/aprobar/", AprobarTrasladoView.as_view(), name="approve"),
    path("<int:pk>/rechazar/", RechazarTrasladoView.as_view(), name="reject"),
    path("<int:pk>/cancelar/", CancelarTrasladoView.as_view(), name="cancel"),
]

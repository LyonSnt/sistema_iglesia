from django.urls import path

from . import views

app_name = "traslados"

urlpatterns = [
    path("", views.TrasladoListView.as_view(), name="list"),
    path("crear/", views.TrasladoCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TrasladoDetailView.as_view(), name="detail"),
    path("<int:pk>/aceptar/", views.AceptarTrasladoView.as_view(), name="aceptar"),
    path("<int:pk>/rechazar/", views.RechazarTrasladoView.as_view(), name="rechazar"),
    path("<int:pk>/anular/", views.AnularTrasladoView.as_view(), name="anular"),
]

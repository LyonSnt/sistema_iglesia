from django.urls import path

from .views import (
    AsignacionCargoCreateView,
    AsignacionCargoDetailView,
    AsignacionCargoListView,
    AsignacionCargoUpdateView,
    FinalizarAsignacionCargoView,
)

app_name = "cargos"

urlpatterns = [
    path("", AsignacionCargoListView.as_view(), name="list"),
    path("crear/", AsignacionCargoCreateView.as_view(), name="create"),
    path("<int:pk>/", AsignacionCargoDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", AsignacionCargoUpdateView.as_view(), name="update"),
    path("<int:pk>/finalizar/", FinalizarAsignacionCargoView.as_view(), name="finalize"),
]

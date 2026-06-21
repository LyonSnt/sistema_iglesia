from django.urls import path

from .views import (
    AgregarParticipacionMinisterioView,
    FinalizarParticipacionMinisterioView,
    MinisterioCreateView,
    MinisterioDetailView,
    MinisterioListView,
    MinisterioUpdateView,
)

app_name = "ministerios"

urlpatterns = [
    path("", MinisterioListView.as_view(), name="list"),
    path("crear/", MinisterioCreateView.as_view(), name="create"),
    path("<int:pk>/", MinisterioDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", MinisterioUpdateView.as_view(), name="update"),
    path("<int:pk>/participaciones/agregar/", AgregarParticipacionMinisterioView.as_view(), name="participacion_add"),
    path(
        "<int:pk>/participaciones/<int:participacion_pk>/finalizar/",
        FinalizarParticipacionMinisterioView.as_view(),
        name="participacion_finalize",
    ),
]

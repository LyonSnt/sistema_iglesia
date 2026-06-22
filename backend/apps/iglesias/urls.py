from django.urls import path

from .views import IglesiaListView, IglesiaUpdateView, NuevaFilialView

app_name = "iglesias"

urlpatterns = [
    path("", IglesiaListView.as_view(), name="list"),
    path("crear/", NuevaFilialView.as_view(), name="create"),
    path("<int:pk>/editar/", IglesiaUpdateView.as_view(), name="update"),
]

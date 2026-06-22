from django.urls import path

from .views import RestablecerPasswordView, UsuarioCreateView, UsuarioListView, UsuarioUpdateView

app_name = "usuarios"

urlpatterns = [
    path("", UsuarioListView.as_view(), name="list"),
    path("crear/", UsuarioCreateView.as_view(), name="create"),
    path("<int:pk>/editar/", UsuarioUpdateView.as_view(), name="update"),
    path("<int:pk>/restablecer-password/", RestablecerPasswordView.as_view(), name="password-reset"),
]

from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, FormView, ListView, UpdateView

from apps.core.iglesias import usuario_es_nacional
from apps.core.permisos import ACCION_GESTIONAR, MODULO_USUARIOS, PermisoModuloMixin

from .forms import RestablecerPasswordForm, UsuarioCreateForm, UsuarioUpdateForm
from .models import Usuario
from .politicas import filtrar_usuarios_gestionables, puede_gestionar_usuario


class UsuariosGestionMixin(PermisoModuloMixin):
    modulo_permiso = MODULO_USUARIOS
    accion_permiso = ACCION_GESTIONAR


class UsuarioListView(UsuariosGestionMixin, ListView):
    model = Usuario
    template_name = "usuarios/usuario_list.html"
    context_object_name = "usuarios"
    paginate_by = 25

    def get_queryset(self):
        queryset = filtrar_usuarios_gestionables(
            Usuario.objects.select_related("iglesia"), self.request.user
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(cedula__icontains=query)
            )
        return queryset.order_by("iglesia__nombre", "username")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        return context


class UsuarioCreateView(UsuariosGestionMixin, CreateView):
    model = Usuario
    form_class = UsuarioCreateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["es_usuario_nacional"] = usuario_es_nacional(self.request.user)
        return context


class UsuarioUpdateView(UsuariosGestionMixin, UpdateView):
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = "usuarios/usuario_form.html"
    success_url = reverse_lazy("usuarios:list")

    def get_queryset(self):
        return filtrar_usuarios_gestionables(Usuario.objects.select_related("iglesia"), self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["actor"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["es_usuario_nacional"] = usuario_es_nacional(self.request.user)
        return context


class RestablecerPasswordView(UsuariosGestionMixin, FormView):
    form_class = RestablecerPasswordForm
    template_name = "usuarios/password_form.html"

    def get_usuario(self):
        usuario = get_object_or_404(Usuario.objects.select_related("iglesia"), pk=self.kwargs["pk"])
        if not puede_gestionar_usuario(self.request.user, usuario):
            raise PermissionDenied
        return usuario

    def form_valid(self, form):
        usuario = self.get_usuario()
        usuario.set_password(form.cleaned_data["password1"])
        usuario.debe_cambiar_password = True
        usuario.save(update_fields=["password", "debe_cambiar_password"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("usuarios:update", args=[self.get_usuario().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["usuario_objetivo"] = self.get_usuario()
        return context

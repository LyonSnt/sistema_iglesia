from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from apps.core.iglesias import usuario_es_nacional
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_IGLESIAS, PermisoModuloMixin
from apps.usuarios.models import Usuario

from .forms import IglesiaUpdateForm, NuevaFilialForm
from .models import Iglesia


def puede_administrar_filiales(user):
    return bool(
        user.is_superuser
        or getattr(user, "rol", None) in {Usuario.Rol.SUPERADMIN, Usuario.Rol.ADMIN_NACIONAL}
    )


class IglesiaListView(PermisoModuloMixin, ListView):
    model = Iglesia
    template_name = "iglesias/iglesia_list.html"
    context_object_name = "iglesias"
    paginate_by = 25
    modulo_permiso = MODULO_IGLESIAS
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = Iglesia.objects.select_related("zona", "iglesia_matriz")
        if not usuario_es_nacional(self.request.user):
            queryset = queryset.filter(pk=self.request.user.iglesia_id)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(codigo__icontains=query) | Q(nombre__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["puede_administrar"] = puede_administrar_filiales(self.request.user)
        return context


class NuevaFilialView(PermisoModuloMixin, CreateView):
    model = Iglesia
    form_class = NuevaFilialForm
    template_name = "iglesias/iglesia_form.html"
    success_url = reverse_lazy("iglesias:list")
    modulo_permiso = MODULO_IGLESIAS
    accion_permiso = ACCION_GESTIONAR

    def dispatch(self, request, *args, **kwargs):
        if not puede_administrar_filiales(request.user):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class IglesiaUpdateView(PermisoModuloMixin, UpdateView):
    model = Iglesia
    form_class = IglesiaUpdateForm
    template_name = "iglesias/iglesia_form.html"
    success_url = reverse_lazy("iglesias:list")
    modulo_permiso = MODULO_IGLESIAS
    accion_permiso = ACCION_GESTIONAR

    def dispatch(self, request, *args, **kwargs):
        if not puede_administrar_filiales(request.user):
            from django.core.exceptions import PermissionDenied

            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL)

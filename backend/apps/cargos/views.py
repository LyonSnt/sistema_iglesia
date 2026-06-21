from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_CARGOS, PermisoModuloMixin, usuario_puede

from .forms import AsignacionCargoForm, FinalizarAsignacionCargoForm
from .models import AsignacionCargo


class AsignacionCargoQuerysetMixin:
    def get_queryset(self):
        queryset = AsignacionCargo.objects.select_related("iglesia", "cargo", "miembro", "usuario")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class AsignacionCargoListView(PermisoModuloMixin, ListView):
    model = AsignacionCargo
    template_name = "cargos/asignacion_list.html"
    context_object_name = "asignaciones"
    paginate_by = 20
    modulo_permiso = MODULO_CARGOS
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = AsignacionCargo.objects.select_related("iglesia", "cargo", "miembro", "usuario")
        queryset = filtrar_queryset_por_iglesia(queryset, self.request.user)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(cargo__nombre__icontains=query)
                | Q(miembro__nombres__icontains=query)
                | Q(miembro__apellidos__icontains=query)
                | Q(usuario__username__icontains=query)
            )

        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["estados"] = AsignacionCargo.Estado.choices
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_CARGOS, ACCION_GESTIONAR)
        return context


class AsignacionCargoDetailView(AsignacionCargoQuerysetMixin, PermisoModuloMixin, DetailView):
    model = AsignacionCargo
    template_name = "cargos/asignacion_detail.html"
    context_object_name = "asignacion"
    modulo_permiso = MODULO_CARGOS
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_CARGOS, ACCION_GESTIONAR)
        return context


class AsignacionCargoFormMixin(AsignacionCargoQuerysetMixin, PermisoModuloMixin):
    model = AsignacionCargo
    form_class = AsignacionCargoForm
    template_name = "cargos/asignacion_form.html"
    success_url = reverse_lazy("cargos:list")
    modulo_permiso = MODULO_CARGOS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class AsignacionCargoCreateView(AsignacionCargoFormMixin, CreateView):
    pass


class AsignacionCargoUpdateView(AsignacionCargoFormMixin, UpdateView):
    pass


class FinalizarAsignacionCargoView(AsignacionCargoQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "cargos/asignacion_finalizar_form.html"
    form_class = FinalizarAsignacionCargoForm
    modulo_permiso = MODULO_CARGOS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["asignacion"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        asignacion = self.get_object()
        asignacion.fecha_fin = form.cleaned_data["fecha_fin"]
        asignacion.estado = AsignacionCargo.Estado.FINALIZADO
        if form.cleaned_data["observacion"]:
            asignacion.observacion = form.cleaned_data["observacion"]
        asignacion.save(update_fields=["fecha_fin", "estado", "observacion"])
        return redirect("cargos:detail", pk=asignacion.pk)

    def get_success_url(self):
        return reverse("cargos:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["asignacion"] = self.get_object()
        return context

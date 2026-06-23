from django.db.models import Q, Sum
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import (
    ACCION_GESTIONAR,
    ACCION_VER,
    MODULO_APORTES_NACIONALES,
    PermisoModuloMixin,
    usuario_puede,
)

from .forms import AporteNacionalForm, RegistrarPagoAporteForm
from .models import AporteNacional
from .servicios import registrar_pago_aporte


class AporteQuerysetMixin:
    def get_queryset(self):
        queryset = AporteNacional.objects.select_related("iglesia", "cierre", "generado_por")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class AporteNacionalListView(AporteQuerysetMixin, PermisoModuloMixin, ListView):
    model = AporteNacional
    template_name = "aportes_nacionales/aporte_list.html"
    context_object_name = "aportes"
    paginate_by = 20
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(Q(iglesia__nombre__icontains=query) | Q(iglesia__codigo__icontains=query))
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)
        anio = self.request.GET.get("anio", "").strip()
        if anio:
            queryset = queryset.filter(anio=anio)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["anio"] = self.request.GET.get("anio", "").strip()
        context["estados"] = AporteNacional.Estado.choices
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_APORTES_NACIONALES, ACCION_GESTIONAR)
        base = self.get_queryset()
        context["total_pendiente"] = base.filter(estado=AporteNacional.Estado.PENDIENTE).aggregate(total=Sum("monto_aporte"))["total"] or 0
        context["total_pagado"] = base.filter(estado=AporteNacional.Estado.PAGADO).aggregate(total=Sum("monto_aporte"))["total"] or 0
        return context


class AporteNacionalDetailView(AporteQuerysetMixin, PermisoModuloMixin, DetailView):
    model = AporteNacional
    template_name = "aportes_nacionales/aporte_detail.html"
    context_object_name = "aporte"
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_APORTES_NACIONALES, ACCION_GESTIONAR)
        return context


class AporteNacionalCreateView(PermisoModuloMixin, CreateView):
    model = AporteNacional
    form_class = AporteNacionalForm
    template_name = "aportes_nacionales/aporte_form.html"
    success_url = reverse_lazy("aportes_nacionales:list")
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_GESTIONAR

    def form_valid(self, form):
        aporte = form.save(commit=False)
        aporte.generado_por = self.request.user
        aporte.save()
        self.object = aporte
        return redirect(self.get_success_url())


class RegistrarPagoAporteView(AporteQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "aportes_nacionales/aporte_pago_form.html"
    form_class = RegistrarPagoAporteForm
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = self.get_queryset().get(pk=self.kwargs["pk"])
        return self.object

    def dispatch(self, request, *args, **kwargs):
        aporte = self.get_object()
        if aporte.estado != AporteNacional.Estado.PENDIENTE:
            return redirect("aportes_nacionales:detail", pk=aporte.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        aporte = registrar_pago_aporte(
            self.get_object(),
            self.request.user,
            form.cleaned_data["fecha_pago"],
            form.cleaned_data["referencia_pago"],
            form.cleaned_data["observacion"],
        )
        return redirect("aportes_nacionales:detail", pk=aporte.pk)

    def get_success_url(self):
        return reverse("aportes_nacionales:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["aporte"] = self.get_object()
        return context

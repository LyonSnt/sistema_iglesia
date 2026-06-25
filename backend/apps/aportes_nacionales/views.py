from django.db.models import Q, Sum
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.core.iglesias import filtrar_queryset_por_iglesia, usuario_es_nacional
from apps.core.permisos import (
    ACCION_GESTIONAR,
    ACCION_VER,
    MODULO_APORTES_NACIONALES,
    PermisoModuloMixin,
    usuario_puede,
)
from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario

from .forms import AporteNacionalForm, RegistrarPagoAporteForm
from .models import AporteNacional
from .pdf import generar_pdf_recibo_aporte
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
        context["puede_registrar_pagos"] = usuario_puede_registrar_pago_aporte(self.request.user)
        base = self.get_queryset()
        context["total_pendiente"] = base.filter(estado=AporteNacional.Estado.PENDIENTE).aggregate(total=Sum("monto_aporte"))["total"] or 0
        context["total_pagado"] = base.filter(estado=AporteNacional.Estado.PAGADO).aggregate(total=Sum("monto_aporte"))["total"] or 0
        return context


class CuentaCorrienteAportesView(AporteQuerysetMixin, PermisoModuloMixin, ListView):
    model = AporteNacional
    template_name = "aportes_nacionales/cuenta_corriente.html"
    context_object_name = "aportes"
    paginate_by = 30
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = super().get_queryset().select_related("registrado_pago_por")
        iglesia = self.request.GET.get("iglesia", "").strip()
        if iglesia and usuario_es_nacional(self.request.user):
            queryset = queryset.filter(iglesia_id=iglesia)
        anio = self.request.GET.get("anio", "").strip()
        if anio:
            queryset = queryset.filter(anio=anio)
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset.order_by("iglesia__nombre", "-anio", "-mes")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base = self.get_queryset()
        total_generado = base.exclude(estado=AporteNacional.Estado.ANULADO).aggregate(
            total=Sum("monto_aporte")
        )["total"] or 0
        total_pagado = base.filter(estado=AporteNacional.Estado.PAGADO).aggregate(
            total=Sum("monto_aporte")
        )["total"] or 0
        total_pendiente = base.filter(estado=AporteNacional.Estado.PENDIENTE).aggregate(
            total=Sum("monto_aporte")
        )["total"] or 0
        context["total_generado"] = total_generado
        context["total_pagado"] = total_pagado
        context["total_pendiente"] = total_pendiente
        context["saldo"] = total_pendiente
        context["iglesia"] = self.request.GET.get("iglesia", "").strip()
        context["anio"] = self.request.GET.get("anio", "").strip()
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["estados"] = AporteNacional.Estado.choices
        es_usuario_nacional = usuario_es_nacional(self.request.user)
        context["es_usuario_nacional"] = es_usuario_nacional
        context["iglesias"] = (
            Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL, activo=True).order_by("nombre")
            if es_usuario_nacional
            else Iglesia.objects.none()
        )
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
        context["puede_registrar_pago"] = usuario_puede_registrar_pago_aporte(self.request.user)
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
    accion_permiso = ACCION_VER

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = self.get_queryset().get(pk=self.kwargs["pk"])
        return self.object

    def dispatch(self, request, *args, **kwargs):
        if not usuario_puede_registrar_pago_aporte(request.user):
            raise PermissionDenied
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


class ReciboAportePDFView(AporteQuerysetMixin, PermisoModuloMixin, View):
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_VER

    def get(self, request, pk):
        aporte = get_object_or_404(
            self.get_queryset().select_related("registrado_pago_por"),
            pk=pk,
            estado=AporteNacional.Estado.PAGADO,
        )
        response = HttpResponse(generar_pdf_recibo_aporte(aporte), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{aporte.numero_recibo}.pdf"'
        return response


def usuario_puede_registrar_pago_aporte(user):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return getattr(user, "rol", None) == Usuario.Rol.ADMIN_NACIONAL

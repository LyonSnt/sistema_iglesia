from django.db.models import Q, Sum
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView, TemplateView

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

from .forms import (
    AcuerdoPagoAporteNacionalForm,
    AjusteAporteNacionalForm,
    AnularAporteNacionalForm,
    AporteNacionalForm,
    RegistrarPagoAporteForm,
)
from .models import AcuerdoPagoAporteNacional, AjusteAporteNacional, AporteNacional, PagoAporteNacional
from .pdf import generar_pdf_recibo_aporte
from .servicios import (
    anular_aporte_pendiente,
    registrar_acuerdo_pago_aporte,
    registrar_ajuste_aporte_pagado,
    registrar_pago_aporte,
)


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
        context["total_pendiente"] = sum(
            aporte.saldo_pendiente for aporte in base.exclude(estado=AporteNacional.Estado.ANULADO)
        )
        context["total_pagado"] = total_pagado_aportes(base)
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
        total_pagado = total_pagado_aportes(base)
        total_pendiente = sum(
            aporte.saldo_pendiente for aporte in base.exclude(estado=AporteNacional.Estado.ANULADO)
        )
        ajustes = AjusteAporteNacional.objects.filter(aporte__in=base)
        total_ajustes_cargo = ajustes.filter(tipo=AjusteAporteNacional.Tipo.CARGO).aggregate(
            total=Sum("monto")
        )["total"] or 0
        total_ajustes_abono = ajustes.filter(tipo=AjusteAporteNacional.Tipo.ABONO).aggregate(
            total=Sum("monto")
        )["total"] or 0
        context["total_generado"] = total_generado
        context["total_pagado"] = total_pagado
        context["total_pendiente"] = total_pendiente
        context["total_ajustes_cargo"] = total_ajustes_cargo
        context["total_ajustes_abono"] = total_ajustes_abono
        context["saldo"] = total_pendiente
        context["total_mora"] = sum(
            aporte.saldo_pendiente
            for aporte in base.filter(
                estado=AporteNacional.Estado.PENDIENTE,
                fecha_vencimiento__lt=timezone.localdate(),
            )
        )
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


class TableroMorosidadAportesView(AporteQuerysetMixin, PermisoModuloMixin, TemplateView):
    template_name = "aportes_nacionales/tablero_morosidad.html"
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = super().get_queryset().select_related("iglesia__zona").prefetch_related("acuerdos", "pagos", "ajustes")

        iglesia = self.request.GET.get("iglesia", "").strip()
        if iglesia and usuario_es_nacional(self.request.user):
            queryset = queryset.filter(iglesia_id=iglesia)

        zona = self.request.GET.get("zona", "").strip()
        if zona and usuario_es_nacional(self.request.user):
            queryset = queryset.filter(iglesia__zona_id=zona)

        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset.exclude(estado=AporteNacional.Estado.ANULADO).order_by(
            "iglesia__nombre",
            "fecha_vencimiento",
            "-anio",
            "-mes",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.localdate()
        aportes = list(self.get_queryset())
        filas = [_fila_morosidad(aporte, hoy) for aporte in aportes if aporte.saldo_pendiente > 0]

        context["filas"] = filas[:200]
        context["total_aportes"] = len(filas)
        context["total_pendiente"] = sum(fila["saldo"] for fila in filas)
        context["total_mora"] = sum(fila["saldo"] for fila in filas if fila["vencido"])
        context["total_con_acuerdo"] = sum(1 for fila in filas if fila["acuerdo_vigente"] is not None)
        context["iglesias"] = (
            Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL, activo=True).select_related("zona").order_by("nombre")
            if usuario_es_nacional(self.request.user)
            else Iglesia.objects.none()
        )
        context["zonas"] = _zonas_filiales()
        context["estados"] = AporteNacional.Estado.choices
        context["es_usuario_nacional"] = usuario_es_nacional(self.request.user)
        context["filtros"] = {
            "iglesia": self.request.GET.get("iglesia", "").strip(),
            "zona": self.request.GET.get("zona", "").strip(),
            "estado": self.request.GET.get("estado", "").strip(),
        }
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
        context["puede_anular"] = (
            context["puede_gestionar"]
            and self.object.estado == AporteNacional.Estado.PENDIENTE
            and self.object.total_pagos == 0
        )
        context["puede_ajustar"] = (
            context["puede_gestionar"] and self.object.estado == AporteNacional.Estado.PAGADO
        )
        context["puede_acordar"] = (
            context["puede_gestionar"] and self.object.estado == AporteNacional.Estado.PENDIENTE
        )
        context["ajustes"] = self.object.ajustes.select_related("registrado_por")
        context["pagos"] = self.object.pagos.select_related("registrado_por")
        context["acuerdos"] = self.object.acuerdos.select_related("registrado_por")
        context["saldo_pendiente"] = self.object.saldo_pendiente
        context["esta_vencido"] = (
            self.object.estado == AporteNacional.Estado.PENDIENTE
            and self.object.fecha_vencimiento is not None
            and self.object.fecha_vencimiento < timezone.localdate()
        )
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["aporte"] = self.get_object()
        return kwargs

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
            form.cleaned_data["monto"],
        )
        return redirect("aportes_nacionales:detail", pk=aporte.pk)

    def get_success_url(self):
        return reverse("aportes_nacionales:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["aporte"] = self.get_object()
        return context


class AnularAporteNacionalView(AporteQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "aportes_nacionales/aporte_anular.html"
    form_class = AnularAporteNacionalForm
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
        aporte = anular_aporte_pendiente(
            self.get_object(),
            self.request.user,
            form.cleaned_data["motivo_anulacion"],
        )
        return redirect("aportes_nacionales:detail", pk=aporte.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["aporte"] = self.get_object()
        return context


class AjusteAporteNacionalCreateView(AporteQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "aportes_nacionales/aporte_ajuste_form.html"
    form_class = AjusteAporteNacionalForm
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = self.get_queryset().get(pk=self.kwargs["pk"])
        return self.object

    def dispatch(self, request, *args, **kwargs):
        aporte = self.get_object()
        if aporte.estado != AporteNacional.Estado.PAGADO:
            return redirect("aportes_nacionales:detail", pk=aporte.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        registrar_ajuste_aporte_pagado(
            self.get_object(),
            self.request.user,
            form.cleaned_data["tipo"],
            form.cleaned_data["monto"],
            form.cleaned_data["motivo"],
            form.cleaned_data["observacion"],
        )
        return redirect("aportes_nacionales:detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["aporte"] = self.get_object()
        return context


class AcuerdoPagoAporteNacionalCreateView(AporteQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "aportes_nacionales/acuerdo_pago_form.html"
    form_class = AcuerdoPagoAporteNacionalForm
    modulo_permiso = MODULO_APORTES_NACIONALES
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = self.get_queryset().get(pk=self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["aporte"] = self.get_object()
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        aporte = self.get_object()
        if aporte.estado != AporteNacional.Estado.PENDIENTE:
            return redirect("aportes_nacionales:detail", pk=aporte.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        registrar_acuerdo_pago_aporte(
            self.get_object(),
            self.request.user,
            form.cleaned_data["fecha_compromiso"],
            form.cleaned_data["monto_comprometido"],
            form.cleaned_data["observacion"],
        )
        return redirect("aportes_nacionales:detail", pk=self.get_object().pk)

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


def total_pagado_aportes(aportes):
    total = 0
    for aporte in aportes:
        pagos = aporte.total_pagos
        if pagos:
            total += pagos
        elif aporte.estado == AporteNacional.Estado.PAGADO:
            total += aporte.monto_aporte
    return total


def _fila_morosidad(aporte, hoy):
    acuerdo_vigente = next(
        (acuerdo for acuerdo in aporte.acuerdos.all() if acuerdo.estado == AcuerdoPagoAporteNacional.Estado.VIGENTE),
        None,
    )
    vencido = (
        aporte.estado == AporteNacional.Estado.PENDIENTE
        and aporte.fecha_vencimiento is not None
        and aporte.fecha_vencimiento < hoy
        and aporte.saldo_pendiente > 0
    )
    return {
        "aporte": aporte,
        "saldo": aporte.saldo_pendiente,
        "pagado": aporte.total_pagos,
        "vencido": vencido,
        "acuerdo_vigente": acuerdo_vigente,
    }


def _zonas_filiales():
    return (
        Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL, activo=True, zona__isnull=False)
        .values("zona_id", "zona__nombre")
        .distinct()
        .order_by("zona__nombre")
    )

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, ListView

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import (
    ACCION_GESTIONAR,
    ACCION_VER,
    MODULO_CERTIFICADOS,
    PermisoModuloMixin,
    usuario_puede,
)
from apps.escuela_dominical.models import (
    ProcesoPromocionEscuelaDominical,
    ResultadoPromocionEscuelaDominical,
)

from .forms import AnularCertificadoForm
from .models import CertificadoEscuelaDominical
from .pdf import generar_pdf_certificado
from .servicios import anular_certificado, emitir_certificado, emitir_certificados_proceso


class CertificadoPermisoMixin(PermisoModuloMixin):
    modulo_permiso = MODULO_CERTIFICADOS


class CertificadoQuerysetMixin:
    def get_queryset(self):
        queryset = CertificadoEscuelaDominical.objects.select_related(
            "iglesia", "resultado_promocion", "emitido_por", "anulado_por"
        )
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class CertificadoListView(CertificadoQuerysetMixin, CertificadoPermisoMixin, ListView):
    model = CertificadoEscuelaDominical
    template_name = "certificados/certificado_list.html"
    context_object_name = "certificados"
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        puede_gestionar = usuario_puede(
            self.request.user, MODULO_CERTIFICADOS, ACCION_GESTIONAR
        )
        context["puede_gestionar"] = puede_gestionar
        if puede_gestionar:
            pendientes = ResultadoPromocionEscuelaDominical.objects.filter(
                proceso__estado=ProcesoPromocionEscuelaDominical.Estado.CONFIRMADO,
                certificado__isnull=True,
            ).select_related(
                "proceso__iglesia",
                "proceso__periodo_origen",
                "matricula_origen__alumno",
                "matricula_origen__clase__nivel",
            )
            context["pendientes"] = filtrar_queryset_por_iglesia(
                pendientes, self.request.user, campo_iglesia="proceso__iglesia"
            )
            procesos = ProcesoPromocionEscuelaDominical.objects.filter(
                estado=ProcesoPromocionEscuelaDominical.Estado.CONFIRMADO,
                resultados__certificado__isnull=True,
            ).select_related("iglesia", "periodo_origen", "periodo_destino").distinct()
            context["procesos_pendientes"] = filtrar_queryset_por_iglesia(
                procesos, self.request.user
            )
        return context


class EmitirCertificadoView(CertificadoPermisoMixin, View):
    accion_permiso = ACCION_GESTIONAR

    def post(self, request, pk):
        resultados = filtrar_queryset_por_iglesia(
            ResultadoPromocionEscuelaDominical.objects.select_related("proceso__iglesia"),
            request.user,
            campo_iglesia="proceso__iglesia",
        )
        resultado = get_object_or_404(resultados, pk=pk)
        try:
            certificado = emitir_certificado(resultado, request.user)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
            return redirect("certificados:list")
        messages.success(request, f"Certificado {certificado.numero} emitido.")
        return redirect("certificados:pdf", pk=certificado.pk)


class EmitirLoteCertificadosView(CertificadoPermisoMixin, View):
    accion_permiso = ACCION_GESTIONAR

    def post(self, request, pk):
        procesos = filtrar_queryset_por_iglesia(
            ProcesoPromocionEscuelaDominical.objects.all(), request.user
        )
        proceso = get_object_or_404(
            procesos, pk=pk, estado=ProcesoPromocionEscuelaDominical.Estado.CONFIRMADO
        )
        try:
            certificados = emitir_certificados_proceso(proceso, request.user)
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        else:
            messages.success(request, f"Se emitieron {len(certificados)} certificados.")
        return redirect("certificados:list")


class CertificadoPDFView(CertificadoQuerysetMixin, CertificadoPermisoMixin, View):
    accion_permiso = ACCION_VER

    def get(self, request, pk):
        certificado = get_object_or_404(self.get_queryset(), pk=pk)
        response = HttpResponse(generar_pdf_certificado(certificado), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{certificado.numero}.pdf"'
        return response


class AnularCertificadoView(CertificadoQuerysetMixin, CertificadoPermisoMixin, FormView):
    form_class = AnularCertificadoForm
    template_name = "certificados/certificado_anular.html"
    accion_permiso = ACCION_GESTIONAR

    def get_certificado(self):
        if not hasattr(self, "certificado"):
            self.certificado = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.certificado

    def form_valid(self, form):
        anular_certificado(
            self.get_certificado(), self.request.user, form.cleaned_data["motivo"]
        )
        messages.success(self.request, "Certificado anulado.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("certificados:list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["certificado"] = self.get_certificado()
        return context

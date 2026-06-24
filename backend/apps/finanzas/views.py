from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_FINANZAS, PermisoModuloMixin, usuario_puede
from apps.documentos.forms import AnularDocumentoAdjuntoForm, DocumentoAdjuntoForm
from apps.documentos.models import DocumentoAdjunto

from .forms import AnularMovimientoForm, CierreMensualFinancieroForm, ConceptoFinancieroForm, MovimientoFinancieroForm, mes_esta_cerrado
from .models import CierreMensualFinanciero, ConceptoFinanciero, MovimientoFinanciero, TipoMovimiento


class FinanzasQuerysetMixin:
    def get_queryset(self):
        queryset = MovimientoFinanciero.objects.select_related("iglesia", "concepto", "registrado_por", "anulado_por")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class MovimientoListView(FinanzasQuerysetMixin, PermisoModuloMixin, ListView):
    model = MovimientoFinanciero
    template_name = "finanzas/movimiento_list.html"
    context_object_name = "movimientos"
    paginate_by = 20
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(descripcion__icontains=query)
                | Q(numero_comprobante__icontains=query)
                | Q(concepto__nombre__icontains=query)
            )
        tipo = self.request.GET.get("tipo", "").strip()
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context["q"] = self.request.GET.get("q", "").strip()
        context["tipo"] = self.request.GET.get("tipo", "").strip()
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["tipos"] = TipoMovimiento.choices
        context["estados"] = MovimientoFinanciero.Estado.choices
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_FINANZAS, ACCION_GESTIONAR)
        total_ingresos = queryset.filter(
            tipo=TipoMovimiento.INGRESO,
            estado=MovimientoFinanciero.Estado.REGISTRADO,
        ).aggregate(total=Sum("monto"))["total"] or 0
        total_egresos = queryset.filter(
            tipo=TipoMovimiento.EGRESO,
            estado=MovimientoFinanciero.Estado.REGISTRADO,
        ).aggregate(total=Sum("monto"))["total"] or 0
        context["total_ingresos"] = total_ingresos
        context["total_egresos"] = total_egresos
        context["saldo"] = total_ingresos - total_egresos
        return context


class MovimientoDetailView(FinanzasQuerysetMixin, PermisoModuloMixin, DetailView):
    model = MovimientoFinanciero
    template_name = "finanzas/movimiento_detail.html"
    context_object_name = "movimiento"
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movimiento = self.object
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_FINANZAS, ACCION_GESTIONAR)
        context["puede_anular"] = (
            context["puede_gestionar"]
            and movimiento.estado == MovimientoFinanciero.Estado.REGISTRADO
            and not mes_esta_cerrado(movimiento.iglesia, movimiento.fecha.year, movimiento.fecha.month)
        )
        context["documentos"] = documentos_movimiento(movimiento)
        context["puede_gestionar_documentos"] = context["puede_gestionar"]
        context["documento_create_url"] = reverse("finanzas:document-create", args=[movimiento.pk])
        context["documento_download_name"] = "finanzas:document-download"
        context["documento_deactivate_name"] = "finanzas:document-deactivate"
        return context


class MovimientoCreateView(PermisoModuloMixin, CreateView):
    model = MovimientoFinanciero
    form_class = MovimientoFinancieroForm
    template_name = "finanzas/movimiento_form.html"
    success_url = reverse_lazy("finanzas:list")
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ConceptoCreateView(PermisoModuloMixin, CreateView):
    model = ConceptoFinanciero
    form_class = ConceptoFinancieroForm
    template_name = "finanzas/concepto_form.html"
    success_url = reverse_lazy("finanzas:list")
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class AnularMovimientoView(FinanzasQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "finanzas/movimiento_anular.html"
    form_class = AnularMovimientoForm
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def dispatch(self, request, *args, **kwargs):
        movimiento = self.get_object()
        if movimiento.estado != MovimientoFinanciero.Estado.REGISTRADO or mes_esta_cerrado(
            movimiento.iglesia,
            movimiento.fecha.year,
            movimiento.fecha.month,
        ):
            return redirect("finanzas:detail", pk=movimiento.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        movimiento = self.get_object()
        movimiento.estado = MovimientoFinanciero.Estado.ANULADO
        movimiento.fecha_anulacion = form.cleaned_data["fecha_anulacion"]
        movimiento.motivo_anulacion = form.cleaned_data["motivo_anulacion"]
        movimiento.anulado_por = self.request.user
        movimiento.save(update_fields=["estado", "fecha_anulacion", "motivo_anulacion", "anulado_por"])
        return redirect("finanzas:detail", pk=movimiento.pk)

    def get_success_url(self):
        return reverse("finanzas:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movimiento"] = self.get_object()
        return context


class CierreQuerysetMixin:
    def get_queryset(self):
        queryset = CierreMensualFinanciero.objects.select_related("iglesia", "cerrado_por")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class CierreMensualListView(CierreQuerysetMixin, PermisoModuloMixin, ListView):
    model = CierreMensualFinanciero
    template_name = "finanzas/cierre_list.html"
    context_object_name = "cierres"
    paginate_by = 20
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = super().get_queryset()
        anio = self.request.GET.get("anio", "").strip()
        if anio:
            queryset = queryset.filter(anio=anio)
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["anio"] = self.request.GET.get("anio", "").strip()
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["estados"] = CierreMensualFinanciero.Estado.choices
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_FINANZAS, ACCION_GESTIONAR)
        return context


class CierreMensualCreateView(PermisoModuloMixin, CreateView):
    model = CierreMensualFinanciero
    form_class = CierreMensualFinancieroForm
    template_name = "finanzas/cierre_form.html"
    success_url = reverse_lazy("finanzas:cierre-list")
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        cierre = form.save(commit=False)
        cierre.cerrado_por = self.request.user
        movimientos = MovimientoFinanciero.objects.filter(
            iglesia=cierre.iglesia,
            fecha__year=cierre.anio,
            fecha__month=cierre.mes,
            estado=MovimientoFinanciero.Estado.REGISTRADO,
        )
        total_ingresos = movimientos.filter(tipo=TipoMovimiento.INGRESO).aggregate(total=Sum("monto"))["total"] or 0
        total_egresos = movimientos.filter(tipo=TipoMovimiento.EGRESO).aggregate(total=Sum("monto"))["total"] or 0
        cierre.total_ingresos = total_ingresos
        cierre.total_egresos = total_egresos
        cierre.saldo = total_ingresos - total_egresos
        cierre.save()
        self.object = cierre
        return redirect(self.get_success_url())


class AdjuntarDocumentoFinanzasView(FinanzasQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = DocumentoAdjuntoForm
    template_name = "documentos/documento_form.html"
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["objeto"] = self.get_object()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return redirect("finanzas:detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        movimiento = self.get_object()
        context = super().get_context_data(**kwargs)
        context["seccion"] = "Finanzas locales"
        context["objeto_titulo"] = f"{movimiento.concepto.nombre} - {movimiento.fecha:%Y-%m-%d}"
        context["cancel_url"] = reverse("finanzas:detail", args=[movimiento.pk])
        return context


class DescargarDocumentoFinanzasView(FinanzasQuerysetMixin, PermisoModuloMixin, FormView):
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_VER

    def get(self, request, pk, documento_pk):
        movimiento = get_object_or_404(self.get_queryset(), pk=pk)
        documento = get_object_or_404(
            documentos_movimiento(movimiento),
            pk=documento_pk,
            estado=DocumentoAdjunto.Estado.ACTIVO,
        )
        return FileResponse(documento.archivo.open("rb"), as_attachment=False, filename=documento.archivo.name.split("/")[-1])


class AnularDocumentoFinanzasView(FinanzasQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = AnularDocumentoAdjuntoForm
    template_name = "documentos/documento_anular.html"
    modulo_permiso = MODULO_FINANZAS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_documento(self):
        if not hasattr(self, "documento"):
            self.documento = get_object_or_404(
                documentos_movimiento(self.get_object()),
                pk=self.kwargs["documento_pk"],
                estado=DocumentoAdjunto.Estado.ACTIVO,
            )
        return self.documento

    def form_valid(self, form):
        documento = self.get_documento()
        documento.estado = DocumentoAdjunto.Estado.ANULADO
        documento.anulado_por = self.request.user
        documento.anulado_en = timezone_now()
        documento.motivo_anulacion = form.cleaned_data["motivo"]
        documento.full_clean()
        documento.save(update_fields=["estado", "anulado_por", "anulado_en", "motivo_anulacion", "actualizado_en"])
        return redirect("finanzas:detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        movimiento = self.get_object()
        context = super().get_context_data(**kwargs)
        context["seccion"] = "Finanzas locales"
        context["documento"] = self.get_documento()
        context["cancel_url"] = reverse("finanzas:detail", args=[movimiento.pk])
        return context


def documentos_movimiento(movimiento):
    return DocumentoAdjunto.objects.filter(
        iglesia=movimiento.iglesia,
        content_type=ContentType.objects.get_for_model(MovimientoFinanciero),
        object_id=movimiento.pk,
    ).select_related("subido_por", "anulado_por")


def timezone_now():
    from django.utils import timezone

    return timezone.now()

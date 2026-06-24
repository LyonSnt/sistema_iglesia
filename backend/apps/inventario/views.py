from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_INVENTARIO, PermisoModuloMixin, usuario_puede
from apps.documentos.forms import AnularDocumentoAdjuntoForm, DocumentoAdjuntoForm
from apps.documentos.models import DocumentoAdjunto

from .forms import ActivoInventarioForm, BajaInventarioForm, MovimientoInventarioForm
from .models import ActivoInventario, MovimientoInventario


class InventarioQuerysetMixin:
    def get_queryset(self):
        queryset = ActivoInventario.objects.select_related("iglesia", "responsable_actual")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class ActivoInventarioListView(InventarioQuerysetMixin, PermisoModuloMixin, ListView):
    model = ActivoInventario
    template_name = "inventario/activo_list.html"
    context_object_name = "activos"
    paginate_by = 20
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query)
                | Q(nombre__icontains=query)
                | Q(categoria__icontains=query)
                | Q(ubicacion_actual__icontains=query)
            )
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        conteos = {item["estado"]: item["total"] for item in queryset.values("estado").annotate(total=Count("id"))}
        context["q"] = self.request.GET.get("q", "").strip()
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["estados"] = ActivoInventario.Estado.choices
        context["conteos_resumen"] = [
            {"estado": estado, "label": label, "total": conteos.get(estado, 0)}
            for estado, label in ActivoInventario.Estado.choices
        ]
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_INVENTARIO, ACCION_GESTIONAR)
        return context


class ActivoInventarioDetailView(InventarioQuerysetMixin, PermisoModuloMixin, DetailView):
    model = ActivoInventario
    template_name = "inventario/activo_detail.html"
    context_object_name = "activo"
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movimientos"] = self.object.movimientos.select_related(
            "registrado_por",
            "responsable_anterior",
            "responsable_nuevo",
        )[:25]
        context["documentos"] = documentos_activo(self.object)
        puede_gestionar = usuario_puede(self.request.user, MODULO_INVENTARIO, ACCION_GESTIONAR)
        context["puede_gestionar"] = puede_gestionar
        context["puede_dar_baja"] = puede_gestionar and self.object.estado != ActivoInventario.Estado.DADO_DE_BAJA
        return context


class ActivoInventarioCreateView(PermisoModuloMixin, CreateView):
    model = ActivoInventario
    form_class = ActivoInventarioForm
    template_name = "inventario/activo_form.html"
    success_url = reverse_lazy("inventario:list")
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ActivoInventarioUpdateView(InventarioQuerysetMixin, PermisoModuloMixin, UpdateView):
    model = ActivoInventario
    form_class = ActivoInventarioForm
    template_name = "inventario/activo_form.html"
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse("inventario:detail", args=[self.object.pk])


class MovimientoInventarioCreateView(InventarioQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = MovimientoInventarioForm
    template_name = "inventario/movimiento_form.html"
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_GESTIONAR

    def get_activo(self):
        if not hasattr(self, "activo"):
            self.activo = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.activo

    def dispatch(self, request, *args, **kwargs):
        activo = self.get_activo()
        if activo.estado == ActivoInventario.Estado.DADO_DE_BAJA:
            return redirect("inventario:detail", pk=activo.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["activo"] = self.get_activo()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return redirect("inventario:detail", pk=self.get_activo().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activo"] = self.get_activo()
        return context


class BajaInventarioView(InventarioQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = BajaInventarioForm
    template_name = "inventario/baja_form.html"
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_GESTIONAR

    def get_activo(self):
        if not hasattr(self, "activo"):
            self.activo = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.activo

    def dispatch(self, request, *args, **kwargs):
        activo = self.get_activo()
        if activo.estado == ActivoInventario.Estado.DADO_DE_BAJA:
            return redirect("inventario:detail", pk=activo.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        activo = self.get_activo()
        MovimientoInventario.objects.create(
            iglesia=activo.iglesia,
            activo=activo,
            tipo=MovimientoInventario.Tipo.BAJA,
            fecha=form.cleaned_data["fecha"],
            ubicacion_anterior=activo.ubicacion_actual,
            ubicacion_nueva=activo.ubicacion_actual,
            responsable_anterior=activo.responsable_actual,
            responsable_nuevo=activo.responsable_actual,
            detalle=form.cleaned_data["motivo"],
            registrado_por=self.request.user,
        )
        activo.estado = ActivoInventario.Estado.DADO_DE_BAJA
        activo.activo = False
        activo.save(update_fields=["estado", "activo", "actualizado_en"])
        return redirect("inventario:detail", pk=activo.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activo"] = self.get_activo()
        return context


class AdjuntarDocumentoInventarioView(InventarioQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = DocumentoAdjuntoForm
    template_name = "inventario/documento_form.html"
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_GESTIONAR

    def get_activo(self):
        if not hasattr(self, "activo"):
            self.activo = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.activo

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["objeto"] = self.get_activo()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return redirect("inventario:detail", pk=self.get_activo().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activo"] = self.get_activo()
        return context


class DescargarDocumentoInventarioView(InventarioQuerysetMixin, PermisoModuloMixin, FormView):
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_VER

    def get(self, request, pk, documento_pk):
        activo = get_object_or_404(self.get_queryset(), pk=pk)
        documento = get_object_or_404(documentos_activo(activo), pk=documento_pk, estado=DocumentoAdjunto.Estado.ACTIVO)
        return FileResponse(documento.archivo.open("rb"), as_attachment=False, filename=documento.archivo.name.split("/")[-1])


class AnularDocumentoInventarioView(InventarioQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = AnularDocumentoAdjuntoForm
    template_name = "inventario/documento_anular.html"
    modulo_permiso = MODULO_INVENTARIO
    accion_permiso = ACCION_GESTIONAR

    def get_activo(self):
        if not hasattr(self, "activo"):
            self.activo = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.activo

    def get_documento(self):
        if not hasattr(self, "documento"):
            self.documento = get_object_or_404(
                documentos_activo(self.get_activo()),
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
        return redirect("inventario:detail", pk=self.get_activo().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["activo"] = self.get_activo()
        context["documento"] = self.get_documento()
        return context


def documentos_activo(activo):
    return DocumentoAdjunto.objects.filter(
        iglesia=activo.iglesia,
        content_type=ContentType.objects.get_for_model(ActivoInventario),
        object_id=activo.pk,
    ).select_related("subido_por", "anulado_por")


def timezone_now():
    from django.utils import timezone

    return timezone.now()

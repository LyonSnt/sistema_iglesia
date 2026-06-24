from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.auditoria.models import RegistroAuditoria
from apps.core.iglesias import usuario_es_nacional
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_TRASLADOS, PermisoModuloMixin
from apps.documentos.forms import AnularDocumentoAdjuntoForm, DocumentoAdjuntoForm
from apps.documentos.models import DocumentoAdjunto

from .forms import ResponderTrasladoForm, TrasladoMiembroForm
from .models import TrasladoMiembro
from .servicios import aceptar_traslado, anular_traslado, rechazar_traslado


class TrasladoQuerysetMixin:
    def get_queryset(self):
        queryset = TrasladoMiembro.objects.select_related(
            "miembro",
            "iglesia_origen",
            "iglesia_destino",
            "solicitado_por",
            "respondido_por",
        )
        if usuario_es_nacional(self.request.user):
            return queryset
        return queryset.filter(
            Q(iglesia_origen=self.request.user.iglesia) | Q(iglesia_destino=self.request.user.iglesia)
        )


class TrasladoListView(TrasladoQuerysetMixin, PermisoModuloMixin, ListView):
    model = TrasladoMiembro
    template_name = "traslados/traslado_list.html"
    context_object_name = "traslados"
    paginate_by = 20
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = super().get_queryset()
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(miembro__nombres__icontains=query)
                | Q(miembro__apellidos__icontains=query)
                | Q(iglesia_origen__nombre__icontains=query)
                | Q(iglesia_destino__nombre__icontains=query)
                | Q(iglesia_origen__codigo__icontains=query)
                | Q(iglesia_destino__codigo__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["q"] = self.request.GET.get("q", "").strip()
        context["estados"] = TrasladoMiembro.Estado.choices
        return context


class TrasladoDetailView(TrasladoQuerysetMixin, PermisoModuloMixin, DetailView):
    model = TrasladoMiembro
    template_name = "traslados/traslado_detail.html"
    context_object_name = "traslado"
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        traslado = self.object
        user = self.request.user
        context["puede_responder"] = traslado.pendiente and (
            usuario_es_nacional(user) or user.iglesia_id == traslado.iglesia_destino_id
        )
        context["puede_anular"] = traslado.pendiente and (
            usuario_es_nacional(user) or user.iglesia_id == traslado.iglesia_origen_id
        )
        context["puede_gestionar_documentos"] = context["puede_responder"] or context["puede_anular"]
        context["documentos"] = documentos_traslado(traslado)
        context["documento_create_url"] = reverse("traslados:document-create", args=[traslado.pk])
        context["documento_download_name"] = "traslados:document-download"
        context["documento_deactivate_name"] = "traslados:document-deactivate"
        return context


class TrasladoCreateView(PermisoModuloMixin, CreateView):
    model = TrasladoMiembro
    form_class = TrasladoMiembroForm
    template_name = "traslados/traslado_form.html"
    success_url = reverse_lazy("traslados:list")
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        RegistroAuditoria.objects.create(
            usuario=self.request.user,
            accion="SOLICITAR",
            modulo="traslados",
            registro_afectado=f"traslados.TrasladoMiembro:{self.object.pk}",
            valor_nuevo={
                "miembro_id": self.object.miembro_id,
                "iglesia_origen_id": self.object.iglesia_origen_id,
                "iglesia_destino_id": self.object.iglesia_destino_id,
                "estado": self.object.estado,
            },
            iglesia=self.object.iglesia_origen,
            motivo="Solicitud de traslado registrada por iglesia origen.",
        )
        messages.success(self.request, "Solicitud de traslado registrada.")
        return response


class ResponderTrasladoView(TrasladoQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "traslados/traslado_responder_form.html"
    form_class = ResponderTrasladoForm
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_GESTIONAR
    accion = ""
    titulo = ""

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        traslado = self.get_object()
        self.validar_alcance_accion(traslado)
        kwargs["traslado"] = traslado
        return kwargs

    def validar_alcance_accion(self, traslado):
        user = self.request.user
        if not traslado.pendiente:
            raise PermissionDenied
        if usuario_es_nacional(user):
            return
        if self.accion in {"aceptar", "rechazar"} and user.iglesia_id != traslado.iglesia_destino_id:
            raise PermissionDenied
        if self.accion == "anular" and user.iglesia_id != traslado.iglesia_origen_id:
            raise PermissionDenied

    def form_valid(self, form):
        traslado = self.get_object()
        self.validar_alcance_accion(traslado)
        observacion = form.cleaned_data["observacion"]

        if self.accion == "aceptar":
            aceptar_traslado(traslado, self.request.user, observacion)
            messages.success(self.request, "Traslado aceptado y miembro movido a la iglesia destino.")
        elif self.accion == "rechazar":
            rechazar_traslado(traslado, self.request.user, observacion)
            messages.success(self.request, "Traslado rechazado.")
        elif self.accion == "anular":
            anular_traslado(traslado, self.request.user, observacion)
            messages.success(self.request, "Traslado anulado.")
        return redirect("traslados:detail", pk=traslado.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["traslado"] = self.get_object()
        context["titulo"] = self.titulo
        context["accion"] = self.accion
        return context


class AceptarTrasladoView(ResponderTrasladoView):
    accion = "aceptar"
    titulo = "Aceptar traslado"


class RechazarTrasladoView(ResponderTrasladoView):
    accion = "rechazar"
    titulo = "Rechazar traslado"


class AnularTrasladoView(ResponderTrasladoView):
    accion = "anular"
    titulo = "Anular traslado"


class AdjuntarDocumentoTrasladoView(TrasladoQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = DocumentoAdjuntoForm
    template_name = "documentos/documento_form.html"
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def dispatch(self, request, *args, **kwargs):
        self.validar_alcance_documento(self.get_object())
        return super().dispatch(request, *args, **kwargs)

    def validar_alcance_documento(self, traslado):
        user = self.request.user
        if usuario_es_nacional(user):
            return
        if user.iglesia_id not in {traslado.iglesia_origen_id, traslado.iglesia_destino_id}:
            raise PermissionDenied

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["objeto"] = self.get_object()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return redirect("traslados:detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        traslado = self.get_object()
        context = super().get_context_data(**kwargs)
        context["seccion"] = "Traslados"
        context["objeto_titulo"] = str(traslado)
        context["cancel_url"] = reverse("traslados:detail", args=[traslado.pk])
        return context


class DescargarDocumentoTrasladoView(TrasladoQuerysetMixin, PermisoModuloMixin, FormView):
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_VER

    def get(self, request, pk, documento_pk):
        traslado = get_object_or_404(self.get_queryset(), pk=pk)
        documento = get_object_or_404(
            documentos_traslado(traslado),
            pk=documento_pk,
            estado=DocumentoAdjunto.Estado.ACTIVO,
        )
        return FileResponse(documento.archivo.open("rb"), as_attachment=False, filename=documento.archivo.name.split("/")[-1])


class AnularDocumentoTrasladoView(AdjuntarDocumentoTrasladoView):
    form_class = AnularDocumentoAdjuntoForm
    template_name = "documentos/documento_anular.html"

    def get_form_kwargs(self):
        return FormView.get_form_kwargs(self)

    def get_documento(self):
        if not hasattr(self, "documento"):
            self.documento = get_object_or_404(
                documentos_traslado(self.get_object()),
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
        return redirect("traslados:detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        traslado = self.get_object()
        context = super().get_context_data(**kwargs)
        context["documento"] = self.get_documento()
        context["cancel_url"] = reverse("traslados:detail", args=[traslado.pk])
        return context


def documentos_traslado(traslado):
    return DocumentoAdjunto.objects.filter(
        iglesia=traslado.iglesia_origen,
        content_type=ContentType.objects.get_for_model(TrasladoMiembro),
        object_id=traslado.pk,
    ).select_related("subido_por", "anulado_por")


def timezone_now():
    from django.utils import timezone

    return timezone.now()

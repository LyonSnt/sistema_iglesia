from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_CARGOS, PermisoModuloMixin, usuario_puede
from apps.documentos.forms import AnularDocumentoAdjuntoForm, DocumentoAdjuntoForm
from apps.documentos.models import DocumentoAdjunto

from .forms import AccionFormalCargoForm, AsignacionCargoForm, FinalizarAsignacionCargoForm, ReemplazarAsignacionCargoForm
from .models import AsignacionCargo
from .servicios import (
    finalizar_acceso_por_asignacion,
    recalcular_acceso_por_usuario,
    registrar_nombramiento,
    registrar_posesion,
    registrar_reemplazo,
    registrar_renuncia,
    rol_para_nombre_cargo,
    sincronizar_acceso_por_asignacion,
)


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
        context["documentos"] = documentos_asignacion(self.object)
        context["historial_formal"] = self.object.historial_formal.select_related(
            "registrado_por",
            "asignacion_relacionada",
        )
        context["puede_gestionar_documentos"] = context["puede_gestionar"]
        context["documento_create_url"] = reverse("cargos:document-create", args=[self.object.pk])
        context["documento_download_name"] = "cargos:document-download"
        context["documento_deactivate_name"] = "cargos:document-deactivate"
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

    def form_valid(self, form):
        usuario_previo = None
        cargo_previo_funcional = False
        if form.instance.pk:
            asignacion_previa = (
                AsignacionCargo.objects.select_related("cargo", "usuario")
                .filter(pk=form.instance.pk)
                .first()
            )
            if asignacion_previa is not None:
                usuario_previo = asignacion_previa.usuario
                cargo_previo_funcional = (
                    rol_para_nombre_cargo(asignacion_previa.cargo.nombre) is not None
                )

        response = super().form_valid(form)
        sincronizar_acceso_por_asignacion(self.object)
        cargo_actual_funcional = rol_para_nombre_cargo(self.object.cargo.nombre) is not None
        if cargo_previo_funcional and usuario_previo != self.object.usuario:
            recalcular_acceso_por_usuario(usuario_previo)
        if cargo_previo_funcional or cargo_actual_funcional:
            recalcular_acceso_por_usuario(self.object.usuario)
        return response


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
        asignacion.save(update_fields=["fecha_fin", "estado", "observacion", "actualizado_en"])
        finalizar_acceso_por_asignacion(asignacion)
        return redirect("cargos:detail", pk=asignacion.pk)

    def get_success_url(self):
        return reverse("cargos:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["asignacion"] = self.get_object()
        return context


class AccionFormalCargoView(AsignacionCargoQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "cargos/asignacion_accion_formal_form.html"
    form_class = AccionFormalCargoForm
    modulo_permiso = MODULO_CARGOS
    accion_permiso = ACCION_GESTIONAR
    titulo = ""
    descripcion = ""
    accion = ""

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["asignacion"] = self.get_object()
        return kwargs

    def ejecutar_accion(self, asignacion, form):
        fecha = form.cleaned_data["fecha"]
        motivo = form.cleaned_data["motivo"]
        if self.accion == "nombramiento":
            return registrar_nombramiento(asignacion, self.request.user, fecha, motivo)
        if self.accion == "posesion":
            return registrar_posesion(asignacion, self.request.user, fecha, motivo)
        if self.accion == "renuncia":
            return registrar_renuncia(asignacion, self.request.user, fecha, motivo)
        return None

    def form_valid(self, form):
        asignacion = self.get_object()
        try:
            self.ejecutar_accion(asignacion, form)
        except ValueError as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        messages.success(self.request, "Accion formal registrada.")
        return redirect("cargos:detail", pk=asignacion.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["asignacion"] = self.get_object()
        context["titulo"] = self.titulo
        context["descripcion"] = self.descripcion
        return context


class RegistrarNombramientoCargoView(AccionFormalCargoView):
    titulo = "Registrar nombramiento"
    descripcion = "Registra el nombramiento formal y deja la asignacion en estado nombrado."
    accion = "nombramiento"


class RegistrarPosesionCargoView(AccionFormalCargoView):
    titulo = "Registrar posesion"
    descripcion = "Confirma la posesion formal y activa el acceso funcional cuando aplique."
    accion = "posesion"


class RegistrarRenunciaCargoView(AccionFormalCargoView):
    titulo = "Registrar renuncia"
    descripcion = "Finaliza la asignacion por renuncia y recalcula el acceso funcional cuando aplique."
    accion = "renuncia"


class RegistrarReemplazoCargoView(AccionFormalCargoView):
    template_name = "cargos/asignacion_reemplazo_form.html"
    form_class = ReemplazarAsignacionCargoForm
    titulo = "Registrar reemplazo"
    descripcion = "Finaliza la asignacion actual y posesiona una asignacion nombrada del mismo cargo."
    accion = "reemplazo"

    def ejecutar_accion(self, asignacion, form):
        return registrar_reemplazo(
            asignacion,
            form.cleaned_data["nueva_asignacion"],
            self.request.user,
            form.cleaned_data["fecha"],
            form.cleaned_data["motivo"],
        )


class AdjuntarDocumentoCargoView(AsignacionCargoQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = DocumentoAdjuntoForm
    template_name = "documentos/documento_form.html"
    modulo_permiso = MODULO_CARGOS
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
        return redirect("cargos:detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        asignacion = self.get_object()
        context = super().get_context_data(**kwargs)
        context["seccion"] = "Cargos"
        context["objeto_titulo"] = f"{asignacion.cargo} - {asignacion.miembro or asignacion.usuario}"
        context["cancel_url"] = reverse("cargos:detail", args=[asignacion.pk])
        return context


class DescargarDocumentoCargoView(AsignacionCargoQuerysetMixin, PermisoModuloMixin, FormView):
    modulo_permiso = MODULO_CARGOS
    accion_permiso = ACCION_VER

    def get(self, request, pk, documento_pk):
        asignacion = get_object_or_404(self.get_queryset(), pk=pk)
        documento = get_object_or_404(
            documentos_asignacion(asignacion),
            pk=documento_pk,
            estado=DocumentoAdjunto.Estado.ACTIVO,
        )
        return FileResponse(documento.archivo.open("rb"), as_attachment=False, filename=documento.archivo.name.split("/")[-1])


class AnularDocumentoCargoView(AsignacionCargoQuerysetMixin, PermisoModuloMixin, FormView):
    form_class = AnularDocumentoAdjuntoForm
    template_name = "documentos/documento_anular.html"
    modulo_permiso = MODULO_CARGOS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_documento(self):
        if not hasattr(self, "documento"):
            self.documento = get_object_or_404(
                documentos_asignacion(self.get_object()),
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
        return redirect("cargos:detail", pk=self.get_object().pk)

    def get_context_data(self, **kwargs):
        asignacion = self.get_object()
        context = super().get_context_data(**kwargs)
        context["seccion"] = "Cargos"
        context["documento"] = self.get_documento()
        context["cancel_url"] = reverse("cargos:detail", args=[asignacion.pk])
        return context


def documentos_asignacion(asignacion):
    return DocumentoAdjunto.objects.filter(
        iglesia=asignacion.iglesia,
        content_type=ContentType.objects.get_for_model(AsignacionCargo),
        object_id=asignacion.pk,
    ).select_related("subido_por", "anulado_por")


def timezone_now():
    from django.utils import timezone

    return timezone.now()

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.auditoria.models import RegistroAuditoria
from apps.core.iglesias import usuario_es_nacional
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_TRASLADOS, PermisoModuloMixin

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

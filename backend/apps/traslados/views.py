from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView

from apps.core.iglesias import usuario_es_nacional
from apps.core.permisos import ACCION_GESTIONAR, MODULO_TRASLADOS, PermisoModuloMixin
from apps.miembros.models import Miembro

from .forms import ResponderTrasladoForm, TrasladoForm
from .models import Traslado


class TrasladoQuerysetMixin:
    def get_queryset(self):
        queryset = Traslado.objects.select_related(
            "iglesia",
            "iglesia_destino",
            "miembro",
            "solicitado_por",
            "respondido_por",
        )
        user = self.request.user
        if usuario_es_nacional(user):
            return queryset
        if getattr(user, "iglesia_id", None) is None:
            return queryset.none()
        return queryset.filter(Q(iglesia=user.iglesia) | Q(iglesia_destino=user.iglesia))


class TrasladoListView(TrasladoQuerysetMixin, PermisoModuloMixin, ListView):
    model = Traslado
    template_name = "traslados/traslado_list.html"
    context_object_name = "traslados"
    paginate_by = 20
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_GESTIONAR

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(miembro__nombres__icontains=query)
                | Q(miembro__apellidos__icontains=query)
                | Q(iglesia__nombre__icontains=query)
                | Q(iglesia_destino__nombre__icontains=query)
            )
        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["estados"] = Traslado.Estado.choices
        return context


class TrasladoDetailView(TrasladoQuerysetMixin, PermisoModuloMixin, DetailView):
    model = Traslado
    template_name = "traslados/traslado_detail.html"
    context_object_name = "traslado"
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_GESTIONAR

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        traslado = self.object
        user = self.request.user
        es_origen = getattr(user, "iglesia_id", None) == traslado.iglesia_id
        es_destino = getattr(user, "iglesia_id", None) == traslado.iglesia_destino_id
        es_nacional = usuario_es_nacional(user)
        context["puede_responder"] = traslado.estado == Traslado.Estado.SOLICITADO and (es_destino or es_nacional)
        context["puede_cancelar"] = traslado.estado == Traslado.Estado.SOLICITADO and (es_origen or es_nacional)
        return context


class TrasladoCreateView(PermisoModuloMixin, CreateView):
    model = Traslado
    form_class = TrasladoForm
    template_name = "traslados/traslado_form.html"
    success_url = reverse_lazy("traslados:list")
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ResponderTrasladoView(TrasladoQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "traslados/traslado_responder_form.html"
    form_class = ResponderTrasladoForm
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_GESTIONAR
    nuevo_estado = None

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def dispatch(self, request, *args, **kwargs):
        traslado = self.get_object()
        user = request.user
        es_destino = getattr(user, "iglesia_id", None) == traslado.iglesia_destino_id
        if traslado.estado != Traslado.Estado.SOLICITADO or not (es_destino or usuario_es_nacional(user)):
            return redirect("traslados:detail", pk=traslado.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        traslado = self.get_object()
        with transaction.atomic():
            traslado.estado = self.nuevo_estado
            traslado.fecha_respuesta = form.cleaned_data["fecha_respuesta"]
            traslado.observacion_respuesta = form.cleaned_data["observacion_respuesta"]
            traslado.respondido_por = self.request.user
            traslado.save(update_fields=["estado", "fecha_respuesta", "observacion_respuesta", "respondido_por"])
            if self.nuevo_estado == Traslado.Estado.APROBADO:
                miembro = traslado.miembro
                miembro.iglesia = traslado.iglesia_destino
                miembro.estado = Miembro.Estado.ACTIVO
                miembro.save(update_fields=["iglesia", "estado"])
        return redirect("traslados:detail", pk=traslado.pk)

    def get_success_url(self):
        return reverse("traslados:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["traslado"] = self.get_object()
        context["accion"] = "Aprobar" if self.nuevo_estado == Traslado.Estado.APROBADO else "Rechazar"
        return context


class AprobarTrasladoView(ResponderTrasladoView):
    nuevo_estado = Traslado.Estado.APROBADO


class RechazarTrasladoView(ResponderTrasladoView):
    nuevo_estado = Traslado.Estado.RECHAZADO


class CancelarTrasladoView(TrasladoQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "traslados/traslado_responder_form.html"
    form_class = ResponderTrasladoForm
    modulo_permiso = MODULO_TRASLADOS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def dispatch(self, request, *args, **kwargs):
        traslado = self.get_object()
        user = request.user
        es_origen = getattr(user, "iglesia_id", None) == traslado.iglesia_id
        if traslado.estado != Traslado.Estado.SOLICITADO or not (es_origen or usuario_es_nacional(user)):
            return redirect("traslados:detail", pk=traslado.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        traslado = self.get_object()
        traslado.estado = Traslado.Estado.CANCELADO
        traslado.fecha_respuesta = form.cleaned_data["fecha_respuesta"]
        traslado.observacion_respuesta = form.cleaned_data["observacion_respuesta"]
        traslado.respondido_por = self.request.user
        traslado.save(update_fields=["estado", "fecha_respuesta", "observacion_respuesta", "respondido_por"])
        return redirect("traslados:detail", pk=traslado.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["traslado"] = self.get_object()
        context["accion"] = "Cancelar"
        return context

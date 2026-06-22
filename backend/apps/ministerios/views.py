from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_MINISTERIOS, PermisoModuloMixin, usuario_puede

from .alcance import filtrar_ministerios_por_usuario, usuario_administra_ministerios
from .forms import FinalizarParticipacionMinisterioForm, MinisterioForm, ParticipacionMinisterioForm
from .models import Ministerio, ParticipacionMinisterio


class MinisterioQuerysetMixin:
    def get_queryset(self):
        queryset = Ministerio.objects.select_related("iglesia", "responsable", "lider")
        return filtrar_ministerios_por_usuario(queryset, self.request.user)


class MinisterioListView(PermisoModuloMixin, ListView):
    model = Ministerio
    template_name = "ministerios/ministerio_list.html"
    context_object_name = "ministerios"
    paginate_by = 20
    modulo_permiso = MODULO_MINISTERIOS
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = Ministerio.objects.select_related("iglesia", "responsable", "lider")
        queryset = filtrar_ministerios_por_usuario(queryset, self.request.user)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(responsable__nombres__icontains=query)
                | Q(responsable__apellidos__icontains=query)
            )

        tipo = self.request.GET.get("tipo", "").strip()
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["tipo"] = self.request.GET.get("tipo", "").strip()
        context["tipos"] = Ministerio.Tipo.choices
        context["puede_gestionar"] = usuario_puede(
            self.request.user, MODULO_MINISTERIOS, ACCION_GESTIONAR
        ) and usuario_administra_ministerios(self.request.user)
        return context


class MinisterioDetailView(MinisterioQuerysetMixin, PermisoModuloMixin, DetailView):
    model = Ministerio
    template_name = "ministerios/ministerio_detail.html"
    context_object_name = "ministerio"
    modulo_permiso = MODULO_MINISTERIOS
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["participaciones"] = self.object.participaciones.select_related("miembro").order_by(
            "estado",
            "-fecha_inicio",
        )
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_MINISTERIOS, ACCION_GESTIONAR)
        context["puede_administrar"] = context["puede_gestionar"] and usuario_administra_ministerios(
            self.request.user
        )
        return context


class MinisterioFormMixin(MinisterioQuerysetMixin, PermisoModuloMixin):
    model = Ministerio
    form_class = MinisterioForm
    template_name = "ministerios/ministerio_form.html"
    success_url = reverse_lazy("ministerios:list")
    modulo_permiso = MODULO_MINISTERIOS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class MinisterioCreateView(MinisterioFormMixin, CreateView):
    def dispatch(self, request, *args, **kwargs):
        if not usuario_administra_ministerios(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class MinisterioUpdateView(MinisterioFormMixin, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if not usuario_administra_ministerios(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ParticipacionMinisterioActionMixin(MinisterioQuerysetMixin, PermisoModuloMixin):
    modulo_permiso = MODULO_MINISTERIOS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_success_url(self):
        return reverse("ministerios:detail", args=[self.get_object().pk])


class AgregarParticipacionMinisterioView(ParticipacionMinisterioActionMixin, FormView):
    template_name = "ministerios/participacion_form.html"
    form_class = ParticipacionMinisterioForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["ministerio"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        participacion = form.save(commit=False)
        participacion.ministerio = self.get_object()
        participacion.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ministerio"] = self.get_object()
        return context


class FinalizarParticipacionMinisterioView(MinisterioQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "ministerios/participacion_finalizar_form.html"
    form_class = FinalizarParticipacionMinisterioForm
    modulo_permiso = MODULO_MINISTERIOS
    accion_permiso = ACCION_GESTIONAR

    def get_ministerio(self):
        if not hasattr(self, "ministerio"):
            self.ministerio = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.ministerio

    def get_participacion(self):
        if not hasattr(self, "participacion"):
            self.participacion = get_object_or_404(
                ParticipacionMinisterio.objects.select_related("ministerio", "miembro"),
                pk=self.kwargs["participacion_pk"],
                ministerio=self.get_ministerio(),
            )
        return self.participacion

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["participacion"] = self.get_participacion()
        return kwargs

    def form_valid(self, form):
        participacion = self.get_participacion()
        participacion.fecha_fin = form.cleaned_data["fecha_fin"]
        participacion.estado = ParticipacionMinisterio.Estado.FINALIZADO
        participacion.activo = False
        if form.cleaned_data["motivo_salida"]:
            participacion.motivo_salida = form.cleaned_data["motivo_salida"]
        participacion.save(update_fields=["fecha_fin", "estado", "activo", "motivo_salida"])
        return redirect("ministerios:detail", pk=self.get_ministerio().pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["ministerio"] = self.get_ministerio()
        context["participacion"] = self.get_participacion()
        return context

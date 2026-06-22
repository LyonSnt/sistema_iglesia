from django.db.models import Q
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import (
    ACCION_GESTIONAR,
    ACCION_VER,
    MODULO_ESCUELA_DOMINICAL,
    PermisoModuloMixin,
    usuario_puede,
)
from apps.parametros.models import Periodo

from .forms import (
    ClaseEscuelaDominicalForm,
    MatriculaEscuelaDominicalForm,
    NivelEscuelaDominicalForm,
    SesionEscuelaDominicalForm,
    TomaAsistenciaForm,
    ProcesoPromocionForm,
    ConfirmarPromocionForm,
)
from .alcance import filtrar_clases_por_usuario, usuario_administra_escuela
from .models import (
    AsistenciaEscuelaDominical,
    ClaseEscuelaDominical,
    MatriculaEscuelaDominical,
    NivelEscuelaDominical,
    SesionEscuelaDominical,
    ProcesoPromocionEscuelaDominical,
)
from .promociones import confirmar_promocion, generar_resultados


class EscuelaDominicalPermisoMixin(PermisoModuloMixin):
    modulo_permiso = MODULO_ESCUELA_DOMINICAL


class ClaseQuerysetMixin:
    def get_queryset(self):
        queryset = ClaseEscuelaDominical.objects.select_related(
            "iglesia",
            "nivel",
            "periodo",
            "maestro",
        )
        return filtrar_clases_por_usuario(queryset, self.request.user)


class ClaseListView(EscuelaDominicalPermisoMixin, ListView):
    model = ClaseEscuelaDominical
    template_name = "escuela_dominical/clase_list.html"
    context_object_name = "clases"
    paginate_by = 20
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = super().get_queryset().select_related("iglesia", "nivel", "periodo", "maestro")
        queryset = filtrar_clases_por_usuario(queryset, self.request.user)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(nivel__nombre__icontains=query)
                | Q(maestro__username__icontains=query)
                | Q(maestro__first_name__icontains=query)
                | Q(maestro__last_name__icontains=query)
            )

        periodo_id = self.request.GET.get("periodo", "").strip()
        if periodo_id:
            queryset = queryset.filter(periodo_id=periodo_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["periodo"] = self.request.GET.get("periodo", "").strip()
        context["periodos"] = Periodo.objects.filter(activo=True).order_by("-fecha_inicio")
        context["puede_gestionar"] = usuario_puede(
            self.request.user,
            MODULO_ESCUELA_DOMINICAL,
            ACCION_GESTIONAR,
        ) and usuario_administra_escuela(self.request.user)
        return context


class ClaseDetailView(ClaseQuerysetMixin, EscuelaDominicalPermisoMixin, DetailView):
    model = ClaseEscuelaDominical
    template_name = "escuela_dominical/clase_detail.html"
    context_object_name = "clase"
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["matriculas"] = self.object.matriculas.select_related("alumno")
        context["sesiones"] = self.object.sesiones.select_related("registrado_por")
        context["puede_gestionar"] = usuario_puede(
            self.request.user,
            MODULO_ESCUELA_DOMINICAL,
            ACCION_GESTIONAR,
        )
        context["puede_administrar"] = context["puede_gestionar"] and usuario_administra_escuela(
            self.request.user
        )
        return context


class ClaseFormMixin(ClaseQuerysetMixin, EscuelaDominicalPermisoMixin):
    model = ClaseEscuelaDominical
    form_class = ClaseEscuelaDominicalForm
    template_name = "escuela_dominical/clase_form.html"
    success_url = reverse_lazy("escuela_dominical:list")
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class ClaseCreateView(ClaseFormMixin, CreateView):
    def dispatch(self, request, *args, **kwargs):
        if not usuario_administra_escuela(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ClaseUpdateView(ClaseFormMixin, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if not usuario_administra_escuela(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class NivelListView(EscuelaDominicalPermisoMixin, ListView):
    model = NivelEscuelaDominical
    template_name = "escuela_dominical/nivel_list.html"
    context_object_name = "niveles"
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = NivelEscuelaDominical.objects.select_related("iglesia")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["puede_gestionar"] = usuario_puede(
            self.request.user,
            MODULO_ESCUELA_DOMINICAL,
            ACCION_GESTIONAR,
        ) and usuario_administra_escuela(self.request.user)
        return context


class NivelFormMixin(EscuelaDominicalPermisoMixin):
    model = NivelEscuelaDominical
    form_class = NivelEscuelaDominicalForm
    template_name = "escuela_dominical/nivel_form.html"
    success_url = reverse_lazy("escuela_dominical:nivel-list")
    accion_permiso = ACCION_GESTIONAR

    def get_queryset(self):
        return filtrar_queryset_por_iglesia(
            NivelEscuelaDominical.objects.select_related("iglesia"),
            self.request.user,
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class NivelCreateView(NivelFormMixin, CreateView):
    def dispatch(self, request, *args, **kwargs):
        if not usuario_administra_escuela(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class NivelUpdateView(NivelFormMixin, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        if not usuario_administra_escuela(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class MatriculaCreateView(ClaseQuerysetMixin, EscuelaDominicalPermisoMixin, FormView):
    form_class = MatriculaEscuelaDominicalForm
    template_name = "escuela_dominical/matricula_form.html"
    accion_permiso = ACCION_GESTIONAR

    def get_clase(self):
        if not hasattr(self, "clase"):
            self.clase = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.clase

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["clase"] = self.get_clase()
        return kwargs

    def form_valid(self, form):
        matricula = form.save(commit=False)
        matricula.clase = self.get_clase()
        matricula.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("escuela_dominical:detail", args=[self.get_clase().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = self.get_clase()
        return context


class MatriculaUpdateView(ClaseQuerysetMixin, EscuelaDominicalPermisoMixin, UpdateView):
    model = MatriculaEscuelaDominical
    form_class = MatriculaEscuelaDominicalForm
    template_name = "escuela_dominical/matricula_form.html"
    pk_url_kwarg = "matricula_pk"
    context_object_name = "matricula"
    accion_permiso = ACCION_GESTIONAR

    def get_clase(self):
        if not hasattr(self, "clase"):
            self.clase = get_object_or_404(self.get_clase_queryset(), pk=self.kwargs["pk"])
        return self.clase

    def get_clase_queryset(self):
        return filtrar_clases_por_usuario(
            ClaseEscuelaDominical.objects.select_related("iglesia"), self.request.user
        )

    def get_queryset(self):
        return MatriculaEscuelaDominical.objects.select_related("clase", "alumno").filter(
            clase=self.get_clase()
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["clase"] = self.get_clase()
        return kwargs

    def get_success_url(self):
        return reverse("escuela_dominical:detail", args=[self.get_clase().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = self.get_clase()
        return context


class SesionQuerysetMixin:
    def get_queryset(self):
        clases = filtrar_clases_por_usuario(
            ClaseEscuelaDominical.objects.all(), self.request.user
        )
        return SesionEscuelaDominical.objects.select_related(
            "clase",
            "clase__iglesia",
            "clase__periodo",
            "registrado_por",
        ).filter(clase__in=clases)


class SesionCreateView(ClaseQuerysetMixin, EscuelaDominicalPermisoMixin, FormView):
    form_class = SesionEscuelaDominicalForm
    template_name = "escuela_dominical/sesion_form.html"
    accion_permiso = ACCION_GESTIONAR

    def get_clase(self):
        if not hasattr(self, "clase"):
            self.clase = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.clase

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["clase"] = self.get_clase()
        return kwargs

    def form_valid(self, form):
        sesion = form.save(commit=False)
        sesion.clase = self.get_clase()
        sesion.registrado_por = self.request.user
        sesion.save()
        self.sesion = sesion
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "escuela_dominical:asistencia",
            args=[self.get_clase().pk, self.sesion.pk],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["clase"] = self.get_clase()
        return context


class SesionDetailView(SesionQuerysetMixin, EscuelaDominicalPermisoMixin, DetailView):
    model = SesionEscuelaDominical
    template_name = "escuela_dominical/sesion_detail.html"
    context_object_name = "sesion"
    pk_url_kwarg = "sesion_pk"
    accion_permiso = ACCION_VER

    def get_queryset(self):
        return super().get_queryset().filter(clase_id=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["asistencias"] = self.object.asistencias.select_related(
            "matricula__alumno"
        )
        puede_gestionar = usuario_puede(
            self.request.user, MODULO_ESCUELA_DOMINICAL, ACCION_GESTIONAR
        )
        context["puede_corregir"] = puede_gestionar and (
            not self.object.cerrada or usuario_administra_escuela(self.request.user)
        )
        return context


class TomaAsistenciaView(SesionQuerysetMixin, EscuelaDominicalPermisoMixin, FormView):
    form_class = TomaAsistenciaForm
    template_name = "escuela_dominical/asistencia_form.html"
    accion_permiso = ACCION_GESTIONAR

    def get_sesion(self):
        if not hasattr(self, "sesion"):
            self.sesion = get_object_or_404(
                self.get_queryset(),
                pk=self.kwargs["sesion_pk"],
                clase_id=self.kwargs["pk"],
            )
            if self.sesion.cerrada and not usuario_administra_escuela(self.request.user):
                raise PermissionDenied
        return self.sesion

    def get_matriculas(self):
        if not hasattr(self, "matriculas"):
            sesion = self.get_sesion()
            self.matriculas = list(
                sesion.clase.matriculas.select_related("alumno")
                .filter(fecha_inscripcion__lte=sesion.fecha)
                .filter(Q(fecha_salida__isnull=True) | Q(fecha_salida__gte=sesion.fecha))
                .order_by("alumno__apellidos", "alumno__nombres")
            )
        return self.matriculas

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["sesion"] = self.get_sesion()
        kwargs["matriculas"] = self.get_matriculas()
        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        sesion = self.get_sesion()
        for matricula, estado, observacion in form.datos_asistencia():
            AsistenciaEscuelaDominical.objects.update_or_create(
                sesion=sesion,
                matricula=matricula,
                defaults={"estado": estado, "observacion": observacion},
            )
        if form.cleaned_data["cerrar_sesion"] and not sesion.cerrada:
            sesion.cerrada = True
            sesion.save(update_fields=["cerrada"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "escuela_dominical:sesion-detail",
            args=[self.get_sesion().clase_id, self.get_sesion().pk],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context["form"]
        context["sesion"] = self.get_sesion()
        context["filas"] = [
            {
                "matricula": matricula,
                "estado": form[f"estado_{matricula.pk}"],
                "observacion": form[f"observacion_{matricula.pk}"],
            }
            for matricula in self.get_matriculas()
        ]
        return context


class PromocionAdminMixin(EscuelaDominicalPermisoMixin):
    accion_permiso = ACCION_GESTIONAR

    def dispatch(self, request, *args, **kwargs):
        if not usuario_administra_escuela(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PromocionListView(PromocionAdminMixin, ListView):
    model = ProcesoPromocionEscuelaDominical
    template_name = "escuela_dominical/promocion_list.html"
    context_object_name = "procesos"

    def get_queryset(self):
        return filtrar_queryset_por_iglesia(
            super().get_queryset().select_related(
                "iglesia", "periodo_origen", "periodo_destino", "confirmado_por"
            ),
            self.request.user,
        )


class PromocionCreateView(PromocionAdminMixin, CreateView):
    model = ProcesoPromocionEscuelaDominical
    form_class = ProcesoPromocionForm
    template_name = "escuela_dominical/promocion_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        generar_resultados(self.object)
        return response

    def get_success_url(self):
        return reverse("escuela_dominical:promocion-detail", args=[self.object.pk])


class PromocionDetailView(PromocionAdminMixin, FormView):
    form_class = ConfirmarPromocionForm
    template_name = "escuela_dominical/promocion_detail.html"

    def get_proceso(self):
        if not hasattr(self, "proceso"):
            queryset = filtrar_queryset_por_iglesia(
                ProcesoPromocionEscuelaDominical.objects.select_related(
                    "iglesia", "periodo_origen", "periodo_destino", "confirmado_por"
                ),
                self.request.user,
            )
            self.proceso = get_object_or_404(queryset, pk=self.kwargs["pk"])
        return self.proceso

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["proceso"] = self.get_proceso()
        return kwargs

    def form_valid(self, form):
        proceso = self.get_proceso()
        if proceso.estado == proceso.Estado.CONFIRMADO:
            return super().form_valid(form)
        try:
            with transaction.atomic():
                form.guardar_destinos()
                confirmar_promocion(proceso, self.request.user)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)
        messages.success(self.request, "La promocion fue confirmada correctamente.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("escuela_dominical:promocion-detail", args=[self.get_proceso().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        proceso = self.get_proceso()
        context["proceso"] = proceso
        resultados = list(proceso.resultados.select_related(
            "matricula_origen__alumno",
            "matricula_origen__clase__nivel",
            "nivel_destino",
            "clase_destino",
        ))
        form = context["form"]
        context["filas_resultados"] = [
            {
                "resultado": resultado,
                "campo_clase": form[f"clase_{resultado.pk}"]
                if f"clase_{resultado.pk}" in form.fields
                else None,
            }
            for resultado in resultados
        ]
        return context

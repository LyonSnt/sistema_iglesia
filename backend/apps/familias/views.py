from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView, View

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_MIEMBROS, PermisoModuloMixin, usuario_puede

from .forms import AgregarIntegranteFamiliaForm, FamiliaForm
from .models import Familia, MiembroFamilia


class FamiliaQuerysetMixin:
    def get_queryset(self):
        queryset = Familia.objects.select_related("iglesia", "jefe_hogar")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class FamiliaListView(PermisoModuloMixin, ListView):
    model = Familia
    template_name = "familias/familia_list.html"
    context_object_name = "familias"
    paginate_by = 20
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = Familia.objects.select_related("iglesia", "jefe_hogar")
        queryset = filtrar_queryset_por_iglesia(queryset, self.request.user)
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(jefe_hogar__nombres__icontains=query)
                | Q(jefe_hogar__apellidos__icontains=query)
                | Q(telefono__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_MIEMBROS, ACCION_GESTIONAR)
        return context


class FamiliaDetailView(FamiliaQuerysetMixin, PermisoModuloMixin, DetailView):
    model = Familia
    template_name = "familias/familia_detail.html"
    context_object_name = "familia"
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["integrantes"] = self.object.integrantes.select_related("miembro").order_by(
            "miembro__apellidos",
            "miembro__nombres",
            "relacion",
        )
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_MIEMBROS, ACCION_GESTIONAR)
        return context


class FamiliaFormMixin(FamiliaQuerysetMixin, PermisoModuloMixin):
    model = Familia
    form_class = FamiliaForm
    template_name = "familias/familia_form.html"
    success_url = reverse_lazy("familias:list")
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class FamiliaCreateView(FamiliaFormMixin, CreateView):
    pass


class FamiliaUpdateView(FamiliaFormMixin, UpdateView):
    pass


class AgregarIntegranteFamiliaView(FamiliaQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "familias/integrante_form.html"
    form_class = AgregarIntegranteFamiliaForm
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["familia"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        integrante, _ = MiembroFamilia.objects.get_or_create(
            familia=self.get_object(),
            miembro=form.cleaned_data["miembro"],
            relacion=form.cleaned_data["relacion"],
        )
        if not integrante.activo:
            integrante.activo = True
            integrante.save(update_fields=["activo"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("familias:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["familia"] = self.get_object()
        return context


class DesactivarIntegranteFamiliaView(FamiliaQuerysetMixin, PermisoModuloMixin, View):
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_GESTIONAR

    def post(self, request, *args, **kwargs):
        familia = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        integrante = get_object_or_404(
            MiembroFamilia.objects.select_related("familia", "miembro"),
            pk=kwargs["integrante_pk"],
            familia=familia,
        )
        if integrante.activo:
            integrante.activo = False
            integrante.save(update_fields=["activo"])
        return redirect("familias:detail", pk=familia.pk)

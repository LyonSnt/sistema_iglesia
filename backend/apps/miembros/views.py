from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.core.permisos import ACCION_GESTIONAR, ACCION_VER, MODULO_MIEMBROS, PermisoModuloMixin, usuario_puede
from apps.familias.models import Familia, Matrimonio, MiembroFamilia

from .forms import (
    AdmisionFormalForm,
    BautismoForm,
    BajaVoluntariaForm,
    CrearFamiliaMiembroForm,
    DisciplinaForm,
    FallecimientoForm,
    MatrimonioForm,
    MiembroForm,
    RestauracionForm,
    SuspensionForm,
    VincularFamiliaMiembroForm,
)
from .models import HistorialPastoralMiembro, Miembro
from .servicios import registrar_accion_pastoral


class MiembroQuerysetMixin:
    def get_queryset(self):
        queryset = Miembro.objects.select_related("iglesia")
        return filtrar_queryset_por_iglesia(queryset, self.request.user)


class MiembroListView(PermisoModuloMixin, ListView):
    model = Miembro
    template_name = "miembros/miembro_list.html"
    context_object_name = "miembros"
    paginate_by = 20
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_VER

    def get_queryset(self):
        queryset = Miembro.objects.select_related("iglesia")
        queryset = filtrar_queryset_por_iglesia(queryset, self.request.user)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(nombres__icontains=query)
                | Q(apellidos__icontains=query)
                | Q(cedula__icontains=query)
                | Q(telefono__icontains=query)
            )

        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["estado"] = self.request.GET.get("estado", "").strip()
        context["estados"] = Miembro.Estado.choices
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_MIEMBROS, ACCION_GESTIONAR)
        return context


class MiembroDetailView(MiembroQuerysetMixin, PermisoModuloMixin, DetailView):
    model = Miembro
    template_name = "miembros/miembro_detail.html"
    context_object_name = "miembro"
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_VER

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["puede_gestionar"] = usuario_puede(self.request.user, MODULO_MIEMBROS, ACCION_GESTIONAR)
        context["familias"] = self.object.familias.select_related("familia").order_by("familia__nombre", "relacion")
        context["matrimonios"] = Matrimonio.objects.select_related("conyuge_1", "conyuge_2", "familia").filter(
            Q(conyuge_1=self.object) | Q(conyuge_2=self.object),
            iglesia=self.object.iglesia,
        ).order_by("-fecha_matrimonio")
        context["historial_pastoral"] = self.object.historial_pastoral.select_related("registrado_por")[:20]
        return context


class MiembroFormMixin(MiembroQuerysetMixin, PermisoModuloMixin):
    model = Miembro
    form_class = MiembroForm
    template_name = "miembros/miembro_form.html"
    success_url = reverse_lazy("miembros:list")
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_GESTIONAR

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_queryset(self):
        return MiembroQuerysetMixin.get_queryset(self)


class MiembroCreateView(MiembroFormMixin, CreateView):
    pass


class MiembroUpdateView(MiembroFormMixin, UpdateView):
    pass


class AccionPastoralView(MiembroQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "miembros/accion_pastoral_form.html"
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_GESTIONAR
    form_class = BautismoForm
    titulo = ""
    descripcion = ""
    campo_fecha = ""
    estado_resultante = None
    activo_resultante = None
    tipo_historial = None

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_initial(self):
        initial = super().get_initial()
        if self.campo_fecha:
            initial["fecha"] = getattr(self.get_object(), self.campo_fecha)
        return initial

    def form_valid(self, form):
        self.object = self.get_object()
        registrar_accion_pastoral(
            self.object,
            self.request.user,
            self.tipo_historial,
            form.cleaned_data["fecha"],
            form.cleaned_data["motivo"],
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("miembros:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["miembro"] = self.get_object()
        context["titulo"] = self.titulo
        context["descripcion"] = self.descripcion
        return context


class RegistrarBautismoView(AccionPastoralView):
    form_class = BautismoForm
    titulo = "Registrar bautismo"
    descripcion = "Guarda la fecha de bautismo del miembro."
    campo_fecha = "fecha_bautismo"
    tipo_historial = HistorialPastoralMiembro.Tipo.BAUTISMO


class RegistrarMembresiaView(AccionPastoralView):
    form_class = AdmisionFormalForm
    titulo = "Registrar admision formal"
    descripcion = "Guarda la fecha de membresia formal y marca al miembro como activo."
    campo_fecha = "fecha_membresia"
    tipo_historial = HistorialPastoralMiembro.Tipo.ADMISION


class RegistrarFallecimientoView(AccionPastoralView):
    form_class = FallecimientoForm
    titulo = "Registrar fallecimiento"
    descripcion = "Guarda la fecha de fallecimiento y marca el miembro como fallecido."
    campo_fecha = "fecha_fallecimiento"
    estado_resultante = Miembro.Estado.FALLECIDO
    activo_resultante = False
    tipo_historial = HistorialPastoralMiembro.Tipo.FALLECIMIENTO


class RegistrarBajaVoluntariaView(AccionPastoralView):
    form_class = BajaVoluntariaForm
    titulo = "Registrar baja voluntaria"
    descripcion = "Marca al miembro como inactivo por baja voluntaria y conserva el historial pastoral."
    tipo_historial = HistorialPastoralMiembro.Tipo.BAJA_VOLUNTARIA


class RegistrarRestauracionView(AccionPastoralView):
    form_class = RestauracionForm
    titulo = "Registrar restauracion"
    descripcion = "Restaura al miembro y lo marca nuevamente como activo."
    tipo_historial = HistorialPastoralMiembro.Tipo.RESTAURACION


class RegistrarDisciplinaView(AccionPastoralView):
    form_class = DisciplinaForm
    titulo = "Registrar disciplina"
    descripcion = "Marca al miembro en disciplina pastoral con motivo obligatorio."
    tipo_historial = HistorialPastoralMiembro.Tipo.DISCIPLINA


class RegistrarSuspensionView(AccionPastoralView):
    form_class = SuspensionForm
    titulo = "Registrar suspension"
    descripcion = "Marca al miembro como suspendido e inactivo con motivo obligatorio."
    tipo_historial = HistorialPastoralMiembro.Tipo.SUSPENSION


class RegistrarMatrimonioView(MiembroQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "miembros/matrimonio_form.html"
    form_class = MatrimonioForm
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_GESTIONAR

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["miembro"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        miembro = self.get_object()
        conyuge = form.cleaned_data["conyuge"]
        matrimonio = Matrimonio.objects.create(
            iglesia=miembro.iglesia,
            conyuge_1=miembro,
            conyuge_2=conyuge,
            fecha_matrimonio=form.cleaned_data["fecha_matrimonio"],
            familia=form.cleaned_data["familia"],
            observacion=form.cleaned_data["observacion"],
        )
        Miembro.objects.filter(pk__in=[miembro.pk, conyuge.pk]).update(estado_civil=Miembro.EstadoCivil.CASADO)

        if matrimonio.familia_id:
            for persona in (miembro, conyuge):
                vinculo, _ = MiembroFamilia.objects.get_or_create(
                    familia=matrimonio.familia,
                    miembro=persona,
                    relacion=MiembroFamilia.Relacion.CONYUGE,
                )
                if not vinculo.activo:
                    vinculo.activo = True
                    vinculo.save(update_fields=["activo"])

        return super().form_valid(form)

    def get_success_url(self):
        return reverse("miembros:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["miembro"] = self.get_object()
        return context


class FamiliaMiembroActionView(MiembroQuerysetMixin, PermisoModuloMixin, FormView):
    template_name = "miembros/familia_miembro_form.html"
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_GESTIONAR
    titulo = ""
    descripcion = ""

    def get_object(self):
        if not hasattr(self, "object"):
            self.object = get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])
        return self.object

    def get_success_url(self):
        return reverse("miembros:detail", args=[self.get_object().pk])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["miembro"] = self.get_object()
        context["titulo"] = self.titulo
        context["descripcion"] = self.descripcion
        return context


class CrearFamiliaMiembroView(FamiliaMiembroActionView):
    form_class = CrearFamiliaMiembroForm
    titulo = "Crear familia"
    descripcion = "Crea una familia en la iglesia del miembro y lo agrega como integrante."

    def form_valid(self, form):
        miembro = self.get_object()
        familia = Familia.objects.create(
            iglesia=miembro.iglesia,
            nombre=form.cleaned_data["nombre"],
            jefe_hogar=miembro,
            direccion=form.cleaned_data["direccion"],
            telefono=form.cleaned_data["telefono"],
        )
        MiembroFamilia.objects.create(
            familia=familia,
            miembro=miembro,
            relacion=form.cleaned_data["relacion"],
        )
        return super().form_valid(form)


class VincularFamiliaMiembroView(FamiliaMiembroActionView):
    form_class = VincularFamiliaMiembroForm
    titulo = "Vincular a familia"
    descripcion = "Agrega el miembro a una familia existente de su misma iglesia."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["miembro"] = self.get_object()
        return kwargs

    def form_valid(self, form):
        MiembroFamilia.objects.create(
            familia=form.cleaned_data["familia"],
            miembro=self.get_object(),
            relacion=form.cleaned_data["relacion"],
        )
        return super().form_valid(form)

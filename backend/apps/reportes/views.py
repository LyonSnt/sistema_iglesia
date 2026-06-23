from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.views.generic import TemplateView

from apps.iglesias.models import Iglesia
from apps.traslados.models import TrasladoMiembro
from apps.usuarios.models import Usuario


class ReporteTrasladosView(LoginRequiredMixin, TemplateView):
    template_name = "reportes/traslados.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (getattr(user, "is_superuser", False) or getattr(user, "rol", None) == Usuario.Rol.ADMIN_NACIONAL):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = TrasladoMiembro.objects.select_related("miembro", "iglesia_origen", "iglesia_destino")

        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        origen = self.request.GET.get("iglesia_origen", "").strip()
        if origen:
            queryset = queryset.filter(iglesia_origen_id=origen)

        destino = self.request.GET.get("iglesia_destino", "").strip()
        if destino:
            queryset = queryset.filter(iglesia_destino_id=destino)

        desde = self.request.GET.get("desde", "").strip()
        if desde:
            queryset = queryset.filter(creado_en__date__gte=desde)

        hasta = self.request.GET.get("hasta", "").strip()
        if hasta:
            queryset = queryset.filter(creado_en__date__lte=hasta)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(miembro__nombres__icontains=query)
                | Q(miembro__apellidos__icontains=query)
                | Q(iglesia_origen__codigo__icontains=query)
                | Q(iglesia_origen__nombre__icontains=query)
                | Q(iglesia_destino__codigo__icontains=query)
                | Q(iglesia_destino__nombre__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        conteos = {item["estado"]: item["total"] for item in queryset.values("estado").annotate(total=Count("id"))}

        context["traslados"] = queryset[:100]
        context["total"] = queryset.count()
        context["conteos_resumen"] = [
            {"estado": estado, "label": label, "total": conteos.get(estado, 0)}
            for estado, label in TrasladoMiembro.Estado.choices
        ]
        context["estados"] = TrasladoMiembro.Estado.choices
        context["iglesias"] = Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL, activo=True).order_by("nombre")
        context["filtros"] = {
            "q": self.request.GET.get("q", "").strip(),
            "estado": self.request.GET.get("estado", "").strip(),
            "iglesia_origen": self.request.GET.get("iglesia_origen", "").strip(),
            "iglesia_destino": self.request.GET.get("iglesia_destino", "").strip(),
            "desde": self.request.GET.get("desde", "").strip(),
            "hasta": self.request.GET.get("hasta", "").strip(),
        }
        return context

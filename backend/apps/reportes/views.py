from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Sum
from django.views.generic import TemplateView

from apps.aportes_nacionales.models import AporteNacional
from apps.core.permisos import ACCION_VER, MODULO_REPORTES, usuario_puede
from apps.finanzas.models import CierreMensualFinanciero
from apps.iglesias.models import Iglesia
from apps.inventario.models import ActivoInventario
from apps.traslados.models import TrasladoMiembro


class ReporteNacionalMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not usuario_puede(request.user, MODULO_REPORTES, ACCION_VER):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ReporteTrasladosView(ReporteNacionalMixin, TemplateView):
    template_name = "reportes/traslados.html"

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


class ReporteFinanzasView(ReporteNacionalMixin, TemplateView):
    template_name = "reportes/finanzas.html"

    def get_queryset(self):
        queryset = CierreMensualFinanciero.objects.select_related(
            "iglesia",
            "iglesia__zona",
            "aporte_nacional",
        ).filter(estado=CierreMensualFinanciero.Estado.CERRADO)

        iglesia = self.request.GET.get("iglesia", "").strip()
        if iglesia:
            queryset = queryset.filter(iglesia_id=iglesia)

        zona = self.request.GET.get("zona", "").strip()
        if zona:
            queryset = queryset.filter(iglesia__zona_id=zona)

        anio = self.request.GET.get("anio", "").strip()
        if anio:
            queryset = queryset.filter(anio=anio)

        mes = self.request.GET.get("mes", "").strip()
        if mes:
            queryset = queryset.filter(mes=mes)

        return queryset.order_by("iglesia__nombre", "-anio", "-mes")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        filas = [_fila_financiera(cierre) for cierre in queryset[:200]]
        totales_cierres = queryset.aggregate(
            ingresos=Sum("total_ingresos"),
            egresos=Sum("total_egresos"),
            saldo=Sum("saldo"),
        )
        aportes = AporteNacional.objects.filter(cierre__in=queryset)
        totales_aportes = aportes.aggregate(
            aporte=Sum("monto_aporte"),
            pagado=Sum("monto_aporte", filter=Q(estado=AporteNacional.Estado.PAGADO)),
            pendiente=Sum("monto_aporte", filter=Q(estado=AporteNacional.Estado.PENDIENTE)),
        )

        context["filas"] = filas
        context["total_cierres"] = queryset.count()
        context["totales"] = {
            "ingresos": totales_cierres["ingresos"] or 0,
            "egresos": totales_cierres["egresos"] or 0,
            "saldo": totales_cierres["saldo"] or 0,
            "aporte": totales_aportes["aporte"] or 0,
            "pagado": totales_aportes["pagado"] or 0,
            "pendiente": totales_aportes["pendiente"] or 0,
        }
        context["iglesias"] = Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL, activo=True).select_related("zona").order_by("nombre")
        context["zonas"] = _zonas_filiales()
        context["meses"] = [(numero, f"{numero:02d}") for numero in range(1, 13)]
        context["filtros"] = {
            "iglesia": self.request.GET.get("iglesia", "").strip(),
            "zona": self.request.GET.get("zona", "").strip(),
            "anio": self.request.GET.get("anio", "").strip(),
            "mes": self.request.GET.get("mes", "").strip(),
        }
        return context


class ReporteInventarioView(ReporteNacionalMixin, TemplateView):
    template_name = "reportes/inventario.html"

    def get_queryset(self):
        queryset = ActivoInventario.objects.select_related(
            "iglesia",
            "iglesia__zona",
            "responsable_actual",
        )

        iglesia = self.request.GET.get("iglesia", "").strip()
        if iglesia:
            queryset = queryset.filter(iglesia_id=iglesia)

        zona = self.request.GET.get("zona", "").strip()
        if zona:
            queryset = queryset.filter(iglesia__zona_id=zona)

        estado = self.request.GET.get("estado", "").strip()
        if estado:
            queryset = queryset.filter(estado=estado)

        categoria = self.request.GET.get("categoria", "").strip()
        if categoria:
            queryset = queryset.filter(categoria=categoria)

        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(codigo__icontains=query)
                | Q(nombre__icontains=query)
                | Q(categoria__icontains=query)
                | Q(ubicacion_actual__icontains=query)
                | Q(iglesia__codigo__icontains=query)
                | Q(iglesia__nombre__icontains=query)
            )

        return queryset.order_by("iglesia__nombre", "categoria", "codigo")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        conteos = {item["estado"]: item["total"] for item in queryset.values("estado").annotate(total=Count("id"))}
        totales = queryset.aggregate(
            total=Count("id"),
            activos=Count("id", filter=Q(activo=True)),
            valor=Sum("valor_referencial"),
        )

        context["activos"] = queryset[:200]
        context["total_activos"] = totales["total"] or 0
        context["total_vigentes"] = totales["activos"] or 0
        context["valor_total"] = totales["valor"] or 0
        context["conteos_resumen"] = [
            {"estado": estado, "label": label, "total": conteos.get(estado, 0)}
            for estado, label in ActivoInventario.Estado.choices
        ]
        context["estados"] = ActivoInventario.Estado.choices
        context["iglesias"] = Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL, activo=True).select_related("zona").order_by("nombre")
        context["zonas"] = _zonas_filiales()
        context["categorias"] = (
            ActivoInventario.objects.exclude(categoria="")
            .values_list("categoria", flat=True)
            .distinct()
            .order_by("categoria")
        )
        context["filtros"] = {
            "q": self.request.GET.get("q", "").strip(),
            "iglesia": self.request.GET.get("iglesia", "").strip(),
            "zona": self.request.GET.get("zona", "").strip(),
            "estado": self.request.GET.get("estado", "").strip(),
            "categoria": self.request.GET.get("categoria", "").strip(),
        }
        return context


def _fila_financiera(cierre):
    aporte = getattr(cierre, "aporte_nacional", None)
    aporte_monto = aporte.monto_aporte if aporte else 0
    aporte_pagado = aporte_monto if aporte and aporte.estado == AporteNacional.Estado.PAGADO else 0
    aporte_pendiente = aporte_monto if aporte and aporte.estado == AporteNacional.Estado.PENDIENTE else 0
    return {
        "cierre": cierre,
        "aporte": aporte,
        "aporte_monto": aporte_monto,
        "aporte_pagado": aporte_pagado,
        "aporte_pendiente": aporte_pendiente,
        "estado_aporte": aporte.get_estado_display() if aporte else "Sin generar",
    }


def _zonas_filiales():
    return (
        Iglesia.objects.filter(tipo=Iglesia.Tipo.FILIAL, activo=True, zona__isnull=False)
        .values("zona_id", "zona__nombre")
        .distinct()
        .order_by("zona__nombre")
    )

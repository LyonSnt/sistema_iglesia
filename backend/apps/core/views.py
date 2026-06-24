from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse
from django.views.generic import TemplateView

from .permisos import (
    ACCION_GESTIONAR,
    ACCION_VER,
    MODULO_APORTES_NACIONALES,
    MODULO_AUDITORIA,
    MODULO_CARGOS,
    MODULO_CERTIFICADOS,
    MODULO_ESCUELA_DOMINICAL,
    MODULO_FINANZAS,
    MODULO_IGLESIAS,
    MODULO_INVENTARIO,
    MODULO_MIEMBROS,
    MODULO_MINISTERIOS,
    MODULO_PARAMETROS,
    MODULO_REPORTES,
    MODULO_TRASLADOS,
    MODULO_USUARIOS,
    usuario_puede,
)


class EcclesiaLoginView(LoginView):
    template_name = "core/login.html"
    redirect_authenticated_user = True


class CambiarPasswordObligatorioView(PasswordChangeView):
    template_name = "core/password_change.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.debe_cambiar_password = False
        self.request.user.save(update_fields=["debe_cambiar_password"])
        return response

    def get_success_url(self):
        return reverse("core:dashboard")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    MODULOS = (
        {
            "codigo": MODULO_MIEMBROS,
            "nombre": "Miembros y familias",
            "descripcion": "Registro pastoral, familias y membresia.",
            "url_name": "familias:list",
        },
        {
            "codigo": MODULO_CARGOS,
            "nombre": "Cargos y directivas",
            "descripcion": "Asignaciones locales y nacionales.",
            "url_name": "cargos:list",
        },
        {
            "codigo": MODULO_MINISTERIOS,
            "nombre": "Ministerios",
            "descripcion": "Equipos de servicio y participacion.",
            "url_name": "ministerios:list",
        },
        {
            "codigo": MODULO_ESCUELA_DOMINICAL,
            "nombre": "Escuela Dominical",
            "descripcion": "Clases, asistencia y promociones.",
            "url_name": "escuela_dominical:list",
        },
        {
            "codigo": MODULO_FINANZAS,
            "nombre": "Finanzas locales",
            "descripcion": "Ingresos, egresos y cierres.",
            "url_name": "finanzas:list",
        },
        {
            "codigo": MODULO_APORTES_NACIONALES,
            "nombre": "Aportes nacionales",
            "descripcion": "Cuenta filial-nacional y recibos.",
            "url_name": "aportes_nacionales:list",
        },
        {
            "codigo": MODULO_CERTIFICADOS,
            "nombre": "Certificados",
            "descripcion": "Documentos, numeracion y control.",
            "url_name": "certificados:list",
        },
        {
            "codigo": MODULO_TRASLADOS,
            "nombre": "Traslados",
            "descripcion": "Movimiento de miembros entre iglesias.",
            "url_name": "traslados:list",
        },
        {
            "codigo": MODULO_INVENTARIO,
            "nombre": "Inventario",
            "descripcion": "Activos, responsables y ubicaciones.",
            "url_name": "inventario:list",
        },
        {
            "codigo": MODULO_IGLESIAS,
            "nombre": "Iglesias y zonas",
            "descripcion": "Estructura nacional y filiales.",
            "url_name": "iglesias:list",
        },
        {
            "codigo": MODULO_USUARIOS,
            "nombre": "Usuarios y roles",
            "descripcion": "Cuentas, perfiles y acceso.",
            "url_name": "usuarios:list",
        },
        {
            "codigo": MODULO_PARAMETROS,
            "nombre": "Parametros",
            "descripcion": "Configuracion funcional general.",
        },
        {
            "codigo": MODULO_REPORTES,
            "nombre": "Reportes",
            "descripcion": "Lecturas consolidadas segun rol.",
            "url_name": "reportes:finanzas",
        },
        {
            "codigo": MODULO_AUDITORIA,
            "nombre": "Auditoria",
            "descripcion": "Revision de acciones criticas.",
        },
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        modulos = []

        for modulo in self.MODULOS:
            puede_gestionar = usuario_puede(user, modulo["codigo"], ACCION_GESTIONAR)
            puede_ver = puede_gestionar or usuario_puede(user, modulo["codigo"], ACCION_VER)
            if puede_ver:
                modulos.append(
                    {
                        **modulo,
                        "puede_gestionar": puede_gestionar,
                        "url": reverse(modulo["url_name"]) if "url_name" in modulo else "",
                    }
                )

        context["modulos"] = modulos
        context["iglesia_actual"] = getattr(user, "iglesia", None)
        return context

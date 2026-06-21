from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework.views import APIView

from apps.core.permisos import (
    ACCION_GESTIONAR,
    ACCION_VER,
    MODULO_FINANZAS,
    MODULO_MIEMBROS,
    PermisoModuloDRF,
    obtener_roles_permitidos,
    usuario_puede,
    usuario_puede_acceder_iglesia,
)
from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario


class PermisosCoreTests(TestCase):
    def setUp(self):
        self.nacional = Iglesia.objects.create(
            codigo="NACIONAL",
            nombre="Iglesia Nacional",
            tipo=Iglesia.Tipo.NACIONAL,
        )
        self.filial = Iglesia.objects.create(
            codigo="PRUEBAS",
            nombre="Iglesia Filial Pruebas",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )
        self.otra_filial = Iglesia.objects.create(
            codigo="OTRA",
            nombre="Otra Iglesia",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )

    def crear_usuario(self, username, rol, iglesia=None, is_superuser=False):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
            is_superuser=is_superuser,
        )

    def test_gestionar_incluye_permiso_de_ver(self):
        roles_ver = obtener_roles_permitidos(MODULO_MIEMBROS, ACCION_VER)

        self.assertIn(Usuario.Rol.SECRETARIO_FILIAL, roles_ver)
        self.assertIn(Usuario.Rol.AUDITOR_NACIONAL, roles_ver)

    def test_usuario_filial_puede_gestionar_modulo_autorizado(self):
        usuario = self.crear_usuario(
            "secretario",
            Usuario.Rol.SECRETARIO_FILIAL,
            self.filial,
        )

        self.assertTrue(usuario_puede(usuario, MODULO_MIEMBROS, ACCION_GESTIONAR))
        self.assertFalse(usuario_puede(usuario, MODULO_FINANZAS, ACCION_GESTIONAR))

    def test_usuario_anonimo_no_tiene_permisos(self):
        self.assertFalse(usuario_puede(AnonymousUser(), MODULO_MIEMBROS, ACCION_VER))

    def test_alcance_por_iglesia_para_usuario_filial(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)

        self.assertTrue(usuario_puede_acceder_iglesia(usuario, self.filial))
        self.assertFalse(usuario_puede_acceder_iglesia(usuario, self.otra_filial))

    def test_usuario_nacional_accede_a_cualquier_iglesia(self):
        usuario = self.crear_usuario("auditor", Usuario.Rol.AUDITOR_NACIONAL, self.nacional)

        self.assertTrue(usuario_puede_acceder_iglesia(usuario, self.filial))
        self.assertTrue(usuario_puede_acceder_iglesia(usuario, self.otra_filial))


class PermisoModuloDRFTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.permission = PermisoModuloDRF()

    def test_drf_permission_usa_modulo_y_accion_de_la_vista(self):
        class Vista(APIView):
            modulo_permiso = MODULO_MIEMBROS
            accion_permiso = ACCION_GESTIONAR

        request = self.factory.get("/")
        request.user = Usuario(username="secretario", rol=Usuario.Rol.SECRETARIO_FILIAL)

        self.assertTrue(self.permission.has_permission(request, Vista()))

    def test_drf_permission_deniega_vista_sin_modulo(self):
        request = self.factory.get("/")
        request.user = Usuario(username="secretario", rol=Usuario.Rol.SECRETARIO_FILIAL)

        self.assertFalse(self.permission.has_permission(request, APIView()))


class CoreViewsTests(TestCase):
    def setUp(self):
        self.nacional = Iglesia.objects.create(
            codigo="NACIONAL",
            nombre="Iglesia Nacional",
            tipo=Iglesia.Tipo.NACIONAL,
        )
        self.filial = Iglesia.objects.create(
            codigo="PRUEBAS",
            nombre="Iglesia Filial Pruebas",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )

    def crear_usuario(self, username, rol, iglesia, is_staff=False):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
            is_staff=is_staff,
        )

    def test_dashboard_redirige_a_login_si_no_hay_sesion(self):
        response = self.client.get(reverse("core:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("core:login"), response["Location"])

    def test_login_permite_autenticar_y_redirige_al_dashboard(self):
        self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)

        response = self.client.post(
            reverse("core:login"),
            {"username": "pastor", "password": "Cambiar12345!"},
        )

        self.assertRedirects(response, reverse("core:dashboard"))

    def test_dashboard_muestra_modulos_permitidos_por_rol(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, "Finanzas locales")
        self.assertContains(response, "Aportes nacionales")
        self.assertNotContains(response, "Usuarios y roles")

    def test_dashboard_muestra_acceso_admin_a_staff(self):
        usuario = self.crear_usuario(
            "admin_nacional",
            Usuario.Rol.ADMIN_NACIONAL,
            self.nacional,
            is_staff=True,
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, "Administracion tecnica")

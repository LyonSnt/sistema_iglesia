from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.iglesias.models import Iglesia
from apps.auditoria.models import RegistroAuditoria

from .models import Usuario


class GestionDelegadaUsuariosTests(TestCase):
    def setUp(self):
        self.nacional = Iglesia.objects.create(
            codigo="NACIONAL", nombre="Iglesia Nacional", tipo=Iglesia.Tipo.NACIONAL
        )
        self.filial = Iglesia.objects.create(
            codigo="CALPAQUI",
            nombre="Calpaqui",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )
        self.otra = Iglesia.objects.create(
            codigo="ILUMAN",
            nombre="Iluman",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )
        for rol in Usuario.Rol.values:
            Group.objects.get_or_create(name=rol)
        self.pastor = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.secretario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.pastor_otra = self.crear_usuario("pastor_otra", Usuario.Rol.PASTOR_FILIAL, self.otra)
        self.admin = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def datos_usuario(self, **overrides):
        data = {
            "username": "maria.perez",
            "first_name": "Maria",
            "last_name": "Perez",
            "email": "maria@example.local",
            "cedula": "",
            "telefono": "",
            "iglesia": self.otra.pk,
            "rol": Usuario.Rol.SOLO_LECTURA,
            "password1": "Temporal12345!",
            "password2": "Temporal12345!",
        }
        data.update(overrides)
        return data

    def test_pastor_solo_lista_cuentas_delegables_de_su_iglesia(self):
        self.client.force_login(self.pastor)

        response = self.client.get(reverse("usuarios:list"))

        self.assertContains(response, "secretario")
        self.assertNotContains(response, "pastor_otra")
        self.assertNotContains(response, "admin_nacional")

    def test_pastor_crea_usuario_en_su_iglesia_aunque_fuerce_otra(self):
        self.client.force_login(self.pastor)

        response = self.client.post(reverse("usuarios:create"), self.datos_usuario())

        self.assertRedirects(response, reverse("usuarios:list"))
        usuario = Usuario.objects.get(username="maria.perez")
        self.assertEqual(usuario.iglesia, self.filial)
        self.assertEqual(usuario.rol, Usuario.Rol.SOLO_LECTURA)
        self.assertEqual(list(usuario.groups.values_list("name", flat=True)), [Usuario.Rol.SOLO_LECTURA])
        self.assertFalse(usuario.is_staff)
        registro = RegistroAuditoria.objects.get(registro_afectado=f"usuarios.Usuario:{usuario.pk}")
        self.assertEqual(registro.usuario, self.pastor)
        self.assertNotIn("password", registro.valor_nuevo)

    def test_pastor_no_puede_asignar_rol_de_autoridad(self):
        self.client.force_login(self.pastor)

        response = self.client.post(
            reverse("usuarios:create"),
            self.datos_usuario(rol=Usuario.Rol.PASTOR_FILIAL),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("rol", response.context["form"].errors)
        self.assertFalse(Usuario.objects.filter(username="maria.perez").exists())

    def test_pastor_no_puede_editar_otro_pastor(self):
        self.client.force_login(self.pastor)

        response = self.client.get(reverse("usuarios:update", args=[self.pastor_otra.pk]))

        self.assertEqual(response.status_code, 404)

    def test_secretario_no_puede_administrar_usuarios(self):
        self.client.force_login(self.secretario)

        response = self.client.get(reverse("usuarios:list"))

        self.assertEqual(response.status_code, 403)

    def test_nacional_crea_solo_autoridad_filial(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("usuarios:create"),
            self.datos_usuario(
                username="encargado.iluman",
                rol=Usuario.Rol.ENCARGADO_FILIAL,
            ),
        )

        self.assertRedirects(response, reverse("usuarios:list"))
        usuario = Usuario.objects.get(username="encargado.iluman")
        self.assertEqual(usuario.iglesia, self.otra)
        self.assertEqual(usuario.rol, Usuario.Rol.ENCARGADO_FILIAL)

    def test_pastor_restablece_password_de_cuenta_delegable(self):
        self.client.force_login(self.pastor)

        response = self.client.post(
            reverse("usuarios:password-reset", args=[self.secretario.pk]),
            {"password1": "NuevaTemporal123!", "password2": "NuevaTemporal123!"},
        )

        self.assertRedirects(response, reverse("usuarios:update", args=[self.secretario.pk]))
        self.secretario.refresh_from_db()
        self.assertTrue(self.secretario.check_password("NuevaTemporal123!"))
        self.assertTrue(self.secretario.debe_cambiar_password)
        registro = RegistroAuditoria.objects.get(accion="MODIFICAR")
        self.assertTrue(registro.valor_nuevo["password_modificada"])
        self.assertNotIn("password", registro.valor_nuevo)

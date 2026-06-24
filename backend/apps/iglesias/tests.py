from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.usuarios.models import Usuario

from .models import Iglesia


class GestionFilialesTests(TestCase):
    def setUp(self):
        self.nacional = Iglesia.objects.create(
            codigo="NACIONAL", nombre="Iglesia Nacional", tipo=Iglesia.Tipo.NACIONAL
        )
        for rol in Usuario.Rol.values:
            Group.objects.get_or_create(name=rol)
        self.admin = Usuario.objects.create_user(
            username="admin_nacional",
            password="Cambiar12345!",
            rol=Usuario.Rol.ADMIN_NACIONAL,
            iglesia=self.nacional,
        )
        self.pastor = Usuario.objects.create_user(
            username="pastor_pruebas",
            password="Cambiar12345!",
            rol=Usuario.Rol.PASTOR_FILIAL,
            iglesia=Iglesia.objects.create(
                codigo="PRUEBAS",
                nombre="Pruebas",
                tipo=Iglesia.Tipo.FILIAL,
                iglesia_matriz=self.nacional,
            ),
        )

    def datos_filial(self, **overrides):
        data = {
            "codigo": "calpaqui",
            "nombre": "Iglesia Calpaqui",
            "direccion": "",
            "telefono": "",
            "email": "",
            "zona": "",
            "responsable_principal": "Juan Perez",
            "responsable_username": "juan.perez",
            "responsable_nombres": "Juan",
            "responsable_apellidos": "Perez",
            "responsable_email": "juan@example.local",
            "responsable_rol": Usuario.Rol.PASTOR_FILIAL,
            "password1": "Temporal12345!",
            "password2": "Temporal12345!",
        }
        data.update(overrides)
        return data

    def test_nacional_crea_filial_y_autoridad_inicial_atomicamente(self):
        self.client.force_login(self.admin)

        response = self.client.post(reverse("iglesias:create"), self.datos_filial())

        self.assertRedirects(response, reverse("iglesias:list"))
        iglesia = Iglesia.objects.get(codigo="CALPAQUI")
        usuario = Usuario.objects.get(username="juan.perez")
        self.assertEqual(iglesia.tipo, Iglesia.Tipo.FILIAL)
        self.assertEqual(iglesia.iglesia_matriz, self.nacional)
        self.assertEqual(usuario.iglesia, iglesia)
        self.assertEqual(usuario.rol, Usuario.Rol.PASTOR_FILIAL)

    def test_alta_filial_distingue_iglesia_autoridad_y_acceso_temporal(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("iglesias:create"))

        self.assertContains(response, "Alta de filial")
        self.assertContains(response, "Datos de la iglesia")
        self.assertContains(response, "Autoridad inicial")
        self.assertContains(response, "Acceso temporal")

    def test_error_en_responsable_no_crea_filial(self):
        Usuario.objects.create_user(username="juan.perez", password="x")
        self.client.force_login(self.admin)

        response = self.client.post(reverse("iglesias:create"), self.datos_filial())

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Iglesia.objects.filter(codigo="CALPAQUI").exists())

    def test_pastor_no_puede_crear_filiales(self):
        self.client.force_login(self.pastor)

        response = self.client.get(reverse("iglesias:create"))

        self.assertEqual(response.status_code, 403)

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario

from .models import RegistroAuditoria


class AuditoriaIntervencionNacionalTests(TestCase):
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
        self.admin_nacional = Usuario.objects.create_user(
            username="admin_nacional",
            password="Cambiar12345!",
            rol=Usuario.Rol.ADMIN_NACIONAL,
            iglesia=self.nacional,
        )
        self.pastor = Usuario.objects.create_user(
            username="pastor",
            password="Cambiar12345!",
            rol=Usuario.Rol.PASTOR_FILIAL,
            iglesia=self.filial,
        )
        Group.objects.get_or_create(name=Usuario.Rol.PASTOR_FILIAL)

    def datos_filial(self):
        return {
            "codigo": "CALPAQUI",
            "nombre": "Iglesia Calpaqui",
            "direccion": "",
            "telefono": "",
            "email": "",
            "zona": "",
            "responsable_principal": "Juan Perez",
            "responsable_username": "juan.perez",
            "responsable_nombres": "Juan",
            "responsable_apellidos": "Perez",
            "responsable_email": "",
            "responsable_rol": Usuario.Rol.PASTOR_FILIAL,
            "password1": "Temporal12345!",
            "password2": "Temporal12345!",
        }

    def test_creacion_nacional_sobre_filial_genera_auditoria(self):
        self.client.force_login(self.admin_nacional)

        response = self.client.post(
            reverse("iglesias:create"),
            self.datos_filial(),
            REMOTE_ADDR="192.0.2.10",
        )

        self.assertEqual(response.status_code, 302)
        registro = RegistroAuditoria.objects.filter(modulo="iglesias").get()
        self.assertEqual(registro.usuario, self.admin_nacional)
        self.assertEqual(registro.accion, "CREAR")
        self.assertEqual(registro.modulo, "iglesias")
        self.assertEqual(registro.iglesia.codigo, "CALPAQUI")
        self.assertEqual(registro.ip, "192.0.2.10")
        self.assertEqual(registro.valor_nuevo["nombre"], "Iglesia Calpaqui")

    def test_modificacion_nacional_guarda_antes_y_despues(self):
        self.client.force_login(self.admin_nacional)

        response = self.client.post(
            reverse("iglesias:update", args=[self.filial.pk]),
            {
                "codigo": self.filial.codigo,
                "nombre": "Iglesia Pruebas Actualizada",
                "direccion": "",
                "telefono": "",
                "email": "",
                "zona": "",
                "estado": Iglesia.Estado.ACTIVA,
                "responsable_principal": "Responsable",
                "activo": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        registro = RegistroAuditoria.objects.filter(accion="MODIFICAR", modulo="iglesias").get()
        self.assertEqual(registro.valor_anterior["nombre"], "Iglesia Filial Pruebas")
        self.assertEqual(registro.valor_nuevo["nombre"], "Iglesia Pruebas Actualizada")

    def test_gestion_de_la_propia_filial_no_genera_auditoria_nacional(self):
        self.client.force_login(self.pastor)

        response = self.client.post(
            reverse("escuela_dominical:nivel-create"),
            {
                "iglesia": self.filial.pk,
                "nombre": "Primarios",
                "edad_minima": 7,
                "edad_maxima": 9,
                "orden": 1,
                "descripcion": "",
                "activo": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(RegistroAuditoria.objects.exists())

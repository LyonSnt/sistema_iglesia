from django.test import TestCase
from django.urls import reverse

from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.traslados.models import TrasladoMiembro
from apps.usuarios.models import Usuario


class ReporteTrasladosTests(TestCase):
    def setUp(self):
        self.nacional = Iglesia.objects.create(
            codigo="NACIONAL",
            nombre="Iglesia Nacional",
            tipo=Iglesia.Tipo.NACIONAL,
        )
        self.origen = Iglesia.objects.create(
            codigo="ORI",
            nombre="Iglesia Origen",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )
        self.destino = Iglesia.objects.create(
            codigo="DES",
            nombre="Iglesia Destino",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )
        self.otra = Iglesia.objects.create(
            codigo="OTRA",
            nombre="Otra Iglesia",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )
        self.miembro = Miembro.objects.create(
            iglesia=self.origen,
            nombres="Ana Maria",
            apellidos="Lopez",
            cedula="0606060606",
            sexo=Miembro.Sexo.FEMENINO,
        )
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra,
            nombres="Carlos",
            apellidos="Mora",
            cedula="0707070707",
            sexo=Miembro.Sexo.MASCULINO,
        )
        solicitante = self.crear_usuario("solicitante", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.traslado = TrasladoMiembro.objects.create(
            miembro=self.miembro,
            iglesia_origen=self.origen,
            iglesia_destino=self.destino,
            motivo="Cambio de domicilio",
            solicitado_por=solicitante,
        )
        self.traslado_rechazado = TrasladoMiembro.objects.create(
            miembro=self.miembro_otra,
            iglesia_origen=self.otra,
            iglesia_destino=self.destino,
            estado=TrasladoMiembro.Estado.RECHAZADO,
            motivo="No procede",
            solicitado_por=self.crear_usuario("solicitante_otra", Usuario.Rol.SECRETARIO_FILIAL, self.otra),
        )

    def crear_usuario(self, username, rol, iglesia, is_superuser=False):
        usuario = Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )
        if is_superuser:
            usuario.is_superuser = True
            usuario.is_staff = True
            usuario.save(update_fields=["is_superuser", "is_staff"])
        return usuario

    def test_admin_nacional_accede_reporte_consolidado(self):
        usuario = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:traslados"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Maria")
        self.assertContains(response, "Carlos")
        self.assertContains(response, "Reporte de traslados")

    def test_filial_no_accede_reporte_nacional(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:traslados"))

        self.assertEqual(response.status_code, 403)

    def test_reporte_filtra_por_estado(self):
        usuario = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:traslados"), {"estado": TrasladoMiembro.Estado.RECHAZADO})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Ana Maria")
        self.assertContains(response, "Carlos")

    def test_superadmin_accede_reporte(self):
        usuario = self.crear_usuario("superadmin", Usuario.Rol.SUPERADMIN, self.nacional, is_superuser=True)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:traslados"))

        self.assertEqual(response.status_code, 200)

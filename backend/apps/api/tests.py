from django.urls import reverse
from rest_framework.test import APITestCase

from apps.cargos.models import AsignacionCargo, Cargo
from apps.familias.models import Familia, Matrimonio, MiembroFamilia
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.usuarios.models import Usuario


class ApiConsultaMiembrosFamiliasTests(APITestCase):
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
        self.miembro = Miembro.objects.create(
            iglesia=self.filial,
            nombres="Ana Maria",
            apellidos="Lopez",
            cedula="0101010101",
            sexo=Miembro.Sexo.FEMENINO,
        )
        self.conyuge = Miembro.objects.create(
            iglesia=self.filial,
            nombres="Luis",
            apellidos="Perez",
            cedula="0202020202",
            sexo=Miembro.Sexo.MASCULINO,
        )
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra_filial,
            nombres="Carlos",
            apellidos="Mora",
            cedula="0303030303",
            sexo=Miembro.Sexo.MASCULINO,
        )
        self.familia = Familia.objects.create(
            iglesia=self.filial,
            nombre="Familia Perez Lopez",
            jefe_hogar=self.conyuge,
        )
        self.familia_otra = Familia.objects.create(
            iglesia=self.otra_filial,
            nombre="Familia Mora",
            jefe_hogar=self.miembro_otra,
        )
        MiembroFamilia.objects.create(
            familia=self.familia,
            miembro=self.miembro,
            relacion=MiembroFamilia.Relacion.CONYUGE,
        )
        self.matrimonio = Matrimonio.objects.create(
            iglesia=self.filial,
            conyuge_1=self.miembro,
            conyuge_2=self.conyuge,
            fecha_matrimonio="2026-06-20",
            familia=self.familia,
        )
        self.matrimonio_otra = Matrimonio.objects.create(
            iglesia=self.otra_filial,
            conyuge_1=self.miembro_otra,
            conyuge_2=self.miembro_otra,
            fecha_matrimonio="2026-06-21",
            familia=self.familia_otra,
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def test_health_es_publico(self):
        response = self.client.get(reverse("api:health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")

    def test_api_requiere_sesion(self):
        response = self.client.get(reverse("api:miembro-list"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_filial_solo_ve_miembros_de_su_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:miembro-list"))

        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.data}
        self.assertIn(self.miembro.id, ids)
        self.assertNotIn(self.miembro_otra.id, ids)

    def test_usuario_nacional_ve_miembros_de_todas_las_iglesias(self):
        usuario = self.crear_usuario("auditor", Usuario.Rol.AUDITOR_NACIONAL, self.nacional)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:miembro-list"))

        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.data}
        self.assertIn(self.miembro.id, ids)
        self.assertIn(self.miembro_otra.id, ids)

    def test_detalle_de_miembro_de_otra_iglesia_responde_404_para_filial(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:miembro-detail", args=[self.miembro_otra.pk]))

        self.assertEqual(response.status_code, 404)

    def test_busqueda_de_miembros(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:miembro-list"), {"q": "010101"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.miembro.id)

    def test_familias_incluye_integrantes_y_respeta_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:familia-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.familia.id)
        self.assertEqual(response.data[0]["integrantes"][0]["miembro"]["id"], self.miembro.id)

    def test_matrimonios_respeta_iglesia_y_filtra_por_miembro(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:matrimonio-list"), {"miembro": self.miembro.pk})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.matrimonio.id)

    def test_rol_sin_permiso_de_miembros_recibe_403(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:miembro-list"))

        self.assertEqual(response.status_code, 403)


class ApiConsultaCargosTests(APITestCase):
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
        self.cargo_filial = Cargo.objects.create(nombre="Pastor", es_nacional=False)
        self.cargo_nacional = Cargo.objects.create(nombre="Presidente", es_nacional=True)
        self.miembro = Miembro.objects.create(
            iglesia=self.filial,
            nombres="Ana Maria",
            apellidos="Lopez",
            cedula="0101010101",
            sexo=Miembro.Sexo.FEMENINO,
        )
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra_filial,
            nombres="Carlos",
            apellidos="Mora",
            cedula="0202020202",
            sexo=Miembro.Sexo.MASCULINO,
        )
        self.asignacion = AsignacionCargo.objects.create(
            iglesia=self.filial,
            cargo=self.cargo_filial,
            miembro=self.miembro,
            fecha_inicio="2026-01-01",
        )
        self.asignacion_otra = AsignacionCargo.objects.create(
            iglesia=self.otra_filial,
            cargo=self.cargo_filial,
            miembro=self.miembro_otra,
            fecha_inicio="2026-01-01",
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def test_lista_cargos_filial_excluye_cargos_nacionales(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:cargo-list"))

        self.assertEqual(response.status_code, 200)
        nombres = {item["nombre"] for item in response.data}
        self.assertIn("Pastor", nombres)
        self.assertNotIn("Presidente", nombres)

    def test_lista_cargos_nacional_incluye_cargos_nacionales(self):
        usuario = self.crear_usuario("auditor", Usuario.Rol.AUDITOR_NACIONAL, self.nacional)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:cargo-list"))

        self.assertEqual(response.status_code, 200)
        nombres = {item["nombre"] for item in response.data}
        self.assertIn("Pastor", nombres)
        self.assertIn("Presidente", nombres)

    def test_asignaciones_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:asignacion-cargo-list"))

        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.data}
        self.assertIn(self.asignacion.id, ids)
        self.assertNotIn(self.asignacion_otra.id, ids)

    def test_asignaciones_nacional_ve_todas(self):
        usuario = self.crear_usuario("auditor", Usuario.Rol.AUDITOR_NACIONAL, self.nacional)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:asignacion-cargo-list"))

        self.assertEqual(response.status_code, 200)
        ids = {item["id"] for item in response.data}
        self.assertIn(self.asignacion.id, ids)
        self.assertIn(self.asignacion_otra.id, ids)

    def test_busqueda_asignaciones(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:asignacion-cargo-list"), {"q": "Ana"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.asignacion.id)

    def test_detalle_de_asignacion_de_otra_iglesia_responde_404_para_filial(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:asignacion-cargo-detail", args=[self.asignacion_otra.pk]))

        self.assertEqual(response.status_code, 404)

    def test_rol_sin_permiso_de_cargos_recibe_403(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_authenticate(usuario)

        response = self.client.get(reverse("api:asignacion-cargo-list"))

        self.assertEqual(response.status_code, 403)

from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.ministerios.models import Ministerio, ParticipacionMinisterio
from apps.usuarios.models import Usuario


class MinisterioViewsTests(TestCase):
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
        self.otro_miembro = Miembro.objects.create(
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
        self.lider = self.crear_usuario("lider", Usuario.Rol.LIDER_MINISTERIO, self.filial)
        self.otro_lider = self.crear_usuario("otro_lider", Usuario.Rol.LIDER_MINISTERIO, self.filial)
        self.ministerio = Ministerio.objects.create(
            iglesia=self.filial,
            nombre="Alabanza",
            tipo=Ministerio.Tipo.MINISTERIO,
            responsable=self.miembro,
            lider=self.lider,
        )
        self.ministerio_otra = Ministerio.objects.create(
            iglesia=self.otra_filial,
            nombre="Jovenes",
            tipo=Ministerio.Tipo.GRUPO,
            responsable=self.miembro_otra,
        )
        self.participacion = ParticipacionMinisterio.objects.create(
            ministerio=self.ministerio,
            miembro=self.otro_miembro,
            cargo="Guitarra",
            fecha_inicio=date(2026, 1, 1),
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def datos_ministerio(self, **overrides):
        data = {
            "iglesia": self.filial.pk,
            "nombre": "Evangelismo",
            "tipo": Ministerio.Tipo.MINISTERIO,
            "descripcion": "",
            "responsable": self.miembro.pk,
            "lider": self.lider.pk,
            "activo": "on",
        }
        data.update(overrides)
        return data

    def test_listado_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("ministerios:list"))

        self.assertContains(response, "Alabanza")
        self.assertNotContains(response, "Jovenes")

    def test_usuario_nacional_no_accede_modulo_operativo_de_ministerios(self):
        usuario = self.crear_usuario("auditor", Usuario.Rol.AUDITOR_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("ministerios:list"))

        self.assertEqual(response.status_code, 403)

    def test_detalle_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("ministerios:detail", args=[self.ministerio.pk]))
        response_otra = self.client.get(reverse("ministerios:detail", args=[self.ministerio_otra.pk]))

        self.assertContains(response, "Alabanza")
        self.assertContains(response, "Guitarra")
        self.assertEqual(response_otra.status_code, 404)

    def test_usuario_con_permiso_puede_crear_ministerio(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(reverse("ministerios:create"), self.datos_ministerio())

        self.assertRedirects(response, reverse("ministerios:list"))
        ministerio = Ministerio.objects.get(nombre="Evangelismo")
        self.assertEqual(ministerio.iglesia, self.filial)

    def test_filial_no_puede_forzar_otra_iglesia(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("ministerios:create"),
            self.datos_ministerio(iglesia=self.otra_filial.pk, nombre="Forzado"),
        )

        self.assertRedirects(response, reverse("ministerios:list"))
        ministerio = Ministerio.objects.get(nombre="Forzado")
        self.assertEqual(ministerio.iglesia, self.filial)

    def test_no_permite_responsable_de_otra_iglesia(self):
        usuario = self.crear_usuario("superadmin", Usuario.Rol.SUPERADMIN, self.nacional)
        usuario.is_superuser = True
        usuario.save(update_fields=["is_superuser"])
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("ministerios:create"),
            self.datos_ministerio(responsable=self.miembro_otra.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El responsable debe pertenecer")

    def test_usuario_sin_gestion_no_puede_crear(self):
        usuario = self.crear_usuario("lectura", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("ministerios:create"))

        self.assertEqual(response.status_code, 403)

    def test_agregar_participacion(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("ministerios:participacion_add", args=[self.ministerio.pk]),
            {
                "miembro": self.miembro.pk,
                "cargo": "Voz",
                "fecha_inicio": "2026-02-01",
                "fecha_fin": "",
                "estado": ParticipacionMinisterio.Estado.ACTIVO,
                "motivo_salida": "",
                "activo": "on",
            },
        )

        self.assertRedirects(response, reverse("ministerios:detail", args=[self.ministerio.pk]))
        self.assertTrue(
            ParticipacionMinisterio.objects.filter(
                ministerio=self.ministerio,
                miembro=self.miembro,
                cargo="Voz",
            ).exists()
        )

    def test_no_permite_participante_de_otra_iglesia(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("ministerios:participacion_add", args=[self.ministerio.pk]),
            {
                "miembro": self.miembro_otra.pk,
                "cargo": "Voz",
                "fecha_inicio": "2026-02-01",
                "fecha_fin": "",
                "estado": ParticipacionMinisterio.Estado.ACTIVO,
                "motivo_salida": "",
                "activo": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("miembro", response.context["form"].errors)

    def test_finalizar_participacion(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("ministerios:participacion_finalize", args=[self.ministerio.pk, self.participacion.pk]),
            {"fecha_fin": "2026-06-01", "motivo_salida": "Cierre de ciclo"},
        )

        self.assertRedirects(response, reverse("ministerios:detail", args=[self.ministerio.pk]))
        self.participacion.refresh_from_db()
        self.assertEqual(self.participacion.estado, ParticipacionMinisterio.Estado.FINALIZADO)
        self.assertEqual(self.participacion.fecha_fin, date(2026, 6, 1))
        self.assertFalse(self.participacion.activo)

    def test_filial_no_puede_finalizar_participacion_de_otra_iglesia(self):
        participacion_otra = ParticipacionMinisterio.objects.create(
            ministerio=self.ministerio_otra,
            miembro=self.miembro_otra,
            cargo="Lider",
            fecha_inicio=date(2026, 1, 1),
        )
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("ministerios:participacion_finalize", args=[self.ministerio_otra.pk, participacion_otra.pk]),
            {"fecha_fin": "2026-06-01", "motivo_salida": ""},
        )

        self.assertEqual(response.status_code, 404)

    def test_lider_solo_ve_ministerio_asignado(self):
        Ministerio.objects.create(
            iglesia=self.filial,
            nombre="Evangelismo",
            tipo=Ministerio.Tipo.MINISTERIO,
            responsable=self.otro_miembro,
            lider=self.otro_lider,
        )
        self.client.force_login(self.lider)

        response = self.client.get(reverse("ministerios:list"))

        self.assertContains(response, "Alabanza")
        self.assertNotContains(response, "Evangelismo")

    def test_lider_no_puede_crear_ni_editar_ministerio(self):
        self.client.force_login(self.lider)

        crear = self.client.get(reverse("ministerios:create"))
        editar = self.client.get(reverse("ministerios:update", args=[self.ministerio.pk]))

        self.assertEqual(crear.status_code, 403)
        self.assertEqual(editar.status_code, 403)

    def test_lider_puede_agregar_participante_a_ministerio_asignado(self):
        self.client.force_login(self.lider)

        response = self.client.post(
            reverse("ministerios:participacion_add", args=[self.ministerio.pk]),
            {
                "miembro": self.miembro.pk,
                "cargo": "Voz",
                "fecha_inicio": "2026-02-01",
                "fecha_fin": "",
                "estado": ParticipacionMinisterio.Estado.ACTIVO,
                "motivo_salida": "",
                "activo": "on",
            },
        )

        self.assertRedirects(response, reverse("ministerios:detail", args=[self.ministerio.pk]))

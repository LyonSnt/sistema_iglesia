from django.test import TestCase
from django.urls import reverse

from apps.familias.models import Familia, MiembroFamilia
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.usuarios.models import Usuario


class FamiliaViewsTests(TestCase):
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
        self.miembro_pruebas = Miembro.objects.create(
            iglesia=self.filial,
            nombres="Ana Maria",
            apellidos="Lopez",
            cedula="0101010101",
            sexo=Miembro.Sexo.FEMENINO,
        )
        self.otro_miembro_pruebas = Miembro.objects.create(
            iglesia=self.filial,
            nombres="Luis",
            apellidos="Lopez",
            cedula="0303030303",
            sexo=Miembro.Sexo.MASCULINO,
        )
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra_filial,
            nombres="Carlos",
            apellidos="Mora",
            cedula="0202020202",
            sexo=Miembro.Sexo.MASCULINO,
        )
        self.familia_pruebas = Familia.objects.create(
            iglesia=self.filial,
            nombre="Familia Lopez",
            jefe_hogar=self.miembro_pruebas,
            telefono="0991111111",
        )
        self.familia_otra = Familia.objects.create(
            iglesia=self.otra_filial,
            nombre="Familia Mora",
            jefe_hogar=self.miembro_otra,
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def datos_familia(self, **overrides):
        data = {
            "iglesia": self.filial.pk,
            "nombre": "Familia Nueva",
            "jefe_hogar": self.miembro_pruebas.pk,
            "direccion": "Calle 1",
            "telefono": "0999999999",
            "activo": "on",
        }
        data.update(overrides)
        return data

    def test_listado_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("familias:list"))

        self.assertContains(response, "Familia Lopez")
        self.assertNotContains(response, "Familia Mora")

    def test_usuario_nacional_ve_todas_las_familias(self):
        usuario = self.crear_usuario("auditor", Usuario.Rol.AUDITOR_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("familias:list"))

        self.assertContains(response, "Familia Lopez")
        self.assertContains(response, "Familia Mora")

    def test_detalle_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("familias:detail", args=[self.familia_pruebas.pk]))
        response_otra = self.client.get(reverse("familias:detail", args=[self.familia_otra.pk]))

        self.assertContains(response, "Familia Lopez")
        self.assertEqual(response_otra.status_code, 404)

    def test_usuario_con_permiso_puede_crear_familia_en_su_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(reverse("familias:create"), self.datos_familia())

        self.assertRedirects(response, reverse("familias:list"))
        familia = Familia.objects.get(nombre="Familia Nueva")
        self.assertEqual(familia.iglesia, self.filial)
        self.assertTrue(
            MiembroFamilia.objects.filter(
                familia=familia,
                miembro=self.miembro_pruebas,
                relacion=MiembroFamilia.Relacion.REPRESENTANTE,
                activo=True,
            ).exists()
        )

    def test_usuario_filial_no_puede_forzar_otra_iglesia_al_crear(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:create"),
            self.datos_familia(iglesia=self.otra_filial.pk, nombre="Familia Forzada"),
        )

        self.assertRedirects(response, reverse("familias:list"))
        familia = Familia.objects.get(nombre="Familia Forzada")
        self.assertEqual(familia.iglesia, self.filial)

    def test_no_permite_jefe_hogar_de_otra_iglesia(self):
        usuario = self.crear_usuario("admin", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:create"),
            self.datos_familia(iglesia=self.filial.pk, jefe_hogar=self.miembro_otra.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El jefe de hogar debe pertenecer")

    def test_usuario_sin_gestion_no_puede_crear(self):
        usuario = self.crear_usuario("lectura", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("familias:create"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_filial_no_puede_editar_familia_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("familias:update", args=[self.familia_otra.pk]))

        self.assertEqual(response.status_code, 404)

    def test_cambiar_jefe_hogar_crea_vinculo_representante(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:update", args=[self.familia_pruebas.pk]),
            self.datos_familia(
                nombre="Familia Lopez",
                jefe_hogar=self.otro_miembro_pruebas.pk,
                telefono="0991111111",
            ),
        )

        self.assertRedirects(response, reverse("familias:list"))
        self.familia_pruebas.refresh_from_db()
        self.assertEqual(self.familia_pruebas.jefe_hogar, self.otro_miembro_pruebas)
        self.assertTrue(
            MiembroFamilia.objects.filter(
                familia=self.familia_pruebas,
                miembro=self.otro_miembro_pruebas,
                relacion=MiembroFamilia.Relacion.REPRESENTANTE,
                activo=True,
            ).exists()
        )

    def test_agregar_integrante_a_familia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:integrante_add", args=[self.familia_pruebas.pk]),
            {
                "miembro": self.otro_miembro_pruebas.pk,
                "relacion": MiembroFamilia.Relacion.HIJO,
            },
        )

        self.assertRedirects(response, reverse("familias:detail", args=[self.familia_pruebas.pk]))
        self.assertTrue(
            MiembroFamilia.objects.filter(
                familia=self.familia_pruebas,
                miembro=self.otro_miembro_pruebas,
                relacion=MiembroFamilia.Relacion.HIJO,
            ).exists()
        )

    def test_no_permite_integrante_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:integrante_add", args=[self.familia_pruebas.pk]),
            {
                "miembro": self.miembro_otra.pk,
                "relacion": MiembroFamilia.Relacion.HIJO,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("miembro", response.context["form"].errors)

    def test_no_permite_duplicar_integrante_con_misma_relacion(self):
        MiembroFamilia.objects.create(
            familia=self.familia_pruebas,
            miembro=self.otro_miembro_pruebas,
            relacion=MiembroFamilia.Relacion.HIJO,
        )
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:integrante_add", args=[self.familia_pruebas.pk]),
            {
                "miembro": self.otro_miembro_pruebas.pk,
                "relacion": MiembroFamilia.Relacion.HIJO,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El integrante ya tiene esa relacion")

    def test_desactivar_integrante(self):
        integrante = MiembroFamilia.objects.create(
            familia=self.familia_pruebas,
            miembro=self.otro_miembro_pruebas,
            relacion=MiembroFamilia.Relacion.HIJO,
        )
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:integrante_deactivate", args=[self.familia_pruebas.pk, integrante.pk])
        )

        self.assertRedirects(response, reverse("familias:detail", args=[self.familia_pruebas.pk]))
        integrante.refresh_from_db()
        self.assertFalse(integrante.activo)

    def test_usuario_sin_gestion_no_puede_desactivar_integrante(self):
        integrante = MiembroFamilia.objects.create(
            familia=self.familia_pruebas,
            miembro=self.otro_miembro_pruebas,
            relacion=MiembroFamilia.Relacion.HIJO,
        )
        usuario = self.crear_usuario("lectura", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:integrante_deactivate", args=[self.familia_pruebas.pk, integrante.pk])
        )

        self.assertEqual(response.status_code, 403)
        integrante.refresh_from_db()
        self.assertTrue(integrante.activo)

    def test_usuario_filial_no_puede_desactivar_integrante_de_otra_iglesia(self):
        integrante = MiembroFamilia.objects.create(
            familia=self.familia_otra,
            miembro=self.miembro_otra,
            relacion=MiembroFamilia.Relacion.HIJO,
        )
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:integrante_deactivate", args=[self.familia_otra.pk, integrante.pk])
        )

        self.assertEqual(response.status_code, 404)
        integrante.refresh_from_db()
        self.assertTrue(integrante.activo)

    def test_agregar_integrante_reactiva_vinculo_inactivo(self):
        integrante = MiembroFamilia.objects.create(
            familia=self.familia_pruebas,
            miembro=self.otro_miembro_pruebas,
            relacion=MiembroFamilia.Relacion.HIJO,
            activo=False,
        )
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("familias:integrante_add", args=[self.familia_pruebas.pk]),
            {
                "miembro": self.otro_miembro_pruebas.pk,
                "relacion": MiembroFamilia.Relacion.HIJO,
            },
        )

        self.assertRedirects(response, reverse("familias:detail", args=[self.familia_pruebas.pk]))
        integrante.refresh_from_db()
        self.assertTrue(integrante.activo)

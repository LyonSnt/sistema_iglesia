from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.traslados.models import Traslado
from apps.usuarios.models import Usuario


class TrasladoViewsTests(TestCase):
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
            cedula="0101010101",
            sexo=Miembro.Sexo.FEMENINO,
        )
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra,
            nombres="Carlos",
            apellidos="Mora",
            cedula="0202020202",
            sexo=Miembro.Sexo.MASCULINO,
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def crear_traslado(self, **overrides):
        usuario = overrides.pop("solicitado_por", None)
        if usuario is None:
            usuario = self.crear_usuario(f"solicitante_{Traslado.objects.count()}", Usuario.Rol.PASTOR_FILIAL, self.origen)
        data = {
            "iglesia": self.origen,
            "iglesia_destino": self.destino,
            "miembro": self.miembro,
            "solicitado_por": usuario,
            "fecha_solicitud": date(2026, 6, 1),
            "motivo": "Cambio de domicilio",
        }
        data.update(overrides)
        return Traslado.objects.create(**data)

    def datos_traslado(self, **overrides):
        data = {
            "iglesia": self.origen.pk,
            "miembro": self.miembro.pk,
            "iglesia_destino": self.destino.pk,
            "fecha_solicitud": "2026-06-01",
            "motivo": "Cambio de domicilio",
        }
        data.update(overrides)
        return data

    def test_listado_muestra_traslados_de_origen_y_destino(self):
        traslado = self.crear_traslado()
        otro = self.crear_traslado(
            iglesia=self.otra,
            iglesia_destino=self.origen,
            miembro=self.miembro_otra,
            solicitado_por=self.crear_usuario("pastor_otra", Usuario.Rol.PASTOR_FILIAL, self.otra),
        )
        self.crear_traslado(
            iglesia=self.destino,
            iglesia_destino=self.otra,
            miembro=Miembro.objects.create(
                iglesia=self.destino,
                nombres="Luis",
                apellidos="Vera",
                cedula="0303030303",
                sexo=Miembro.Sexo.MASCULINO,
            ),
            solicitado_por=self.crear_usuario("pastor_destino", Usuario.Rol.PASTOR_FILIAL, self.destino),
        )
        usuario = self.crear_usuario("pastor_origen", Usuario.Rol.PASTOR_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.get(reverse("traslados:list"))

        self.assertContains(response, traslado.miembro.nombres)
        self.assertContains(response, otro.miembro.nombres)
        self.assertNotContains(response, "Luis")

    def test_usuario_sin_permiso_no_accede(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.get(reverse("traslados:list"))

        self.assertEqual(response.status_code, 403)

    def test_crear_traslado_usa_iglesia_del_usuario(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("traslados:create"),
            self.datos_traslado(iglesia=self.otra.pk),
        )

        self.assertRedirects(response, reverse("traslados:list"))
        traslado = Traslado.objects.get(miembro=self.miembro)
        self.assertEqual(traslado.iglesia, self.origen)
        self.assertEqual(traslado.solicitado_por, usuario)

    def test_no_permite_miembro_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("traslados:create"),
            self.datos_traslado(miembro=self.miembro_otra.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Traslado.objects.exists())
        self.assertIn("miembro", response.context["form"].errors)

    def test_no_permite_destino_igual_al_origen(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("traslados:create"),
            self.datos_traslado(iglesia_destino=self.origen.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Traslado.objects.exists())
        self.assertIn("iglesia_destino", response.context["form"].errors)

    def test_destino_aprueba_y_mueve_miembro(self):
        traslado = self.crear_traslado()
        usuario = self.crear_usuario("pastor_destino", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("traslados:approve", args=[traslado.pk]),
            {"fecha_respuesta": "2026-06-02", "observacion_respuesta": "Recibido"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.miembro.refresh_from_db()
        self.assertEqual(traslado.estado, Traslado.Estado.APROBADO)
        self.assertEqual(traslado.respondido_por, usuario)
        self.assertEqual(self.miembro.iglesia, self.destino)
        self.assertEqual(self.miembro.estado, Miembro.Estado.ACTIVO)

    def test_origen_no_puede_aprobar(self):
        traslado = self.crear_traslado()
        usuario = self.crear_usuario("pastor_origen", Usuario.Rol.PASTOR_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("traslados:approve", args=[traslado.pk]),
            {"fecha_respuesta": "2026-06-02", "observacion_respuesta": ""},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.miembro.refresh_from_db()
        self.assertEqual(traslado.estado, Traslado.Estado.SOLICITADO)
        self.assertEqual(self.miembro.iglesia, self.origen)

    def test_destino_rechaza_sin_mover_miembro(self):
        traslado = self.crear_traslado()
        usuario = self.crear_usuario("pastor_destino", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("traslados:reject", args=[traslado.pk]),
            {"fecha_respuesta": "2026-06-02", "observacion_respuesta": "No procede"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.miembro.refresh_from_db()
        self.assertEqual(traslado.estado, Traslado.Estado.RECHAZADO)
        self.assertEqual(self.miembro.iglesia, self.origen)

    def test_origen_cancela_solicitud(self):
        traslado = self.crear_traslado()
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("traslados:cancel", args=[traslado.pk]),
            {"fecha_respuesta": "2026-06-02", "observacion_respuesta": "Duplicado"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.assertEqual(traslado.estado, Traslado.Estado.CANCELADO)

    def test_filial_no_ve_traslado_sin_relacion(self):
        traslado = self.crear_traslado()
        usuario = self.crear_usuario("pastor_otra", Usuario.Rol.PASTOR_FILIAL, self.otra)
        self.client.force_login(usuario)

        response = self.client.get(reverse("traslados:detail", args=[traslado.pk]))

        self.assertEqual(response.status_code, 404)

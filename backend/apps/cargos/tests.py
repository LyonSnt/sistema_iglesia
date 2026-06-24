from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.cargos.models import AsignacionCargo, Cargo
from apps.documentos.models import DocumentoAdjunto
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.usuarios.models import Usuario


class AsignacionCargoViewsTests(TestCase):
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
            fecha_inicio=date(2026, 1, 1),
        )
        self.asignacion_otra = AsignacionCargo.objects.create(
            iglesia=self.otra_filial,
            cargo=self.cargo_filial,
            miembro=self.miembro_otra,
            fecha_inicio=date(2026, 1, 1),
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def datos_asignacion(self, **overrides):
        data = {
            "iglesia": self.filial.pk,
            "cargo": self.cargo_filial.pk,
            "miembro": self.miembro.pk,
            "usuario": "",
            "fecha_inicio": "2026-02-01",
            "fecha_fin": "",
            "estado": AsignacionCargo.Estado.VIGENTE,
            "observacion": "",
            "activo": "on",
        }
        data.update(overrides)
        return data

    def test_listado_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("cargos:list"))

        self.assertContains(response, "Ana Maria")
        self.assertNotContains(response, "Carlos")

    def test_usuario_nacional_no_accede_modulo_operativo_de_cargos(self):
        usuario = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("cargos:list"))

        self.assertEqual(response.status_code, 403)

    def test_detalle_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("cargos:detail", args=[self.asignacion.pk]))
        response_otra = self.client.get(reverse("cargos:detail", args=[self.asignacion_otra.pk]))

        self.assertContains(response, "Pastor")
        self.assertEqual(response_otra.status_code, 404)

    def test_usuario_con_permiso_puede_crear_asignacion(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(reverse("cargos:create"), self.datos_asignacion(fecha_inicio="2026-03-01"))

        self.assertRedirects(response, reverse("cargos:list"))
        asignacion = AsignacionCargo.objects.get(fecha_inicio=date(2026, 3, 1))
        self.assertEqual(asignacion.iglesia, self.filial)
        self.assertEqual(asignacion.miembro, self.miembro)

    def test_usuario_filial_no_puede_forzar_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:create"),
            self.datos_asignacion(iglesia=self.otra_filial.pk, fecha_inicio="2026-03-02"),
        )

        self.assertRedirects(response, reverse("cargos:list"))
        asignacion = AsignacionCargo.objects.get(fecha_inicio=date(2026, 3, 2))
        self.assertEqual(asignacion.iglesia, self.filial)

    def test_no_permite_miembro_de_otra_iglesia(self):
        usuario = self.crear_usuario("superadmin", Usuario.Rol.SUPERADMIN, self.nacional)
        usuario.is_superuser = True
        usuario.save(update_fields=["is_superuser"])
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:create"),
            self.datos_asignacion(miembro=self.miembro_otra.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El miembro debe pertenecer")

    def test_filial_no_puede_asignar_cargo_nacional(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:create"),
            self.datos_asignacion(cargo=self.cargo_nacional.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("cargo", response.context["form"].errors)

    def test_requiere_miembro_o_usuario_no_ambos(self):
        usuario_asignado = self.crear_usuario("asignado", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:create"),
            self.datos_asignacion(usuario=usuario_asignado.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seleccione solo un miembro")

    def test_fecha_fin_no_puede_ser_anterior(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:create"),
            self.datos_asignacion(fecha_inicio="2026-03-10", fecha_fin="2026-03-01"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "La fecha de fin no puede ser anterior")

    def test_usuario_sin_gestion_no_puede_crear(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("cargos:create"))

        self.assertEqual(response.status_code, 403)

    def test_finalizar_asignacion(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:finalize", args=[self.asignacion.pk]),
            {"fecha_fin": "2026-06-01", "observacion": "Cierre de periodo"},
        )

        self.assertRedirects(response, reverse("cargos:detail", args=[self.asignacion.pk]))
        self.asignacion.refresh_from_db()
        self.assertEqual(self.asignacion.estado, AsignacionCargo.Estado.FINALIZADO)
        self.assertEqual(self.asignacion.fecha_fin, date(2026, 6, 1))
        self.assertEqual(self.asignacion.observacion, "Cierre de periodo")

    def test_filial_no_puede_finalizar_asignacion_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:finalize", args=[self.asignacion_otra.pk]),
            {"fecha_fin": "2026-06-01", "observacion": ""},
        )

        self.assertEqual(response.status_code, 404)

    def test_adjunta_documento_a_asignacion(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:document-create", args=[self.asignacion.pk]),
            {
                "archivo": SimpleUploadedFile("acta.pdf", b"%PDF-1.4", content_type="application/pdf"),
                "nombre": "Acta de designacion",
                "tipo": DocumentoAdjunto.Tipo.ACTA,
                "descripcion": "Documento de respaldo",
            },
        )

        self.assertRedirects(response, reverse("cargos:detail", args=[self.asignacion.pk]))
        documento = DocumentoAdjunto.objects.get(nombre="Acta de designacion")
        self.assertEqual(documento.iglesia, self.filial)
        self.assertEqual(documento.content_object, self.asignacion)
        self.assertEqual(documento.subido_por, usuario)

    def test_descarga_documento_respeta_alcance_de_asignacion(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        usuario_otra = self.crear_usuario("secretario_otra", Usuario.Rol.SECRETARIO_FILIAL, self.otra_filial)
        documento = DocumentoAdjunto.objects.create(
            iglesia=self.otra_filial,
            content_object=self.asignacion_otra,
            archivo=SimpleUploadedFile("acta.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre="Acta externa",
            tipo=DocumentoAdjunto.Tipo.ACTA,
            subido_por=usuario_otra,
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("cargos:document-download", args=[self.asignacion_otra.pk, documento.pk]))

        self.assertEqual(response.status_code, 404)

    def test_anula_documento_de_asignacion_sin_borrar_archivo(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        documento = DocumentoAdjunto.objects.create(
            iglesia=self.filial,
            content_object=self.asignacion,
            archivo=SimpleUploadedFile("acta.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre="Acta de designacion",
            tipo=DocumentoAdjunto.Tipo.ACTA,
            subido_por=usuario,
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("cargos:document-deactivate", args=[self.asignacion.pk, documento.pk]),
            {"motivo": "Archivo reemplazado"},
        )

        self.assertRedirects(response, reverse("cargos:detail", args=[self.asignacion.pk]))
        documento.refresh_from_db()
        self.assertEqual(documento.estado, DocumentoAdjunto.Estado.ANULADO)
        self.assertEqual(documento.anulado_por, usuario)
        self.assertTrue(documento.archivo.name)

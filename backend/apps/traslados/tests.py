from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.auditoria.models import RegistroAuditoria
from apps.documentos.models import DocumentoAdjunto
from apps.familias.models import Familia, MiembroFamilia
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.traslados.models import TrasladoMiembro
from apps.usuarios.models import Usuario


class TrasladoMiembroTests(TestCase):
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
        self.familia = Familia.objects.create(
            iglesia=self.origen,
            nombre="Familia Lopez",
            jefe_hogar=self.miembro,
        )
        self.vinculo_familiar = MiembroFamilia.objects.create(
            familia=self.familia,
            miembro=self.miembro,
            relacion=MiembroFamilia.Relacion.REPRESENTANTE,
        )

    def crear_usuario(self, username, rol, iglesia, superuser=False):
        usuario = Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )
        if superuser:
            usuario.is_superuser = True
            usuario.is_staff = True
            usuario.save(update_fields=["is_superuser", "is_staff"])
        return usuario

    def crear_traslado(self):
        secretario = self.crear_usuario("solicitante", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        return TrasladoMiembro.objects.create(
            miembro=self.miembro,
            iglesia_origen=self.origen,
            iglesia_destino=self.destino,
            motivo="Cambio de domicilio",
            solicitado_por=secretario,
        )

    def datos_traslado(self, **overrides):
        data = {
            "miembro": self.miembro.pk,
            "iglesia_destino": self.destino.pk,
            "motivo": "Cambio de domicilio",
        }
        data.update(overrides)
        return data

    def test_secretario_origen_puede_solicitar_traslado(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.post(reverse("traslados:create"), self.datos_traslado())

        self.assertRedirects(response, reverse("traslados:list"))
        traslado = TrasladoMiembro.objects.get()
        self.assertEqual(traslado.iglesia_origen, self.origen)
        self.assertEqual(traslado.iglesia_destino, self.destino)
        self.assertEqual(traslado.estado, TrasladoMiembro.Estado.SOLICITADO)
        self.assertEqual(traslado.solicitado_por, usuario)
        self.miembro.refresh_from_db()
        self.assertEqual(self.miembro.iglesia, self.origen)
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="traslados", accion="SOLICITAR").exists())

    def test_filial_no_puede_solicitar_miembro_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.post(reverse("traslados:create"), self.datos_traslado(miembro=self.miembro_otra.pk))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TrasladoMiembro.objects.exists())

    def test_usuario_no_autorizado_no_accede_traslados(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.get(reverse("traslados:list"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_nacional_no_operativo_no_accede_traslados(self):
        usuario = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("traslados:list"))

        self.assertEqual(response.status_code, 403)

    def test_listado_muestra_origen_y_destino_pero_no_terceras_iglesias(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_destino", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)

        response = self.client.get(reverse("traslados:list"))

        self.assertContains(response, traslado.miembro.nombres)

        usuario_otra = self.crear_usuario("pastor_otra", Usuario.Rol.PASTOR_FILIAL, self.otra)
        self.client.force_login(usuario_otra)
        response_otra = self.client.get(reverse("traslados:list"))

        self.assertNotContains(response_otra, traslado.miembro.nombres)

    def test_destino_puede_aceptar_y_mueve_miembro(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_destino", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)

        response = self.client.post(
            reverse("traslados:aceptar", args=[traslado.pk]),
            {"observacion": "Recibido"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.miembro.refresh_from_db()
        self.vinculo_familiar.refresh_from_db()
        self.assertEqual(traslado.estado, TrasladoMiembro.Estado.ACEPTADO)
        self.assertEqual(traslado.respondido_por, usuario_destino)
        self.assertEqual(self.miembro.iglesia, self.destino)
        self.assertFalse(self.vinculo_familiar.activo)
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="traslados", accion="ACEPTAR").exists())

    def test_origen_no_puede_aceptar_su_propio_traslado(self):
        traslado = self.crear_traslado()
        usuario_origen = self.crear_usuario("pastor_origen", Usuario.Rol.PASTOR_FILIAL, self.origen)
        self.client.force_login(usuario_origen)

        response = self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": ""})

        self.assertEqual(response.status_code, 403)
        self.miembro.refresh_from_db()
        self.assertEqual(self.miembro.iglesia, self.origen)

    def test_destino_puede_rechazar_sin_mover_miembro(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("secretario_destino", Usuario.Rol.SECRETARIO_FILIAL, self.destino)
        self.client.force_login(usuario_destino)

        response = self.client.post(
            reverse("traslados:rechazar", args=[traslado.pk]),
            {"observacion": "No procede"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.miembro.refresh_from_db()
        self.assertEqual(traslado.estado, TrasladoMiembro.Estado.RECHAZADO)
        self.assertEqual(self.miembro.iglesia, self.origen)
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="traslados", accion="RECHAZAR").exists())

    def test_origen_puede_anular_sin_mover_miembro(self):
        traslado = self.crear_traslado()
        usuario_origen = self.crear_usuario("secretario_origen", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario_origen)

        response = self.client.post(
            reverse("traslados:anular", args=[traslado.pk]),
            {"observacion": "Solicitud duplicada"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.miembro.refresh_from_db()
        self.assertEqual(traslado.estado, TrasladoMiembro.Estado.ANULADO)
        self.assertEqual(self.miembro.iglesia, self.origen)
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="traslados", accion="ANULAR").exists())

    def test_no_permite_duplicar_traslado_pendiente(self):
        self.crear_traslado()
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.post(reverse("traslados:create"), self.datos_traslado())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ya tiene un traslado pendiente")
        self.assertEqual(TrasladoMiembro.objects.count(), 1)

    def test_adjunta_documento_a_traslado_desde_destino(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("secretario_destino_doc", Usuario.Rol.SECRETARIO_FILIAL, self.destino)
        self.client.force_login(usuario_destino)

        response = self.client.post(
            reverse("traslados:document-create", args=[traslado.pk]),
            {
                "archivo": SimpleUploadedFile("solicitud.pdf", b"%PDF-1.4", content_type="application/pdf"),
                "nombre": "Solicitud firmada",
                "tipo": DocumentoAdjunto.Tipo.ACTA,
                "descripcion": "Respaldo del traslado",
            },
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        documento = DocumentoAdjunto.objects.get(nombre="Solicitud firmada")
        self.assertEqual(documento.iglesia, self.origen)
        self.assertEqual(documento.content_object, traslado)
        self.assertEqual(documento.subido_por, usuario_destino)

    def test_tercera_iglesia_no_descarga_documento_de_traslado(self):
        traslado = self.crear_traslado()
        usuario_origen = self.crear_usuario("secretario_origen_doc", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        documento = DocumentoAdjunto.objects.create(
            iglesia=self.origen,
            content_object=traslado,
            archivo=SimpleUploadedFile("solicitud.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre="Solicitud firmada",
            tipo=DocumentoAdjunto.Tipo.ACTA,
            subido_por=usuario_origen,
        )
        usuario_otra = self.crear_usuario("secretario_otra_doc", Usuario.Rol.SECRETARIO_FILIAL, self.otra)
        self.client.force_login(usuario_otra)

        response = self.client.get(reverse("traslados:document-download", args=[traslado.pk, documento.pk]))

        self.assertEqual(response.status_code, 404)

    def test_anula_documento_de_traslado(self):
        traslado = self.crear_traslado()
        usuario_origen = self.crear_usuario("secretario_origen_doc", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        documento = DocumentoAdjunto.objects.create(
            iglesia=self.origen,
            content_object=traslado,
            archivo=SimpleUploadedFile("solicitud.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre="Solicitud firmada",
            tipo=DocumentoAdjunto.Tipo.ACTA,
            subido_por=usuario_origen,
        )
        self.client.force_login(usuario_origen)

        response = self.client.post(
            reverse("traslados:document-deactivate", args=[traslado.pk, documento.pk]),
            {"motivo": "Documento corregido"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        documento.refresh_from_db()
        self.assertEqual(documento.estado, DocumentoAdjunto.Estado.ANULADO)
        self.assertEqual(documento.anulado_por, usuario_origen)

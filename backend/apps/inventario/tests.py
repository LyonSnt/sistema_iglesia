from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.documentos.models import DocumentoAdjunto
from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario

from .models import ActivoInventario, MovimientoInventario


class InventarioTests(TestCase):
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
        self.otra = Iglesia.objects.create(
            codigo="OTRA",
            nombre="Otra Iglesia",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )
        self.superadmin = self.crear_usuario("superadmin", Usuario.Rol.SUPERADMIN, self.nacional, is_superuser=True)
        self.tesorero = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.lectura = self.crear_usuario("lectura", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.responsable = self.crear_usuario("responsable", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.responsable_otra = self.crear_usuario("responsable_otra", Usuario.Rol.SOLO_LECTURA, self.otra)

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

    def crear_activo(self, iglesia=None, **overrides):
        data = {
            "iglesia": iglesia or self.filial,
            "codigo": "EQ-001",
            "nombre": "Equipo de sonido",
            "categoria": "Audio",
            "ubicacion_actual": "Templo principal",
            "responsable_actual": self.responsable if (iglesia or self.filial) == self.filial else None,
            "estado": ActivoInventario.Estado.DISPONIBLE,
            "valor_referencial": Decimal("120.00"),
        }
        data.update(overrides)
        return ActivoInventario.objects.create(**data)

    def datos_activo(self, **overrides):
        data = {
            "iglesia": self.otra.pk,
            "codigo": "EQ-002",
            "nombre": "Proyector",
            "categoria": "Video",
            "descripcion": "",
            "ubicacion_actual": "Aula 1",
            "responsable_actual": self.responsable.pk,
            "estado": ActivoInventario.Estado.DISPONIBLE,
            "fecha_adquisicion": "",
            "valor_referencial": "250.00",
            "activo": "on",
        }
        data.update(overrides)
        return data

    def test_tesorero_crea_activo_en_su_iglesia_aunque_fuerce_otra(self):
        self.client.force_login(self.tesorero)

        response = self.client.post(reverse("inventario:create"), self.datos_activo())

        self.assertRedirects(response, reverse("inventario:list"))
        activo = ActivoInventario.objects.get(codigo="EQ-002")
        self.assertEqual(activo.iglesia, self.filial)
        self.assertEqual(activo.responsable_actual, self.responsable)

    def test_no_permite_responsable_de_otra_iglesia(self):
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("inventario:create"),
            self.datos_activo(iglesia=self.filial.pk, responsable_actual=self.responsable_otra.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "misma iglesia")
        self.assertFalse(ActivoInventario.objects.filter(codigo="EQ-002").exists())

    def test_listado_respeta_alcance_por_iglesia(self):
        self.crear_activo()
        self.crear_activo(self.otra, codigo="OTR-001", nombre="Silla", responsable_actual=None)
        self.client.force_login(self.tesorero)

        response = self.client.get(reverse("inventario:list"))

        self.assertContains(response, "EQ-001")
        self.assertNotContains(response, "OTR-001")

    def test_lectura_puede_ver_pero_no_gestionar(self):
        activo = self.crear_activo()
        self.client.force_login(self.lectura)

        detalle = self.client.get(reverse("inventario:detail", args=[activo.pk]))
        crear = self.client.get(reverse("inventario:create"))

        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(crear.status_code, 403)

    def test_movimiento_actualiza_ubicacion_y_guarda_historial(self):
        activo = self.crear_activo()
        self.client.force_login(self.tesorero)

        response = self.client.post(
            reverse("inventario:movement", args=[activo.pk]),
            {
                "tipo": MovimientoInventario.Tipo.UBICACION,
                "fecha": "2026-06-24",
                "ubicacion_nueva": "Bodega",
                "responsable_nuevo": "",
                "detalle": "Cambio por reorganizacion.",
            },
        )

        self.assertRedirects(response, reverse("inventario:detail", args=[activo.pk]))
        activo.refresh_from_db()
        self.assertEqual(activo.ubicacion_actual, "Bodega")
        movimiento = activo.movimientos.get()
        self.assertEqual(movimiento.ubicacion_anterior, "Templo principal")
        self.assertEqual(movimiento.ubicacion_nueva, "Bodega")
        self.assertEqual(movimiento.registrado_por, self.tesorero)

    def test_baja_no_borra_activo_y_registra_movimiento(self):
        activo = self.crear_activo()
        self.client.force_login(self.tesorero)

        response = self.client.post(
            reverse("inventario:deactivate", args=[activo.pk]),
            {"fecha": "2026-06-24", "motivo": "Equipo obsoleto."},
        )

        self.assertRedirects(response, reverse("inventario:detail", args=[activo.pk]))
        activo.refresh_from_db()
        self.assertFalse(activo.activo)
        self.assertEqual(activo.estado, ActivoInventario.Estado.DADO_DE_BAJA)
        self.assertTrue(activo.movimientos.filter(tipo=MovimientoInventario.Tipo.BAJA).exists())

    def test_filial_no_accede_activo_de_otra_iglesia(self):
        activo = self.crear_activo(self.otra, codigo="OTR-001", responsable_actual=None)
        self.client.force_login(self.tesorero)

        response = self.client.get(reverse("inventario:detail", args=[activo.pk]))

        self.assertEqual(response.status_code, 404)

    def test_dashboard_muestra_enlace_a_inventario(self):
        self.client.force_login(self.tesorero)

        response = self.client.get(reverse("core:dashboard"))

        self.assertContains(response, "Inventario")
        self.assertContains(response, reverse("inventario:list"))

    def test_adjunta_documento_a_activo(self):
        activo = self.crear_activo()
        self.client.force_login(self.tesorero)
        archivo = SimpleUploadedFile("factura.pdf", b"%PDF-1.4 prueba", content_type="application/pdf")

        response = self.client.post(
            reverse("inventario:document-create", args=[activo.pk]),
            {
                "archivo": archivo,
                "nombre": "Factura de compra",
                "tipo": DocumentoAdjunto.Tipo.FACTURA,
                "descripcion": "Documento de respaldo.",
            },
        )

        self.assertRedirects(response, reverse("inventario:detail", args=[activo.pk]))
        documento = DocumentoAdjunto.objects.get(nombre="Factura de compra")
        self.assertEqual(documento.iglesia, self.filial)
        self.assertEqual(documento.content_object, activo)
        self.assertEqual(documento.subido_por, self.tesorero)

    def test_rechaza_documento_con_extension_no_permitida(self):
        activo = self.crear_activo()
        self.client.force_login(self.tesorero)
        archivo = SimpleUploadedFile("script.exe", b"contenido", content_type="application/octet-stream")

        response = self.client.post(
            reverse("inventario:document-create", args=[activo.pk]),
            {
                "archivo": archivo,
                "nombre": "Archivo invalido",
                "tipo": DocumentoAdjunto.Tipo.OTRO,
                "descripcion": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tipo de archivo no permitido")
        self.assertFalse(DocumentoAdjunto.objects.exists())

    def test_descarga_documento_respeta_alcance_por_iglesia(self):
        activo = self.crear_activo(self.otra, codigo="OTR-001", responsable_actual=None)
        documento = DocumentoAdjunto.objects.create(
            iglesia=self.otra,
            content_object=activo,
            archivo=SimpleUploadedFile("foto.png", b"png", content_type="image/png"),
            nombre="Foto",
            tipo=DocumentoAdjunto.Tipo.FOTO,
            subido_por=self.superadmin,
        )
        self.client.force_login(self.tesorero)

        response = self.client.get(reverse("inventario:document-download", args=[activo.pk, documento.pk]))

        self.assertEqual(response.status_code, 404)

    def test_anula_documento_sin_borrar_archivo(self):
        activo = self.crear_activo()
        documento = DocumentoAdjunto.objects.create(
            iglesia=self.filial,
            content_object=activo,
            archivo=SimpleUploadedFile("garantia.pdf", b"%PDF", content_type="application/pdf"),
            nombre="Garantia",
            tipo=DocumentoAdjunto.Tipo.GARANTIA,
            subido_por=self.tesorero,
        )
        self.client.force_login(self.tesorero)

        response = self.client.post(
            reverse("inventario:document-deactivate", args=[activo.pk, documento.pk]),
            {"motivo": "Documento reemplazado."},
        )

        self.assertRedirects(response, reverse("inventario:detail", args=[activo.pk]))
        documento.refresh_from_db()
        self.assertEqual(documento.estado, DocumentoAdjunto.Estado.ANULADO)
        self.assertEqual(documento.anulado_por, self.tesorero)
        self.assertTrue(documento.archivo.name)

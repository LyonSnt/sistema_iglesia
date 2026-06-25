from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.aportes_nacionales.models import AporteNacional
from apps.documentos.models import DocumentoAdjunto
from apps.finanzas.models import CierreMensualFinanciero, ConceptoFinanciero, MovimientoFinanciero, TipoMovimiento
from apps.iglesias.models import Iglesia
from apps.usuarios.models import Usuario


class FinanzasLocalesTests(TestCase):
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
        self.concepto_ingreso = ConceptoFinanciero.objects.create(
            iglesia=self.filial,
            nombre="Diezmos",
            tipo=TipoMovimiento.INGRESO,
        )
        self.concepto_egreso = ConceptoFinanciero.objects.create(
            iglesia=self.filial,
            nombre="Servicios basicos",
            tipo=TipoMovimiento.EGRESO,
        )
        self.concepto_otra = ConceptoFinanciero.objects.create(
            iglesia=self.otra_filial,
            nombre="Ofrendas",
            tipo=TipoMovimiento.INGRESO,
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def crear_movimiento(self, **overrides):
        usuario = overrides.pop("registrado_por", None)
        if usuario is None:
            usuario = self.crear_usuario(f"tesorero_{MovimientoFinanciero.objects.count()}", Usuario.Rol.TESORERO_FILIAL, self.filial)
        data = {
            "iglesia": self.filial,
            "concepto": self.concepto_ingreso,
            "tipo": TipoMovimiento.INGRESO,
            "fecha": date(2026, 6, 1),
            "monto": Decimal("100.00"),
            "descripcion": "Registro de prueba",
            "numero_comprobante": "REC-001",
            "registrado_por": usuario,
        }
        data.update(overrides)
        return MovimientoFinanciero.objects.create(**data)

    def datos_concepto(self, **overrides):
        data = {
            "iglesia": self.filial.pk,
            "nombre": "Mision local",
            "tipo": TipoMovimiento.INGRESO,
            "descripcion": "",
            "activo": "on",
        }
        data.update(overrides)
        return data

    def datos_movimiento(self, **overrides):
        data = {
            "iglesia": self.filial.pk,
            "concepto": self.concepto_ingreso.pk,
            "tipo": TipoMovimiento.INGRESO,
            "fecha": "2026-06-01",
            "monto": "100.00",
            "descripcion": "Diezmo semanal",
            "numero_comprobante": "REC-001",
        }
        data.update(overrides)
        return data

    def test_tesorero_lista_solo_movimientos_de_su_iglesia(self):
        self.crear_movimiento(descripcion="Movimiento local")
        self.crear_movimiento(
            iglesia=self.otra_filial,
            concepto=self.concepto_otra,
            descripcion="Movimiento externo",
            registrado_por=self.crear_usuario("tesorero_otra", Usuario.Rol.TESORERO_FILIAL, self.otra_filial),
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("finanzas:list"))

        self.assertContains(response, "Movimiento local")
        self.assertNotContains(response, "Movimiento externo")

    def test_pastor_consulta_y_gestiona_finanzas(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response_list = self.client.get(reverse("finanzas:list"))
        response_create = self.client.get(reverse("finanzas:create"))

        self.assertEqual(response_list.status_code, 200)
        self.assertEqual(response_create.status_code, 200)

    def test_usuario_sin_permiso_no_accede(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("finanzas:list"))

        self.assertEqual(response.status_code, 403)

    def test_crear_concepto_usa_iglesia_del_usuario(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:concept-create"),
            self.datos_concepto(iglesia=self.otra_filial.pk),
        )

        self.assertRedirects(response, reverse("finanzas:list"))
        concepto = ConceptoFinanciero.objects.get(nombre="Mision local")
        self.assertEqual(concepto.iglesia, self.filial)

    def test_crear_movimiento_usa_iglesia_y_usuario_actual(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:create"),
            self.datos_movimiento(iglesia=self.otra_filial.pk),
        )

        self.assertRedirects(response, reverse("finanzas:list"))
        movimiento = MovimientoFinanciero.objects.get(descripcion="Diezmo semanal")
        self.assertEqual(movimiento.iglesia, self.filial)
        self.assertEqual(movimiento.registrado_por, usuario)

    def test_no_permite_concepto_de_otra_iglesia(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:create"),
            self.datos_movimiento(concepto=self.concepto_otra.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(MovimientoFinanciero.objects.filter(descripcion="Diezmo semanal").exists())
        self.assertIn("concepto", response.context["form"].errors)

    def test_tipo_debe_coincidir_con_concepto(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:create"),
            self.datos_movimiento(tipo=TipoMovimiento.EGRESO),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "debe coincidir")

    def test_monto_debe_ser_mayor_a_cero(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:create"),
            self.datos_movimiento(monto="0.00"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mayor a cero")

    def test_anular_movimiento(self):
        movimiento = self.crear_movimiento()
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:annul", args=[movimiento.pk]),
            {"fecha_anulacion": "2026-06-02", "motivo_anulacion": "Comprobante duplicado"},
        )

        self.assertRedirects(response, reverse("finanzas:detail", args=[movimiento.pk]))
        movimiento.refresh_from_db()
        self.assertEqual(movimiento.estado, MovimientoFinanciero.Estado.ANULADO)
        self.assertEqual(movimiento.anulado_por, usuario)
        self.assertEqual(movimiento.motivo_anulacion, "Comprobante duplicado")

    def test_no_anula_movimiento_de_otra_iglesia(self):
        movimiento = self.crear_movimiento(
            iglesia=self.otra_filial,
            concepto=self.concepto_otra,
            registrado_por=self.crear_usuario("tesorero_otra", Usuario.Rol.TESORERO_FILIAL, self.otra_filial),
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:annul", args=[movimiento.pk]),
            {"fecha_anulacion": "2026-06-02", "motivo_anulacion": "No corresponde"},
        )

        self.assertEqual(response.status_code, 404)

    def test_tesorero_genera_cierre_con_totales_del_mes(self):
        self.crear_movimiento(monto=Decimal("150.00"), fecha=date(2026, 6, 1))
        self.crear_movimiento(
            concepto=self.concepto_egreso,
            tipo=TipoMovimiento.EGRESO,
            monto=Decimal("40.00"),
            fecha=date(2026, 6, 10),
            descripcion="Pago de servicios",
        )
        self.crear_movimiento(monto=Decimal("90.00"), fecha=date(2026, 7, 1), descripcion="Otro mes")
        self.crear_movimiento(monto=Decimal("25.00"), fecha=date(2026, 6, 2), estado=MovimientoFinanciero.Estado.ANULADO)
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:cierre-create"),
            {"iglesia": self.otra_filial.pk, "anio": "2026", "mes": "6", "observacion": "Cierre de junio"},
        )

        self.assertRedirects(response, reverse("finanzas:cierre-list"))
        cierre = CierreMensualFinanciero.objects.get(anio=2026, mes=6)
        self.assertEqual(cierre.iglesia, self.filial)
        self.assertEqual(cierre.total_ingresos, Decimal("150.00"))
        self.assertEqual(cierre.total_egresos, Decimal("40.00"))
        self.assertEqual(cierre.saldo, Decimal("110.00"))
        self.assertEqual(cierre.cerrado_por, usuario)

    def test_no_duplica_cierre_del_mismo_mes(self):
        CierreMensualFinanciero.objects.create(
            iglesia=self.filial,
            anio=2026,
            mes=6,
            cerrado_por=self.crear_usuario("tesorero_base", Usuario.Rol.TESORERO_FILIAL, self.filial),
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:cierre-create"),
            {"iglesia": self.filial.pk, "anio": "2026", "mes": "6", "observacion": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un cierre")
        self.assertEqual(CierreMensualFinanciero.objects.filter(iglesia=self.filial, anio=2026, mes=6).count(), 1)

    def test_pastor_consulta_y_genera_cierres(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response_list = self.client.get(reverse("finanzas:cierre-list"))
        response_create = self.client.get(reverse("finanzas:cierre-create"))

        self.assertEqual(response_list.status_code, 200)
        self.assertEqual(response_create.status_code, 200)

    def test_cierres_respetan_aislamiento_por_iglesia(self):
        usuario_base = self.crear_usuario("tesorero_base", Usuario.Rol.TESORERO_FILIAL, self.filial)
        CierreMensualFinanciero.objects.create(iglesia=self.filial, anio=2026, mes=6, cerrado_por=usuario_base)
        CierreMensualFinanciero.objects.create(
            iglesia=self.otra_filial,
            anio=2026,
            mes=6,
            cerrado_por=self.crear_usuario("tesorero_otra", Usuario.Rol.TESORERO_FILIAL, self.otra_filial),
        )
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("finanzas:cierre-list"))

        self.assertContains(response, "PRUEBAS")
        self.assertNotContains(response, "OTRA")

    def test_no_registra_movimiento_en_mes_cerrado(self):
        CierreMensualFinanciero.objects.create(
            iglesia=self.filial,
            anio=2026,
            mes=6,
            cerrado_por=self.crear_usuario("tesorero_base", Usuario.Rol.TESORERO_FILIAL, self.filial),
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(reverse("finanzas:create"), self.datos_movimiento(fecha="2026-06-15"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mes cerrado")
        self.assertFalse(MovimientoFinanciero.objects.filter(descripcion="Diezmo semanal").exists())

    def test_no_anula_movimiento_en_mes_cerrado(self):
        movimiento = self.crear_movimiento(fecha=date(2026, 6, 1))
        CierreMensualFinanciero.objects.create(
            iglesia=self.filial,
            anio=2026,
            mes=6,
            cerrado_por=self.crear_usuario("tesorero_base", Usuario.Rol.TESORERO_FILIAL, self.filial),
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:annul", args=[movimiento.pk]),
            {"fecha_anulacion": "2026-06-02", "motivo_anulacion": "No debe anular"},
        )

        self.assertRedirects(response, reverse("finanzas:detail", args=[movimiento.pk]))
        movimiento.refresh_from_db()
        self.assertEqual(movimiento.estado, MovimientoFinanciero.Estado.REGISTRADO)

    def test_anula_cierre_sin_aporte_y_permite_corregir_y_regenerar(self):
        self.crear_movimiento(monto=Decimal("100.00"), fecha=date(2026, 6, 1))
        usuario = self.crear_usuario("tesorero_correccion", Usuario.Rol.TESORERO_FILIAL, self.filial)
        cierre = CierreMensualFinanciero.objects.create(
            iglesia=self.filial,
            anio=2026,
            mes=6,
            total_ingresos=Decimal("100.00"),
            total_egresos=Decimal("0.00"),
            saldo=Decimal("100.00"),
            cerrado_por=usuario,
        )
        self.client.force_login(usuario)

        response_anular = self.client.post(
            reverse("finanzas:cierre-annul", args=[cierre.pk]),
            {"motivo_anulacion": "Falto registrar una ofrenda"},
        )

        self.assertRedirects(response_anular, reverse("finanzas:cierre-list"))
        cierre.refresh_from_db()
        self.assertEqual(cierre.estado, CierreMensualFinanciero.Estado.ANULADO)
        self.assertIn("Falto registrar una ofrenda", cierre.observacion)

        response_movimiento = self.client.post(
            reverse("finanzas:create"),
            self.datos_movimiento(
                fecha="2026-06-15",
                monto="25.00",
                descripcion="Ofrenda pendiente",
                numero_comprobante="REC-002",
            ),
        )

        self.assertRedirects(response_movimiento, reverse("finanzas:list"))
        response_regenerar = self.client.post(
            reverse("finanzas:cierre-create"),
            {"iglesia": self.filial.pk, "anio": "2026", "mes": "6", "observacion": "Cierre corregido"},
        )

        self.assertRedirects(response_regenerar, reverse("finanzas:cierre-list"))
        cierre.refresh_from_db()
        self.assertEqual(CierreMensualFinanciero.objects.filter(iglesia=self.filial, anio=2026, mes=6).count(), 1)
        self.assertEqual(cierre.estado, CierreMensualFinanciero.Estado.CERRADO)
        self.assertEqual(cierre.total_ingresos, Decimal("125.00"))
        self.assertEqual(cierre.saldo, Decimal("125.00"))
        self.assertEqual(cierre.observacion, "Cierre corregido")

    def test_no_anula_cierre_con_aporte_nacional_generado(self):
        usuario = self.crear_usuario("tesorero_con_aporte", Usuario.Rol.TESORERO_FILIAL, self.filial)
        cierre = CierreMensualFinanciero.objects.create(
            iglesia=self.filial,
            anio=2026,
            mes=6,
            total_ingresos=Decimal("100.00"),
            total_egresos=Decimal("0.00"),
            saldo=Decimal("100.00"),
            cerrado_por=usuario,
        )
        AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("100.00"),
            monto_aporte=Decimal("10.00"),
            generado_por=usuario,
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:cierre-annul", args=[cierre.pk]),
            {"motivo_anulacion": "No debe anularse"},
        )

        self.assertRedirects(response, reverse("finanzas:cierre-list"))
        cierre.refresh_from_db()
        self.assertEqual(cierre.estado, CierreMensualFinanciero.Estado.CERRADO)

    def test_adjunta_documento_a_movimiento_financiero(self):
        movimiento = self.crear_movimiento()
        usuario = self.crear_usuario("tesorero_doc", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:document-create", args=[movimiento.pk]),
            {
                "archivo": SimpleUploadedFile("comprobante.pdf", b"%PDF-1.4", content_type="application/pdf"),
                "nombre": "Comprobante de ingreso",
                "tipo": DocumentoAdjunto.Tipo.COMPROBANTE,
                "descripcion": "Soporte del movimiento",
            },
        )

        self.assertRedirects(response, reverse("finanzas:detail", args=[movimiento.pk]))
        documento = DocumentoAdjunto.objects.get(nombre="Comprobante de ingreso")
        self.assertEqual(documento.iglesia, self.filial)
        self.assertEqual(documento.content_object, movimiento)
        self.assertEqual(documento.subido_por, usuario)

    def test_rechaza_tipo_documento_no_permitido_para_finanzas(self):
        movimiento = self.crear_movimiento()
        usuario = self.crear_usuario("tesorero_doc", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:document-create", args=[movimiento.pk]),
            {
                "archivo": SimpleUploadedFile("garantia.pdf", b"%PDF-1.4", content_type="application/pdf"),
                "nombre": "Garantia incorrecta",
                "tipo": DocumentoAdjunto.Tipo.GARANTIA,
                "descripcion": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(DocumentoAdjunto.objects.filter(nombre="Garantia incorrecta").exists())

    def test_descarga_documento_financiero_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("tesorero_doc", Usuario.Rol.TESORERO_FILIAL, self.filial)
        usuario_otra = self.crear_usuario("tesorero_otra_doc", Usuario.Rol.TESORERO_FILIAL, self.otra_filial)
        movimiento_otra = self.crear_movimiento(
            iglesia=self.otra_filial,
            concepto=self.concepto_otra,
            registrado_por=usuario_otra,
        )
        documento = DocumentoAdjunto.objects.create(
            iglesia=self.otra_filial,
            content_object=movimiento_otra,
            archivo=SimpleUploadedFile("comprobante.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre="Comprobante externo",
            tipo=DocumentoAdjunto.Tipo.COMPROBANTE,
            subido_por=usuario_otra,
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("finanzas:document-download", args=[movimiento_otra.pk, documento.pk]))

        self.assertEqual(response.status_code, 404)

    def test_anula_documento_financiero_sin_borrar_archivo(self):
        usuario = self.crear_usuario("tesorero_doc", Usuario.Rol.TESORERO_FILIAL, self.filial)
        movimiento = self.crear_movimiento(registrado_por=usuario)
        documento = DocumentoAdjunto.objects.create(
            iglesia=self.filial,
            content_object=movimiento,
            archivo=SimpleUploadedFile("comprobante.pdf", b"%PDF-1.4", content_type="application/pdf"),
            nombre="Comprobante de ingreso",
            tipo=DocumentoAdjunto.Tipo.COMPROBANTE,
            subido_por=usuario,
        )
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("finanzas:document-deactivate", args=[movimiento.pk, documento.pk]),
            {"motivo": "Soporte reemplazado"},
        )

        self.assertRedirects(response, reverse("finanzas:detail", args=[movimiento.pk]))
        documento.refresh_from_db()
        self.assertEqual(documento.estado, DocumentoAdjunto.Estado.ANULADO)
        self.assertEqual(documento.anulado_por, usuario)
        self.assertTrue(documento.archivo.name)

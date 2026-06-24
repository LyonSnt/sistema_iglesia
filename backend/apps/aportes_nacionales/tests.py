from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.aportes_nacionales.models import AporteNacional
from apps.finanzas.models import CierreMensualFinanciero
from apps.iglesias.models import Iglesia
from apps.parametros.models import ParametroGeneral
from apps.usuarios.models import Usuario


class AportesNacionalesTests(TestCase):
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
        self.superadmin = self.crear_usuario("superadmin", Usuario.Rol.SUPERADMIN, self.nacional, is_superuser=True)
        self.cierre = CierreMensualFinanciero.objects.create(
            iglesia=self.filial,
            anio=2026,
            mes=6,
            total_ingresos=Decimal("1000.00"),
            total_egresos=Decimal("250.00"),
            saldo=Decimal("750.00"),
            cerrado_por=self.superadmin,
        )
        self.cierre_otra = CierreMensualFinanciero.objects.create(
            iglesia=self.otra_filial,
            anio=2026,
            mes=6,
            total_ingresos=Decimal("500.00"),
            total_egresos=Decimal("100.00"),
            saldo=Decimal("400.00"),
            cerrado_por=self.superadmin,
        )
        ParametroGeneral.objects.create(
            clave="APORTE_NACIONAL_PORCENTAJE",
            nombre="Porcentaje de aporte nacional",
            valor="10",
            tipo_dato=ParametroGeneral.TipoDato.DECIMAL,
        )
        ParametroGeneral.objects.create(
            clave="APORTES_RECIBOS_PREFIJO",
            nombre="Prefijo de recibos de aportes",
            valor="AP",
            tipo_dato=ParametroGeneral.TipoDato.TEXTO,
        )
        ParametroGeneral.objects.create(
            clave="APORTES_RECIBOS_SECUENCIAL_INICIAL",
            nombre="Secuencial de recibos de aportes",
            valor="1",
            tipo_dato=ParametroGeneral.TipoDato.ENTERO,
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

    def test_superadmin_genera_aporte_desde_cierre(self):
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("aportes_nacionales:create"),
            {"cierre": self.cierre.pk, "porcentaje": "10.00", "observacion": "Aporte junio"},
        )

        self.assertRedirects(response, reverse("aportes_nacionales:list"))
        aporte = AporteNacional.objects.get(cierre=self.cierre)
        self.assertEqual(aporte.iglesia, self.filial)
        self.assertEqual(aporte.anio, 2026)
        self.assertEqual(aporte.mes, 6)
        self.assertEqual(aporte.monto_base, Decimal("1000.00"))
        self.assertEqual(aporte.monto_aporte, Decimal("100.00"))
        self.assertEqual(aporte.generado_por, self.superadmin)

    def test_porcentaje_default_sale_de_parametro(self):
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:create"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].fields["porcentaje"].initial, Decimal("10"))

    def test_no_permite_porcentaje_invalido(self):
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("aportes_nacionales:create"),
            {"cierre": self.cierre.pk, "porcentaje": "0", "observacion": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "mayor a cero")
        self.assertFalse(AporteNacional.objects.exists())

    def test_no_duplica_aporte_para_cierre(self):
        AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:create"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.cierre, list(response.context["form"].fields["cierre"].queryset))

    def test_tesorero_filial_consulta_solo_sus_aportes(self):
        AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        AporteNacional.objects.create(
            iglesia=self.otra_filial,
            cierre=self.cierre_otra,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("500.00"),
            monto_aporte=Decimal("50.00"),
            generado_por=self.superadmin,
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("aportes_nacionales:list"))

        self.assertContains(response, "PRUEBAS")
        self.assertNotContains(response, "OTRA")

    def test_tesorero_no_genera_aportes(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("aportes_nacionales:create"))

        self.assertEqual(response.status_code, 403)

    def test_pastor_consulta_detalle_de_su_iglesia(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("aportes_nacionales:detail", args=[aporte.pk]))

        self.assertEqual(response.context["aporte"].monto_aporte, Decimal("100.00"))
        self.assertContains(response, "PRUEBAS")

    def test_filial_no_ve_detalle_de_otra_iglesia(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.otra_filial,
            cierre=self.cierre_otra,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("500.00"),
            monto_aporte=Decimal("50.00"),
            generado_por=self.superadmin,
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("aportes_nacionales:detail", args=[aporte.pk]))

        self.assertEqual(response.status_code, 404)

    def test_superadmin_registra_pago_y_reserva_recibo(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("aportes_nacionales:payment", args=[aporte.pk]),
            {"fecha_pago": "2026-07-05", "referencia_pago": "DEP-001", "observacion": "Pago recibido"},
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        aporte.refresh_from_db()
        self.assertEqual(aporte.estado, AporteNacional.Estado.PAGADO)
        self.assertEqual(aporte.numero_recibo, "AP-000001")
        self.assertEqual(aporte.referencia_pago, "DEP-001")
        self.assertEqual(aporte.registrado_pago_por, self.superadmin)
        self.assertEqual(ParametroGeneral.objects.get(clave="APORTES_RECIBOS_SECUENCIAL_INICIAL").valor, "2")

    def test_no_registra_pago_de_aporte_pagado_dos_veces(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            estado=AporteNacional.Estado.PAGADO,
            numero_recibo="AP-000001",
            fecha_pago="2026-07-05",
            referencia_pago="DEP-001",
            generado_por=self.superadmin,
            registrado_pago_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("aportes_nacionales:payment", args=[aporte.pk]),
            {"fecha_pago": "2026-07-06", "referencia_pago": "DEP-002", "observacion": ""},
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        aporte.refresh_from_db()
        self.assertEqual(aporte.numero_recibo, "AP-000001")
        self.assertEqual(aporte.referencia_pago, "DEP-001")

    def test_tesorero_filial_no_registra_pago(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("aportes_nacionales:payment", args=[aporte.pk]))

        self.assertEqual(response.status_code, 403)

    def test_listado_resume_pendiente_y_pagado(self):
        AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        AporteNacional.objects.create(
            iglesia=self.otra_filial,
            cierre=self.cierre_otra,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("500.00"),
            monto_aporte=Decimal("50.00"),
            estado=AporteNacional.Estado.PAGADO,
            numero_recibo="AP-000001",
            generado_por=self.superadmin,
            registrado_pago_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:list"))

        self.assertEqual(response.context["total_pendiente"], Decimal("100.00"))
        self.assertEqual(response.context["total_pagado"], Decimal("50.00"))

    def test_cuenta_corriente_muestra_totales_detallados(self):
        AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        AporteNacional.objects.create(
            iglesia=self.otra_filial,
            cierre=self.cierre_otra,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("500.00"),
            monto_aporte=Decimal("50.00"),
            estado=AporteNacional.Estado.PAGADO,
            numero_recibo="AP-000001",
            fecha_pago="2026-07-05",
            referencia_pago="DEP-001",
            generado_por=self.superadmin,
            registrado_pago_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:account"))

        self.assertContains(response, "Cuenta corriente")
        self.assertEqual(response.context["total_generado"], Decimal("150.00"))
        self.assertEqual(response.context["total_pagado"], Decimal("50.00"))
        self.assertEqual(response.context["saldo"], Decimal("100.00"))
        self.assertContains(response, "AP-000001")

    def test_cuenta_corriente_filial_respeta_alcance_por_iglesia(self):
        AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        AporteNacional.objects.create(
            iglesia=self.otra_filial,
            cierre=self.cierre_otra,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("500.00"),
            monto_aporte=Decimal("50.00"),
            generado_por=self.superadmin,
        )
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("aportes_nacionales:account"))

        self.assertContains(response, "PRUEBAS")
        self.assertNotContains(response, "OTRA")
        self.assertEqual(response.context["total_generado"], Decimal("100.00"))

    def test_recibo_pdf_solo_para_aporte_pagado(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            estado=AporteNacional.Estado.PAGADO,
            numero_recibo="AP-000001",
            fecha_pago="2026-07-05",
            referencia_pago="DEP-001",
            generado_por=self.superadmin,
            registrado_pago_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:receipt-pdf", args=[aporte.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response.content[:4], b"%PDF")
        self.assertIn("AP-000001.pdf", response["Content-Disposition"])

    def test_recibo_pdf_no_existe_para_aporte_pendiente(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            generado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:receipt-pdf", args=[aporte.pk]))

        self.assertEqual(response.status_code, 404)

    def test_seed_inicial_crea_parametros_de_recibos(self):
        ParametroGeneral.objects.filter(
            clave__in=["APORTES_RECIBOS_PREFIJO", "APORTES_RECIBOS_SECUENCIAL_INICIAL"]
        ).delete()

        from django.core.management import call_command

        call_command("seed_inicial")

        self.assertTrue(ParametroGeneral.objects.filter(clave="APORTES_RECIBOS_PREFIJO").exists())
        self.assertTrue(ParametroGeneral.objects.filter(clave="APORTES_RECIBOS_SECUENCIAL_INICIAL").exists())

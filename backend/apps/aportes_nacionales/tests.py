from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.aportes_nacionales.models import (
    AcuerdoPagoAporteNacional,
    AjusteAporteNacional,
    AporteNacional,
    PagoAporteNacional,
)
from apps.finanzas.models import CierreMensualFinanciero
from apps.iglesias.models import Iglesia
from apps.parametros.models import ParametroGeneral
from apps.usuarios.models import Usuario
from apps.zonas.models import Zona


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
        self.admin_nacional = self.crear_usuario(
            "admin_nacional",
            Usuario.Rol.ADMIN_NACIONAL,
            self.nacional,
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

    def test_superadmin_anula_aporte_pendiente_para_correccion(self):
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
            reverse("aportes_nacionales:annul", args=[aporte.pk]),
            {"motivo_anulacion": "Ingreso registrado con error"},
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        aporte.refresh_from_db()
        self.assertEqual(aporte.estado, AporteNacional.Estado.ANULADO)
        self.assertEqual(aporte.anulado_por, self.superadmin)
        self.assertEqual(aporte.motivo_anulacion, "Ingreso registrado con error")
        self.assertIn("Ingreso registrado con error", aporte.observacion)

    def test_no_muestra_anulacion_si_aporte_pendiente_tiene_pagos(self):
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
        PagoAporteNacional.objects.create(
            iglesia=self.filial,
            aporte=aporte,
            monto=Decimal("40.00"),
            fecha_pago="2026-07-05",
            referencia_pago="DEP-PARCIAL",
            registrado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:detail", args=[aporte.pk]))

        self.assertFalse(response.context["puede_anular"])

    def test_no_anula_aporte_pagado_para_correccion(self):
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
            reverse("aportes_nacionales:annul", args=[aporte.pk]),
            {"motivo_anulacion": "No debe anular pagado"},
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        aporte.refresh_from_db()
        self.assertEqual(aporte.estado, AporteNacional.Estado.PAGADO)
        self.assertEqual(aporte.motivo_anulacion, "")

    def test_regenera_aporte_anulado_desde_cierre_corregido(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            estado=AporteNacional.Estado.ANULADO,
            anulado_por=self.superadmin,
            motivo_anulacion="Correccion de cierre",
            generado_por=self.superadmin,
        )
        self.cierre.total_ingresos = Decimal("1200.00")
        self.cierre.saldo = Decimal("950.00")
        self.cierre.save(update_fields=["total_ingresos", "saldo"])
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("aportes_nacionales:create"),
            {"cierre": self.cierre.pk, "porcentaje": "10.00", "observacion": "Aporte corregido"},
        )

        self.assertRedirects(response, reverse("aportes_nacionales:list"))
        aporte.refresh_from_db()
        self.assertEqual(AporteNacional.objects.count(), 1)
        self.assertEqual(aporte.estado, AporteNacional.Estado.PENDIENTE)
        self.assertEqual(aporte.monto_base, Decimal("1200.00"))
        self.assertEqual(aporte.monto_aporte, Decimal("120.00"))
        self.assertIsNone(aporte.anulado_por)
        self.assertEqual(aporte.motivo_anulacion, "")
        self.assertEqual(aporte.observacion, "Aporte corregido")

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

    def test_admin_nacional_consulta_aportes_pero_no_genera(self):
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
        self.client.force_login(self.admin_nacional)

        response_list = self.client.get(reverse("aportes_nacionales:list"))
        response_create = self.client.get(reverse("aportes_nacionales:create"))

        self.assertEqual(response_list.status_code, 200)
        self.assertContains(response_list, "PRUEBAS")
        self.assertEqual(response_create.status_code, 403)

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
        self.assertEqual(aporte.pagos.get().monto, Decimal("100.00"))
        self.assertEqual(ParametroGeneral.objects.get(clave="APORTES_RECIBOS_SECUENCIAL_INICIAL").valor, "2")

    def test_registra_pago_parcial_sin_reservar_recibo(self):
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
            {
                "fecha_pago": "2026-07-05",
                "monto": "40.00",
                "referencia_pago": "DEP-PARCIAL",
                "observacion": "Primer abono",
            },
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        aporte.refresh_from_db()
        self.assertEqual(aporte.estado, AporteNacional.Estado.PENDIENTE)
        self.assertIsNone(aporte.numero_recibo)
        self.assertEqual(aporte.total_pagos, Decimal("40.00"))
        self.assertEqual(aporte.saldo_pendiente, Decimal("60.00"))

    def test_pago_final_completa_aporte_parcial_y_reserva_recibo(self):
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
        PagoAporteNacional.objects.create(
            iglesia=self.filial,
            aporte=aporte,
            monto=Decimal("40.00"),
            fecha_pago="2026-07-05",
            referencia_pago="DEP-PARCIAL",
            registrado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("aportes_nacionales:payment", args=[aporte.pk]),
            {
                "fecha_pago": "2026-07-10",
                "monto": "60.00",
                "referencia_pago": "DEP-FINAL",
                "observacion": "Saldo cancelado",
            },
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        aporte.refresh_from_db()
        self.assertEqual(aporte.estado, AporteNacional.Estado.PAGADO)
        self.assertEqual(aporte.numero_recibo, "AP-000001")
        self.assertEqual(aporte.total_pagos, Decimal("100.00"))
        self.assertEqual(aporte.saldo_pendiente, Decimal("0.00"))

    def test_no_permite_pago_mayor_al_saldo(self):
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
            {
                "fecha_pago": "2026-07-05",
                "monto": "101.00",
                "referencia_pago": "DEP-ERR",
                "observacion": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no puede superar el saldo")
        self.assertFalse(PagoAporteNacional.objects.exists())

    def test_admin_nacional_registra_pago_y_reserva_recibo(self):
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
        self.client.force_login(self.admin_nacional)

        response = self.client.post(
            reverse("aportes_nacionales:payment", args=[aporte.pk]),
            {"fecha_pago": "2026-07-05", "referencia_pago": "DEP-001", "observacion": "Pago recibido"},
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        aporte.refresh_from_db()
        self.assertEqual(aporte.estado, AporteNacional.Estado.PAGADO)
        self.assertEqual(aporte.numero_recibo, "AP-000001")
        self.assertEqual(aporte.registrado_pago_por, self.admin_nacional)

    def test_superadmin_registra_acuerdo_de_pago(self):
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
            reverse("aportes_nacionales:agreement-create", args=[aporte.pk]),
            {
                "fecha_compromiso": "2026-07-31",
                "monto_comprometido": "100.00",
                "observacion": "Pago al cierre del mes",
            },
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        acuerdo = AcuerdoPagoAporteNacional.objects.get()
        self.assertEqual(acuerdo.aporte, aporte)
        self.assertEqual(acuerdo.estado, AcuerdoPagoAporteNacional.Estado.VIGENTE)
        self.assertEqual(acuerdo.registrado_por, self.superadmin)

    def test_no_registra_dos_acuerdos_vigentes_para_el_mismo_aporte(self):
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
        AcuerdoPagoAporteNacional.objects.create(
            iglesia=self.filial,
            aporte=aporte,
            fecha_compromiso="2026-07-31",
            monto_comprometido=Decimal("100.00"),
            registrado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.post(
            reverse("aportes_nacionales:agreement-create", args=[aporte.pk]),
            {
                "fecha_compromiso": "2026-08-15",
                "monto_comprometido": "100.00",
                "observacion": "Duplicado",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(AcuerdoPagoAporteNacional.objects.count(), 1)

    def test_superadmin_registra_ajuste_sobre_aporte_pagado(self):
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
            reverse("aportes_nacionales:adjustment-create", args=[aporte.pk]),
            {
                "tipo": AjusteAporteNacional.Tipo.CARGO,
                "monto": "15.00",
                "motivo": "Diferencia por cierre corregido",
                "observacion": "Se cobrara en el siguiente periodo",
            },
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        ajuste = AjusteAporteNacional.objects.get()
        self.assertEqual(ajuste.aporte, aporte)
        self.assertEqual(ajuste.iglesia, self.filial)
        self.assertEqual(ajuste.tipo, AjusteAporteNacional.Tipo.CARGO)
        self.assertEqual(ajuste.monto, Decimal("15.00"))
        self.assertEqual(ajuste.registrado_por, self.superadmin)

    def test_no_registra_ajuste_sobre_aporte_pendiente(self):
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
            reverse("aportes_nacionales:adjustment-create", args=[aporte.pk]),
            {
                "tipo": AjusteAporteNacional.Tipo.CARGO,
                "monto": "15.00",
                "motivo": "No corresponde",
                "observacion": "",
            },
        )

        self.assertRedirects(response, reverse("aportes_nacionales:detail", args=[aporte.pk]))
        self.assertFalse(AjusteAporteNacional.objects.exists())

    def test_admin_nacional_no_registra_ajustes(self):
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
        self.client.force_login(self.admin_nacional)

        response = self.client.get(reverse("aportes_nacionales:adjustment-create", args=[aporte.pk]))

        self.assertEqual(response.status_code, 403)

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

    def test_cuenta_corriente_incluye_ajustes_de_aportes_pagados(self):
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
        AjusteAporteNacional.objects.create(
            iglesia=self.filial,
            aporte=aporte,
            tipo=AjusteAporteNacional.Tipo.CARGO,
            monto=Decimal("15.00"),
            motivo="Diferencia a cobrar",
            registrado_por=self.superadmin,
        )
        AjusteAporteNacional.objects.create(
            iglesia=self.filial,
            aporte=aporte,
            tipo=AjusteAporteNacional.Tipo.ABONO,
            monto=Decimal("5.00"),
            motivo="Compensacion",
            registrado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:account"))

        self.assertEqual(response.context["total_ajustes_cargo"], Decimal("15.00"))
        self.assertEqual(response.context["total_ajustes_abono"], Decimal("5.00"))
        self.assertEqual(response.context["saldo"], Decimal("10.00"))

    def test_cuenta_corriente_incluye_pagos_parciales_y_mora(self):
        aporte = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            fecha_vencimiento="2026-01-31",
            generado_por=self.superadmin,
        )
        PagoAporteNacional.objects.create(
            iglesia=self.filial,
            aporte=aporte,
            monto=Decimal("40.00"),
            fecha_pago="2026-07-05",
            referencia_pago="DEP-PARCIAL",
            registrado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:account"))

        self.assertEqual(response.context["total_pagado"], Decimal("40.00"))
        self.assertEqual(response.context["saldo"], Decimal("60.00"))
        self.assertEqual(response.context["total_mora"], Decimal("60.00"))

    def test_tablero_morosidad_resume_pendientes_vencidos_y_acuerdos(self):
        aporte_vencido = AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            fecha_vencimiento="2026-01-31",
            generado_por=self.superadmin,
        )
        PagoAporteNacional.objects.create(
            iglesia=self.filial,
            aporte=aporte_vencido,
            monto=Decimal("40.00"),
            fecha_pago="2026-07-05",
            referencia_pago="DEP-PARCIAL",
            registrado_por=self.superadmin,
        )
        aporte_con_acuerdo = AporteNacional.objects.create(
            iglesia=self.otra_filial,
            cierre=self.cierre_otra,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("500.00"),
            monto_aporte=Decimal("50.00"),
            fecha_vencimiento="2099-01-31",
            generado_por=self.superadmin,
        )
        AcuerdoPagoAporteNacional.objects.create(
            iglesia=self.otra_filial,
            aporte=aporte_con_acuerdo,
            fecha_compromiso="2099-02-15",
            monto_comprometido=Decimal("50.00"),
            registrado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:arrears-dashboard"))

        self.assertContains(response, "Tablero de morosidad")
        self.assertEqual(response.context["total_aportes"], 2)
        self.assertEqual(response.context["total_pendiente"], Decimal("110.00"))
        self.assertEqual(response.context["total_mora"], Decimal("60.00"))
        self.assertEqual(response.context["total_con_acuerdo"], 1)

    def test_tablero_morosidad_respeta_alcance_de_filial(self):
        AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            fecha_vencimiento="2026-01-31",
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
            fecha_vencimiento="2026-01-31",
            generado_por=self.superadmin,
        )
        usuario = self.crear_usuario("tesorero_tablero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("aportes_nacionales:arrears-dashboard"))

        self.assertContains(response, "PRUEBAS")
        self.assertNotContains(response, "OTRA")
        self.assertEqual(response.context["total_pendiente"], Decimal("100.00"))

    def test_tablero_morosidad_filtra_por_zona(self):
        costa = Zona.objects.create(nombre="Costa tablero", codigo="COSTA-T")
        sierra = Zona.objects.create(nombre="Sierra tablero", codigo="SIERRA-T")
        self.filial.zona = costa
        self.filial.save(update_fields=["zona"])
        self.otra_filial.zona = sierra
        self.otra_filial.save(update_fields=["zona"])
        AporteNacional.objects.create(
            iglesia=self.filial,
            cierre=self.cierre,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("1000.00"),
            monto_aporte=Decimal("100.00"),
            fecha_vencimiento="2026-01-31",
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
            fecha_vencimiento="2026-01-31",
            generado_por=self.superadmin,
        )
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("aportes_nacionales:arrears-dashboard"), {"zona": costa.pk})

        codigos = [fila["aporte"].iglesia.codigo for fila in response.context["filas"]]
        self.assertEqual(codigos, ["PRUEBAS"])
        self.assertEqual(response.context["total_pendiente"], Decimal("100.00"))

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

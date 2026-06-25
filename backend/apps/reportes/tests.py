from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.aportes_nacionales.models import AporteNacional
from apps.finanzas.models import CierreMensualFinanciero
from apps.iglesias.models import Iglesia
from apps.inventario.models import ActivoInventario
from apps.miembros.models import Miembro
from apps.traslados.models import TrasladoMiembro
from apps.usuarios.models import Usuario
from apps.zonas.models import Zona


class ReporteTrasladosTests(TestCase):
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
            cedula="0606060606",
            sexo=Miembro.Sexo.FEMENINO,
        )
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra,
            nombres="Carlos",
            apellidos="Mora",
            cedula="0707070707",
            sexo=Miembro.Sexo.MASCULINO,
        )
        solicitante = self.crear_usuario("solicitante", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.traslado = TrasladoMiembro.objects.create(
            miembro=self.miembro,
            iglesia_origen=self.origen,
            iglesia_destino=self.destino,
            motivo="Cambio de domicilio",
            solicitado_por=solicitante,
        )
        self.traslado_rechazado = TrasladoMiembro.objects.create(
            miembro=self.miembro_otra,
            iglesia_origen=self.otra,
            iglesia_destino=self.destino,
            estado=TrasladoMiembro.Estado.RECHAZADO,
            motivo="No procede",
            solicitado_por=self.crear_usuario("solicitante_otra", Usuario.Rol.SECRETARIO_FILIAL, self.otra),
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

    def test_admin_nacional_accede_reporte_consolidado(self):
        usuario = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:traslados"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Maria")
        self.assertContains(response, "Carlos")
        self.assertContains(response, "Reporte de traslados")

    def test_filial_no_accede_reporte_nacional(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.origen)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:traslados"))

        self.assertEqual(response.status_code, 403)

    def test_reporte_filtra_por_estado(self):
        usuario = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:traslados"), {"estado": TrasladoMiembro.Estado.RECHAZADO})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Ana Maria")
        self.assertContains(response, "Carlos")

    def test_superadmin_accede_reporte(self):
        usuario = self.crear_usuario("superadmin", Usuario.Rol.SUPERADMIN, self.nacional, is_superuser=True)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:traslados"))

        self.assertEqual(response.status_code, 200)


class ReporteFinanzasTests(TestCase):
    def setUp(self):
        self.nacional = Iglesia.objects.create(
            codigo="NACIONAL",
            nombre="Iglesia Nacional",
            tipo=Iglesia.Tipo.NACIONAL,
        )
        self.costa = Zona.objects.create(nombre="Costa", codigo="COSTA")
        self.sierra = Zona.objects.create(nombre="Sierra", codigo="SIERRA")
        self.filial = Iglesia.objects.create(
            codigo="PRU",
            nombre="Iglesia Pruebas",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
            zona=self.costa,
        )
        self.otra = Iglesia.objects.create(
            codigo="OTR",
            nombre="Otra Iglesia",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
            zona=self.sierra,
        )
        self.admin = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
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
            iglesia=self.otra,
            anio=2026,
            mes=6,
            total_ingresos=Decimal("500.00"),
            total_egresos=Decimal("100.00"),
            saldo=Decimal("400.00"),
            cerrado_por=self.superadmin,
        )
        AporteNacional.objects.create(
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
        AporteNacional.objects.create(
            iglesia=self.otra,
            cierre=self.cierre_otra,
            anio=2026,
            mes=6,
            porcentaje=Decimal("10.00"),
            monto_base=Decimal("500.00"),
            monto_aporte=Decimal("50.00"),
            generado_por=self.superadmin,
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

    def test_admin_nacional_accede_reporte_financiero_consolidado(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("reportes:finanzas"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reporte financiero consolidado")
        self.assertContains(response, "PRU")
        self.assertContains(response, "OTR")
        self.assertEqual(response.context["totales"]["ingresos"], Decimal("1500.00"))
        self.assertEqual(response.context["totales"]["egresos"], Decimal("350.00"))
        self.assertEqual(response.context["totales"]["saldo"], Decimal("1150.00"))
        self.assertEqual(response.context["totales"]["aporte"], Decimal("150.00"))
        self.assertEqual(response.context["totales"]["pagado"], Decimal("100.00"))
        self.assertEqual(response.context["totales"]["pendiente"], Decimal("50.00"))

    def test_entrada_reportes_redirige_al_reporte_financiero(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("reportes:index"))

        self.assertRedirects(response, reverse("reportes:finanzas"))

    def test_filial_no_accede_reporte_financiero_nacional(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:finanzas"))

        self.assertEqual(response.status_code, 403)

    def test_reporte_financiero_filtra_por_zona(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("reportes:finanzas"), {"zona": self.costa.pk})

        codigos = [fila["cierre"].iglesia.codigo for fila in response.context["filas"]]
        self.assertEqual(codigos, ["PRU"])
        self.assertEqual(response.context["totales"]["ingresos"], Decimal("1000.00"))

    def test_reporte_financiero_filtra_por_iglesia_anio_y_mes(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("reportes:finanzas"),
            {"iglesia": self.otra.pk, "anio": "2026", "mes": "6"},
        )

        codigos = [fila["cierre"].iglesia.codigo for fila in response.context["filas"]]
        self.assertEqual(codigos, ["OTR"])
        self.assertEqual(response.context["totales"]["pendiente"], Decimal("50.00"))


class ReporteInventarioTests(TestCase):
    def setUp(self):
        self.nacional = Iglesia.objects.create(
            codigo="NACIONAL",
            nombre="Iglesia Nacional",
            tipo=Iglesia.Tipo.NACIONAL,
        )
        self.costa = Zona.objects.create(nombre="Costa", codigo="COSTA")
        self.sierra = Zona.objects.create(nombre="Sierra", codigo="SIERRA")
        self.filial = Iglesia.objects.create(
            codigo="PRU",
            nombre="Iglesia Pruebas",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
            zona=self.costa,
        )
        self.otra = Iglesia.objects.create(
            codigo="OTR",
            nombre="Otra Iglesia",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
            zona=self.sierra,
        )
        self.admin = self.crear_usuario("admin_nacional_inv", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.superadmin = self.crear_usuario("superadmin_inv", Usuario.Rol.SUPERADMIN, self.nacional, is_superuser=True)
        self.responsable = self.crear_usuario("responsable", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.proyector = ActivoInventario.objects.create(
            iglesia=self.filial,
            codigo="EQ-001",
            nombre="Proyector principal",
            categoria="Equipos",
            ubicacion_actual="Templo",
            responsable_actual=self.responsable,
            estado=ActivoInventario.Estado.ASIGNADO,
            valor_referencial=Decimal("800.00"),
        )
        self.sillas = ActivoInventario.objects.create(
            iglesia=self.filial,
            codigo="MOB-001",
            nombre="Sillas plasticas",
            categoria="Mobiliario",
            ubicacion_actual="Bodega",
            estado=ActivoInventario.Estado.DISPONIBLE,
            valor_referencial=Decimal("300.00"),
        )
        self.parlante = ActivoInventario.objects.create(
            iglesia=self.otra,
            codigo="EQ-010",
            nombre="Parlante auxiliar",
            categoria="Equipos",
            ubicacion_actual="Salon",
            estado=ActivoInventario.Estado.EN_REPARACION,
            valor_referencial=Decimal("200.00"),
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

    def test_admin_nacional_accede_reporte_inventario_consolidado(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("reportes:inventario"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reporte de inventario")
        self.assertContains(response, "EQ-001")
        self.assertContains(response, "EQ-010")
        self.assertEqual(response.context["total_activos"], 3)
        self.assertEqual(response.context["total_vigentes"], 3)
        self.assertEqual(response.context["valor_total"], Decimal("1300.00"))

    def test_filial_no_accede_reporte_inventario_nacional(self):
        usuario = self.crear_usuario("pastor_inv", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("reportes:inventario"))

        self.assertEqual(response.status_code, 403)

    def test_superadmin_accede_reporte_inventario(self):
        self.client.force_login(self.superadmin)

        response = self.client.get(reverse("reportes:inventario"))

        self.assertEqual(response.status_code, 200)

    def test_reporte_inventario_filtra_por_zona_iglesia_estado_y_categoria(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("reportes:inventario"),
            {
                "zona": self.costa.pk,
                "iglesia": self.filial.pk,
                "estado": ActivoInventario.Estado.ASIGNADO,
                "categoria": "Equipos",
            },
        )

        codigos = [activo.codigo for activo in response.context["activos"]]
        self.assertEqual(codigos, ["EQ-001"])
        self.assertEqual(response.context["total_activos"], 1)
        self.assertEqual(response.context["valor_total"], Decimal("800.00"))

    def test_reporte_inventario_filtra_por_busqueda(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("reportes:inventario"), {"q": "Bodega"})

        codigos = [activo.codigo for activo in response.context["activos"]]
        self.assertEqual(codigos, ["MOB-001"])
        self.assertContains(response, "Sillas plasticas")
        self.assertNotContains(response, "Proyector principal")

from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.auditoria.models import RegistroAuditoria
from apps.cargos.models import AsignacionCargo, Cargo
from apps.escuela_dominical.models import ClaseEscuelaDominical, MatriculaEscuelaDominical, NivelEscuelaDominical
from apps.familias.models import Familia, Matrimonio, MiembroFamilia
from apps.iglesias.models import Iglesia
from apps.miembros.models import HistorialPastoralMiembro, Miembro
from apps.ministerios.models import Ministerio, ParticipacionMinisterio
from apps.parametros.models import Periodo
from apps.usuarios.models import Usuario


class MiembroListViewTests(TestCase):
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
            telefono="0990000001",
        )
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra_filial,
            nombres="Carlos",
            apellidos="Mora",
            cedula="0202020202",
            sexo=Miembro.Sexo.MASCULINO,
            telefono="0990000002",
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def test_redirige_a_login_si_no_hay_sesion(self):
        response = self.client.get(reverse("miembros:list"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("core:login"), response["Location"])

    def test_usuario_filial_solo_ve_miembros_de_su_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:list"))

        self.assertContains(response, "Ana Maria")
        self.assertNotContains(response, "Carlos")

    def test_usuario_nacional_no_accede_modulo_operativo_de_miembros(self):
        usuario = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:list"))

        self.assertEqual(response.status_code, 403)

    def test_busqueda_filtra_resultados(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:list"), {"q": "010101"})

        self.assertContains(response, "Ana Maria")
        self.assertNotContains(response, "Carlos")

    def test_rol_no_autorizado_recibe_403(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:list"))

        self.assertEqual(response.status_code, 403)


class MiembroFormViewTests(TestCase):
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
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra_filial,
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

    def datos_formulario(self, **overrides):
        data = {
            "iglesia": self.filial.pk,
            "nombres": "Nuevo",
            "apellidos": "Miembro",
            "cedula": "",
            "fecha_nacimiento": "",
            "sexo": Miembro.Sexo.MASCULINO,
            "estado_civil": "",
            "telefono": "",
            "direccion": "",
            "fecha_conversion": "",
            "fecha_bautismo": "",
            "fecha_membresia": "",
            "estado": Miembro.Estado.ACTIVO,
            "fecha_fallecimiento": "",
            "observacion": "",
            "activo": "on",
        }
        data.update(overrides)
        return data

    def test_usuario_con_permiso_puede_crear_miembro_en_su_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(reverse("miembros:create"), self.datos_formulario())

        self.assertRedirects(response, reverse("miembros:list"))
        miembro = Miembro.objects.get(nombres="Nuevo")
        self.assertEqual(miembro.iglesia, self.filial)

    def test_usuario_filial_no_puede_forzar_otra_iglesia_al_crear(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:create"),
            self.datos_formulario(iglesia=self.otra_filial.pk, nombres="Forzado"),
        )

        self.assertRedirects(response, reverse("miembros:list"))
        miembro = Miembro.objects.get(nombres="Forzado")
        self.assertEqual(miembro.iglesia, self.filial)

    def test_superadmin_puede_elegir_iglesia_al_crear(self):
        usuario = self.crear_usuario("superadmin", Usuario.Rol.SUPERADMIN, self.nacional)
        usuario.is_superuser = True
        usuario.save(update_fields=["is_superuser"])
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:create"),
            self.datos_formulario(iglesia=self.otra_filial.pk, nombres="Nacional"),
        )

        self.assertRedirects(response, reverse("miembros:list"))
        miembro = Miembro.objects.get(nombres="Nacional")
        self.assertEqual(miembro.iglesia, self.otra_filial)

    def test_usuario_no_autorizado_no_puede_crear(self):
        usuario = self.crear_usuario("tesorero", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:create"))

        self.assertEqual(response.status_code, 403)

    def test_usuario_filial_no_puede_editar_miembro_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:update", args=[self.miembro_otra.pk]))

        self.assertEqual(response.status_code, 404)

    def test_usuario_con_permiso_puede_editar_miembro_de_su_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:update", args=[self.miembro_pruebas.pk]),
            self.datos_formulario(nombres="Ana Editada", apellidos="Lopez"),
        )

        self.assertRedirects(response, reverse("miembros:list"))
        self.miembro_pruebas.refresh_from_db()
        self.assertEqual(self.miembro_pruebas.nombres, "Ana Editada")
        self.assertEqual(self.miembro_pruebas.iglesia, self.filial)


class MiembroDetalleYAccionesPastoralesTests(TestCase):
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
        self.miembro_otra = Miembro.objects.create(
            iglesia=self.otra_filial,
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

    def test_detalle_respeta_alcance_por_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:detail", args=[self.miembro_pruebas.pk]))
        response_otra = self.client.get(reverse("miembros:detail", args=[self.miembro_otra.pk]))

        self.assertContains(response, "Ana Maria")
        self.assertEqual(response_otra.status_code, 404)

    def test_registrar_bautismo_actualiza_fecha(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:bautismo", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-01", "motivo": "Profesion publica de fe."},
        )

        self.assertRedirects(response, reverse("miembros:detail", args=[self.miembro_pruebas.pk]))
        self.miembro_pruebas.refresh_from_db()
        self.assertEqual(self.miembro_pruebas.fecha_bautismo, date(2026, 6, 1))
        historial = HistorialPastoralMiembro.objects.get(miembro=self.miembro_pruebas)
        self.assertEqual(historial.tipo, HistorialPastoralMiembro.Tipo.BAUTISMO)
        self.assertEqual(historial.motivo, "Profesion publica de fe.")
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="miembros", accion="BAUTISMO").exists())

    def test_registrar_admision_actualiza_fecha_y_activa_miembro(self):
        self.miembro_pruebas.estado = Miembro.Estado.INACTIVO
        self.miembro_pruebas.activo = False
        self.miembro_pruebas.save(update_fields=["estado", "activo"])
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:membresia", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-02", "motivo": "Recibida como miembro oficial."},
        )

        self.assertRedirects(response, reverse("miembros:detail", args=[self.miembro_pruebas.pk]))
        self.miembro_pruebas.refresh_from_db()
        self.assertEqual(self.miembro_pruebas.fecha_membresia, date(2026, 6, 2))
        self.assertEqual(self.miembro_pruebas.estado, Miembro.Estado.ACTIVO)
        self.assertTrue(self.miembro_pruebas.activo)
        self.assertTrue(
            HistorialPastoralMiembro.objects.filter(
                miembro=self.miembro_pruebas,
                tipo=HistorialPastoralMiembro.Tipo.ADMISION,
            ).exists()
        )

    def test_registrar_fallecimiento_actualiza_fecha_estado_y_activo(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:fallecimiento", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-03", "motivo": "Registro por acta pastoral."},
        )

        self.assertRedirects(response, reverse("miembros:detail", args=[self.miembro_pruebas.pk]))
        self.miembro_pruebas.refresh_from_db()
        self.assertEqual(self.miembro_pruebas.fecha_fallecimiento, date(2026, 6, 3))
        self.assertEqual(self.miembro_pruebas.estado, Miembro.Estado.FALLECIDO)
        self.assertFalse(self.miembro_pruebas.activo)
        self.assertTrue(
            HistorialPastoralMiembro.objects.filter(
                miembro=self.miembro_pruebas,
                tipo=HistorialPastoralMiembro.Tipo.FALLECIMIENTO,
            ).exists()
        )

    def test_fallecimiento_cierra_relaciones_activas_del_miembro(self):
        familia = Familia.objects.create(
            iglesia=self.filial,
            nombre="Familia Lopez",
            jefe_hogar=self.miembro_pruebas,
        )
        vinculo = MiembroFamilia.objects.create(
            familia=familia,
            miembro=self.miembro_pruebas,
            relacion=MiembroFamilia.Relacion.REPRESENTANTE,
        )
        cargo = Cargo.objects.create(nombre="Diacono")
        asignacion = AsignacionCargo.objects.create(
            iglesia=self.filial,
            cargo=cargo,
            miembro=self.miembro_pruebas,
            fecha_inicio=date(2026, 1, 1),
        )
        ministerio = Ministerio.objects.create(
            iglesia=self.filial,
            nombre="Alabanza",
            responsable=self.miembro_pruebas,
        )
        participacion = ParticipacionMinisterio.objects.create(
            ministerio=ministerio,
            miembro=self.miembro_pruebas,
            cargo="Vocalista",
            fecha_inicio=date(2026, 1, 1),
        )
        periodo = Periodo.objects.create(
            nombre="2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )
        nivel = NivelEscuelaDominical.objects.create(
            iglesia=self.filial,
            nombre="Intermedios",
            edad_minima=10,
            edad_maxima=12,
        )
        clase = ClaseEscuelaDominical.objects.create(
            iglesia=self.filial,
            nombre="Intermedios A",
            nivel=nivel,
            periodo=periodo,
        )
        matricula = MatriculaEscuelaDominical.objects.create(
            clase=clase,
            alumno=self.miembro_pruebas,
            fecha_inscripcion=date(2026, 1, 5),
        )
        usuario = self.crear_usuario("pastor_fallecimiento", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:fallecimiento", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-03", "motivo": "Fallecimiento confirmado."},
        )

        self.assertRedirects(response, reverse("miembros:detail", args=[self.miembro_pruebas.pk]))
        familia.refresh_from_db()
        vinculo.refresh_from_db()
        asignacion.refresh_from_db()
        ministerio.refresh_from_db()
        participacion.refresh_from_db()
        matricula.refresh_from_db()
        self.assertFalse(familia.activo)
        self.assertFalse(vinculo.activo)
        self.assertEqual(asignacion.estado, AsignacionCargo.Estado.FINALIZADO)
        self.assertEqual(asignacion.fecha_fin, date(2026, 6, 3))
        self.assertIsNone(ministerio.responsable)
        self.assertEqual(participacion.estado, ParticipacionMinisterio.Estado.FINALIZADO)
        self.assertFalse(participacion.activo)
        self.assertEqual(matricula.estado, MatriculaEscuelaDominical.Estado.RETIRADA)
        self.assertFalse(matricula.activo)
        historial = HistorialPastoralMiembro.objects.get(
            miembro=self.miembro_pruebas,
            tipo=HistorialPastoralMiembro.Tipo.FALLECIMIENTO,
        )
        self.assertEqual(historial.resumen_cierre["asignaciones_cargos"], 1)
        self.assertEqual(historial.resumen_cierre["participaciones_ministerios"], 1)
        self.assertEqual(historial.resumen_cierre["matriculas_escuela_dominical"], 1)

    def test_registra_baja_restauracion_disciplina_y_suspension(self):
        usuario = self.crear_usuario("pastor_ciclo", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        self.client.post(
            reverse("miembros:baja_voluntaria", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-04", "motivo": "Solicitud formal del miembro."},
        )
        self.miembro_pruebas.refresh_from_db()
        self.assertEqual(self.miembro_pruebas.estado, Miembro.Estado.INACTIVO)
        self.assertFalse(self.miembro_pruebas.activo)

        self.client.post(
            reverse("miembros:restauracion", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-05", "motivo": "Restauracion aprobada."},
        )
        self.miembro_pruebas.refresh_from_db()
        self.assertEqual(self.miembro_pruebas.estado, Miembro.Estado.ACTIVO)
        self.assertTrue(self.miembro_pruebas.activo)

        self.client.post(
            reverse("miembros:disciplina", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-06", "motivo": "Proceso pastoral documentado."},
        )
        self.miembro_pruebas.refresh_from_db()
        self.assertEqual(self.miembro_pruebas.estado, Miembro.Estado.DISCIPLINA)
        self.assertTrue(self.miembro_pruebas.activo)

        self.client.post(
            reverse("miembros:suspension", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-07", "motivo": "Suspension temporal aprobada."},
        )
        self.miembro_pruebas.refresh_from_db()
        self.assertEqual(self.miembro_pruebas.estado, Miembro.Estado.SUSPENDIDO)
        self.assertFalse(self.miembro_pruebas.activo)
        self.assertEqual(HistorialPastoralMiembro.objects.filter(miembro=self.miembro_pruebas).count(), 4)

    def test_accion_pastoral_requiere_motivo(self):
        usuario = self.crear_usuario("pastor_motivo", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:baja_voluntaria", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-04", "motivo": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("motivo", response.context["form"].errors)
        self.assertFalse(HistorialPastoralMiembro.objects.exists())

    def test_usuario_sin_gestion_no_puede_registrar_accion_pastoral(self):
        usuario = self.crear_usuario("lectura", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:bautismo", args=[self.miembro_pruebas.pk]),
            {"fecha": "2026-06-01", "motivo": "No permitido"},
        )

        self.assertEqual(response.status_code, 403)

    def test_usuario_filial_no_puede_registrar_accion_en_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:bautismo", args=[self.miembro_otra.pk]),
            {"fecha": "2026-06-01", "motivo": "No permitido"},
        )

        self.assertEqual(response.status_code, 404)


class MiembroFamiliasTests(TestCase):
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

    def test_detalle_muestra_familias_del_miembro(self):
        MiembroFamilia.objects.create(
            familia=self.familia_pruebas,
            miembro=self.miembro_pruebas,
            relacion=MiembroFamilia.Relacion.MADRE,
        )
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:detail", args=[self.miembro_pruebas.pk]))

        self.assertContains(response, "Familia Lopez")
        self.assertContains(response, "Madre")

    def test_crear_familia_desde_miembro_usa_iglesia_del_miembro(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:familia_create", args=[self.miembro_pruebas.pk]),
            {
                "nombre": "Familia Nueva",
                "relacion": MiembroFamilia.Relacion.REPRESENTANTE,
                "direccion": "Calle 1",
                "telefono": "0999999999",
            },
        )

        self.assertRedirects(response, reverse("miembros:detail", args=[self.miembro_pruebas.pk]))
        familia = Familia.objects.get(nombre="Familia Nueva")
        self.assertEqual(familia.iglesia, self.filial)
        self.assertEqual(familia.jefe_hogar, self.miembro_pruebas)
        self.assertTrue(
            MiembroFamilia.objects.filter(
                familia=familia,
                miembro=self.miembro_pruebas,
                relacion=MiembroFamilia.Relacion.REPRESENTANTE,
            ).exists()
        )

    def test_vincular_miembro_a_familia_existente_de_su_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:familia_link", args=[self.miembro_pruebas.pk]),
            {
                "familia": self.familia_pruebas.pk,
                "relacion": MiembroFamilia.Relacion.HIJO,
            },
        )

        self.assertRedirects(response, reverse("miembros:detail", args=[self.miembro_pruebas.pk]))
        self.assertTrue(
            MiembroFamilia.objects.filter(
                familia=self.familia_pruebas,
                miembro=self.miembro_pruebas,
                relacion=MiembroFamilia.Relacion.HIJO,
            ).exists()
        )

    def test_no_permite_vincular_familia_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:familia_link", args=[self.miembro_pruebas.pk]),
            {
                "familia": self.familia_otra.pk,
                "relacion": MiembroFamilia.Relacion.HIJO,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("familia", response.context["form"].errors)
        self.assertFalse(
            MiembroFamilia.objects.filter(
                familia=self.familia_otra,
                miembro=self.miembro_pruebas,
            ).exists()
        )

    def test_no_permite_duplicar_misma_relacion_en_familia(self):
        MiembroFamilia.objects.create(
            familia=self.familia_pruebas,
            miembro=self.miembro_pruebas,
            relacion=MiembroFamilia.Relacion.HIJO,
        )
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:familia_link", args=[self.miembro_pruebas.pk]),
            {
                "familia": self.familia_pruebas.pk,
                "relacion": MiembroFamilia.Relacion.HIJO,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El miembro ya tiene esa relacion")

    def test_usuario_sin_gestion_no_puede_crear_familia(self):
        usuario = self.crear_usuario("lectura", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:familia_create", args=[self.miembro_pruebas.pk]))

        self.assertEqual(response.status_code, 403)

    def test_usuario_filial_no_puede_crear_familia_para_miembro_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:familia_create", args=[self.miembro_otra.pk]))

        self.assertEqual(response.status_code, 404)


class MiembroMatrimonioTests(TestCase):
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
        self.conyuge = Miembro.objects.create(
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
        self.familia = Familia.objects.create(
            iglesia=self.filial,
            nombre="Familia Perez Lopez",
            jefe_hogar=self.conyuge,
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def test_registrar_matrimonio_crea_vinculo_y_actualiza_estado_civil(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:matrimonio", args=[self.miembro.pk]),
            {
                "conyuge": self.conyuge.pk,
                "fecha_matrimonio": "2026-06-20",
                "familia": self.familia.pk,
                "observacion": "Registro inicial",
            },
        )

        self.assertRedirects(response, reverse("miembros:detail", args=[self.miembro.pk]))
        matrimonio = Matrimonio.objects.get(conyuge_1=self.miembro, conyuge_2=self.conyuge)
        self.assertEqual(matrimonio.iglesia, self.filial)
        self.assertEqual(matrimonio.familia, self.familia)
        self.miembro.refresh_from_db()
        self.conyuge.refresh_from_db()
        self.assertEqual(self.miembro.estado_civil, Miembro.EstadoCivil.CASADO)
        self.assertEqual(self.conyuge.estado_civil, Miembro.EstadoCivil.CASADO)
        self.assertTrue(
            MiembroFamilia.objects.filter(
                familia=self.familia,
                miembro=self.miembro,
                relacion=MiembroFamilia.Relacion.CONYUGE,
                activo=True,
            ).exists()
        )
        self.assertTrue(
            MiembroFamilia.objects.filter(
                familia=self.familia,
                miembro=self.conyuge,
                relacion=MiembroFamilia.Relacion.CONYUGE,
                activo=True,
            ).exists()
        )

    def test_detalle_muestra_matrimonio(self):
        Matrimonio.objects.create(
            iglesia=self.filial,
            conyuge_1=self.miembro,
            conyuge_2=self.conyuge,
            fecha_matrimonio="2026-06-20",
        )
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:detail", args=[self.miembro.pk]))

        self.assertContains(response, "Perez Luis")
        self.assertContains(response, "2026-06-20")

    def test_no_permite_conyuge_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:matrimonio", args=[self.miembro.pk]),
            {
                "conyuge": self.miembro_otra.pk,
                "fecha_matrimonio": "2026-06-20",
                "familia": "",
                "observacion": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("conyuge", response.context["form"].errors)
        self.assertFalse(Matrimonio.objects.exists())

    def test_no_permite_matrimonio_activo_duplicado(self):
        Matrimonio.objects.create(
            iglesia=self.filial,
            conyuge_1=self.conyuge,
            conyuge_2=self.miembro,
            fecha_matrimonio="2026-06-20",
        )
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("miembros:matrimonio", args=[self.miembro.pk]),
            {
                "conyuge": self.conyuge.pk,
                "fecha_matrimonio": "2026-06-21",
                "familia": "",
                "observacion": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un matrimonio activo")
        self.assertEqual(Matrimonio.objects.count(), 1)

    def test_usuario_sin_gestion_no_puede_registrar_matrimonio(self):
        usuario = self.crear_usuario("lectura", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:matrimonio", args=[self.miembro.pk]))

        self.assertEqual(response.status_code, 403)

    def test_usuario_filial_no_puede_registrar_matrimonio_de_miembro_de_otra_iglesia(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("miembros:matrimonio", args=[self.miembro_otra.pk]))

        self.assertEqual(response.status_code, 404)

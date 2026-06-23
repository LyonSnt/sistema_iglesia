from datetime import date

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from django.test import TestCase
from django.urls import reverse

from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.parametros.models import Periodo
from apps.usuarios.models import Usuario

from .admin import MatriculaEscuelaDominicalAdmin
from .models import (
    AsistenciaEscuelaDominical,
    ClaseEscuelaDominical,
    MatriculaEscuelaDominical,
    NivelEscuelaDominical,
    SesionEscuelaDominical,
    ProcesoPromocionEscuelaDominical,
    ResultadoPromocionEscuelaDominical,
)
from .promociones import confirmar_promocion, generar_resultados


class EscuelaDominicalViewsTests(TestCase):
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
        self.periodo = Periodo.objects.create(
            nombre="2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )
        self.nivel = NivelEscuelaDominical.objects.create(
            iglesia=self.filial,
            nombre="Primarios",
            edad_minima=7,
            edad_maxima=9,
        )
        self.nivel_otra = NivelEscuelaDominical.objects.create(
            iglesia=self.otra_filial,
            nombre="Jovenes",
            edad_minima=13,
            edad_maxima=17,
        )
        self.maestro = self.crear_usuario("maestro", Usuario.Rol.SOLO_LECTURA, self.filial)
        self.maestro_otra = self.crear_usuario("maestro_otra", Usuario.Rol.SOLO_LECTURA, self.otra_filial)
        self.alumno = Miembro.objects.create(
            iglesia=self.filial,
            nombres="Ana Maria",
            apellidos="Lopez",
            sexo=Miembro.Sexo.FEMENINO,
        )
        self.otro_alumno = Miembro.objects.create(
            iglesia=self.filial,
            nombres="Luis",
            apellidos="Perez",
            sexo=Miembro.Sexo.MASCULINO,
        )
        self.alumno_otra = Miembro.objects.create(
            iglesia=self.otra_filial,
            nombres="Carlos",
            apellidos="Mora",
            sexo=Miembro.Sexo.MASCULINO,
        )
        self.clase = ClaseEscuelaDominical.objects.create(
            iglesia=self.filial,
            nombre="Primarios A",
            nivel=self.nivel,
            periodo=self.periodo,
            maestro=self.maestro,
            cupo=2,
        )
        self.clase_otra = ClaseEscuelaDominical.objects.create(
            iglesia=self.otra_filial,
            nombre="Jovenes A",
            nivel=self.nivel_otra,
            periodo=self.periodo,
            maestro=self.maestro_otra,
        )
        self.matricula = MatriculaEscuelaDominical.objects.create(
            clase=self.clase,
            alumno=self.alumno,
            fecha_inscripcion=date(2026, 1, 5),
        )

    def crear_usuario(self, username, rol, iglesia):
        return Usuario.objects.create_user(
            username=username,
            password="Cambiar12345!",
            rol=rol,
            iglesia=iglesia,
        )

    def datos_nivel(self, **overrides):
        data = {
            "iglesia": self.filial.pk,
            "nombre": "Prejuveniles",
            "edad_minima": 10,
            "edad_maxima": 12,
            "orden": 2,
            "descripcion": "",
            "activo": "on",
        }
        data.update(overrides)
        return data

    def datos_clase(self, **overrides):
        data = {
            "iglesia": self.filial.pk,
            "nombre": "Primarios B",
            "nivel": self.nivel.pk,
            "periodo": self.periodo.pk,
            "maestro": self.maestro.pk,
            "aula": "Salon 2",
            "horario": "Domingos 09:00",
            "cupo": 20,
            "descripcion": "",
            "activo": "on",
        }
        data.update(overrides)
        return data

    def test_listado_respeta_alcance_por_iglesia(self):
        self.client.force_login(self.maestro)

        response = self.client.get(reverse("escuela_dominical:list"))

        self.assertContains(response, "Primarios A")
        self.assertNotContains(response, "Jovenes A")

    def test_usuario_nacional_no_accede_modulo_operativo_de_escuela(self):
        usuario = self.crear_usuario("admin_nacional", Usuario.Rol.ADMIN_NACIONAL, self.nacional)
        self.client.force_login(usuario)

        response = self.client.get(reverse("escuela_dominical:list"))

        self.assertEqual(response.status_code, 403)

    def test_detalle_de_otra_iglesia_responde_404(self):
        self.client.force_login(self.maestro)

        response = self.client.get(reverse("escuela_dominical:detail", args=[self.clase_otra.pk]))

        self.assertEqual(response.status_code, 404)


class PromocionEscuelaDominicalTests(TestCase):
    def setUp(self):
        self.nacional = Iglesia.objects.create(
            codigo="NACIONAL-P", nombre="Iglesia Nacional", tipo=Iglesia.Tipo.NACIONAL
        )
        self.iglesia = Iglesia.objects.create(
            codigo="PROMO",
            nombre="Iglesia Promociones",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=self.nacional,
        )
        self.origen = Periodo.objects.create(
            nombre="2026 promocion", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
        )
        self.destino = Periodo.objects.create(
            nombre="2027 promocion", fecha_inicio=date(2027, 1, 1), fecha_fin=date(2027, 12, 31)
        )
        self.nivel_1 = NivelEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="Nivel 1", edad_minima=1, edad_maxima=3, orden=1
        )
        self.nivel_2 = NivelEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="Nivel 2", edad_minima=4, edad_maxima=6, orden=2
        )
        self.nivel_5 = NivelEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="Nivel 5", edad_minima=13, edad_maxima=18, orden=5
        )
        self.clase_1 = ClaseEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="Nivel 1 - 2026", nivel=self.nivel_1, periodo=self.origen
        )
        self.clase_2_destino = ClaseEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="Nivel 2 - 2027", nivel=self.nivel_2, periodo=self.destino
        )
        self.clase_5 = ClaseEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="Nivel 5 - 2026", nivel=self.nivel_5, periodo=self.origen
        )
        self.pastor = Usuario.objects.create_user(
            username="pastor_promocion",
            password="Cambiar12345!",
            rol=Usuario.Rol.PASTOR_FILIAL,
            iglesia=self.iglesia,
        )
        self.maestro = Usuario.objects.create_user(
            username="maestro_promocion",
            password="Cambiar12345!",
            rol=Usuario.Rol.SOLO_LECTURA,
            iglesia=self.iglesia,
        )

    def crear_matricula(self, nombres, nacimiento, clase):
        alumno = Miembro.objects.create(
            iglesia=self.iglesia,
            nombres=nombres,
            apellidos="Prueba",
            sexo=Miembro.Sexo.FEMENINO,
            fecha_nacimiento=nacimiento,
        )
        return MatriculaEscuelaDominical.objects.create(
            clase=clase, alumno=alumno, fecha_inscripcion=date(2026, 1, 1)
        )

    def crear_proceso(self):
        return ProcesoPromocionEscuelaDominical.objects.create(
            iglesia=self.iglesia,
            periodo_origen=self.origen,
            periodo_destino=self.destino,
            fecha_corte=date(2027, 1, 10),
        )

    def test_cumpleanos_en_el_corte_promueve_y_despues_del_corte_espera(self):
        en_corte = self.crear_matricula("Cumple en corte", date(2023, 1, 10), self.clase_1)
        despues = self.crear_matricula("Cumple despues", date(2023, 1, 11), self.clase_1)

        resultados = generar_resultados(self.crear_proceso())

        self.assertEqual([resultado.matricula_origen for resultado in resultados], [en_corte])
        self.assertFalse(
            ResultadoPromocionEscuelaDominical.objects.filter(matricula_origen=despues).exists()
        )

    def test_adolescente_de_18_al_corte_egresa_a_jovenes(self):
        matricula = self.crear_matricula("Adolescente", date(2009, 1, 10), self.clase_5)

        resultado = generar_resultados(self.crear_proceso())[0]

        self.assertEqual(resultado.matricula_origen, matricula)
        self.assertEqual(resultado.edad_al_corte, 18)
        self.assertEqual(resultado.destino, ResultadoPromocionEscuelaDominical.Destino.JOVENES)
        self.assertIsNone(resultado.clase_destino)

    def test_confirmacion_cierra_origen_y_crea_matricula_destino(self):
        origen = self.crear_matricula("Promovida", date(2023, 1, 10), self.clase_1)
        proceso = self.crear_proceso()
        resultado = generar_resultados(proceso)[0]
        resultado.clase_destino = self.clase_2_destino
        resultado.save(update_fields=["clase_destino"])

        confirmar_promocion(proceso, self.pastor)

        origen.refresh_from_db()
        proceso.refresh_from_db()
        resultado.refresh_from_db()
        self.assertEqual(origen.estado, MatriculaEscuelaDominical.Estado.PROMOVIDA)
        self.assertEqual(origen.fecha_salida, proceso.fecha_corte)
        self.assertEqual(resultado.matricula_destino.clase, self.clase_2_destino)
        self.assertEqual(proceso.estado, ProcesoPromocionEscuelaDominical.Estado.CONFIRMADO)
        self.assertEqual(proceso.confirmado_por, self.pastor)

    def test_confirmar_dos_veces_no_duplica_la_matricula_destino(self):
        self.crear_matricula("Promocion unica", date(2023, 1, 10), self.clase_1)
        proceso = self.crear_proceso()
        resultado = generar_resultados(proceso)[0]
        resultado.clase_destino = self.clase_2_destino
        resultado.save(update_fields=["clase_destino"])

        confirmar_promocion(proceso, self.pastor)
        confirmar_promocion(proceso, self.pastor)

        self.assertEqual(
            MatriculaEscuelaDominical.objects.filter(
                clase=self.clase_2_destino, alumno=resultado.matricula_origen.alumno
            ).count(),
            1,
        )

    def test_maestro_no_puede_administrar_promociones(self):
        self.client.force_login(self.maestro)

        response = self.client.get(reverse("escuela_dominical:promocion-list"))

        self.assertEqual(response.status_code, 403)

    def test_pastor_prepara_y_revisa_un_corte_desde_la_interfaz(self):
        self.crear_matricula("Candidata web", date(2023, 1, 10), self.clase_1)
        self.client.force_login(self.pastor)

        response = self.client.post(
            reverse("escuela_dominical:promocion-create"),
            {
                "periodo_origen": self.origen.pk,
                "periodo_destino": self.destino.pk,
                "fecha_corte": "2027-01-10",
            },
        )

        proceso = ProcesoPromocionEscuelaDominical.objects.get()
        self.assertRedirects(
            response, reverse("escuela_dominical:promocion-detail", args=[proceso.pk])
        )
        detalle = self.client.get(
            reverse("escuela_dominical:promocion-detail", args=[proceso.pk])
        )
        self.assertContains(detalle, "Candidata web")
        self.assertContains(detalle, "Nivel 2 - 2027")


class EscuelaDominicalViewsContinuacionTests(TestCase):
    setUp = EscuelaDominicalViewsTests.setUp
    crear_usuario = EscuelaDominicalViewsTests.crear_usuario
    datos_nivel = EscuelaDominicalViewsTests.datos_nivel
    datos_clase = EscuelaDominicalViewsTests.datos_clase

    def test_filial_crea_nivel_en_su_iglesia(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("escuela_dominical:nivel-create"),
            self.datos_nivel(iglesia=self.otra_filial.pk),
        )

        self.assertRedirects(response, reverse("escuela_dominical:nivel-list"))
        self.assertEqual(NivelEscuelaDominical.objects.get(nombre="Prejuveniles").iglesia, self.filial)

    def test_nivel_rechaza_rango_de_edad_invalido(self):
        usuario = self.crear_usuario("pastor", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("escuela_dominical:nivel-create"),
            self.datos_nivel(edad_minima=12, edad_maxima=10),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("edad_maxima", response.context["form"].errors)

    def test_pastor_puede_crear_clase_en_su_iglesia(self):
        usuario = self.crear_usuario("pastor_crea", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.post(reverse("escuela_dominical:create"), self.datos_clase())

        self.assertRedirects(response, reverse("escuela_dominical:list"))
        self.assertEqual(ClaseEscuelaDominical.objects.get(nombre="Primarios B").iglesia, self.filial)

    def test_maestro_solo_ve_sus_clases(self):
        otro_maestro = self.crear_usuario("otro_maestro", Usuario.Rol.SOLO_LECTURA, self.filial)
        ClaseEscuelaDominical.objects.create(
            iglesia=self.filial,
            nombre="Primarios B",
            nivel=self.nivel,
            periodo=self.periodo,
            maestro=otro_maestro,
        )
        self.client.force_login(self.maestro)

        response = self.client.get(reverse("escuela_dominical:list"))

        self.assertContains(response, "Primarios A")
        self.assertNotContains(response, "Primarios B")

    def test_maestro_no_puede_crear_ni_editar_clases_o_niveles(self):
        self.client.force_login(self.maestro)

        respuestas = (
            self.client.get(reverse("escuela_dominical:create")),
            self.client.get(reverse("escuela_dominical:update", args=[self.clase.pk])),
            self.client.get(reverse("escuela_dominical:nivel-create")),
            self.client.get(reverse("escuela_dominical:nivel-update", args=[self.nivel.pk])),
        )

        self.assertTrue(all(response.status_code == 403 for response in respuestas))

    def test_clase_rechaza_maestro_de_otra_iglesia(self):
        usuario = self.crear_usuario("superadmin", Usuario.Rol.SUPERADMIN, self.nacional)
        usuario.is_superuser = True
        usuario.save(update_fields=["is_superuser"])
        self.client.force_login(usuario)

        response = self.client.post(
            reverse("escuela_dominical:create"),
            self.datos_clase(maestro=self.maestro_otra.pk),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "El maestro debe pertenecer")

    def test_matricula_alumno_de_la_misma_iglesia(self):
        self.client.force_login(self.maestro)

        response = self.client.post(
            reverse("escuela_dominical:matricula-add", args=[self.clase.pk]),
            {
                "alumno": self.otro_alumno.pk,
                "fecha_inscripcion": "2026-01-06",
                "estado": MatriculaEscuelaDominical.Estado.ACTIVA,
                "fecha_salida": "",
                "observacion": "",
                "activo": "on",
            },
        )

        self.assertRedirects(response, reverse("escuela_dominical:detail", args=[self.clase.pk]))
        self.assertTrue(self.clase.matriculas.filter(alumno=self.otro_alumno).exists())

    def test_matricula_rechaza_alumno_de_otra_iglesia(self):
        self.client.force_login(self.maestro)

        response = self.client.post(
            reverse("escuela_dominical:matricula-add", args=[self.clase.pk]),
            {
                "alumno": self.alumno_otra.pk,
                "fecha_inscripcion": "2026-01-06",
                "estado": MatriculaEscuelaDominical.Estado.ACTIVA,
                "fecha_salida": "",
                "observacion": "",
                "activo": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("alumno", response.context["form"].errors)

    def test_matricula_respeta_cupo(self):
        MatriculaEscuelaDominical.objects.create(
            clase=self.clase,
            alumno=self.otro_alumno,
            fecha_inscripcion=date(2026, 1, 6),
        )
        tercer_alumno = Miembro.objects.create(
            iglesia=self.filial,
            nombres="Marta",
            apellidos="Rios",
            sexo=Miembro.Sexo.FEMENINO,
        )
        self.client.force_login(self.maestro)

        response = self.client.post(
            reverse("escuela_dominical:matricula-add", args=[self.clase.pk]),
            {
                "alumno": tercer_alumno.pk,
                "fecha_inscripcion": "2026-01-07",
                "estado": MatriculaEscuelaDominical.Estado.ACTIVA,
                "fecha_salida": "",
                "observacion": "",
                "activo": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alcanzo el cupo")

    def test_rol_sin_permiso_recibe_403(self):
        usuario = self.crear_usuario("secretario", Usuario.Rol.SECRETARIO_FILIAL, self.filial)
        self.client.force_login(usuario)

        response = self.client.get(reverse("escuela_dominical:list"))

        self.assertEqual(response.status_code, 403)

    def test_admin_de_matriculas_respeta_iglesia(self):
        MatriculaEscuelaDominical.objects.create(
            clase=self.clase_otra,
            alumno=self.alumno_otra,
            fecha_inscripcion=date(2026, 1, 5),
        )
        request = RequestFactory().get("/admin/escuela_dominical/matriculaescueladominical/")
        request.user = self.maestro
        model_admin = MatriculaEscuelaDominicalAdmin(MatriculaEscuelaDominical, AdminSite())

        queryset = model_admin.get_queryset(request)

        self.assertEqual(list(queryset), [self.matricula])

    def test_usuario_con_otro_rol_opera_clase_si_esta_asignado(self):
        tesorero = self.crear_usuario("tesorero_maestro", Usuario.Rol.TESORERO_FILIAL, self.filial)
        self.clase.maestro = tesorero
        self.clase.save(update_fields=["maestro"])
        self.client.force_login(tesorero)

        listado = self.client.get(reverse("escuela_dominical:list"))
        detalle = self.client.get(reverse("escuela_dominical:detail", args=[self.clase.pk]))

        self.assertContains(listado, "Primarios A")
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, "Matricular alumno")
        self.assertNotContains(detalle, reverse("escuela_dominical:update", args=[self.clase.pk]))

    def test_maestro_asignado_crea_sesion_y_va_a_asistencia(self):
        self.client.force_login(self.maestro)

        response = self.client.post(
            reverse("escuela_dominical:sesion-create", args=[self.clase.pk]),
            {"fecha": "2026-02-01", "tema": "La fe", "observacion": ""},
        )

        sesion = SesionEscuelaDominical.objects.get(clase=self.clase, fecha=date(2026, 2, 1))
        self.assertRedirects(
            response,
            reverse("escuela_dominical:asistencia", args=[self.clase.pk, sesion.pk]),
        )
        self.assertEqual(sesion.registrado_por, self.maestro)

    def test_sesion_rechaza_fecha_fuera_del_periodo(self):
        self.client.force_login(self.maestro)

        response = self.client.post(
            reverse("escuela_dominical:sesion-create", args=[self.clase.pk]),
            {"fecha": "2027-01-01", "tema": "Fuera", "observacion": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("fecha", response.context["form"].errors)

    def test_asistencia_incluye_solo_matriculas_vigentes_en_la_fecha(self):
        matricula_futura = MatriculaEscuelaDominical.objects.create(
            clase=self.clase,
            alumno=self.otro_alumno,
            fecha_inscripcion=date(2026, 3, 1),
        )
        sesion = SesionEscuelaDominical.objects.create(
            clase=self.clase,
            fecha=date(2026, 2, 1),
            registrado_por=self.maestro,
        )
        self.client.force_login(self.maestro)

        response = self.client.get(
            reverse("escuela_dominical:asistencia", args=[self.clase.pk, sesion.pk])
        )

        self.assertContains(response, self.alumno.nombres)
        self.assertNotContains(response, matricula_futura.alumno.nombres)

    def test_guardar_asistencia_crea_un_registro_por_matricula(self):
        sesion = SesionEscuelaDominical.objects.create(
            clase=self.clase,
            fecha=date(2026, 2, 1),
            registrado_por=self.maestro,
        )
        self.client.force_login(self.maestro)

        response = self.client.post(
            reverse("escuela_dominical:asistencia", args=[self.clase.pk, sesion.pk]),
            {
                f"estado_{self.matricula.pk}": AsistenciaEscuelaDominical.Estado.JUSTIFICADO,
                f"observacion_{self.matricula.pk}": "Enfermedad",
                "cerrar_sesion": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("escuela_dominical:sesion-detail", args=[self.clase.pk, sesion.pk]),
        )
        asistencia = AsistenciaEscuelaDominical.objects.get(sesion=sesion)
        self.assertEqual(asistencia.matricula, self.matricula)
        self.assertEqual(asistencia.estado, AsistenciaEscuelaDominical.Estado.JUSTIFICADO)
        self.assertEqual(asistencia.observacion, "Enfermedad")
        sesion.refresh_from_db()
        self.assertTrue(sesion.cerrada)

    def test_maestro_no_corrige_sesion_cerrada_pero_pastor_si(self):
        sesion = SesionEscuelaDominical.objects.create(
            clase=self.clase,
            fecha=date(2026, 2, 1),
            registrado_por=self.maestro,
            cerrada=True,
        )
        self.client.force_login(self.maestro)

        respuesta_maestro = self.client.get(
            reverse("escuela_dominical:asistencia", args=[self.clase.pk, sesion.pk])
        )

        pastor = self.crear_usuario("pastor_corrige", Usuario.Rol.PASTOR_FILIAL, self.filial)
        self.client.force_login(pastor)
        respuesta_pastor = self.client.get(
            reverse("escuela_dominical:asistencia", args=[self.clase.pk, sesion.pk])
        )

        self.assertEqual(respuesta_maestro.status_code, 403)
        self.assertEqual(respuesta_pastor.status_code, 200)

    def test_sesion_de_otra_iglesia_no_es_accesible(self):
        sesion_otra = SesionEscuelaDominical.objects.create(
            clase=self.clase_otra,
            fecha=date(2026, 2, 1),
            registrado_por=self.maestro_otra,
        )
        self.client.force_login(self.maestro)

        response = self.client.get(
            reverse(
                "escuela_dominical:sesion-detail",
                args=[self.clase_otra.pk, sesion_otra.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.cargos.models import AsignacionCargo, Cargo
from apps.escuela_dominical.models import (
    ClaseEscuelaDominical,
    MatriculaEscuelaDominical,
    NivelEscuelaDominical,
    ProcesoPromocionEscuelaDominical,
    ResultadoPromocionEscuelaDominical,
)
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.parametros.models import ParametroGeneral, Periodo
from apps.usuarios.models import Usuario

from .models import CertificadoEscuelaDominical
from .servicios import anular_certificado, emitir_certificado


class CertificadosEscuelaDominicalTests(TestCase):
    def setUp(self):
        nacional = Iglesia.objects.create(
            codigo="NAC-CERT", nombre="Nacional", tipo=Iglesia.Tipo.NACIONAL
        )
        self.iglesia = Iglesia.objects.create(
            codigo="CERT",
            nombre="Iglesia Alianza Nueva Jerusalen",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=nacional,
        )
        self.otra = Iglesia.objects.create(
            codigo="OTRA-CERT",
            nombre="Otra filial",
            tipo=Iglesia.Tipo.FILIAL,
            iglesia_matriz=nacional,
        )
        origen = Periodo.objects.create(
            nombre="2026 certificados", fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31)
        )
        destino = Periodo.objects.create(
            nombre="2027 certificados", fecha_inicio=date(2027, 1, 1), fecha_fin=date(2027, 12, 31)
        )
        nivel_1 = NivelEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="1ro Nivel", edad_minima=1, edad_maxima=3, orden=1
        )
        nivel_2 = NivelEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="2do Nivel", edad_minima=4, edad_maxima=6, orden=2
        )
        clase_origen = ClaseEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="Nivel 1", nivel=nivel_1, periodo=origen
        )
        clase_destino = ClaseEscuelaDominical.objects.create(
            iglesia=self.iglesia, nombre="Nivel 2", nivel=nivel_2, periodo=destino
        )
        alumno = Miembro.objects.create(
            iglesia=self.iglesia,
            nombres="Nahomy",
            apellidos="Santacruz",
            sexo=Miembro.Sexo.FEMENINO,
            fecha_nacimiento=date(2023, 1, 1),
        )
        matricula_origen = MatriculaEscuelaDominical.objects.create(
            clase=clase_origen,
            alumno=alumno,
            fecha_inscripcion=date(2026, 1, 1),
            estado=MatriculaEscuelaDominical.Estado.PROMOVIDA,
            fecha_salida=date(2027, 1, 10),
        )
        matricula_destino = MatriculaEscuelaDominical.objects.create(
            clase=clase_destino, alumno=alumno, fecha_inscripcion=date(2027, 1, 10)
        )
        self.proceso = ProcesoPromocionEscuelaDominical.objects.create(
            iglesia=self.iglesia,
            periodo_origen=origen,
            periodo_destino=destino,
            fecha_corte=date(2027, 1, 10),
            estado=ProcesoPromocionEscuelaDominical.Estado.CONFIRMADO,
        )
        self.resultado = ResultadoPromocionEscuelaDominical.objects.create(
            proceso=self.proceso,
            matricula_origen=matricula_origen,
            edad_al_corte=4,
            destino=ResultadoPromocionEscuelaDominical.Destino.NIVEL_SIGUIENTE,
            nivel_destino=nivel_2,
            clase_destino=clase_destino,
            matricula_destino=matricula_destino,
        )
        self.secretario = Usuario.objects.create_user(
            username="secretario_cert",
            password="Cambiar12345!",
            rol=Usuario.Rol.SECRETARIO_FILIAL,
            iglesia=self.iglesia,
        )
        self.pastor_usuario = Usuario.objects.create_user(
            username="pastor_cert",
            password="Cambiar12345!",
            first_name="Roberto",
            last_name="Ramos",
            rol=Usuario.Rol.PASTOR_FILIAL,
            iglesia=self.iglesia,
        )
        director = Miembro.objects.create(
            iglesia=self.iglesia,
            nombres="Leonel",
            apellidos="Santacruz",
            sexo=Miembro.Sexo.MASCULINO,
        )
        cargo_pastor = Cargo.objects.create(nombre="Pastor")
        cargo_director = Cargo.objects.create(nombre="Director de Escuela Dominical")
        AsignacionCargo.objects.create(
            iglesia=self.iglesia,
            cargo=cargo_pastor,
            usuario=self.pastor_usuario,
            fecha_inicio=date(2026, 1, 1),
        )
        AsignacionCargo.objects.create(
            iglesia=self.iglesia,
            cargo=cargo_director,
            miembro=director,
            fecha_inicio=date(2026, 1, 1),
        )
        ParametroGeneral.objects.create(
            clave="CERTIFICADOS_PREFIJO", nombre="Prefijo", valor="EC"
        )
        ParametroGeneral.objects.create(
            clave="CERTIFICADOS_SECUENCIAL_INICIAL",
            nombre="Secuencial",
            valor="1",
            tipo_dato=ParametroGeneral.TipoDato.ENTERO,
        )

    def test_emision_congela_datos_y_reserva_numero(self):
        certificado = emitir_certificado(
            self.resultado, self.secretario, fecha_emision=date(2027, 1, 25)
        )

        self.assertEqual(certificado.numero, "EC-000001")
        self.assertEqual(certificado.nombre_alumno, "Nahomy Santacruz")
        self.assertEqual(certificado.nivel_cursado, "1ro Nivel")
        self.assertEqual(certificado.nombre_pastor, "Roberto Ramos")
        self.assertEqual(certificado.nombre_director, "Leonel Santacruz")
        self.assertEqual(
            ParametroGeneral.objects.get(clave="CERTIFICADOS_SECUENCIAL_INICIAL").valor,
            "2",
        )

    def test_emision_repetida_devuelve_el_mismo_certificado(self):
        primero = emitir_certificado(self.resultado, self.secretario)
        segundo = emitir_certificado(self.resultado, self.secretario)

        self.assertEqual(primero.pk, segundo.pk)
        self.assertEqual(CertificadoEscuelaDominical.objects.count(), 1)

    def test_no_emite_sin_director_vigente(self):
        AsignacionCargo.objects.filter(cargo__nombre="Director de Escuela Dominical").update(
            estado=AsignacionCargo.Estado.FINALIZADO, fecha_fin=date(2026, 12, 31)
        )

        with self.assertRaisesMessage(ValidationError, "Director de Escuela Dominical"):
            emitir_certificado(self.resultado, self.secretario, date(2027, 1, 25))

        self.assertEqual(CertificadoEscuelaDominical.objects.count(), 0)
        self.assertEqual(
            ParametroGeneral.objects.get(clave="CERTIFICADOS_SECUENCIAL_INICIAL").valor,
            "1",
        )

    def test_secretario_emite_y_pastor_consulta_pdf(self):
        self.client.force_login(self.secretario)
        response = self.client.post(reverse("certificados:emitir", args=[self.resultado.pk]))
        certificado = CertificadoEscuelaDominical.objects.get()
        self.assertRedirects(response, reverse("certificados:pdf", args=[certificado.pk]))

        self.client.force_login(self.pastor_usuario)
        pdf = self.client.get(reverse("certificados:pdf", args=[certificado.pk]))
        self.assertEqual(pdf.status_code, 200)
        self.assertEqual(pdf["Content-Type"], "application/pdf")
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_certificado_de_otra_iglesia_no_es_visible(self):
        certificado = emitir_certificado(self.resultado, self.secretario)
        usuario = Usuario.objects.create_user(
            username="pastor_otra_cert",
            password="Cambiar12345!",
            rol=Usuario.Rol.PASTOR_FILIAL,
            iglesia=self.otra,
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse("certificados:pdf", args=[certificado.pk]))

        self.assertEqual(response.status_code, 404)

    def test_anulacion_conserva_certificado_y_motivo(self):
        certificado = emitir_certificado(self.resultado, self.secretario)

        anular_certificado(certificado, self.secretario, "Error en el nombre impreso")

        certificado.refresh_from_db()
        self.assertEqual(certificado.estado, CertificadoEscuelaDominical.Estado.ANULADO)
        self.assertEqual(certificado.motivo_anulacion, "Error en el nombre impreso")
        self.assertEqual(CertificadoEscuelaDominical.objects.count(), 1)

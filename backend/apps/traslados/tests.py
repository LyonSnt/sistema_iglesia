from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.auditoria.models import RegistroAuditoria
from apps.cargos.models import AsignacionCargo, Cargo
from apps.documentos.models import DocumentoAdjunto
from apps.escuela_dominical.models import (
    ClaseEscuelaDominical,
    MatriculaEscuelaDominical,
    NivelEscuelaDominical,
)
from apps.familias.models import Familia, MiembroFamilia
from apps.iglesias.models import Iglesia
from apps.miembros.models import Miembro
from apps.ministerios.models import Ministerio, ParticipacionMinisterio
from apps.parametros.models import Periodo
from apps.traslados.models import TareaPastoralTraslado, TrasladoFamiliarIntegrante, TrasladoMiembro
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

    def test_destino_acepta_traslado_familiar_y_mueve_integrantes_adicionales(self):
        hijo = Miembro.objects.create(
            iglesia=self.origen,
            nombres="Luis",
            apellidos="Lopez",
            cedula="0606060606",
            sexo=Miembro.Sexo.MASCULINO,
        )
        vinculo_hijo = MiembroFamilia.objects.create(
            familia=self.familia,
            miembro=hijo,
            relacion=MiembroFamilia.Relacion.HIJO,
        )
        usuario_origen = self.crear_usuario("secretario_familiar", Usuario.Rol.SECRETARIO_FILIAL, self.origen)
        self.client.force_login(usuario_origen)

        response = self.client.post(
            reverse("traslados:create"),
            {
                "miembro": self.miembro.pk,
                "iglesia_destino": self.destino.pk,
                "es_familiar": "on",
                "familia_origen": self.familia.pk,
                "integrantes_familiares": [hijo.pk],
                "motivo": "Traslado familiar por cambio de domicilio",
            },
        )

        self.assertRedirects(response, reverse("traslados:list"))
        traslado = TrasladoMiembro.objects.get(motivo="Traslado familiar por cambio de domicilio")
        self.assertTrue(traslado.es_familiar)
        self.assertEqual(traslado.familia_origen, self.familia)
        integrante = TrasladoFamiliarIntegrante.objects.get(traslado=traslado)
        self.assertEqual(integrante.miembro, hijo)
        self.assertEqual(integrante.relacion, MiembroFamilia.Relacion.HIJO)

        usuario_destino = self.crear_usuario("pastor_destino_familiar", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        response = self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Familia recibida"})

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        self.miembro.refresh_from_db()
        hijo.refresh_from_db()
        self.vinculo_familiar.refresh_from_db()
        vinculo_hijo.refresh_from_db()
        self.assertEqual(self.miembro.iglesia, self.destino)
        self.assertEqual(hijo.iglesia, self.destino)
        self.assertFalse(self.vinculo_familiar.activo)
        self.assertFalse(vinculo_hijo.activo)
        auditoria = RegistroAuditoria.objects.get(modulo="traslados", accion="ACEPTAR")
        self.assertTrue(auditoria.valor_nuevo["traslado_familiar"])
        self.assertEqual(len(auditoria.valor_nuevo["integrantes_familiares_movidos"]), 1)

    def test_aceptar_traslado_cierra_asignaciones_locales_de_origen(self):
        cargo = Cargo.objects.create(nombre="Diacono")
        asignacion = AsignacionCargo.objects.create(
            iglesia=self.origen,
            cargo=cargo,
            miembro=self.miembro,
            fecha_inicio=date(2026, 1, 1),
        )
        ministerio = Ministerio.objects.create(
            iglesia=self.origen,
            nombre="Alabanza",
            responsable=self.miembro,
        )
        participacion = ParticipacionMinisterio.objects.create(
            ministerio=ministerio,
            miembro=self.miembro,
            cargo="Vocalista",
            fecha_inicio=date(2026, 1, 1),
        )
        periodo = Periodo.objects.create(
            nombre="2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )
        nivel = NivelEscuelaDominical.objects.create(
            iglesia=self.origen,
            nombre="Intermedios",
            edad_minima=10,
            edad_maxima=12,
        )
        clase = ClaseEscuelaDominical.objects.create(
            iglesia=self.origen,
            nombre="Intermedios A",
            nivel=nivel,
            periodo=periodo,
        )
        matricula = MatriculaEscuelaDominical.objects.create(
            clase=clase,
            alumno=self.miembro,
            fecha_inscripcion=date(2026, 1, 5),
        )
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_destino_integral", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)

        response = self.client.post(
            reverse("traslados:aceptar", args=[traslado.pk]),
            {"observacion": "Recibido con historial cerrado"},
        )

        fecha_cierre = timezone.localdate()
        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        self.familia.refresh_from_db()
        self.vinculo_familiar.refresh_from_db()
        asignacion.refresh_from_db()
        ministerio.refresh_from_db()
        participacion.refresh_from_db()
        matricula.refresh_from_db()
        self.assertFalse(self.familia.activo)
        self.assertFalse(self.vinculo_familiar.activo)
        self.assertEqual(asignacion.estado, AsignacionCargo.Estado.FINALIZADO)
        self.assertEqual(asignacion.fecha_fin, fecha_cierre)
        self.assertEqual(asignacion.observacion, "Cierre automatico por traslado aceptado.")
        self.assertIsNone(ministerio.responsable)
        self.assertEqual(participacion.estado, ParticipacionMinisterio.Estado.FINALIZADO)
        self.assertEqual(participacion.fecha_fin, fecha_cierre)
        self.assertFalse(participacion.activo)
        self.assertEqual(matricula.estado, MatriculaEscuelaDominical.Estado.RETIRADA)
        self.assertEqual(matricula.fecha_salida, fecha_cierre)
        self.assertFalse(matricula.activo)
        auditoria = RegistroAuditoria.objects.get(modulo="traslados", accion="ACEPTAR")
        self.assertEqual(auditoria.valor_nuevo["cierres_origen"]["asignaciones_cargos"], 1)
        self.assertEqual(auditoria.valor_nuevo["cierres_origen"]["participaciones_ministerios"], 1)
        self.assertEqual(auditoria.valor_nuevo["cierres_origen"]["matriculas_escuela_dominical"], 1)

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

    def test_destino_confirma_recepcion_pastoral_de_traslado_aceptado(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_recepcion", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})

        response = self.client.post(
            reverse("traslados:recepcion", args=[traslado.pk]),
            {"observacion_recepcion": "Visitado y presentado a la congregacion."},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.assertFalse(traslado.pendiente_recepcion)
        self.assertEqual(traslado.recepcion_confirmada_por, usuario_destino)
        self.assertIsNotNone(traslado.recepcion_confirmada_en)
        self.assertEqual(traslado.observacion_recepcion, "Visitado y presentado a la congregacion.")
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="traslados", accion="CONFIRMAR_RECEPCION").exists())
        self.assertEqual(traslado.tareas_pastorales.count(), 2)

    def test_recepcion_de_traslado_familiar_crea_tarea_pastoral_familiar(self):
        hijo = Miembro.objects.create(
            iglesia=self.origen,
            nombres="Mateo",
            apellidos="Lopez",
            cedula="0707070707",
            sexo=Miembro.Sexo.MASCULINO,
        )
        MiembroFamilia.objects.create(
            familia=self.familia,
            miembro=hijo,
            relacion=MiembroFamilia.Relacion.HIJO,
        )
        traslado = self.crear_traslado()
        traslado.es_familiar = True
        traslado.familia_origen = self.familia
        traslado.save(update_fields=["es_familiar", "familia_origen"])
        TrasladoFamiliarIntegrante.objects.create(
            traslado=traslado,
            miembro=hijo,
            relacion=MiembroFamilia.Relacion.HIJO,
        )
        usuario_destino = self.crear_usuario("pastor_tareas_familia", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})

        response = self.client.post(
            reverse("traslados:recepcion", args=[traslado.pk]),
            {"observacion_recepcion": "Familia recibida"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.assertEqual(traslado.tareas_pastorales.count(), 3)
        self.assertTrue(
            traslado.tareas_pastorales.filter(
                descripcion="Revisar integracion pastoral de la familia trasladada."
            ).exists()
        )

    def test_destino_crea_y_completa_tarea_pastoral_de_traslado(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_tareas", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado.pk]), {"observacion_recepcion": "Recibido"})

        response = self.client.post(
            reverse("traslados:tarea-create", args=[traslado.pk]),
            {"descripcion": "Coordinar visita de seguimiento"},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        tarea = TareaPastoralTraslado.objects.get(descripcion="Coordinar visita de seguimiento")
        self.assertEqual(tarea.traslado, traslado)
        self.assertEqual(tarea.creada_por, usuario_destino)
        self.assertTrue(RegistroAuditoria.objects.filter(modulo="traslados", accion="CREAR_TAREA_PASTORAL").exists())

        response = self.client.post(
            reverse("traslados:tarea-completar", args=[traslado.pk, tarea.pk]),
            {"observacion": "Visita realizada."},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        tarea.refresh_from_db()
        self.assertEqual(tarea.estado, TareaPastoralTraslado.Estado.COMPLETADA)
        self.assertEqual(tarea.completada_por, usuario_destino)
        self.assertEqual(tarea.observacion, "Visita realizada.")
        self.assertTrue(
            RegistroAuditoria.objects.filter(modulo="traslados", accion="COMPLETAR_TAREA_PASTORAL").exists()
        )

    def test_origen_no_completa_tarea_pastoral_en_destino(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_destino_tarea", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado.pk]), {"observacion_recepcion": "Recibido"})
        tarea = traslado.tareas_pastorales.first()

        usuario_origen = self.crear_usuario("pastor_origen_tarea", Usuario.Rol.PASTOR_FILIAL, self.origen)
        self.client.force_login(usuario_origen)
        response = self.client.post(
            reverse("traslados:tarea-completar", args=[traslado.pk, tarea.pk]),
            {"observacion": "No corresponde"},
        )

        self.assertEqual(response.status_code, 403)
        tarea.refresh_from_db()
        self.assertEqual(tarea.estado, TareaPastoralTraslado.Estado.PENDIENTE)

    def test_no_confirma_recepcion_si_traslado_no_esta_aceptado(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_recepcion_pendiente", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)

        response = self.client.post(
            reverse("traslados:recepcion", args=[traslado.pk]),
            {"observacion_recepcion": "Intento anticipado"},
        )

        self.assertEqual(response.status_code, 403)
        traslado.refresh_from_db()
        self.assertIsNone(traslado.recepcion_confirmada_en)

    def test_origen_no_confirma_recepcion_en_destino(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_destino_recepcion", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})

        usuario_origen = self.crear_usuario("pastor_origen_recepcion", Usuario.Rol.PASTOR_FILIAL, self.origen)
        self.client.force_login(usuario_origen)
        response = self.client.post(
            reverse("traslados:recepcion", args=[traslado.pk]),
            {"observacion_recepcion": "No corresponde"},
        )

        self.assertEqual(response.status_code, 403)
        traslado.refresh_from_db()
        self.assertIsNone(traslado.recepcion_confirmada_en)

    def test_listado_filtra_recepciones_pendientes(self):
        traslado_pendiente = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_destino_filtro", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado_pendiente.pk]), {"observacion": "Aceptado"})

        otro_miembro = Miembro.objects.create(
            iglesia=self.origen,
            nombres="Beatriz",
            apellidos="Santos",
            cedula="0303030303",
            sexo=Miembro.Sexo.FEMENINO,
        )
        traslado_confirmado = TrasladoMiembro.objects.create(
            miembro=otro_miembro,
            iglesia_origen=self.origen,
            iglesia_destino=self.destino,
            motivo="Cambio de domicilio",
            solicitado_por=self.crear_usuario("solicitante_confirmado", Usuario.Rol.SECRETARIO_FILIAL, self.origen),
        )
        self.client.post(reverse("traslados:aceptar", args=[traslado_confirmado.pk]), {"observacion": "Aceptado"})
        self.client.post(
            reverse("traslados:recepcion", args=[traslado_confirmado.pk]),
            {"observacion_recepcion": "Integrada"},
        )

        response = self.client.get(reverse("traslados:list"), {"recepcion": "pendiente"})

        self.assertContains(response, traslado_pendiente.miembro.nombres)
        self.assertNotContains(response, traslado_confirmado.miembro.nombres)

    def test_destino_revisa_integracion_familiar_pendiente(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_integracion_familia", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado.pk]), {"observacion_recepcion": "Recibido"})

        traslado.refresh_from_db()
        self.assertTrue(traslado.integracion_familiar_pendiente)

        response = self.client.post(
            reverse("traslados:integracion-familia", args=[traslado.pk]),
            {"observacion": "Se revisara vinculacion familiar en visita pastoral."},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.assertFalse(traslado.integracion_familiar_pendiente)
        self.assertEqual(traslado.familia_destino_revisada_por, usuario_destino)
        self.assertIsNotNone(traslado.familia_destino_revisada_en)
        self.assertEqual(
            traslado.observacion_familia_destino,
            "Se revisara vinculacion familiar en visita pastoral.",
        )
        self.assertTrue(
            RegistroAuditoria.objects.filter(modulo="traslados", accion="REVISAR_INTEGRACION_FAMILIAR").exists()
        )

    def test_destino_vincula_familia_desde_integracion_de_traslado(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_vincula_familia", Usuario.Rol.PASTOR_FILIAL, self.destino)
        jefe_destino = Miembro.objects.create(
            iglesia=self.destino,
            nombres="Julia",
            apellidos="Perez",
            cedula="0505050505",
            sexo=Miembro.Sexo.FEMENINO,
        )
        familia_destino = Familia.objects.create(
            iglesia=self.destino,
            nombre="Familia Perez",
            jefe_hogar=jefe_destino,
        )
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado.pk]), {"observacion_recepcion": "Recibido"})

        response = self.client.post(
            reverse("traslados:vincular-familia", args=[traslado.pk]),
            {
                "familia": familia_destino.pk,
                "relacion": MiembroFamilia.Relacion.OTRO,
                "observacion": "Integrado a familia cercana.",
            },
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        vinculo = MiembroFamilia.objects.get(
            familia=familia_destino,
            miembro=self.miembro,
            relacion=MiembroFamilia.Relacion.OTRO,
        )
        self.assertTrue(vinculo.activo)
        self.assertFalse(traslado.integracion_familiar_pendiente)
        self.assertEqual(traslado.familia_destino_revisada_por, usuario_destino)
        self.assertEqual(traslado.observacion_familia_destino, "Integrado a familia cercana.")
        self.assertTrue(
            RegistroAuditoria.objects.filter(modulo="traslados", accion="VINCULAR_FAMILIA_DESTINO").exists()
        )

    def test_destino_revisa_escuela_dominical_pendiente_para_menor(self):
        self.miembro.fecha_nacimiento = date(2014, 5, 10)
        self.miembro.save(update_fields=["fecha_nacimiento"])
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_integracion_escuela", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado.pk]), {"observacion_recepcion": "Recibido"})

        traslado.refresh_from_db()
        self.assertTrue(traslado.revision_escuela_dominical_pendiente)

        response = self.client.post(
            reverse("traslados:integracion-escuela", args=[traslado.pk]),
            {"observacion": "Debe matricularse en una clase del periodo actual."},
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        self.assertFalse(traslado.revision_escuela_dominical_pendiente)
        self.assertEqual(traslado.escuela_dominical_destino_revisada_por, usuario_destino)
        self.assertIsNotNone(traslado.escuela_dominical_destino_revisada_en)
        self.assertEqual(
            traslado.observacion_escuela_dominical_destino,
            "Debe matricularse en una clase del periodo actual.",
        )
        self.assertTrue(
            RegistroAuditoria.objects.filter(modulo="traslados", accion="REVISAR_INTEGRACION_ESCUELA").exists()
        )

    def test_destino_matricula_escuela_desde_integracion_de_traslado(self):
        self.miembro.fecha_nacimiento = date(2014, 5, 10)
        self.miembro.save(update_fields=["fecha_nacimiento"])
        periodo = Periodo.objects.create(
            nombre="2026 destino",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
        )
        nivel = NivelEscuelaDominical.objects.create(
            iglesia=self.destino,
            nombre="Intermedios destino",
            edad_minima=10,
            edad_maxima=12,
        )
        clase = ClaseEscuelaDominical.objects.create(
            iglesia=self.destino,
            nombre="Intermedios destino A",
            nivel=nivel,
            periodo=periodo,
        )
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_matricula_escuela", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado.pk]), {"observacion_recepcion": "Recibido"})

        response = self.client.post(
            reverse("traslados:matricular-escuela", args=[traslado.pk]),
            {
                "clase": clase.pk,
                "fecha_inscripcion": "2026-02-01",
                "observacion": "Matricula por traslado aceptado.",
            },
        )

        self.assertRedirects(response, reverse("traslados:detail", args=[traslado.pk]))
        traslado.refresh_from_db()
        matricula = MatriculaEscuelaDominical.objects.get(clase=clase, alumno=self.miembro)
        self.assertTrue(matricula.activo)
        self.assertEqual(matricula.estado, MatriculaEscuelaDominical.Estado.ACTIVA)
        self.assertEqual(matricula.fecha_inscripcion, date(2026, 2, 1))
        self.assertFalse(traslado.revision_escuela_dominical_pendiente)
        self.assertEqual(traslado.escuela_dominical_destino_revisada_por, usuario_destino)
        self.assertEqual(traslado.observacion_escuela_dominical_destino, "Matricula por traslado aceptado.")
        self.assertTrue(
            RegistroAuditoria.objects.filter(modulo="traslados", accion="MATRICULAR_ESCUELA_DESTINO").exists()
        )

    def test_origen_no_revisa_integracion_en_destino(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_destino_integracion", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado.pk]), {"observacion_recepcion": "Recibido"})

        usuario_origen = self.crear_usuario("pastor_origen_integracion", Usuario.Rol.PASTOR_FILIAL, self.origen)
        self.client.force_login(usuario_origen)
        response = self.client.post(
            reverse("traslados:integracion-familia", args=[traslado.pk]),
            {"observacion": "No corresponde"},
        )

        self.assertEqual(response.status_code, 403)
        traslado.refresh_from_db()
        self.assertIsNone(traslado.familia_destino_revisada_en)

    def test_listado_filtra_integraciones_pendientes(self):
        traslado_pendiente = self.crear_traslado()
        usuario_destino = self.crear_usuario("pastor_destino_integracion_filtro", Usuario.Rol.PASTOR_FILIAL, self.destino)
        self.client.force_login(usuario_destino)
        self.client.post(reverse("traslados:aceptar", args=[traslado_pendiente.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado_pendiente.pk]), {"observacion_recepcion": "Recibido"})

        otro_miembro = Miembro.objects.create(
            iglesia=self.origen,
            nombres="Diana",
            apellidos="Rios",
            cedula="0404040404",
            sexo=Miembro.Sexo.FEMENINO,
        )
        traslado_revisado = TrasladoMiembro.objects.create(
            miembro=otro_miembro,
            iglesia_origen=self.origen,
            iglesia_destino=self.destino,
            motivo="Cambio de domicilio",
            solicitado_por=self.crear_usuario("solicitante_revisado", Usuario.Rol.SECRETARIO_FILIAL, self.origen),
        )
        self.client.post(reverse("traslados:aceptar", args=[traslado_revisado.pk]), {"observacion": "Aceptado"})
        self.client.post(reverse("traslados:recepcion", args=[traslado_revisado.pk]), {"observacion_recepcion": "Recibido"})
        self.client.post(
            reverse("traslados:integracion-familia", args=[traslado_revisado.pk]),
            {"observacion": "Revision completa"},
        )

        response = self.client.get(reverse("traslados:list"), {"recepcion": "integracion_pendiente"})

        self.assertContains(response, traslado_pendiente.miembro.nombres)
        self.assertNotContains(response, traslado_revisado.miembro.nombres)

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

    def test_rechaza_tipo_documento_no_permitido_para_traslado(self):
        traslado = self.crear_traslado()
        usuario_destino = self.crear_usuario("secretario_destino_doc", Usuario.Rol.SECRETARIO_FILIAL, self.destino)
        self.client.force_login(usuario_destino)

        response = self.client.post(
            reverse("traslados:document-create", args=[traslado.pk]),
            {
                "archivo": SimpleUploadedFile("garantia.pdf", b"%PDF-1.4", content_type="application/pdf"),
                "nombre": "Garantia incorrecta",
                "tipo": DocumentoAdjunto.Tipo.GARANTIA,
                "descripcion": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(DocumentoAdjunto.objects.filter(nombre="Garantia incorrecta").exists())

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

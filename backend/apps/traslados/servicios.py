from django.db import transaction
from django.utils import timezone

from apps.auditoria.models import RegistroAuditoria
from apps.cargos.models import AsignacionCargo
from apps.escuela_dominical.models import MatriculaEscuelaDominical
from apps.familias.models import Familia, MiembroFamilia
from apps.miembros.models import Miembro
from apps.ministerios.models import Ministerio, ParticipacionMinisterio

from .models import TrasladoMiembro


MOTIVO_CIERRE_TRASLADO = "Cierre automatico por traslado aceptado."


def _registrar_auditoria(traslado, usuario, accion, motivo, valor_anterior=None, valor_nuevo=None, iglesia=None):
    RegistroAuditoria.objects.create(
        usuario=usuario,
        accion=accion,
        modulo="traslados",
        registro_afectado=f"traslados.TrasladoMiembro:{traslado.pk}",
        valor_anterior=valor_anterior,
        valor_nuevo=valor_nuevo,
        iglesia=iglesia or traslado.iglesia_destino,
        motivo=motivo,
    )


@transaction.atomic
def aceptar_traslado(traslado, usuario, observacion=""):
    traslado = TrasladoMiembro.objects.select_for_update().select_related(
        "miembro",
        "iglesia_origen",
        "iglesia_destino",
    ).get(pk=traslado.pk)
    if not traslado.pendiente:
        return traslado

    miembro = Miembro.objects.select_for_update().get(pk=traslado.miembro_id)
    iglesia_origen_id = miembro.iglesia_id
    fecha_cierre = timezone.localdate()

    resumen_cierre = _cerrar_relaciones_origen(miembro, iglesia_origen_id, fecha_cierre)

    miembro.iglesia = traslado.iglesia_destino
    miembro.estado = Miembro.Estado.ACTIVO
    miembro.save(update_fields=["iglesia", "estado", "actualizado_en"])

    ahora = timezone.now()
    traslado.estado = TrasladoMiembro.Estado.ACEPTADO
    traslado.respondido_por = usuario
    traslado.respondido_en = ahora
    traslado.completado_en = ahora
    traslado.observacion_respuesta = observacion
    traslado.save(
        update_fields=[
            "estado",
            "respondido_por",
            "respondido_en",
            "completado_en",
            "observacion_respuesta",
            "actualizado_en",
        ]
    )

    _registrar_auditoria(
        traslado=traslado,
        usuario=usuario,
        accion="ACEPTAR",
        valor_anterior={"miembro_id": miembro.pk, "iglesia_id": iglesia_origen_id},
        valor_nuevo={
            "miembro_id": miembro.pk,
            "iglesia_id": traslado.iglesia_destino_id,
            "cierres_origen": resumen_cierre,
        },
        motivo="Traslado de miembro aceptado por iglesia destino.",
    )
    return traslado


@transaction.atomic
def vincular_familia_destino(traslado, usuario, familia, relacion, observacion=""):
    traslado = TrasladoMiembro.objects.select_for_update().select_related(
        "miembro",
        "iglesia_destino",
    ).get(pk=traslado.pk)
    if not traslado.integracion_familiar_pendiente or familia.iglesia_id != traslado.iglesia_destino_id:
        return traslado

    vinculo, _ = MiembroFamilia.objects.get_or_create(
        familia=familia,
        miembro=traslado.miembro,
        relacion=relacion,
    )
    if not vinculo.activo:
        vinculo.activo = True
        vinculo.save(update_fields=["activo", "actualizado_en"])

    ahora = timezone.now()
    traslado.familia_destino_revisada_por = usuario
    traslado.familia_destino_revisada_en = ahora
    traslado.observacion_familia_destino = observacion
    traslado.save(
        update_fields=[
            "familia_destino_revisada_por",
            "familia_destino_revisada_en",
            "observacion_familia_destino",
            "actualizado_en",
        ]
    )
    _registrar_auditoria(
        traslado=traslado,
        usuario=usuario,
        accion="VINCULAR_FAMILIA_DESTINO",
        valor_anterior={"familia_destino_revisada_en": None},
        valor_nuevo={
            "miembro_id": traslado.miembro_id,
            "familia_id": familia.pk,
            "relacion": relacion,
            "iglesia_destino_id": traslado.iglesia_destino_id,
        },
        iglesia=traslado.iglesia_destino,
        motivo="Miembro vinculado a familia en destino desde traslado.",
    )
    return traslado


@transaction.atomic
def matricular_escuela_destino(traslado, usuario, clase, fecha_inscripcion, observacion=""):
    traslado = TrasladoMiembro.objects.select_for_update().select_related(
        "miembro",
        "iglesia_destino",
    ).get(pk=traslado.pk)
    if not traslado.revision_escuela_dominical_pendiente or clase.iglesia_id != traslado.iglesia_destino_id:
        return traslado

    matricula, created = MatriculaEscuelaDominical.objects.get_or_create(
        clase=clase,
        alumno=traslado.miembro,
        defaults={
            "fecha_inscripcion": fecha_inscripcion,
            "observacion": observacion,
        },
    )
    if not created:
        matricula.fecha_inscripcion = fecha_inscripcion
        matricula.fecha_salida = None
        matricula.estado = MatriculaEscuelaDominical.Estado.ACTIVA
        matricula.observacion = observacion
        matricula.activo = True
        matricula.full_clean()
        matricula.save(
            update_fields=[
                "fecha_inscripcion",
                "fecha_salida",
                "estado",
                "observacion",
                "activo",
                "actualizado_en",
            ]
        )

    ahora = timezone.now()
    traslado.escuela_dominical_destino_revisada_por = usuario
    traslado.escuela_dominical_destino_revisada_en = ahora
    traslado.observacion_escuela_dominical_destino = observacion
    traslado.save(
        update_fields=[
            "escuela_dominical_destino_revisada_por",
            "escuela_dominical_destino_revisada_en",
            "observacion_escuela_dominical_destino",
            "actualizado_en",
        ]
    )
    _registrar_auditoria(
        traslado=traslado,
        usuario=usuario,
        accion="MATRICULAR_ESCUELA_DESTINO",
        valor_anterior={"escuela_dominical_destino_revisada_en": None},
        valor_nuevo={
            "miembro_id": traslado.miembro_id,
            "clase_id": clase.pk,
            "fecha_inscripcion": fecha_inscripcion.isoformat(),
            "iglesia_destino_id": traslado.iglesia_destino_id,
        },
        iglesia=traslado.iglesia_destino,
        motivo="Miembro matriculado en Escuela Dominical desde traslado.",
    )
    return traslado


def _cerrar_relaciones_origen(miembro, iglesia_origen_id, fecha_cierre):
    ahora = timezone.now()
    vinculos_familiares = MiembroFamilia.objects.filter(
        miembro=miembro,
        activo=True,
        familia__iglesia_id=iglesia_origen_id,
    ).update(activo=False, actualizado_en=ahora)

    familias_jefatura = Familia.objects.filter(
        iglesia_id=iglesia_origen_id,
        jefe_hogar=miembro,
        activo=True,
    ).update(activo=False, actualizado_en=ahora)

    asignaciones_cargos = AsignacionCargo.objects.filter(
        iglesia_id=iglesia_origen_id,
        miembro=miembro,
        estado=AsignacionCargo.Estado.VIGENTE,
    ).update(
        estado=AsignacionCargo.Estado.FINALIZADO,
        fecha_fin=fecha_cierre,
        observacion=MOTIVO_CIERRE_TRASLADO,
        actualizado_en=ahora,
    )

    participaciones = ParticipacionMinisterio.objects.filter(
        ministerio__iglesia_id=iglesia_origen_id,
        miembro=miembro,
        estado=ParticipacionMinisterio.Estado.ACTIVO,
        activo=True,
    ).update(
        estado=ParticipacionMinisterio.Estado.FINALIZADO,
        fecha_fin=fecha_cierre,
        motivo_salida=MOTIVO_CIERRE_TRASLADO,
        activo=False,
        actualizado_en=ahora,
    )

    matriculas = MatriculaEscuelaDominical.objects.filter(
        clase__iglesia_id=iglesia_origen_id,
        alumno=miembro,
        estado=MatriculaEscuelaDominical.Estado.ACTIVA,
        activo=True,
    ).update(
        estado=MatriculaEscuelaDominical.Estado.RETIRADA,
        fecha_salida=fecha_cierre,
        observacion=MOTIVO_CIERRE_TRASLADO,
        activo=False,
        actualizado_en=ahora,
    )

    ministerios_responsable = Ministerio.objects.filter(
        iglesia_id=iglesia_origen_id,
        responsable=miembro,
    ).update(responsable=None, actualizado_en=ahora)

    return {
        "vinculos_familiares": vinculos_familiares,
        "familias_jefatura": familias_jefatura,
        "asignaciones_cargos": asignaciones_cargos,
        "participaciones_ministerios": participaciones,
        "matriculas_escuela_dominical": matriculas,
        "ministerios_responsable": ministerios_responsable,
    }


@transaction.atomic
def rechazar_traslado(traslado, usuario, observacion=""):
    traslado = TrasladoMiembro.objects.select_for_update().get(pk=traslado.pk)
    if not traslado.pendiente:
        return traslado

    traslado.estado = TrasladoMiembro.Estado.RECHAZADO
    traslado.respondido_por = usuario
    traslado.respondido_en = timezone.now()
    traslado.observacion_respuesta = observacion
    traslado.save(
        update_fields=[
            "estado",
            "respondido_por",
            "respondido_en",
            "observacion_respuesta",
            "actualizado_en",
        ]
    )
    _registrar_auditoria(
        traslado=traslado,
        usuario=usuario,
        accion="RECHAZAR",
        valor_anterior={"estado": TrasladoMiembro.Estado.SOLICITADO},
        valor_nuevo={"estado": TrasladoMiembro.Estado.RECHAZADO},
        motivo="Traslado de miembro rechazado por iglesia destino.",
    )
    return traslado


@transaction.atomic
def anular_traslado(traslado, usuario, observacion=""):
    traslado = TrasladoMiembro.objects.select_for_update().get(pk=traslado.pk)
    if not traslado.pendiente:
        return traslado

    traslado.estado = TrasladoMiembro.Estado.ANULADO
    traslado.respondido_por = usuario
    traslado.respondido_en = timezone.now()
    traslado.observacion_respuesta = observacion
    traslado.save(
        update_fields=[
            "estado",
            "respondido_por",
            "respondido_en",
            "observacion_respuesta",
            "actualizado_en",
        ]
    )
    _registrar_auditoria(
        traslado=traslado,
        usuario=usuario,
        accion="ANULAR",
        valor_anterior={"estado": TrasladoMiembro.Estado.SOLICITADO},
        valor_nuevo={"estado": TrasladoMiembro.Estado.ANULADO},
        iglesia=traslado.iglesia_origen,
        motivo="Traslado de miembro anulado por iglesia origen.",
    )
    return traslado


@transaction.atomic
def confirmar_recepcion_traslado(traslado, usuario, observacion_recepcion=""):
    traslado = TrasladoMiembro.objects.select_for_update().select_related(
        "miembro",
        "iglesia_destino",
    ).get(pk=traslado.pk)
    if not traslado.pendiente_recepcion:
        return traslado

    ahora = timezone.now()
    traslado.recepcion_confirmada_por = usuario
    traslado.recepcion_confirmada_en = ahora
    traslado.observacion_recepcion = observacion_recepcion
    traslado.save(
        update_fields=[
            "recepcion_confirmada_por",
            "recepcion_confirmada_en",
            "observacion_recepcion",
            "actualizado_en",
        ]
    )
    _registrar_auditoria(
        traslado=traslado,
        usuario=usuario,
        accion="CONFIRMAR_RECEPCION",
        valor_anterior={"recepcion_confirmada_en": None},
        valor_nuevo={
            "miembro_id": traslado.miembro_id,
            "iglesia_destino_id": traslado.iglesia_destino_id,
            "recepcion_confirmada_en": ahora.isoformat(),
        },
        iglesia=traslado.iglesia_destino,
        motivo="Recepcion pastoral confirmada por iglesia destino.",
    )
    return traslado


@transaction.atomic
def confirmar_revision_integracion_destino(traslado, usuario, tipo, observacion=""):
    traslado = TrasladoMiembro.objects.select_for_update().select_related(
        "miembro",
        "iglesia_destino",
    ).get(pk=traslado.pk)

    ahora = timezone.now()
    if tipo == "familia" and traslado.integracion_familiar_pendiente:
        traslado.familia_destino_revisada_por = usuario
        traslado.familia_destino_revisada_en = ahora
        traslado.observacion_familia_destino = observacion
        update_fields = [
            "familia_destino_revisada_por",
            "familia_destino_revisada_en",
            "observacion_familia_destino",
            "actualizado_en",
        ]
        accion = "REVISAR_INTEGRACION_FAMILIAR"
        motivo = "Revision familiar en destino confirmada."
    elif tipo == "escuela" and traslado.revision_escuela_dominical_pendiente:
        traslado.escuela_dominical_destino_revisada_por = usuario
        traslado.escuela_dominical_destino_revisada_en = ahora
        traslado.observacion_escuela_dominical_destino = observacion
        update_fields = [
            "escuela_dominical_destino_revisada_por",
            "escuela_dominical_destino_revisada_en",
            "observacion_escuela_dominical_destino",
            "actualizado_en",
        ]
        accion = "REVISAR_INTEGRACION_ESCUELA"
        motivo = "Revision de Escuela Dominical en destino confirmada."
    else:
        return traslado

    traslado.save(update_fields=update_fields)
    _registrar_auditoria(
        traslado=traslado,
        usuario=usuario,
        accion=accion,
        valor_anterior={"revision_confirmada_en": None},
        valor_nuevo={
            "miembro_id": traslado.miembro_id,
            "iglesia_destino_id": traslado.iglesia_destino_id,
            "tipo": tipo,
            "revision_confirmada_en": ahora.isoformat(),
        },
        iglesia=traslado.iglesia_destino,
        motivo=motivo,
    )
    return traslado

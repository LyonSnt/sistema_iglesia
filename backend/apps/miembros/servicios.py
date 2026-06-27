from django.db import transaction
from django.utils import timezone

from apps.auditoria.models import RegistroAuditoria
from apps.cargos.models import AsignacionCargo
from apps.escuela_dominical.models import MatriculaEscuelaDominical
from apps.familias.models import Familia, MiembroFamilia
from apps.ministerios.models import Ministerio, ParticipacionMinisterio

from .models import HistorialPastoralMiembro, Miembro


MOTIVO_CIERRE_FALLECIMIENTO = "Cierre automatico por fallecimiento."


@transaction.atomic
def registrar_accion_pastoral(miembro, usuario, tipo, fecha, motivo):
    miembro = Miembro.objects.select_for_update().get(pk=miembro.pk)
    estado_anterior = miembro.estado
    activo_anterior = miembro.activo
    resumen_cierre = None

    if tipo == HistorialPastoralMiembro.Tipo.BAUTISMO:
        miembro.fecha_bautismo = fecha
    elif tipo == HistorialPastoralMiembro.Tipo.ADMISION:
        miembro.fecha_membresia = fecha
        miembro.estado = Miembro.Estado.ACTIVO
        miembro.activo = True
    elif tipo == HistorialPastoralMiembro.Tipo.BAJA_VOLUNTARIA:
        miembro.estado = Miembro.Estado.INACTIVO
        miembro.activo = False
    elif tipo == HistorialPastoralMiembro.Tipo.RESTAURACION:
        miembro.estado = Miembro.Estado.ACTIVO
        miembro.activo = True
    elif tipo == HistorialPastoralMiembro.Tipo.DISCIPLINA:
        miembro.estado = Miembro.Estado.DISCIPLINA
        miembro.activo = True
    elif tipo == HistorialPastoralMiembro.Tipo.SUSPENSION:
        miembro.estado = Miembro.Estado.SUSPENDIDO
        miembro.activo = False
    elif tipo == HistorialPastoralMiembro.Tipo.FALLECIMIENTO:
        miembro.fecha_fallecimiento = fecha
        miembro.estado = Miembro.Estado.FALLECIDO
        miembro.activo = False
        resumen_cierre = cerrar_relaciones_por_fallecimiento(miembro, fecha)

    miembro.save()
    historial = HistorialPastoralMiembro.objects.create(
        miembro=miembro,
        tipo=tipo,
        fecha=fecha,
        motivo=motivo,
        registrado_por=usuario,
        estado_anterior=estado_anterior,
        estado_nuevo=miembro.estado,
        activo_anterior=activo_anterior,
        activo_nuevo=miembro.activo,
        resumen_cierre=resumen_cierre,
    )
    RegistroAuditoria.objects.create(
        usuario=usuario,
        accion=tipo,
        modulo="miembros",
        registro_afectado=f"miembros.Miembro:{miembro.pk}",
        valor_anterior={"estado": estado_anterior, "activo": activo_anterior},
        valor_nuevo={
            "estado": miembro.estado,
            "activo": miembro.activo,
            "fecha": fecha.isoformat(),
            "historial_id": historial.pk,
            "resumen_cierre": resumen_cierre,
        },
        iglesia=miembro.iglesia,
        motivo=motivo,
    )
    return historial


def cerrar_relaciones_por_fallecimiento(miembro, fecha_cierre):
    ahora = timezone.now()
    vinculos_familiares = MiembroFamilia.objects.filter(
        miembro=miembro,
        activo=True,
        familia__iglesia=miembro.iglesia,
    ).update(activo=False, actualizado_en=ahora)

    familias_jefatura = Familia.objects.filter(
        iglesia=miembro.iglesia,
        jefe_hogar=miembro,
        activo=True,
    ).update(activo=False, actualizado_en=ahora)

    asignaciones_cargos = AsignacionCargo.objects.filter(
        iglesia=miembro.iglesia,
        miembro=miembro,
        estado=AsignacionCargo.Estado.VIGENTE,
    ).update(
        estado=AsignacionCargo.Estado.FINALIZADO,
        fecha_fin=fecha_cierre,
        observacion=MOTIVO_CIERRE_FALLECIMIENTO,
        actualizado_en=ahora,
    )

    participaciones = ParticipacionMinisterio.objects.filter(
        ministerio__iglesia=miembro.iglesia,
        miembro=miembro,
        estado=ParticipacionMinisterio.Estado.ACTIVO,
        activo=True,
    ).update(
        estado=ParticipacionMinisterio.Estado.FINALIZADO,
        fecha_fin=fecha_cierre,
        motivo_salida=MOTIVO_CIERRE_FALLECIMIENTO,
        activo=False,
        actualizado_en=ahora,
    )

    matriculas = MatriculaEscuelaDominical.objects.filter(
        clase__iglesia=miembro.iglesia,
        alumno=miembro,
        estado=MatriculaEscuelaDominical.Estado.ACTIVA,
        activo=True,
    ).update(
        estado=MatriculaEscuelaDominical.Estado.RETIRADA,
        fecha_salida=fecha_cierre,
        observacion=MOTIVO_CIERRE_FALLECIMIENTO,
        activo=False,
        actualizado_en=ahora,
    )

    ministerios_responsable = Ministerio.objects.filter(
        iglesia=miembro.iglesia,
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

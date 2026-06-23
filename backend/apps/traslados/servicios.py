from django.db import transaction
from django.utils import timezone

from apps.auditoria.models import RegistroAuditoria
from apps.familias.models import MiembroFamilia
from apps.miembros.models import Miembro

from .models import TrasladoMiembro


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

    MiembroFamilia.objects.filter(
        miembro=miembro,
        activo=True,
        familia__iglesia_id=iglesia_origen_id,
    ).update(activo=False)

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
        valor_nuevo={"miembro_id": miembro.pk, "iglesia_id": traslado.iglesia_destino_id},
        motivo="Traslado de miembro aceptado por iglesia destino.",
    )
    return traslado


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

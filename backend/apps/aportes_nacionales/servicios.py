from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.parametros.models import ParametroGeneral

from .models import AcuerdoPagoAporteNacional, AjusteAporteNacional, AporteNacional, PagoAporteNacional


def _reservar_numero_recibo():
    try:
        prefijo = ParametroGeneral.objects.get(clave="APORTES_RECIBOS_PREFIJO", activo=True).valor.strip()
        secuencial = ParametroGeneral.objects.select_for_update().get(
            clave="APORTES_RECIBOS_SECUENCIAL_INICIAL", activo=True
        )
        valor = int(secuencial.valor)
    except ParametroGeneral.DoesNotExist as exc:
        raise ValidationError("Falta configurar la numeracion de recibos de aportes.") from exc
    except ValueError as exc:
        raise ValidationError("El secuencial de recibos de aportes no es un numero valido.") from exc
    secuencial.valor = str(valor + 1)
    secuencial.save(update_fields=["valor", "actualizado_en"])
    return f"{prefijo}-{valor:06d}"


@transaction.atomic
def registrar_pago_aporte(aporte, usuario, fecha_pago, referencia_pago, observacion="", monto=None):
    aporte = AporteNacional.objects.select_for_update().get(pk=aporte.pk)
    if aporte.estado == AporteNacional.Estado.PAGADO:
        return aporte
    if aporte.estado != AporteNacional.Estado.PENDIENTE:
        raise ValidationError("Solo se pueden pagar aportes pendientes.")
    saldo = aporte.saldo_pendiente
    monto_pago = monto or saldo
    if monto_pago <= 0:
        raise ValidationError("El monto del pago debe ser mayor a cero.")
    if monto_pago > saldo:
        raise ValidationError("El monto del pago no puede superar el saldo pendiente.")

    pago = PagoAporteNacional(
        iglesia=aporte.iglesia,
        aporte=aporte,
        monto=monto_pago,
        fecha_pago=fecha_pago,
        referencia_pago=referencia_pago,
        registrado_por=usuario,
        observacion=observacion,
    )
    pago.full_clean()
    pago.save()

    aporte.refresh_from_db()
    if aporte.saldo_pendiente == 0:
        aporte.estado = AporteNacional.Estado.PAGADO
        aporte.fecha_pago = fecha_pago
        aporte.referencia_pago = referencia_pago
        aporte.registrado_pago_por = usuario
        aporte.numero_recibo = _reservar_numero_recibo()
        if observacion:
            aporte.observacion = observacion
        aporte.save(
            update_fields=[
                "estado",
                "fecha_pago",
                "referencia_pago",
                "registrado_pago_por",
                "numero_recibo",
                "observacion",
                "actualizado_en",
            ]
        )
        AcuerdoPagoAporteNacional.objects.filter(
            aporte=aporte,
            estado=AcuerdoPagoAporteNacional.Estado.VIGENTE,
        ).update(estado=AcuerdoPagoAporteNacional.Estado.CUMPLIDO)
    return aporte


@transaction.atomic
def anular_aporte_pendiente(aporte, usuario, motivo):
    aporte = AporteNacional.objects.select_for_update().get(pk=aporte.pk)
    if aporte.estado == AporteNacional.Estado.ANULADO:
        return aporte
    if aporte.estado != AporteNacional.Estado.PENDIENTE:
        raise ValidationError("Solo se pueden anular aportes pendientes.")
    if aporte.total_pagos > 0:
        raise ValidationError("No se puede anular un aporte con pagos registrados.")
    aporte.estado = AporteNacional.Estado.ANULADO
    aporte.anulado_por = usuario
    aporte.anulado_en = timezone.now()
    aporte.motivo_anulacion = motivo
    aporte.observacion = _agregar_observacion_anulacion(aporte.observacion, motivo)
    aporte.save(
        update_fields=[
            "estado",
            "anulado_por",
            "anulado_en",
            "motivo_anulacion",
            "observacion",
            "actualizado_en",
        ]
    )
    return aporte


def _agregar_observacion_anulacion(observacion_actual, motivo):
    texto = f"Anulado para correccion de cierre: {motivo}"
    if observacion_actual:
        return f"{observacion_actual}\n{texto}"
    return texto


@transaction.atomic
def registrar_ajuste_aporte_pagado(aporte, usuario, tipo, monto, motivo, observacion=""):
    aporte = AporteNacional.objects.select_for_update().get(pk=aporte.pk)
    if aporte.estado != AporteNacional.Estado.PAGADO:
        raise ValidationError("Solo se pueden ajustar aportes pagados con recibo.")
    ajuste = AjusteAporteNacional(
        iglesia=aporte.iglesia,
        aporte=aporte,
        tipo=tipo,
        monto=monto,
        motivo=motivo,
        observacion=observacion,
        registrado_por=usuario,
    )
    ajuste.full_clean()
    ajuste.save()
    return ajuste


@transaction.atomic
def registrar_acuerdo_pago_aporte(aporte, usuario, fecha_compromiso, monto_comprometido, observacion=""):
    aporte = AporteNacional.objects.select_for_update().get(pk=aporte.pk)
    if aporte.estado != AporteNacional.Estado.PENDIENTE:
        raise ValidationError("Solo se pueden acordar pagos de aportes pendientes.")
    acuerdo = AcuerdoPagoAporteNacional(
        iglesia=aporte.iglesia,
        aporte=aporte,
        fecha_compromiso=fecha_compromiso,
        monto_comprometido=monto_comprometido,
        observacion=observacion,
        registrado_por=usuario,
    )
    acuerdo.full_clean()
    acuerdo.save()
    return acuerdo

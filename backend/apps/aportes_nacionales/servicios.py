from django.core.exceptions import ValidationError
from django.db import transaction

from apps.parametros.models import ParametroGeneral

from .models import AporteNacional


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
def registrar_pago_aporte(aporte, usuario, fecha_pago, referencia_pago, observacion=""):
    aporte = AporteNacional.objects.select_for_update().get(pk=aporte.pk)
    if aporte.estado == AporteNacional.Estado.PAGADO:
        return aporte
    if aporte.estado != AporteNacional.Estado.PENDIENTE:
        raise ValidationError("Solo se pueden pagar aportes pendientes.")
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
    return aporte

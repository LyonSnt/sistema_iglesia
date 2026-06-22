from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.cargos.models import AsignacionCargo
from apps.escuela_dominical.models import (
    ProcesoPromocionEscuelaDominical,
    ResultadoPromocionEscuelaDominical,
)
from apps.parametros.models import ParametroGeneral

from .models import CertificadoEscuelaDominical


def _nombre_persona(asignacion):
    if asignacion.miembro_id:
        return f"{asignacion.miembro.nombres} {asignacion.miembro.apellidos}".strip()
    nombre = asignacion.usuario.get_full_name().strip()
    return nombre or asignacion.usuario.username


def _firmante_vigente(iglesia, cargo, fecha):
    asignacion = (
        AsignacionCargo.objects.select_related("miembro", "usuario", "cargo")
        .filter(
            iglesia=iglesia,
            cargo__nombre__iexact=cargo,
            estado=AsignacionCargo.Estado.VIGENTE,
            activo=True,
            fecha_inicio__lte=fecha,
        )
        .filter(Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha))
        .order_by("-fecha_inicio")
        .first()
    )
    if asignacion is None:
        raise ValidationError(f"No existe una asignacion vigente para el cargo {cargo}.")
    return _nombre_persona(asignacion)


def _reservar_numero():
    try:
        prefijo = ParametroGeneral.objects.get(clave="CERTIFICADOS_PREFIJO", activo=True).valor.strip()
        secuencial = ParametroGeneral.objects.select_for_update().get(
            clave="CERTIFICADOS_SECUENCIAL_INICIAL", activo=True
        )
        valor = int(secuencial.valor)
    except ParametroGeneral.DoesNotExist as exc:
        raise ValidationError("Falta configurar la numeracion de certificados.") from exc
    except ValueError as exc:
        raise ValidationError("El secuencial de certificados no es un numero valido.") from exc
    secuencial.valor = str(valor + 1)
    secuencial.save(update_fields=["valor", "actualizado_en"])
    return f"{prefijo}-{valor:06d}"


@transaction.atomic
def emitir_certificado(resultado, usuario, fecha_emision=None):
    resultado = ResultadoPromocionEscuelaDominical.objects.select_for_update().select_related(
        "proceso__iglesia",
        "proceso__periodo_origen",
        "matricula_origen__alumno",
        "matricula_origen__clase__nivel",
    ).get(pk=resultado.pk)
    if resultado.proceso.estado != ProcesoPromocionEscuelaDominical.Estado.CONFIRMADO:
        raise ValidationError("Solo se certifican promociones confirmadas.")
    existente = CertificadoEscuelaDominical.objects.filter(
        resultado_promocion=resultado
    ).first()
    if existente:
        return existente

    fecha_emision = fecha_emision or timezone.localdate()
    iglesia = resultado.proceso.iglesia
    certificado = CertificadoEscuelaDominical(
        iglesia=iglesia,
        resultado_promocion=resultado,
        numero=_reservar_numero(),
        fecha_emision=fecha_emision,
        fecha_graduacion=resultado.proceso.fecha_corte,
        nombre_alumno=(
            f"{resultado.matricula_origen.alumno.nombres} "
            f"{resultado.matricula_origen.alumno.apellidos}"
        ).strip(),
        nivel_cursado=resultado.matricula_origen.clase.nivel.nombre,
        periodo_lectivo=resultado.proceso.periodo_origen.nombre,
        nombre_pastor=_firmante_vigente(iglesia, "Pastor", fecha_emision),
        nombre_director=_firmante_vigente(
            iglesia, "Director de Escuela Dominical", fecha_emision
        ),
        emitido_por=usuario,
    )
    certificado.full_clean()
    certificado.save()
    return certificado


@transaction.atomic
def emitir_certificados_proceso(proceso, usuario, fecha_emision=None):
    resultados = proceso.resultados.select_related("proceso").order_by("pk")
    return [emitir_certificado(resultado, usuario, fecha_emision) for resultado in resultados]


@transaction.atomic
def anular_certificado(certificado, usuario, motivo):
    certificado = CertificadoEscuelaDominical.objects.select_for_update().get(pk=certificado.pk)
    if certificado.estado == certificado.Estado.ANULADO:
        return certificado
    certificado.estado = certificado.Estado.ANULADO
    certificado.anulado_por = usuario
    certificado.anulado_en = timezone.now()
    certificado.motivo_anulacion = motivo
    certificado.save(
        update_fields=[
            "estado",
            "anulado_por",
            "anulado_en",
            "motivo_anulacion",
            "actualizado_en",
        ]
    )
    return certificado

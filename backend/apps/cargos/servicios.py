from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.auditoria.models import RegistroAuditoria
from apps.documentos.models import DocumentoAdjunto
from apps.usuarios.models import Usuario

from .models import AsignacionCargo, HistorialAsignacionCargo


ROLES_POR_CARGO_LOCAL = {
    "Pastor": Usuario.Rol.PASTOR_FILIAL,
    "Encargado": Usuario.Rol.ENCARGADO_FILIAL,
    "Secretario": Usuario.Rol.SECRETARIO_FILIAL,
    "Tesorero": Usuario.Rol.TESORERO_FILIAL,
}

PRIORIDAD_ROLES_LOCALES = (
    Usuario.Rol.PASTOR_FILIAL,
    Usuario.Rol.ENCARGADO_FILIAL,
    Usuario.Rol.SECRETARIO_FILIAL,
    Usuario.Rol.TESORERO_FILIAL,
)


def sincronizar_acceso_por_asignacion(asignacion):
    rol = rol_para_asignacion(asignacion)
    usuario = asignacion.usuario
    if rol is None or usuario is None:
        return
    if usuario.es_usuario_nacional or usuario.is_superuser:
        return
    actualizar_rol_y_grupo(usuario, rol)


def finalizar_acceso_por_asignacion(asignacion):
    usuario = asignacion.usuario
    rol_finalizado = rol_para_nombre_cargo(asignacion.cargo.nombre)
    if usuario is None or rol_finalizado is None:
        return
    if usuario.es_usuario_nacional or usuario.is_superuser or usuario.rol != rol_finalizado:
        return
    recalcular_acceso_por_usuario(usuario)


def recalcular_acceso_por_usuario(usuario):
    if usuario is None:
        return
    if usuario.es_usuario_nacional or usuario.is_superuser:
        return
    actualizar_rol_y_grupo(usuario, rol_vigente_para_usuario(usuario))


def rol_para_asignacion(asignacion):
    if asignacion.estado != AsignacionCargo.Estado.VIGENTE or not asignacion.activo:
        return None
    return rol_para_nombre_cargo(asignacion.cargo.nombre)


def rol_para_nombre_cargo(nombre):
    return ROLES_POR_CARGO_LOCAL.get(nombre)


def rol_vigente_para_usuario(usuario):
    roles_vigentes = set(
        AsignacionCargo.objects.filter(
            usuario=usuario,
            iglesia=usuario.iglesia,
            estado=AsignacionCargo.Estado.VIGENTE,
            activo=True,
            cargo__nombre__in=ROLES_POR_CARGO_LOCAL.keys(),
        ).values_list("cargo__nombre", flat=True)
    )
    roles = {ROLES_POR_CARGO_LOCAL[nombre] for nombre in roles_vigentes}
    for rol in PRIORIDAD_ROLES_LOCALES:
        if rol in roles:
            return rol
    return Usuario.Rol.SOLO_LECTURA


def actualizar_rol_y_grupo(usuario, rol):
    if usuario.rol != rol:
        usuario.rol = rol
        usuario.save(update_fields=["rol"])
    grupo, _ = Group.objects.get_or_create(name=rol)
    usuario.groups.set([grupo])


@transaction.atomic
def registrar_nombramiento(asignacion, usuario, fecha, motivo):
    asignacion = AsignacionCargo.objects.select_for_update().select_related("cargo", "iglesia").get(
        pk=asignacion.pk
    )
    estado_anterior = asignacion.estado
    asignacion.estado = AsignacionCargo.Estado.NOMBRADO
    asignacion.observacion = motivo
    asignacion.save(update_fields=["estado", "observacion", "actualizado_en"])
    if estado_anterior == AsignacionCargo.Estado.VIGENTE:
        finalizar_acceso_por_asignacion(asignacion)
    return _registrar_historial_y_auditoria(
        asignacion,
        usuario,
        HistorialAsignacionCargo.Tipo.NOMBRAMIENTO,
        fecha,
        motivo,
        estado_anterior,
        asignacion.estado,
    )


@transaction.atomic
def registrar_posesion(asignacion, usuario, fecha, motivo):
    asignacion = AsignacionCargo.objects.select_for_update().select_related("cargo", "iglesia").get(
        pk=asignacion.pk
    )
    if asignacion.cargo.requiere_documento_posesion and not tiene_acta_activa(asignacion):
        raise ValueError("La posesion requiere un acta activa adjunta.")

    estado_anterior = asignacion.estado
    asignacion.estado = AsignacionCargo.Estado.VIGENTE
    asignacion.fecha_inicio = fecha
    asignacion.observacion = motivo
    asignacion.save(update_fields=["estado", "fecha_inicio", "observacion", "actualizado_en"])
    sincronizar_acceso_por_asignacion(asignacion)
    historial = _registrar_historial_y_auditoria(
        asignacion,
        usuario,
        HistorialAsignacionCargo.Tipo.POSESION,
        fecha,
        motivo,
        estado_anterior,
        asignacion.estado,
    )
    recalcular_acceso_por_usuario(asignacion.usuario)
    return historial


@transaction.atomic
def registrar_renuncia(asignacion, usuario, fecha, motivo):
    asignacion = AsignacionCargo.objects.select_for_update().select_related("cargo", "iglesia").get(
        pk=asignacion.pk
    )
    estado_anterior = asignacion.estado
    asignacion.estado = AsignacionCargo.Estado.FINALIZADO
    asignacion.fecha_fin = fecha
    asignacion.observacion = motivo
    asignacion.save(update_fields=["estado", "fecha_fin", "observacion", "actualizado_en"])
    finalizar_acceso_por_asignacion(asignacion)
    return _registrar_historial_y_auditoria(
        asignacion,
        usuario,
        HistorialAsignacionCargo.Tipo.RENUNCIA,
        fecha,
        motivo,
        estado_anterior,
        asignacion.estado,
    )


@transaction.atomic
def registrar_reemplazo(asignacion, nueva_asignacion, usuario, fecha, motivo):
    asignacion = AsignacionCargo.objects.select_for_update().select_related("cargo", "iglesia").get(
        pk=asignacion.pk
    )
    nueva_asignacion = AsignacionCargo.objects.select_for_update().select_related("cargo", "iglesia").get(
        pk=nueva_asignacion.pk
    )
    estado_anterior = asignacion.estado
    asignacion.estado = AsignacionCargo.Estado.FINALIZADO
    asignacion.fecha_fin = fecha
    asignacion.observacion = motivo
    asignacion.save(update_fields=["estado", "fecha_fin", "observacion", "actualizado_en"])
    finalizar_acceso_por_asignacion(asignacion)
    _registrar_historial_y_auditoria(
        asignacion,
        usuario,
        HistorialAsignacionCargo.Tipo.REEMPLAZO,
        fecha,
        motivo,
        estado_anterior,
        asignacion.estado,
        asignacion_relacionada=nueva_asignacion,
    )

    estado_anterior_nueva = nueva_asignacion.estado
    nueva_asignacion.estado = AsignacionCargo.Estado.VIGENTE
    nueva_asignacion.fecha_inicio = fecha
    nueva_asignacion.asignacion_reemplazada = asignacion
    nueva_asignacion.observacion = motivo
    nueva_asignacion.save(
        update_fields=["estado", "fecha_inicio", "asignacion_reemplazada", "observacion", "actualizado_en"]
    )
    sincronizar_acceso_por_asignacion(nueva_asignacion)
    historial = _registrar_historial_y_auditoria(
        nueva_asignacion,
        usuario,
        HistorialAsignacionCargo.Tipo.REEMPLAZO,
        fecha,
        motivo,
        estado_anterior_nueva,
        nueva_asignacion.estado,
        asignacion_relacionada=asignacion,
    )
    recalcular_acceso_por_usuario(asignacion.usuario)
    recalcular_acceso_por_usuario(nueva_asignacion.usuario)
    return historial


def tiene_acta_activa(asignacion):
    return DocumentoAdjunto.objects.filter(
        iglesia=asignacion.iglesia,
        content_type=ContentType.objects.get_for_model(AsignacionCargo),
        object_id=asignacion.pk,
        tipo=DocumentoAdjunto.Tipo.ACTA,
        estado=DocumentoAdjunto.Estado.ACTIVO,
    ).exists()


def _registrar_historial_y_auditoria(
    asignacion,
    usuario,
    tipo,
    fecha,
    motivo,
    estado_anterior,
    estado_nuevo,
    asignacion_relacionada=None,
):
    historial = HistorialAsignacionCargo.objects.create(
        asignacion=asignacion,
        tipo=tipo,
        fecha=fecha,
        motivo=motivo,
        registrado_por=usuario,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        asignacion_relacionada=asignacion_relacionada,
    )
    RegistroAuditoria.objects.create(
        usuario=usuario,
        accion=tipo,
        modulo="cargos",
        registro_afectado=f"cargos.AsignacionCargo:{asignacion.pk}",
        valor_anterior={"estado": estado_anterior},
        valor_nuevo={
            "estado": estado_nuevo,
            "fecha": fecha.isoformat(),
            "historial_id": historial.pk,
            "asignacion_relacionada_id": asignacion_relacionada.pk if asignacion_relacionada else None,
        },
        iglesia=asignacion.iglesia,
        motivo=motivo,
    )
    return historial

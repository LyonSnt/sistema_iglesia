from django.contrib.auth.models import Group

from apps.usuarios.models import Usuario

from .models import AsignacionCargo


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

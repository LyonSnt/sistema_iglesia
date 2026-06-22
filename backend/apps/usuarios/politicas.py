from apps.core.iglesias import usuario_es_nacional

from .models import Usuario


ROLES_AUTORIDAD_FILIAL = (
    Usuario.Rol.PASTOR_FILIAL,
    Usuario.Rol.ENCARGADO_FILIAL,
)

ROLES_DELEGABLES_FILIAL = (
    Usuario.Rol.SECRETARIO_FILIAL,
    Usuario.Rol.TESORERO_FILIAL,
    Usuario.Rol.LIDER_MINISTERIO,
    Usuario.Rol.MAESTRO,
    Usuario.Rol.SOLO_LECTURA,
)


def es_administrador_local(user):
    return getattr(user, "rol", None) in ROLES_AUTORIDAD_FILIAL and not usuario_es_nacional(user)


def roles_asignables_por(user):
    if usuario_es_nacional(user):
        return ROLES_AUTORIDAD_FILIAL
    if es_administrador_local(user):
        return ROLES_DELEGABLES_FILIAL
    return ()


def filtrar_usuarios_gestionables(queryset, user):
    if usuario_es_nacional(user):
        return queryset.filter(rol__in=ROLES_AUTORIDAD_FILIAL)
    if es_administrador_local(user):
        return queryset.filter(iglesia=user.iglesia, rol__in=ROLES_DELEGABLES_FILIAL)
    return queryset.none()


def puede_gestionar_usuario(actor, objetivo):
    if actor.pk == objetivo.pk:
        return False
    return filtrar_usuarios_gestionables(Usuario.objects.filter(pk=objetivo.pk), actor).exists()

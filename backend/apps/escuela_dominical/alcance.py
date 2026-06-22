from apps.core.iglesias import filtrar_queryset_por_iglesia
from apps.usuarios.models import Usuario


ROLES_CON_ALCANCE_COMPLETO_FILIAL = {
    Usuario.Rol.PASTOR_FILIAL,
    Usuario.Rol.ENCARGADO_FILIAL,
    Usuario.Rol.SOLO_LECTURA,
}


def filtrar_clases_por_usuario(queryset, user):
    queryset = filtrar_queryset_por_iglesia(queryset, user)
    if (
        getattr(user, "rol", None) not in ROLES_CON_ALCANCE_COMPLETO_FILIAL
        and not getattr(user, "es_usuario_nacional", False)
        and not user.is_superuser
    ):
        queryset = queryset.filter(maestro=user)
    return queryset


def usuario_administra_escuela(user):
    return bool(
        user.is_superuser
        or getattr(user, "es_usuario_nacional", False)
        or getattr(user, "rol", None)
        in {Usuario.Rol.PASTOR_FILIAL, Usuario.Rol.ENCARGADO_FILIAL}
    )

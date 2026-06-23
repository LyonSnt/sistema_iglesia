from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from rest_framework.permissions import BasePermission

from apps.usuarios.models import Usuario


ACCION_VER = "ver"
ACCION_GESTIONAR = "gestionar"
ACCION_AUDITAR = "auditar"

MODULO_IGLESIAS = "iglesias"
MODULO_USUARIOS = "usuarios"
MODULO_PARAMETROS = "parametros"
MODULO_MIEMBROS = "miembros"
MODULO_CARGOS = "cargos"
MODULO_MINISTERIOS = "ministerios"
MODULO_ESCUELA_DOMINICAL = "escuela_dominical"
MODULO_FINANZAS = "finanzas"
MODULO_APORTES_NACIONALES = "aportes_nacionales"
MODULO_CERTIFICADOS = "certificados"
MODULO_TRASLADOS = "traslados"
MODULO_INVENTARIO = "inventario"
MODULO_REPORTES = "reportes"
MODULO_AUDITORIA = "auditoria"

ROLES_TODOS = frozenset(Usuario.Rol.values)
ROLES_NACIONALES = frozenset(
    {
        Usuario.Rol.SUPERADMIN,
        Usuario.Rol.ADMIN_NACIONAL,
    }
)
ROLES_FILIALES = ROLES_TODOS - ROLES_NACIONALES
ROLES_LECTURA_FILIAL = frozenset({Usuario.Rol.SOLO_LECTURA})
ROLES_ADMIN_FILIAL = frozenset({Usuario.Rol.PASTOR_FILIAL, Usuario.Rol.ENCARGADO_FILIAL})

MATRIZ_PERMISOS_MODULOS = {
    MODULO_IGLESIAS: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.ADMIN_NACIONAL,
            }
        ),
        ACCION_VER: frozenset(),
    },
    MODULO_USUARIOS: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.ADMIN_NACIONAL,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
            }
        ),
        ACCION_VER: frozenset(),
    },
    MODULO_PARAMETROS: {
        ACCION_GESTIONAR: frozenset({Usuario.Rol.SUPERADMIN}),
        ACCION_VER: frozenset(),
    },
    MODULO_MIEMBROS: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
                Usuario.Rol.SECRETARIO_FILIAL,
            }
        ),
        ACCION_VER: ROLES_LECTURA_FILIAL,
    },
    MODULO_CARGOS: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
                Usuario.Rol.SECRETARIO_FILIAL,
            }
        ),
        ACCION_VER: ROLES_LECTURA_FILIAL,
    },
    MODULO_MINISTERIOS: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
            }
        ),
        ACCION_VER: ROLES_LECTURA_FILIAL,
    },
    MODULO_ESCUELA_DOMINICAL: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
            }
        ),
        ACCION_VER: ROLES_LECTURA_FILIAL,
    },
    MODULO_FINANZAS: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
                Usuario.Rol.TESORERO_FILIAL,
            }
        ),
        ACCION_VER: ROLES_LECTURA_FILIAL,
    },
    MODULO_APORTES_NACIONALES: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
            }
        ),
        ACCION_VER: frozenset(
            {
                Usuario.Rol.TESORERO_FILIAL,
                Usuario.Rol.PASTOR_FILIAL,
            }
        ),
    },
    MODULO_CERTIFICADOS: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
                Usuario.Rol.SECRETARIO_FILIAL,
            }
        ),
        ACCION_VER: frozenset(
            {
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.SOLO_LECTURA,
            }
        ),
    },
    MODULO_TRASLADOS: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
                Usuario.Rol.SECRETARIO_FILIAL,
            }
        ),
        ACCION_VER: frozenset(),
    },
    MODULO_INVENTARIO: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.TESORERO_FILIAL,
                Usuario.Rol.ENCARGADO_FILIAL,
            }
        ),
        ACCION_VER: frozenset(
            {
                Usuario.Rol.PASTOR_FILIAL,
                Usuario.Rol.SOLO_LECTURA,
            }
        ),
    },
    MODULO_REPORTES: {
        ACCION_GESTIONAR: frozenset({Usuario.Rol.SUPERADMIN}),
        ACCION_VER: frozenset({Usuario.Rol.ADMIN_NACIONAL}),
    },
    MODULO_AUDITORIA: {
        ACCION_GESTIONAR: frozenset(
            {
                Usuario.Rol.SUPERADMIN,
                Usuario.Rol.ADMIN_NACIONAL,
            }
        ),
        ACCION_VER: frozenset(),
    },
}


def obtener_roles_permitidos(modulo, accion=ACCION_VER):
    acciones = MATRIZ_PERMISOS_MODULOS.get(modulo, {})
    roles = set(acciones.get(accion, ()))
    if accion == ACCION_VER:
        roles.update(acciones.get(ACCION_GESTIONAR, ()))
        roles.update(acciones.get(ACCION_AUDITAR, ()))
    return frozenset(roles)


def usuario_tiene_rol(user, roles):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return getattr(user, "rol", None) in roles


def usuario_puede(user, modulo, accion=ACCION_VER):
    roles = obtener_roles_permitidos(modulo, accion)
    if usuario_tiene_rol(user, roles):
        return True
    if not getattr(user, "is_authenticated", False):
        return False
    if modulo == MODULO_MINISTERIOS and accion in {ACCION_VER, ACCION_GESTIONAR}:
        return user.ministerios_liderados.filter(activo=True).exists()
    if modulo == MODULO_ESCUELA_DOMINICAL and accion in {ACCION_VER, ACCION_GESTIONAR}:
        return user.clases_escuela_dominical.filter(activo=True).exists()
    return False


def usuario_puede_acceder_iglesia(user, iglesia):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "es_usuario_nacional", False) or getattr(user, "is_superuser", False):
        return True
    return iglesia is not None and getattr(user, "iglesia_id", None) == getattr(iglesia, "id", None)


def usuario_puede_acceder_objeto(user, obj, campo_iglesia="iglesia"):
    iglesia = getattr(obj, campo_iglesia, None)
    return usuario_puede_acceder_iglesia(user, iglesia)


def permiso_modulo_requerido(modulo, accion=ACCION_VER):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not usuario_puede(request.user, modulo, accion):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


class PermisoModuloMixin(View):
    modulo_permiso = None
    accion_permiso = ACCION_VER

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not self.modulo_permiso:
            raise ImproperlyConfigured("Define modulo_permiso en la vista.")
        if not usuario_puede(request.user, self.modulo_permiso, self.accion_permiso):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class PermisoModuloDRF(BasePermission):
    message = "No tiene permisos para acceder a este modulo."

    def has_permission(self, request, view):
        modulo = getattr(view, "modulo_permiso", None)
        accion = getattr(view, "accion_permiso", ACCION_VER)
        if not modulo:
            return False
        return usuario_puede(request.user, modulo, accion)

    def has_object_permission(self, request, view, obj):
        campo_iglesia = getattr(view, "campo_iglesia", "iglesia")
        return self.has_permission(request, view) and usuario_puede_acceder_objeto(
            request.user,
            obj,
            campo_iglesia,
        )

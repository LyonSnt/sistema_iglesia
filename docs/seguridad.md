# Seguridad

## Variables sensibles

Las variables sensibles viven en `.env`. No se versiona `.env`.

## Sesiones y cookies

Variables soportadas:

- `SESSION_COOKIE_AGE`
- `SESSION_COOKIE_NAME`
- `CSRF_COOKIE_NAME`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`

## CSRF

CSRF permanece activo. Toda vista HTMX debe enviar token CSRF cuando haga mutaciones.

## django-axes

Se usa `django-axes` para bloquear intentos fallidos.

Variables:

- `AXES_FAILURE_LIMIT`
- `AXES_COOLOFF_TIME`

## Archivos

Los archivos subidos deben validarse por:

- Tipo.
- Tamano.
- Extension.
- Permisos de acceso.

## Auditoria

Acciones criticas:

- Finanzas.
- Recibos nacionales.
- Traslados.
- Certificados.
- Usuarios.
- Roles.
- Directivas.
- Cargos.
- Iglesias.

## Regla

No se debe confiar en datos de iglesia, usuario o permisos enviados por el cliente.

## Helpers de permisos

La matriz funcional vive en `apps.core.permisos` y debe usarse como puerta de
entrada para vistas Django, vistas DRF y servicios internos.

Funciones principales:

- `usuario_puede(user, modulo, accion)`.
- `usuario_puede_acceder_iglesia(user, iglesia)`.
- `usuario_puede_acceder_objeto(user, obj, campo_iglesia="iglesia")`.

Para vistas Django:

```python
from apps.core.permisos import ACCION_GESTIONAR, MODULO_MIEMBROS, permiso_modulo_requerido


@permiso_modulo_requerido(MODULO_MIEMBROS, ACCION_GESTIONAR)
def crear_miembro(request):
    ...
```

Para class-based views:

```python
from apps.core.permisos import ACCION_VER, MODULO_MIEMBROS, PermisoModuloMixin


class MiembroListView(PermisoModuloMixin, ListView):
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_VER
```

Para DRF:

```python
from apps.core.permisos import ACCION_VER, MODULO_MIEMBROS, PermisoModuloDRF


class MiembroAPIView(APIView):
    permission_classes = [PermisoModuloDRF]
    modulo_permiso = MODULO_MIEMBROS
    accion_permiso = ACCION_VER
```

Estos helpers no reemplazan el filtro por iglesia. Cada queryset con datos
filiales debe seguir usando `filtrar_queryset_por_iglesia`.

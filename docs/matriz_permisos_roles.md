# Matriz de Permisos y Roles

## Principio Central

Los roles del sistema representan nivel de acceso, no cargos eclesiasticos.

Los cargos organizacionales se registran como:

- `Cargo`.
- `AsignacionCargo`.
- `Ministerio.lider`.
- `ClaseEscuelaDominical.maestro`.

Ejemplos de cargos o asignaciones que no son roles base:

- Presidente.
- Vicepresidente.
- Auditor.
- Pastor.
- Encargado.
- Lider de ministerio.
- Maestro.
- Director de Escuela Dominical.

## Roles Vigentes

- `SUPERADMIN`
- `ADMIN_NACIONAL`
- `PASTOR_FILIAL`
- `ENCARGADO_FILIAL`
- `SECRETARIO_FILIAL`
- `TESORERO_FILIAL`
- `SOLO_LECTURA`

## Alcance

| Rol | Alcance | Uso |
| --- | --- | --- |
| `SUPERADMIN` | Global | Administracion tecnica total del sistema |
| `ADMIN_NACIONAL` | Nacional | Iglesias filiales, autoridades iniciales, reportes, auditoria y supervision |
| `PASTOR_FILIAL` | Filial | Administracion pastoral y operativa local |
| `ENCARGADO_FILIAL` | Filial | Administracion operativa local |
| `SECRETARIO_FILIAL` | Filial | Miembros, familias, cargos, documentos y traslados |
| `TESORERO_FILIAL` | Filial | Finanzas locales, aportes e inventario |
| `SOLO_LECTURA` | Filial/asignacion | Lectura o acceso funcional limitado por asignacion concreta |

## Reglas

- `SUPERADMIN` es el unico rol tecnico con acceso total.
- `ADMIN_NACIONAL` administra la estructura organizacional, no la operacion
  cotidiana de las filiales.
- Los usuarios nacionales supervisan mediante reportes y auditoria.
- Las filiales administran su propia operacion diaria.
- Ninguna filial puede crear iglesias, usuarios nacionales ni superusuarios.
- Ninguna filial puede acceder a informacion de otra iglesia.
- El filtro por iglesia es obligatorio incluso cuando existe permiso de lectura.
- Liderar un ministerio no requiere un rol `LIDER_MINISTERIO`; se concede por
  `Ministerio.lider`.
- Ser maestro no requiere un rol `MAESTRO`; se concede por
  `ClaseEscuelaDominical.maestro`.
- La auditoria nacional no requiere un rol `AUDITOR_NACIONAL`; se concede por
  permiso de auditoria a `ADMIN_NACIONAL` o por una futura asignacion/cargo si
  se necesita separar esa funcion.

## Permisos Django Sembrados

El comando `seed_inicial` crea o actualiza un grupo Django por cada rol vigente.

| Rol | Permisos Django base |
| --- | --- |
| `SUPERADMIN` | Todos |
| `ADMIN_NACIONAL` | Iglesias/zonas limitadas y consulta de auditoria |
| Roles filiales | Sin acceso a Django Admin; usan vistas funcionales |

Estos permisos son una base tecnica. Las reglas funcionales por modulo se
validan en vistas, servicios, formularios, admin y API junto con el alcance por
iglesia.

## Matriz Funcional

| Modulo | Gestion | Lectura/asignacion | Alcance |
| --- | --- | --- | --- |
| Iglesias y zonas | `SUPERADMIN`, `ADMIN_NACIONAL` | - | Nacional crea y mantiene filiales |
| Usuarios y roles | `SUPERADMIN`, `ADMIN_NACIONAL`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL` | - | Nacional crea autoridades filiales; filial crea cuentas locales |
| Parametros generales | `SUPERADMIN` | - | Tecnico/global |
| Miembros y familias | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `SECRETARIO_FILIAL` | `SOLO_LECTURA` | Filial solo su iglesia |
| Cargos y directivas | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `SECRETARIO_FILIAL` | `SOLO_LECTURA` | Filial solo su iglesia |
| Ministerios | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL` | `SOLO_LECTURA`; lider asignado opera su ministerio | Filial; asignado solo su ministerio |
| Escuela Dominical | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL` | `SOLO_LECTURA`; maestro asignado opera su clase | Filial; asignado solo su clase |
| Finanzas locales | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `TESORERO_FILIAL` | `SOLO_LECTURA` | Filial |
| Aportes nacionales | `SUPERADMIN` | `TESORERO_FILIAL`, `PASTOR_FILIAL` | Operacion filial; consolidado en reportes |
| Certificados y documentos | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `SECRETARIO_FILIAL` | `SOLO_LECTURA` | Filial |
| Traslados | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `SECRETARIO_FILIAL` | - | Entre iglesias con auditoria |
| Inventario | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `TESORERO_FILIAL` | `SOLO_LECTURA` | Filial |
| Reportes | `SUPERADMIN` | `ADMIN_NACIONAL` | Nacional consolida supervision aqui |
| Auditoria | `SUPERADMIN`, `ADMIN_NACIONAL` | - | Supervision nacional sin operacion local |

## Delegacion De Usuarios

- Nacional crea la filial junto con su primer `PASTOR_FILIAL` o
  `ENCARGADO_FILIAL`.
- Pastor y encargado pueden crear, editar, desactivar y restablecer contrasenas
  de `SECRETARIO_FILIAL`, `TESORERO_FILIAL` y `SOLO_LECTURA` de su propia
  iglesia.
- Una autoridad filial no puede crear otra autoridad, asignar roles nacionales,
  mover usuarios entre iglesias ni crear superusuarios.
- Las cuentas no se eliminan; se desactivan para conservar historial.
- Toda administracion de cuentas locales queda auditada sin almacenar hashes de
  contrasena.

## Comando De Normalizacion Tecnica

```bash
python manage.py normalizar_superusuario --username admin
```

El comando asigna rol `SUPERADMIN`, grupo `SUPERADMIN`, iglesia `NACIONAL`,
`is_staff=True`, `is_active=True` y `debe_cambiar_password=False`.

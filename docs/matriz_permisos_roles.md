# Matriz de Permisos y Roles

## Roles iniciales

- `SUPERADMIN`
- `ADMIN_NACIONAL`
- `PRESIDENTE_NACIONAL`
- `VICEPRESIDENTE_NACIONAL`
- `SECRETARIO_NACIONAL`
- `TESORERO_NACIONAL`
- `AUDITOR_NACIONAL`
- `PASTOR_FILIAL`
- `ENCARGADO_FILIAL`
- `SECRETARIO_FILIAL`
- `TESORERO_FILIAL`
- `LIDER_MINISTERIO`
- `MAESTRO`
- `SOLO_LECTURA`

## Principios

- Los roles definen alcance general.
- Cada usuario tiene un rol administrativo principal.
- Las funciones adicionales se conceden mediante asignaciones concretas, por
  ejemplo liderar un ministerio o impartir una clase.
- Los permisos granulares definen acciones concretas.
- Ningun rol nacional tiene acceso a modulos operativos de las filiales.
- `ADMIN_NACIONAL` crea filiales y sus autoridades iniciales, sin administrar
  la operacion cotidiana.
- El filtro por iglesia se aplica incluso cuando hay permisos de lectura.
- `SUPERADMIN` es para administracion tecnica y tiene acceso global.
- Los grupos Django se llaman igual que cada valor de `Usuario.Rol`.

## Alcance inicial

| Rol | Alcance | Notas |
| --- | --- | --- |
| SUPERADMIN | Global | Unico rol con administracion tecnica total |
| ADMIN_NACIONAL | Nacional | Alta de filiales, autoridades iniciales y reportes |
| PRESIDENTE_NACIONAL | Nacional | Consulta directiva y reportes |
| VICEPRESIDENTE_NACIONAL | Nacional | Consulta directiva y reportes |
| SECRETARIO_NACIONAL | Nacional | Reportes de su competencia |
| AUDITOR_NACIONAL | Nacional | Reportes y registros de auditoria |
| TESORERO_NACIONAL | Nacional | Reportes financieros consolidados |
| PASTOR_FILIAL | Filial | Gestion pastoral de su iglesia |
| ENCARGADO_FILIAL | Filial | Gestion operativa de su iglesia |
| SECRETARIO_FILIAL | Filial | Miembros, familias, documentos |
| TESORERO_FILIAL | Filial | Finanzas locales |
| LIDER_MINISTERIO | Filial/ministerio | Gestion de ministerio asignado |
| MAESTRO | Filial/escuela | Escuela Dominical |
| SOLO_LECTURA | Limitado | Lectura segun autorizacion |

## Permisos Django Sembrados

El comando `seed_inicial` crea o actualiza un grupo Django por cada rol y asigna
permisos base por accion:

| Rol | Permisos Django base |
| --- | --- |
| `SUPERADMIN` | Todos |
| `ADMIN_NACIONAL` | Iglesias/zonas limitadas y consulta de auditoria |
| `PRESIDENTE_NACIONAL` | Ver auditoria |
| `VICEPRESIDENTE_NACIONAL` | Ver auditoria |
| `SECRETARIO_NACIONAL` | Sin permisos de Django Admin |
| `TESORERO_NACIONAL` | Sin permisos de Django Admin |
| `AUDITOR_NACIONAL` | Ver auditoria |
| Roles filiales | Sin acceso a Django Admin; usan vistas funcionales |

Estos permisos son una base tecnica. Las reglas funcionales por modulo deben
validarse en vistas, servicios y admin junto con el alcance por iglesia.

## Matriz Funcional Inicial

| Modulo | Roles con gestion | Roles con lectura/auditoria | Alcance |
| --- | --- | --- | --- |
| Iglesias y zonas | `SUPERADMIN`, `ADMIN_NACIONAL` | - | Nacional crea y mantiene filiales |
| Usuarios y roles | `SUPERADMIN`, `ADMIN_NACIONAL` crean autoridades filiales; `PASTOR_FILIAL`, `ENCARGADO_FILIAL` crean cuentas locales delegables | - | Nacional administra el arranque; filial administra su equipo local |
| Parametros generales | `SUPERADMIN` | - | Tecnico/global |
| Miembros y familias | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `SECRETARIO_FILIAL` | `SOLO_LECTURA` | Filial solo su iglesia; Nacional consulta mediante reportes |
| Cargos y directivas | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `SECRETARIO_FILIAL` | `SOLO_LECTURA` | Filial solo su iglesia; Nacional consulta mediante reportes |
| Ministerios | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`; asignados operan participantes | `SOLO_LECTURA` | Filial; usuario asignado solo su ministerio |
| Asistencia y Escuela Dominical | `SUPERADMIN`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`; asignados operan clases | `SOLO_LECTURA` | Filial; usuario asignado solo su clase |
| Finanzas locales | `SUPERADMIN`, `TESORERO_FILIAL` | `PASTOR_FILIAL` | Filial; Nacional consulta mediante reportes |
| Aportes nacionales | `SUPERADMIN` | `TESORERO_FILIAL`, `PASTOR_FILIAL` | Operacion filial; consolidado en reportes |
| Certificados y documentos | `SUPERADMIN`, `SECRETARIO_FILIAL` | `PASTOR_FILIAL`, `SOLO_LECTURA` | Filial; Nacional consulta mediante reportes |
| Traslados | `SUPERADMIN`, `PASTOR_FILIAL`, `SECRETARIO_FILIAL` | - | Entre iglesias con auditoria |
| Inventario | `SUPERADMIN`, `TESORERO_FILIAL`, `ENCARGADO_FILIAL` | `PASTOR_FILIAL`, `SOLO_LECTURA` | Filial |
| Reportes | `SUPERADMIN` | Todos los roles segun reporte | Nacional obtiene supervision consolidada aqui |
| Auditoria | `SUPERADMIN`, `AUDITOR_NACIONAL` | `ADMIN_NACIONAL`, `PRESIDENTE_NACIONAL`, `VICEPRESIDENTE_NACIONAL` | Supervision nacional sin operacion local |

## Comando de Normalizacion Tecnica

El superusuario tecnico creado con `createsuperuser` debe quedar consistente con
roles y grupos:

```bash
python manage.py normalizar_superusuario --username admin
```

El comando asigna rol `SUPERADMIN`, grupo `SUPERADMIN`, iglesia `NACIONAL`,
`is_staff=True`, `is_active=True` y `debe_cambiar_password=False`.

## Pendiente Funcional

- Usar los helpers/decoradores de `apps.core.permisos` en las proximas vistas.
- Ajustar permisos finos por objeto en los futuros flujos de traslados.

## Intervencion Nacional

- Los usuarios nacionales consultan informacion consolidada mediante reportes,
  no entrando a modulos operativos.
- Solo `SUPERADMIN` puede intervenir tecnicamente sobre datos operativos.
- Toda creacion o modificacion autorizada de Nacional sobre una filial genera un
  `RegistroAuditoria` automatico con usuario, IP y valores anterior/nuevo.
- La operacion cotidiana corresponde a los roles de la propia filial.

## Delegacion de Usuarios

- Nacional crea la filial junto con su primer `PASTOR_FILIAL` o
  `ENCARGADO_FILIAL`.
- Pastor y encargado pueden crear, editar, desactivar y restablecer contrasenas
  de `SECRETARIO_FILIAL`, `TESORERO_FILIAL`, `LIDER_MINISTERIO`, `MAESTRO` y
  `SOLO_LECTURA` de su propia iglesia.
- Una autoridad filial no puede crear otra autoridad, asignar roles nacionales,
  mover usuarios entre iglesias ni crear superusuarios.
- Las cuentas no se eliminan; se desactivan para conservar historial.
- Toda administracion de cuentas locales queda auditada sin almacenar hashes de
  contrasena.

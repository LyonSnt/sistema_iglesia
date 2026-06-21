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
- Los permisos granulares definen acciones concretas.
- El rol nacional no significa acceso ilimitado.
- El filtro por iglesia se aplica incluso cuando hay permisos de lectura.
- `SUPERADMIN` es para administracion tecnica y tiene acceso global.
- Los grupos Django se llaman igual que cada valor de `Usuario.Rol`.

## Alcance inicial

| Rol | Alcance | Notas |
| --- | --- | --- |
| SUPERADMIN | Global | Uso tecnico y administracion total |
| ADMIN_NACIONAL | Nacional | Gestion general segun permisos |
| PRESIDENTE_NACIONAL | Nacional | Consulta directiva y reportes |
| VICEPRESIDENTE_NACIONAL | Nacional | Consulta directiva y reportes |
| SECRETARIO_NACIONAL | Nacional | Gestion documental y membresia consolidada |
| AUDITOR_NACIONAL | Nacional | Lectura y auditoria |
| TESORERO_NACIONAL | Nacional | Aportes y recibos nacionales |
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
| `ADMIN_NACIONAL` | Todos |
| `PRESIDENTE_NACIONAL` | Ver |
| `VICEPRESIDENTE_NACIONAL` | Ver |
| `SECRETARIO_NACIONAL` | Ver, crear, editar |
| `TESORERO_NACIONAL` | Ver, crear, editar |
| `AUDITOR_NACIONAL` | Ver |
| `PASTOR_FILIAL` | Ver, crear, editar |
| `ENCARGADO_FILIAL` | Ver, crear, editar |
| `SECRETARIO_FILIAL` | Ver, crear, editar |
| `TESORERO_FILIAL` | Ver, crear, editar |
| `LIDER_MINISTERIO` | Ver |
| `MAESTRO` | Ver |
| `SOLO_LECTURA` | Ver |

Estos permisos son una base tecnica. Las reglas funcionales por modulo deben
validarse en vistas, servicios y admin junto con el alcance por iglesia.

## Matriz Funcional Inicial

| Modulo | Roles con gestion | Roles con lectura/auditoria | Alcance |
| --- | --- | --- | --- |
| Iglesias y zonas | `SUPERADMIN`, `ADMIN_NACIONAL`, `SECRETARIO_NACIONAL` | `PRESIDENTE_NACIONAL`, `VICEPRESIDENTE_NACIONAL`, `AUDITOR_NACIONAL`, `SOLO_LECTURA` | Global/nacional |
| Usuarios y roles | `SUPERADMIN`, `ADMIN_NACIONAL` | `AUDITOR_NACIONAL` | Global/nacional |
| Parametros generales | `SUPERADMIN`, `ADMIN_NACIONAL` | `AUDITOR_NACIONAL` | Global |
| Miembros y familias | `SUPERADMIN`, `ADMIN_NACIONAL`, `SECRETARIO_NACIONAL`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `SECRETARIO_FILIAL` | `AUDITOR_NACIONAL`, `SOLO_LECTURA` | Nacional ve consolidado; filial solo su iglesia |
| Cargos y directivas | `SUPERADMIN`, `ADMIN_NACIONAL`, `SECRETARIO_NACIONAL`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `SECRETARIO_FILIAL` | `AUDITOR_NACIONAL`, `SOLO_LECTURA` | Nacional o filial segun cargo |
| Ministerios | `SUPERADMIN`, `ADMIN_NACIONAL`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `LIDER_MINISTERIO` | `AUDITOR_NACIONAL`, `SOLO_LECTURA` | Filial; lider solo ministerios asignados |
| Asistencia y Escuela Dominical | `SUPERADMIN`, `ADMIN_NACIONAL`, `PASTOR_FILIAL`, `ENCARGADO_FILIAL`, `MAESTRO` | `AUDITOR_NACIONAL`, `SOLO_LECTURA` | Filial; maestro segun clase/asignacion futura |
| Finanzas locales | `SUPERADMIN`, `ADMIN_NACIONAL`, `TESORERO_NACIONAL`, `TESORERO_FILIAL` | `AUDITOR_NACIONAL`, `PASTOR_FILIAL` | Filial; nacional consolida/audita |
| Aportes nacionales | `SUPERADMIN`, `ADMIN_NACIONAL`, `TESORERO_NACIONAL` | `AUDITOR_NACIONAL`, `TESORERO_FILIAL`, `PASTOR_FILIAL` | Nacional con consulta filial |
| Certificados y documentos | `SUPERADMIN`, `ADMIN_NACIONAL`, `SECRETARIO_NACIONAL`, `SECRETARIO_FILIAL` | `AUDITOR_NACIONAL`, `PASTOR_FILIAL`, `SOLO_LECTURA` | Filial; nacional consulta y audita |
| Traslados | `SUPERADMIN`, `ADMIN_NACIONAL`, `SECRETARIO_NACIONAL`, `PASTOR_FILIAL`, `SECRETARIO_FILIAL` | `AUDITOR_NACIONAL` | Entre iglesias con auditoria |
| Inventario | `SUPERADMIN`, `ADMIN_NACIONAL`, `TESORERO_FILIAL`, `ENCARGADO_FILIAL` | `AUDITOR_NACIONAL`, `PASTOR_FILIAL`, `SOLO_LECTURA` | Filial |
| Reportes | `SUPERADMIN`, `ADMIN_NACIONAL` | Roles nacionales y filiales segun modulo | Mismo alcance del dato reportado |
| Auditoria | `SUPERADMIN`, `ADMIN_NACIONAL`, `AUDITOR_NACIONAL` | `PRESIDENTE_NACIONAL`, `VICEPRESIDENTE_NACIONAL` | Global/nacional |

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
- Ajustar permisos finos por objeto cuando existan asignaciones de ministerio,
  clases de Escuela Dominical y flujos de traslados.

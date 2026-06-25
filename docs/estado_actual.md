# Estado Actual

Ultima actualizacion: 2026-06-25.

## Resumen

Ecclesia es un sistema web centralizado multi-iglesia para una organizacion
religiosa nacional con mas de 30 iglesias filiales.

La iglesia nacional necesita supervision, reportes, auditoria y control general.
Cada iglesia filial debe administrar sus propios datos como si el sistema fuera
solo de esa filial.

## Decisiones Vigentes

- Se usara una sola base PostgreSQL: `sistema_iglesia`.
- No se usara multitenant por base de datos.
- No se usaran bases por iglesia filial.
- No se usaran rutas tipo `/pruebas/`.
- La separacion de datos sera por campo `iglesia`, roles, permisos y filtros obligatorios.
- `SUPERADMIN` es el unico rol con acceso tecnico total.
- `ADMIN_NACIONAL` solo gestiona filiales, autoridades iniciales, reportes y
  consulta de auditoria; no accede a modulos operativos.
- El soporte nacional a filiales debe ser excepcional, justificado, limitado y
  auditado; sus criterios funcionales estan documentados en
  `docs/soporte_nacional.md`.
- Los cargos organizacionales nacionales se modelan como cargos/asignaciones,
  no como roles base del sistema.
- Lideres de ministerio y maestros reciben acceso por asignacion concreta, no
  por rol principal.
- `PRUEBAS` sera una iglesia filial de validacion dentro de la misma base.
- El backend Django vive en `backend/`.
- Las apps Django viven en `backend/apps/`.
- La configuracion Django se llama `config`.
- Tailwind se compila con Node, sin CDN.
- Docker usa tres archivos:
  - `docker-compose.yml`: base comun sin puertos.
  - `docker-compose.dev.yml`: desarrollo.
  - `docker-compose.prod.yml`: produccion base.
- Puertos de Ecclesia:
  - App: `8020`.
  - PostgreSQL publicado en desarrollo: `5434`.

## Implementado

### Infraestructura

- Dockerfile con build multi-stage:
  - etapa Node para compilar Tailwind;
  - etapa Python final sin Node.
- `docker-compose.yml`.
- `docker-compose.dev.yml`.
- `docker-compose.prod.yml`.
- PostgreSQL.
- Redis.
- Celery worker.
- Celery Beat.
- Volumen para PostgreSQL.
- Volumen para `media`.
- Volumen para `staticfiles`.

### Backend

- Proyecto Django `config`.
- Django REST Framework configurado.
- Endpoint de salud: `/api/health/`.
- API inicial de consulta:
  - `/api/miembros/`.
  - `/api/miembros/<id>/`.
  - `/api/familias/`.
  - `/api/familias/<id>/`.
  - `/api/matrimonios/`.
  - `/api/cargos/`.
  - `/api/asignaciones-cargos/`.
  - `/api/asignaciones-cargos/<id>/`.
  - `/api/ministerios/`.
  - `/api/ministerios/<id>/`.
  - `/api/participaciones-ministerios/`.
  - `/api/participaciones-ministerios/<id>/`.
  - `/api/traslados/`.
  - `/api/traslados/<id>/`.
- Modulo Cargos/directivas iniciado:
  - listado en `/cargos/`;
  - detalle de asignacion;
  - creacion y edicion;
  - finalizacion de asignaciones;
  - sincronizacion de acceso para cargos funcionales locales asignados a
    usuarios: Pastor, Encargado, Secretario y Tesorero;
  - recalculo del rol del usuario al finalizar una asignacion funcional,
    conservando otro cargo vigente o bajando a solo lectura;
  - documentos adjuntos protegidos por permiso y alcance por iglesia.
- Modulo Ministerios iniciado:
  - listado en `/ministerios/`;
  - detalle de ministerio;
  - creacion y edicion;
  - agregado y finalizacion de participaciones.
- Modulo Escuela Dominical iniciado:
  - listado de clases en `/escuela-dominical/`;
  - detalle, creacion y edicion de clases;
  - niveles por iglesia con rangos de edad;
  - clases por periodo, nivel, maestro, aula, horario y cupo;
  - matricula y edicion de alumnos por clase;
  - sesiones por clase y fecha;
  - toma masiva de asistencia con estados presente, ausente y justificado;
  - cierre de sesiones y correccion reservada a autoridades;
  - corte anual en una fecha exacta de enero;
  - promocion por edad con asistencia informativa;
  - revision y confirmacion por pastor o encargado;
  - matricula automatica en el nivel siguiente y egreso a Jovenes a los 18 anos.
- Modulo Certificados iniciado:
  - listado funcional en `/certificados/`;
  - certificados para cada cambio de nivel y egreso a Jovenes;
  - emision individual o por lote desde promociones confirmadas;
  - numeracion transaccional unica;
  - PDF A4 horizontal con datos de alumno, nivel, periodo y firmantes;
  - firmas historicas de Pastor y Director de Escuela Dominical;
  - anulacion sin borrado ni reutilizacion del numero;
  - hoja funcional documentada para certificados institucionales futuros:
    membresia, bautismo, traslado, cargo/directiva y constancia pastoral.
- Modulo Traslados iniciado:
  - listado en `/traslados/`;
  - solicitud de traslado entre iglesias filiales;
  - aceptacion, rechazo y anulacion segun origen/destino;
  - movimiento del miembro a la iglesia destino al aceptar;
  - cierre automatico de relaciones locales activas en origen al aceptar:
    vinculos familiares, jefatura familiar, cargos, participaciones
    ministeriales, matriculas de Escuela Dominical y responsables de
    ministerio;
  - documentos adjuntos protegidos por permiso y alcance origen/destino;
  - auditoria explicita del flujo de traslado;
  - reporte inicial de traslados en `/reportes/traslados/`.
- Modulo Reportes iniciado:
  - entrada principal de Reportes apunta al reporte financiero consolidado;
  - reporte nacional de traslados en `/reportes/traslados/`;
  - reporte financiero consolidado en `/reportes/finanzas/`;
  - reporte nacional de inventario en `/reportes/inventario/`;
  - estrategia general de reportes documentada en `docs/reportes.md`;
  - filtros financieros por filial, zona, anio y mes;
  - filtros de inventario por filial, zona, categoria, estado y busqueda;
  - totales de ingresos, egresos, saldo local, aporte pagado y aporte
    pendiente.
- Estrategia de auditoria documentada en `docs/auditoria.md`:
  - cobertura esperada por modulo;
  - eventos criticos;
  - datos minimos;
  - prioridades de implementacion.
- Modulo Finanzas locales iniciado:
  - listado en `/finanzas/`;
  - conceptos financieros por iglesia y tipo ingreso/egreso;
  - registro de movimientos de ingreso y egreso;
  - documentos adjuntos protegidos por permiso y alcance por iglesia;
  - resumen de ingresos, egresos y saldo segun filtros;
  - detalle de movimiento;
  - anulacion sin borrado fisico;
  - cierres mensuales en `/finanzas/cierres/`;
  - totales congelados por iglesia, anio y mes;
  - bloqueo de nuevos movimientos y anulaciones dentro de meses cerrados;
  - anulacion controlada de cierres sin aporte nacional generado para corregir
    movimientos y regenerar el cierre con totales recalculados.
- Modulo Aportes nacionales iniciado:
  - listado en `/aportes-nacionales/`;
  - generacion de aporte desde cierres mensuales cerrados;
  - porcentaje inicial desde `APORTE_NACIONAL_PORCENTAJE`;
  - monto base congelado desde ingresos del cierre;
  - consulta por filial con alcance por iglesia;
  - generacion de aportes reservada a `SUPERADMIN`;
  - registro de pago por `SUPERADMIN` o `ADMIN_NACIONAL`;
  - numeracion transaccional de recibos;
  - resumen de pendiente y pagado;
  - cuenta corriente detallada en `/aportes-nacionales/cuenta-corriente/`;
  - recibo PDF para aportes pagados.
- Modulo Inventario iniciado:
  - listado en `/inventario/`;
  - registro y edicion de activos por iglesia filial;
  - codigo interno unico por iglesia;
  - categoria, ubicacion actual, responsable actual, estado, fecha de
    adquisicion y valor referencial;
  - historial de movimientos por cambio de ubicacion, responsable, reparacion
    y baja;
  - documentos adjuntos protegidos por permiso y alcance por iglesia;
  - baja sin borrado fisico;
  - reporte nacional consolidado con filtros por filial, zona, categoria,
    estado y busqueda;
  - alcance por iglesia y permisos de gestion segun matriz funcional.
- Modulo Documentos iniciado:
  - modelo reutilizable `DocumentoAdjunto`;
  - asociacion generica a registros con `ContentType`;
  - validacion de extension y tamano;
  - clasificacion de tipos documentales permitidos por modulo;
  - el formulario muestra solo los tipos validos para el registro asociado;
  - el modelo rechaza tipos no permitidos para el modulo asociado;
  - anulado logico sin borrado fisico;
  - integracion funcional en Inventario, Cargos, Traslados y Finanzas.
- HTMX preparado en plantilla base.
- Login propio en `/login/`.
- Logout por POST en `/logout/`.
- Dashboard inicial protegido en `/`.
- Gestion de filiales en `/iglesias/`:
  - alta de filial con pastor o encargado inicial en una sola operacion;
  - interfaz de alta separa datos de iglesia, autoridad inicial y acceso
    temporal;
  - edicion y desactivacion sin borrar historial.
- Gestion delegada de usuarios en `/usuarios/`:
  - Nacional gestiona autoridades iniciales de filiales;
  - pastor y encargado gestionan solo cuentas locales delegables;
  - interfaz independiente aclara que agrega cuentas a filiales existentes;
  - creacion, edicion, desactivacion y restablecimiento de contrasena;
  - cambio obligatorio de contrasena temporal en el primer acceso.
- Listado inicial de miembros en `/miembros/`.
- Tailwind compilado desde `backend/static/css/input.css` hacia `backend/static/css/app.css`.
- `django-environ` para variables de entorno.
- `django-axes` para proteccion contra fuerza bruta.
- `reportlab` para generacion de certificados PDF.
- Usuario personalizado `apps.usuarios.Usuario`.
- Roles de acceso vigentes definidos en `Usuario.Rol`.
- Apps creadas segun arquitectura inicial.
- Modelos base iniciales:
  - `Zona`.
  - `Iglesia`.
  - `Usuario`.
  - `Periodo`.
  - `ParametroGeneral`.
  - `Miembro`.
  - `Familia`.
  - `MiembroFamilia`.
  - `Cargo`.
  - `AsignacionCargo`.
  - `Ministerio`.
  - `ParticipacionMinisterio`.
  - `NivelEscuelaDominical`.
  - `ClaseEscuelaDominical`.
  - `MatriculaEscuelaDominical`.
  - `SesionEscuelaDominical`.
  - `AsistenciaEscuelaDominical`.
  - `ProcesoPromocionEscuelaDominical`.
  - `ResultadoPromocionEscuelaDominical`.
  - `CertificadoEscuelaDominical`.
  - `TrasladoMiembro`.
  - `ConceptoFinanciero`.
  - `MovimientoFinanciero`.
  - `CierreMensualFinanciero`.
  - `AporteNacional`.
  - `ActivoInventario`.
  - `MovimientoInventario`.
  - `DocumentoAdjunto`.
  - `RegistroAuditoria`.
- Admin basico para modelos iniciales.
- Migraciones iniciales creadas y aplicadas.

### Multi-Iglesia

- `IglesiaScopedModel` como modelo abstracto para datos con campo `iglesia`.
- Helpers de alcance por iglesia en `apps.core.iglesias`:
  - `usuario_es_nacional`.
  - `obtener_iglesia_usuario`.
  - `filtrar_queryset_por_iglesia`.
  - `IglesiaQuerysetMixin`.
- `IglesiaScopedAdminMixin` usa los helpers de alcance por iglesia.

### Seed Inicial

- Comando idempotente:

```bash
python manage.py seed_inicial
```

- El seed crea:
  - zonas base;
  - Iglesia Nacional;
  - Iglesia Filial Pruebas;
  - cargos base;
  - parametros generales;
  - periodo anual actual;
  - grupos Django por cada rol de `Usuario.Rol`.

### Usuarios de Prueba

- Comando idempotente:

```bash
python manage.py seed_usuarios_prueba
```

- Usuarios nacionales creados:
  - `admin_nacional`: `ADMIN_NACIONAL`, iglesia `NACIONAL`.
- Usuarios filiales creados:
  - `pastor_pruebas`: `PASTOR_FILIAL`, iglesia `PRUEBAS`.
  - `encargado_pruebas`: `ENCARGADO_FILIAL`, iglesia `PRUEBAS`.
  - `secretario_pruebas`: `SECRETARIO_FILIAL`, iglesia `PRUEBAS`.
  - `tesorero_pruebas`: `TESORERO_FILIAL`, iglesia `PRUEBAS`.
  - `lectura_pruebas`: `SOLO_LECTURA`, iglesia `PRUEBAS`.
- Contrasena de desarrollo usada: `Cambiar12345!`.
- Todos quedan con grupo Django alineado con su rol.
- El superusuario tecnico `admin` fue normalizado como `SUPERADMIN`, iglesia `NACIONAL`.

## Datos Base Creados

El comando `seed_inicial` fue ejecutado en la base local.

### Iglesias

- `NACIONAL`: Iglesia Nacional.
- `PRUEBAS`: Iglesia Filial Pruebas.

### Zonas

- Costa.
- Sierra.
- Oriente.
- Insular.

### Cargos

- Presidente.
- Vicepresidente.
- Secretario.
- Tesorero.
- Auditor.
- Vocal.
- Pastor.
- Encargado.
- Lider de ministerio.
- Maestro.
- Director de Escuela Dominical.

### Parametros

- `APORTE_NACIONAL_PORCENTAJE`.
- `ESCUELA_DOMINICAL_DIA_CORTE`.
- `CERTIFICADOS_PREFIJO`.
- `CERTIFICADOS_SECUENCIAL_INICIAL`.
- `APORTES_RECIBOS_PREFIJO`.
- `APORTES_RECIBOS_SECUENCIAL_INICIAL`.

### Grupos

Se creo un grupo Django por cada rol inicial:

- `SUPERADMIN`
- `ADMIN_NACIONAL`
- `PASTOR_FILIAL`
- `ENCARGADO_FILIAL`
- `SECRETARIO_FILIAL`
- `TESORERO_FILIAL`
- `SOLO_LECTURA`

## Validado

- Docker levanta y Django responde en `http://localhost:8020`.
- `/admin/` responde correctamente.
- `/api/health/` responde correctamente.
- `python manage.py check` no reporta issues.
- `python manage.py makemigrations --check --dry-run` no reporta cambios pendientes.
- `seed_inicial` fue probado dos veces y es idempotente.
- `seed_usuarios_prueba` fue ejecutado y es idempotente.
- Usuarios de prueba tienen rol, grupo e iglesia correctos.
- Existe comando para normalizar el superusuario tecnico:
  `python manage.py normalizar_superusuario --username admin`.
- Helpers/decoradores de permisos funcionales en `apps.core.permisos`.
- Roles de acceso simplificados: cargos organizacionales y asignaciones
  funcionales ya no se modelan como roles principales de usuario.
- Separacion estricta entre `SUPERADMIN` y roles nacionales validada en
  dashboard, vistas, API y Django Admin.
- Lideres de ministerio limitados a ministerios asignados; pueden operar
  participantes, pero no crear ni redefinir ministerios.
- Maestros limitados a clases asignadas; pueden operar matriculas, pero no
  crear niveles ni clases.
- Auditoria automatica para creaciones y modificaciones realizadas por
  usuarios nacionales sobre datos de una filial.
- Auditoria de administracion local de cuentas sin almacenar contrasenas ni
  hashes.
- El acceso funcional adicional se obtiene por asignacion a ministerio o clase,
  sin necesidad de crear otra cuenta ni cambiar el rol principal.
- Dashboard inicial usa la matriz de permisos para mostrar modulos disponibles por rol.
- Modulo Miembros iniciado con listado, busqueda, filtro por estado, detalle,
  creacion, edicion, acciones pastorales iniciales y alcance por iglesia.
- Familias integradas al detalle de Miembros:
  - crear familia desde un miembro;
  - vincular miembro a familia existente de la misma iglesia.
- Modulo Familias iniciado con listado, detalle, creacion, edicion y agregado
  de integrantes.
- Familias permite desactivar vinculos familiares sin borrar historial.
- Al crear o editar familia, el jefe de hogar queda vinculado como
  `REPRESENTANTE` activo y debe pertenecer a la misma iglesia.
- Matrimonios implementados dentro del flujo Miembros/Familias:
  - modelo `Matrimonio`;
  - registro desde el detalle de miembro;
  - actualizacion de estado civil a `CASADO`;
  - vinculacion opcional de ambos miembros como `CONYUGE` en una familia.
- `normalizar_superusuario --username admin` fue ejecutado correctamente.
- La matriz funcional inicial de permisos por modulo quedo documentada.
- Tests de `apps.core` cubren permisos, login y dashboard inicial.
- Tests de `apps.miembros` cubren acceso, permisos, busqueda, detalle,
  creacion, edicion, acciones pastorales iniciales y aislamiento por iglesia.
- Tests de familias dentro de Miembros cubren creacion, vinculacion, duplicados,
  permisos y aislamiento por iglesia.
- Tests de `apps.familias` cubren listado, detalle, creacion, edicion,
  agregado de integrantes, permisos y aislamiento por iglesia.
- Tests de `apps.familias` tambien cubren desactivacion/reactivacion de vinculos
  y ajuste de jefe de hogar.
- Tests de matrimonios cubren registro, duplicados, permisos, alcance por
  iglesia, estado civil y vinculos familiares opcionales.
- Tests de `apps.api` cubren health publico, autenticacion, permisos, busqueda
  y alcance por iglesia para Miembros/Familias/Matrimonios.
- Tests de `apps.api` cubren consulta, filtros, permisos y alcance por iglesia
  para Ministerios y participaciones ministeriales.
- Tests de `apps.cargos` cubren listado, detalle, creacion, validaciones,
  finalizacion, sincronizacion de roles por asignacion funcional, documentos
  adjuntos, permisos y aislamiento por iglesia.
- API de Cargos/directivas expone cargos y asignaciones en modo consulta,
  protegida por permisos y alcance por iglesia.
- Tests de `apps.ministerios` cubren listado, detalle, creacion, validaciones,
  participaciones, finalizacion, permisos y aislamiento por iglesia.
- Tests de `apps.escuela_dominical` cubren niveles, clases, maestros, matriculas,
  cupos, sesiones, asistencia, cierre, permisos, aislamiento por iglesia,
  cortes de edad, promociones, egreso a Jovenes e idempotencia.
- Tests de `apps.certificados` cubren elegibilidad, numeracion, firmas vigentes,
  emision idempotente, PDF, permisos, aislamiento por iglesia y anulacion.
- Tests de `apps.traslados` cubren solicitud, permisos, alcance por iglesia,
  aceptacion, rechazo, anulacion, auditoria, documentos adjuntos y movimiento
  del miembro, incluyendo cierre de relaciones locales activas en origen.
- Tests de `apps.reportes` cubren reporte inicial de traslados.
- Tests de `apps.reportes` cubren reporte financiero consolidado, permisos
  nacionales, filtros y totales.
- Tests de `apps.reportes` cubren reporte nacional de inventario, permisos
  nacionales, filtros y totales.
- Tests de `apps.inventario` cubren creacion, permisos, consulta, aislamiento
  por iglesia, movimientos, historial, documentos adjuntos protegidos y baja
  sin borrado fisico.
- Tests de `apps.finanzas` cubren conceptos, movimientos, permisos, gestion
  local, aislamiento por iglesia, validaciones, anulacion, cierres mensuales,
  totales congelados, duplicados, documentos adjuntos, bloqueo por mes cerrado
  y correccion posterior de cierres sin aporte nacional generado.
- Tests de `apps.aportes_nacionales` cubren generacion desde cierre mensual,
  porcentaje parametrizado, permisos, no duplicar aportes, aislamiento por
  iglesia, registro de pago por operacion financiera nacional, numeracion de
  recibos, totales pendiente/pagado y seed de parametros documentales, cuenta
  corriente y recibo PDF.
- Tests de `apps.auditoria` cubren intervencion nacional sobre filiales y
  ausencia de auditoria nacional en la gestion propia de una filial.
- Tests de `apps.iglesias` y `apps.usuarios` cubren la separacion visual entre
  alta de filial, autoridad inicial, usuarios delegados y acceso temporal.
- Tailwind ya no usa CDN.
- Compose dev y prod validan correctamente.
- Migracion `escuela_dominical.0003` aplicada para procesos y resultados de
  promocion.
- Migracion `certificados.0001` aplicada para certificados de Escuela Dominical.
- Migracion `inventario.0001` aplicada para activos y movimientos de inventario.
- Migracion `documentos.0001` aplicada para documentos adjuntos reutilizables.
- Migracion `finanzas.0003` creada para permitir regenerar cierres anulados y
  conservar unicidad solo entre cierres cerrados por iglesia, anio y mes.
- Suite completa validada: 243 tests aprobados.
- Validacion focalizada de documentos adjuntos y modulos integrados en Cargos,
  Traslados, Finanzas e Inventario: 69 tests aprobados.
- `python manage.py check` sin issues y sin migraciones pendientes.

## Pendiente Proximo Recomendado

Siguiente bloque recomendado:

1. Validar el diseno PDF con la plantilla institucional e incorporar logotipo
   o fondo oficial cuando se entregue el archivo fuente.
2. Documentar convenciones de formularios HTMX antes de crecer pantallas con
   interacciones parciales.

No conviene iniciar vistas de modulos grandes hasta cerrar permisos y acceso por
iglesia.

## Comandos Utiles

Levantar desarrollo:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

Ver logs:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f web
```

Ejecutar migraciones:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py migrate
```

Ejecutar seed:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_inicial
```

Crear o actualizar usuarios de prueba:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py seed_usuarios_prueba
```

Normalizar superusuario tecnico:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py normalizar_superusuario --username admin
```

Validar Django:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py check
```

Validar migraciones pendientes:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python manage.py makemigrations --check --dry-run
```

## Documentos Relacionados

- [Requerimientos vigentes](requerimientos.md)
- [Arquitectura](arquitectura.md)
- [Modelo multi-iglesia](multi_iglesia.md)
- [Seed inicial](seed_inicial.md)
- [Usuarios de prueba](usuarios_prueba.md)
- [Matriz de permisos y roles](matriz_permisos_roles.md)
- [Seguridad](seguridad.md)
- [Soporte nacional auditado](soporte_nacional.md)
- [Estrategia de auditoria](auditoria.md)
- [Pendientes](pendientes.md)
- [Analisis funcional](analisis_funcional.md)
- [Estrategia general de reportes](reportes.md)
- [Documentos adjuntos](documentos_adjuntos.md)
- [Tailwind CSS](tailwind.md)

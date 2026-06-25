# Analisis Funcional De Ecclesia

Ultima actualizacion: 2026-06-24.

Este documento registra una revision funcional de Ecclesia como sistema de uso
real para una organizacion religiosa nacional con iglesias filiales.

No propone cambios tecnologicos ni implementaciones. Su objetivo es ordenar los
hallazgos funcionales para corregirlos uno por uno.

## Criterio De Revision

La revision considera:

- coherencia de los flujos operativos por modulo;
- procesos importantes aun no contemplados;
- casos de uso que pueden aparecer en una iglesia real;
- riesgos de errores operativos;
- integraciones necesarias entre modulos;
- consistencia entre reglas nacionales y filiales;
- alineacion con una organizacion religiosa nacional.

## Hallazgos Criticos

### 1. Efectos incompletos del traslado de miembros

El flujo de Traslados permite solicitar, aceptar, rechazar y anular traslados
entre iglesias filiales. Al aceptar, el miembro pasa a la iglesia destino.

Estado: corregido funcionalmente en el bloque de Traslados e integraciones.

Riesgo funcional:

- el miembro puede quedar con familia, ministerios, cargos, escuela dominical,
  responsabilidades o relaciones locales que pertenecen a la iglesia origen;
- la iglesia destino puede recibir al miembro sin un estado local claro;
- la iglesia origen puede conservar asignaciones activas que ya no deberian
  operar;
- los reportes locales podrian mezclar historial correcto con datos activos
  incoherentes.

Decision funcional pendiente:

- mantener documentada la regla de cierre en origen y activacion en destino para
  futuras integraciones.

Modulos relacionados:

- Miembros.
- Familias.
- Ministerios.
- Cargos/directivas.
- Escuela Dominical.
- Certificados.
- Documentos.
- Auditoria.

Prioridad: alta.

### 2. Registro de pagos de aportes nacionales restringido a SUPERADMIN

El modulo de Aportes nacionales permite generar aportes desde cierres mensuales
y registrar pagos con numeracion de recibos. Actualmente el registro de pago
esta documentado como accion de `SUPERADMIN`.

Estado: corregido funcionalmente en el bloque de Aportes nacionales y operacion
financiera nacional.

Riesgo funcional:

- una tarea financiera nacional recurrente depende de un rol tecnico;
- el personal administrativo nacional no podria operar pagos sin intervencion
  tecnica;
- se mezcla administracion tecnica con operacion contable.

Decision funcional pendiente:

- mantener documentada la separacion entre generacion tecnica de aportes y
  registro nacional de pagos.

Modulos relacionados:

- Aportes nacionales.
- Finanzas locales.
- Reportes.
- Auditoria.
- Usuarios y roles.

Prioridad: alta.

### 3. Falta de flujo formal para correcciones despues de cierre financiero

Finanzas locales bloquea nuevos movimientos y anulaciones dentro de meses
cerrados. La regla protege los cierres, pero no se documenta un proceso formal
para errores detectados despues del cierre.

Estado: corregido funcionalmente para cierres sin aporte nacional generado.

Riesgo funcional:

- errores de caja, comprobantes tardios o movimientos mal clasificados podrian
  no tener un tratamiento operativo claro;
- usuarios podrian intentar corregir fuera del sistema;
- los aportes nacionales podrian quedar calculados sobre cierres incorrectos;
- la auditoria podria perder trazabilidad de ajustes posteriores.

Decision funcional pendiente:

- definir en un bloque futuro el tratamiento de cierres que ya tienen aporte
  nacional generado o pagado.

Modulos relacionados:

- Finanzas locales.
- Aportes nacionales.
- Reportes financieros.
- Auditoria.
- Documentos adjuntos.

Prioridad: alta.

## Hallazgos Importantes

### 1. Relacion entre cargos eclesiasticos y accesos funcionales

La decision vigente es correcta: los cargos eclesiasticos no son roles base del
sistema. Sin embargo, falta documentar el flujo operativo cuando cambia una
autoridad o asignacion clave.

Estado: corregido funcionalmente para cargos locales que determinan rol
principal de acceso.

Casos a resolver:

- cambio de Pastor o Encargado;
- cambio de Director de Escuela Dominical;
- cambio de lider de ministerio;
- finalizacion de un cargo con usuario que aun conserva acceso;
- nuevo cargo que necesita operar una funcion ya existente.

Riesgo funcional:

- una persona puede dejar un cargo pero conservar acceso operativo;
- una autoridad nueva puede figurar como cargo pero no tener usuario o permiso;
- certificados pueden tomar firmas historicas correctas, pero el acceso actual
  puede quedar desalineado.

Regla vigente:

- las asignaciones vigentes de `Pastor`, `Encargado`, `Secretario` y `Tesorero`
  a un usuario sincronizan el rol principal de acceso;
- al finalizar una asignacion funcional, el rol se recalcula segun otros cargos
  funcionales vigentes o baja a `SOLO_LECTURA`;
- `Director de Escuela Dominical`, lideres de ministerio y maestros conservan
  su acceso por asignacion especifica del modulo, no por rol principal.

Prioridad: media-alta.

### 2. Certificados limitados a Escuela Dominical

El modulo de Certificados esta bien iniciado para promociones y egreso a
Jovenes. Sin embargo, en una iglesia real suelen emitirse otros documentos
institucionales.

Estado: corregido documentalmente en `docs/certificados.md`. La hoja funcional
institucional ya define alcance futuro, prioridades y reglas comunes, pero los
nuevos tipos documentales no estan implementados.

Casos frecuentes no documentados como implementados:

- constancia de membresia;
- certificado o constancia de bautismo;
- constancia de traslado;
- certificacion de cargo o directiva;
- constancia pastoral.

Riesgo funcional:

- usuarios podrian esperar que "Certificados" cubra documentos institucionales
  generales;
- se podrian crear soluciones paralelas fuera del sistema.

Prioridad: media.

### 3. Estrategia general de reportes pendiente

Existen reportes de traslados, finanzas e inventario. Aun esta pendiente
documentar una estrategia general de reportes.

Estado: corregido documentalmente en `docs/reportes.md`.

Aspectos a definir:

- reportes nacionales y reportes locales;
- filtros minimos estandar por filial, zona, periodo y estado;
- criterios de corte temporal;
- totales y subtotales esperados;
- exportacion o impresion cuando aplique;
- permisos de lectura por rol.

Riesgo funcional:

- cada reporte puede crecer con criterios distintos;
- la nacional puede recibir informacion no comparable entre modulos;
- la continuidad operativa se dificulta cuando aumenten los reportes.

Prioridad: media.

### 4. Inconsistencia documental sobre API de Ministerios

`estado_actual.md` indica que la API inicial incluye ministerios y
participaciones ministeriales. `pendientes.md` aun marca "pendiente API" para
Ministerios.

Estado: corregido documentalmente. La API de consulta para Ministerios y
participaciones ministeriales ya esta implementada y validada.

Riesgo funcional:

- puede confundir la planificacion del siguiente bloque;
- puede hacer que se repita trabajo ya hecho o que se omita una API incompleta.

Decision funcional pendiente:

- mantener sincronizados `estado_actual.md` y `pendientes.md` cuando cambie el
  alcance de la API.

Prioridad: media.

### 5. Ciclo de vida pastoral del miembro aun parcial

Miembros contempla listado, busqueda, detalle, creacion, edicion y acciones
pastorales iniciales como bautismo, membresia y fallecimiento.

Casos pastorales que pueden aparecer:

- baja voluntaria;
- cambio de estado de membresia;
- restauracion;
- disciplina o suspension;
- visitante o simpatizante antes de membresia;
- seguimiento pastoral historico.

Riesgo funcional:

- la membresia oficial puede no reflejar procesos pastorales reales;
- algunos cambios pueden terminar registrandose como ediciones simples, sin
  historial suficiente.

Prioridad: media.

### 6. Responsabilidades formales en inventario

Inventario maneja activos, responsable actual, movimientos, reparacion y baja.
Funcionalmente es una buena base, pero falta documentar si las entregas o bajas
requieren aprobacion o acta.

Casos posibles:

- entrega formal de activo a responsable;
- devolucion;
- baja por dano, perdida o venta;
- aprobacion pastoral o administrativa;
- documento de respaldo obligatorio en ciertos movimientos.

Riesgo funcional:

- activos pueden cambiar de responsable sin evidencia formal suficiente;
- bajas pueden quedar registradas sin soporte institucional.

Prioridad: media-baja.

### 7. Cobertura uniforme de auditoria por modulo

La auditoria esta definida para acciones criticas. Ya existen validaciones en
flujos importantes, pero conviene documentar con precision que eventos se
auditan por modulo.

Estado: corregido documentalmente en `docs/auditoria.md`.

Eventos candidatos:

- cambios de iglesia o autoridad;
- creacion y desactivacion de usuarios;
- cierres financieros;
- generacion y pago de aportes;
- emision y anulacion de certificados;
- aceptacion, rechazo o anulacion de traslados;
- baja de inventario;
- finalizacion de cargos.

Riesgo funcional:

- auditoria desigual entre modulos;
- dificultad para reconstruir responsabilidades ante revisiones nacionales.

Prioridad: media.

## Hallazgos Menores

### 1. Intervencion nacional en soporte a filiales

La regla vigente impide a `ADMIN_NACIONAL` operar modulos locales. Es una buena
separacion, pero puede requerir un procedimiento de soporte auditado cuando una
filial necesite ayuda.

Prioridad: baja.

### 2. Promocion de Escuela Dominical centrada en edad

La promocion por edad con asistencia informativa tiene sentido. Debe quedar
claro que la revision y confirmacion pastoral permite excepciones funcionales si
la organizacion las acepta.

Prioridad: baja.

### 3. Tipos de documentos adjuntos por modulo

El modelo reutilizable de documentos adjuntos es adecuado. Funcionalmente
conviene clasificar tipos documentales por modulo para mejorar busqueda y
revision.

Prioridad: baja.

### 4. Separacion entre datos de prueba y datos reales

La filial `PRUEBAS` es correcta para validacion. En operacion real debe
mantenerse claramente identificada para evitar reportes institucionales
contaminados por pruebas.

Prioridad: baja.

## Modulos Muy Bien Disenados

### Modelo multi-iglesia

La separacion por `iglesia`, roles, permisos, filtros obligatorios y auditoria
encaja bien con una organizacion nacional con filiales. Permite consolidacion
nacional sin convertir cada filial en un sistema aislado.

### Matriz de roles y permisos

La separacion entre roles de acceso y cargos eclesiasticos es funcionalmente
solida. Evita crear roles para cada cargo y permite que liderazgos concretos se
otorguen por asignacion.

### Escuela Dominical

El flujo es completo y coherente: niveles, clases, maestros, matriculas,
sesiones, asistencia, cierre, promocion, revision y egreso. Refleja un proceso
real con control local y validacion pastoral.

### Finanzas locales y aportes nacionales

La relacion entre movimientos locales, cierres mensuales, aportes calculados y
cuenta corriente nacional es una base fuerte para control financiero.

### Documentos adjuntos

El modelo reutilizable integrado con inventario, cargos, traslados y finanzas
evita duplicidad funcional y permite una base documental comun.

### Gestion delegada de usuarios

El flujo donde la nacional crea filiales con autoridad inicial y la autoridad
local administra cuentas delegables es coherente con una estructura eclesiastica
descentralizada.

### Traslados

El concepto principal esta bien planteado: solicitud, respuesta origen/destino,
documentos y auditoria. Lo pendiente es definir mejor sus efectos en modulos
relacionados.

## Recomendaciones Priorizadas

1. Definir criterios de soporte nacional auditado a filiales.
2. Clasificar tipos de documentos adjuntos por modulo.

## Orden Sugerido Para Correccion Uno A Uno

### Bloque 1: Traslados e integraciones

Objetivo: definir y luego implementar el comportamiento funcional al aceptar un
traslado.

Estado: corregido.

Resultado esperado:

- cierre de vinculos familiares activos en origen;
- desactivacion de familias donde el trasladado era jefe de hogar;
- finalizacion de cargos vigentes del miembro en origen;
- finalizacion de participaciones ministeriales activas en origen;
- retiro de matriculas activas de Escuela Dominical en origen;
- limpieza de responsable de ministerio cuando el trasladado era responsable;
- auditoria con resumen de cierres aplicados.

### Bloque 2: Aportes nacionales y operacion financiera nacional

Objetivo: definir el rol funcional que registra pagos nacionales y sus permisos.

Estado: corregido.

Resultado esperado:

- `SUPERADMIN` conserva la generacion de aportes desde cierres mensuales;
- `ADMIN_NACIONAL` puede consultar aportes nacionales y registrar pagos
  pendientes;
- filiales conservan consulta de su propia cuenta corriente sin registrar
  pagos;
- la numeracion transaccional de recibos se mantiene.

### Bloque 3: Correcciones de cierres financieros

Objetivo: definir como corregir errores despues de cerrar un mes.

Estado: corregido parcialmente para cierres sin aporte nacional generado.

Resultado esperado:

- anulacion controlada de cierres cerrados sin aporte nacional generado;
- apertura del mes para registrar o anular movimientos correctivos;
- regeneracion del cierre sobre el mismo periodo con totales recalculados;
- bloqueo de anulacion cuando ya existe aporte nacional, para no alterar cuenta
  corriente ni recibos.

### Bloque 4: Cargos, autoridades y accesos

Objetivo: alinear cambios de autoridad con accesos funcionales.

Estado: corregido para cargos locales que sincronizan rol principal.

Resultado esperado:

- asignar `Pastor`, `Encargado`, `Secretario` o `Tesorero` a un usuario ajusta
  su rol y grupo;
- finalizar una asignacion funcional recalcula el rol del usuario;
- otros cargos organizacionales permanecen como historial o como insumo de
  firmas, sin convertirse en roles base.

### Bloque 5: Documentacion de reportes y certificados

Objetivo: ordenar los siguientes crecimientos funcionales sin mezclar alcances.

Resultado esperado:

- estrategia general de reportes;
- alcance de certificados institucionales;
- criterios de prioridad por uso real.

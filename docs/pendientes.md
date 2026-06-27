# Pendientes

## Infraestructura

- [x] Integrar Tailwind compilado con Node en Docker.
- Crear scripts de backup y restore.
- Preparar Nginx para produccion.
- Definir estrategia de logs.

## Backend

- [x] Crear seed inicial de roles, cargos, parametros y zonas.
- [x] Crear iglesia nacional e iglesia filial `PRUEBAS` para validacion.
- [x] Crear mixins de filtro por iglesia.
- [x] Crear grupos Django por rol y permisos base.
- [x] Crear comando para normalizar superusuario tecnico.
- [x] Crear helpers/decoradores de permisos para vistas.
- [x] Crear login/logout y dashboard inicial minimo.
- [x] Crear serializers base y endpoints iniciales de consulta para Miembros,
  Familias y Matrimonios.
- [x] Crear API de consulta para Cargos y Ministerios.
- [x] Crear pruebas iniciales de modelos y flujos funcionales implementados.

## Modulos

- Recomendacion funcional prioritaria: antes de iniciar modulos grandes nuevos,
  cerrar ciclos administrativos ya iniciados, reforzar controles preventivos y
  automatizar seguimiento operativo.
- Miembros: [x] listado inicial; [x] creacion y edicion; [x] detalle;
  [x] bautismo, membresia y fallecimiento inicial; [x] vinculacion inicial con
  familias; [x] gestion inicial de familias; [x] desactivar vinculos y ajuste
  de jefe de hogar; [x] matrimonios; [x] ciclo pastoral ampliado con admision
  formal, baja voluntaria, restauracion, disciplina, suspension, historial,
  auditoria y cierre completo por fallecimiento; pendiente visitantes o
  simpatizantes, soporte documental pastoral y controles preventivos de
  duplicados.
- Familias y matrimonios: pendiente separacion, divorcio, viudez,
  recomposicion familiar y controles de jefatura activa.
- Cargos/directivas: [x] listado; [x] detalle; [x] creacion y edicion;
  [x] finalizacion; [x] API de consulta; [x] documentos adjuntos;
  [x] recalculo de rol funcional al finalizar desde edicion general;
  [x] flujo formal de nombramiento, posesion, renuncia y reemplazo;
  [x] cargos interinos o suplentes; [x] incompatibilidades para cargos
  sensibles; [x] documentos obligatorios para posesion de cargos sensibles;
  pendiente autoridades nacionales o regionales como asignaciones
  organizacionales y constancias de cargo.
- Ministerios: [x] listado; [x] detalle; [x] creacion y edicion;
  [x] participaciones; [x] finalizacion de participaciones; [x] API de
  consulta; pendiente responsables suplentes, ministerios temporales, informes
  periodicos y alertas de ministerios sin responsable.
- Traslados: [x] flujo origen/destino; [x] auditoria; [x] reporte inicial;
  [x] documentos adjuntos; [x] recepcion pastoral en destino; [x] checklist de
  integracion familiar y Escuela Dominical en destino; [x] vinculacion familiar
  asistida; [x] matricula asistida de Escuela Dominical; [x] traslado familiar
  completo; [x] tareas pastorales posteriores a recepcion; pendiente constancia
  de traslado.
- Finanzas: [x] conceptos; [x] ingresos; [x] egresos; [x] anulacion;
  [x] cierre mensual; [x] correccion posterior de cierres sin aporte nacional;
  [x] correccion posterior de cierres con aporte nacional pendiente anulado;
  [x] reporte consolidado; [x] documentos adjuntos; pendiente presupuesto,
  cajas o cuentas bancarias, conciliacion y aprobacion de egresos.
- Aportes nacionales: [x] generacion desde cierre mensual; [x] calculo por
  porcentaje; [x] consulta por filial; [x] registro de pago; [x] numeracion de
  recibos; [x] recibos PDF; [x] cuenta corriente detallada; [x] anulacion de
  aportes pendientes para correccion de cierre; [x] regeneracion de aporte
  anulado; [x] ajustes autorizados sobre aportes pagados; [x] pagos parciales;
  [x] acuerdos de pago; [x] identificacion de mora por vencimiento; [x] tablero
  de pendientes y morosidad consolidada.
- Certificados: [x] numeracion, [x] emision individual y por lote,
  [x] PDF de Escuela Dominical, [x] anulacion, [x] validacion de firmantes antes
  de reservar secuencial, [x] hoja funcional de certificados institucionales;
  pendiente reimpresion controlada, vista previa obligatoria, validar el fondo y
  logotipo institucional, e implementar otros tipos documentales.
- Inventario: [x] activos; [x] historial de ubicacion, responsable, reparacion
  y baja; [x] documentos adjuntos; [x] reportes; pendiente inventario fisico
  periodico, actas de entrega/devolucion y aprobaciones de baja segun
  `docs/inventario.md`; quedan como crecimiento posterior perdida, robo, venta,
  garantias y mantenimiento preventivo avanzado.
- Documentos adjuntos: [x] base reutilizable; [x] integracion en inventario,
  finanzas, traslados y cargos; [x] clasificacion de tipos por modulo;
  pendiente vigencia documental, versionamiento, sensibilidad, vista previa y
  deteccion de duplicados.
- Escuela Dominical: [x] niveles, [x] clases y matriculas, [x] sesiones y
  asistencia, [x] corte y promocion, [x] certificados por cada nivel y egreso,
  [x] control de una sola matricula activa por alumno y periodo; pendiente
  inscripcion masiva, retiro durante el anio, cambio de clase, suplencias,
  control de sesiones pendientes, ausentismo y reportes pedagogicos.
- Reportes: pendiente reportes locales operativos, exportaciones oficiales,
  programacion de reportes, comparativos historicos y tablero de alertas.
- Auditoria: pendiente interfaz de revision, severidad de eventos, seguimiento
  de hallazgos, auditoria de lectura sensible y resumen periodico de eventos
  criticos.

## Documentacion

- [x] Completar matriz funcional inicial de permisos.
- [x] Documentar convenciones de formularios HTMX.
- [x] Reporte financiero consolidado inicial.
- [x] Documentar estrategia general de reportes.
- [x] Documentar estrategia de auditoria por modulo.
- [x] Documentar criterios de soporte nacional auditado a filiales.
- [x] Clasificar tipos de documentos adjuntos por modulo.

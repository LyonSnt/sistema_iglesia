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

- Miembros: [x] listado inicial; [x] creacion y edicion; [x] detalle;
  [x] bautismo, membresia y fallecimiento inicial; [x] vinculacion inicial con
  familias; [x] gestion inicial de familias; [x] desactivar vinculos y ajuste
  de jefe de hogar; [x] matrimonios.
- Cargos/directivas: [x] listado; [x] detalle; [x] creacion y edicion;
  [x] finalizacion; [x] API de consulta; pendiente documentos adjuntos.
- Ministerios: [x] listado; [x] detalle; [x] creacion y edicion;
  [x] participaciones; [x] finalizacion de participaciones; pendiente API.
- Traslados: flujo origen, destino y auditoria nacional.
- Finanzas: ingresos, egresos y cierre mensual.
- Aportes nacionales: cuenta corriente filial-nacional.
- Certificados: [x] numeracion, [x] emision individual y por lote,
  [x] PDF de Escuela Dominical, [x] anulacion; pendiente validar el fondo y
  logotipo institucional, y desarrollar otros tipos documentales.
- Inventario: historial de ubicacion, responsable y reparacion.
- Escuela Dominical: [x] niveles, [x] clases y matriculas, [x] sesiones y
  asistencia, [x] corte y promocion, [x] certificados por cada nivel y egreso.

## Documentacion

- [x] Completar matriz funcional inicial de permisos.
- Documentar convenciones de formularios HTMX.
- Documentar estrategia de reportes.

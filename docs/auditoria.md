# Estrategia De Auditoria

Ultima actualizacion: 2026-06-24.

## Objetivo

La auditoria de Ecclesia debe permitir reconstruir acciones sensibles sin
convertir todos los cambios ordinarios en ruido operativo.

La auditoria debe responder:

- quien realizo la accion;
- sobre que iglesia;
- que registro fue afectado;
- que cambio ocurrio;
- cuando ocurrio;
- desde donde, si existe IP;
- por que motivo, cuando aplique.

## Estado Actual

Actualmente existen:

- modelo `RegistroAuditoria`;
- auditoria automatica cuando un usuario nacional interviene datos de una
  filial;
- auditoria de administracion delegada de cuentas locales;
- auditoria explicita del flujo de traslados;
- pruebas que validan intervencion nacional sobre filiales y ausencia de
  auditoria nacional en la gestion propia de una filial.

## Principios

- No almacenar contrasenas ni hashes.
- No registrar cambios sin usuario autenticado salvo procesos internos
  documentados.
- Registrar auditoria explicita en acciones criticas, aunque ya existan datos
  historicos del modulo.
- Evitar duplicar auditoria para acciones de lectura normal.
- Mantener `valor_anterior` y `valor_nuevo` cuando el cambio sea modificacion
  de estado o datos criticos.
- Usar `motivo` cuando la accion implique decision humana.

## Cobertura Esperada Por Modulo

### Iglesias y zonas

Auditar:

- creacion de filial;
- edicion de datos de filial;
- desactivacion o reactivacion;
- cambio de zona;
- cambio de responsable principal.

Datos minimos:

- usuario;
- iglesia afectada;
- valores antes y despues;
- IP cuando exista.

Estado:

- cubierto por auditoria automatica de intervencion nacional sobre filiales.

### Usuarios y roles

Auditar:

- creacion de autoridad inicial;
- creacion de cuenta local delegada;
- cambio de rol;
- cambio de iglesia;
- desactivacion o reactivacion;
- restablecimiento de contrasena temporal.

Datos minimos:

- usuario ejecutor;
- usuario afectado;
- iglesia;
- rol anterior y nuevo cuando cambie;
- indicador de contrasena modificada, sin almacenar contrasena ni hash.

Estado:

- cubierto parcialmente por auditoria automatica para administracion delegada.

### Miembros y familias

Auditar:

- intervencion nacional sobre datos de filial;
- fallecimiento;
- cambios pastorales sensibles;
- desactivacion o reactivacion de vinculos familiares;
- cambio de jefe de hogar.

Datos minimos:

- miembro o familia afectada;
- iglesia;
- estado anterior y nuevo;
- motivo cuando exista.

Estado:

- intervencion nacional cubierta; eventos pastorales locales deben evaluarse
  antes de implementar auditoria adicional.

### Cargos y directivas

Auditar:

- creacion de asignacion;
- finalizacion;
- anulacion;
- cambio de cargo funcional que sincroniza rol;
- documentos adjuntos sensibles.

Datos minimos:

- cargo;
- persona o usuario asignado;
- fecha inicio;
- fecha fin;
- rol anterior y nuevo cuando se sincronice acceso.

Estado:

- requiere cobertura explicita adicional para sincronizacion de acceso si se
  desea trazabilidad completa.

### Ministerios

Auditar:

- creacion o edicion de ministerio;
- cambio de lider;
- cambio de responsable;
- finalizacion de participacion.

Datos minimos:

- ministerio;
- miembro o usuario afectado;
- iglesia;
- fechas y estado.

Estado:

- intervencion nacional cubierta; gestion local ordinaria no se audita de forma
  explicita.

### Soporte Nacional A Filiales

Auditar:

- intervencion nacional sobre datos de una filial;
- correccion de inconsistencias entre filiales;
- desbloqueo administrativo validado por autoridad nacional;
- intervencion tecnica excepcional de `SUPERADMIN`;
- reemplazo o normalizacion de autoridad principal cuando afecte accesos.

Datos minimos:

- iglesia filial afectada;
- modulo y registros afectados;
- usuario solicitante;
- usuario aprobador cuando aplique;
- usuario ejecutor;
- motivo;
- accion realizada;
- estado anterior y nuevo cuando sea posible;
- documentos de soporte si existen.

Estado:

- criterios funcionales documentados en `docs/soporte_nacional.md`; pendiente
  de implementacion solo si se habilitan permisos o pantallas especificas para
  soporte nacional directo.

### Escuela Dominical

Auditar:

- cierre o correccion de sesiones;
- confirmacion de promociones;
- cambios masivos por promocion;
- asignacion o cambio de maestro.

Datos minimos:

- clase;
- periodo;
- proceso de promocion;
- usuario que confirma o corrige;
- conteos cuando sea operacion masiva.

Estado:

- pendiente de definir si la auditoria sera explicita o por historial propio de
  los modelos.

### Certificados

Auditar:

- emision individual;
- emision por lote;
- anulacion;
- fallo por falta de firmantes no necesita auditoria si no consume numeracion.

Datos minimos:

- certificado;
- numero;
- alumno o sujeto certificado;
- usuario emisor;
- usuario anulador;
- motivo de anulacion.

Estado:

- el modelo conserva emision y anulacion; auditoria explicita puede agregarse si
  se requiere supervision nacional centralizada.

### Traslados

Auditar:

- solicitud;
- aceptacion;
- rechazo;
- anulacion;
- cierres automaticos en origen al aceptar.

Datos minimos:

- miembro;
- iglesia origen;
- iglesia destino;
- estado anterior y nuevo;
- usuario que responde;
- resumen de cierres locales aplicados.

Estado:

- cubierto con auditoria explicita.

### Finanzas locales

Auditar:

- creacion de movimientos;
- anulacion de movimientos;
- generacion de cierres;
- anulacion de cierres para correccion;
- regeneracion de cierres corregidos;
- documentos adjuntos financieros.

Datos minimos:

- movimiento o cierre;
- montos;
- periodo;
- estado anterior y nuevo;
- motivo de anulacion o correccion.

Estado:

- el flujo funcional existe; auditoria explicita adicional debe priorizarse por
  criticidad financiera.

### Aportes nacionales

Auditar:

- generacion de aporte;
- registro de pago;
- numeracion de recibo;
- anulacion futura si se implementa.

Datos minimos:

- cierre origen;
- filial;
- monto base;
- porcentaje;
- monto aporte;
- numero de recibo;
- usuario que registra pago.

Estado:

- el modelo conserva usuario generador y usuario registrador de pago; auditoria
  explicita puede agregarse para supervision financiera nacional.

### Inventario

Auditar:

- alta de activo;
- cambio de responsable;
- cambio de ubicacion;
- reparacion;
- baja;
- documentos adjuntos relevantes.

Datos minimos:

- activo;
- responsable anterior y nuevo;
- ubicacion anterior y nueva;
- estado;
- motivo o detalle.

Estado:

- el modulo conserva historial de movimientos; auditoria explicita puede
  limitarse a bajas y cambios sensibles.

### Documentos adjuntos

Auditar:

- carga de documentos sensibles;
- anulacion de documentos;
- reemplazo de soportes.

Datos minimos:

- modulo origen;
- registro afectado;
- tipo de documento;
- usuario;
- motivo de anulacion.

Estado:

- el modelo conserva usuario de carga y anulacion; auditoria explicita puede
  agregarse para documentos financieros, traslados y cargos.

## Acciones Normalizadas

Usar nombres simples y consistentes:

- `CREAR`;
- `MODIFICAR`;
- `ANULAR`;
- `FINALIZAR`;
- `SOLICITAR`;
- `ACEPTAR`;
- `RECHAZAR`;
- `REGISTRAR_PAGO`;
- `GENERAR`;
- `CONFIRMAR`;
- `CORREGIR`;
- `BAJA`.

## Prioridad Recomendada

1. Finanzas locales y cierres.
2. Aportes nacionales y recibos.
3. Cargos funcionales que sincronizan acceso.
4. Certificados emitidos o anulados.
5. Escuela Dominical en promociones y correcciones.
6. Inventario en bajas y cambios de responsable.
7. Documentos adjuntos sensibles.

## Regla De No Auditoria

No se deben auditar lecturas comunes, busquedas, filtros o navegacion normal.

Tampoco conviene auditar cada edicion menor de catalogos locales si el modulo ya
tiene historial suficiente y el cambio no afecta acceso, dinero, documentos,
estado pastoral o supervision nacional.

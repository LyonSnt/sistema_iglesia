# Analisis Funcional De Ecclesia

Ultima actualizacion: 2026-06-25.

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

Estado: corregido funcionalmente para cierres sin aporte nacional generado y
para cierres con aporte nacional pendiente, siempre que el aporte se anule
formalmente antes de abrir el cierre. Para aportes ya pagados con recibo, la
correccion se registra como ajuste formal por cargo o abono, sin modificar el
recibo original.

Riesgo funcional:

- errores de caja, comprobantes tardios o movimientos mal clasificados podrian
  no tener un tratamiento operativo claro;
- usuarios podrian intentar corregir fuera del sistema;
- los aportes nacionales podrian quedar calculados sobre cierres incorrectos;
- la auditoria podria perder trazabilidad de ajustes posteriores.

Decision funcional vigente:

- no alterar recibos ya emitidos;
- registrar diferencias posteriores mediante ajustes autorizados de cargo o
  abono en la cuenta corriente.

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
principal de acceso. Tambien queda cubierto el caso en que una asignacion
funcional se marca como finalizada desde la edicion general, porque el rol del
usuario se recalcula contra sus otros cargos funcionales vigentes.

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
  funcionales vigentes o baja a `SOLO_LECTURA`, tanto desde el flujo especifico
  de finalizacion como desde la edicion general;
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

Estado: corregido funcionalmente para admision formal, baja voluntaria,
restauracion, disciplina, suspension, historial pastoral, auditoria y cierre
completo por fallecimiento.

Casos pastorales que quedan como crecimiento futuro:

- visitantes o simpatizantes antes de membresia;
- soporte documental pastoral obligatorio segun tipo de accion;
- seguimiento pastoral periodico o tareas de acompanamiento;
- reportes pastorales por estado y periodo.

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

Estado: documentado en `docs/soporte_nacional.md`.

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

Estado: corregido y documentado en `docs/documentos_adjuntos.md`.

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
evita duplicidad funcional y permite una base documental comun. La clasificacion
por modulo reduce errores operativos al impedir tipos documentales incoherentes
con el proceso asociado.

### Gestion delegada de usuarios

El flujo donde la nacional crea filiales con autoridad inicial y la autoridad
local administra cuentas delegables es coherente con una estructura eclesiastica
descentralizada.

### Traslados

El concepto principal esta bien planteado: solicitud, respuesta origen/destino,
documentos, auditoria y cierre de relaciones operativas en origen al aceptar.

## Revision Funcional Por Modulo

Esta revision se realizo sobre el estado implementado al 2026-06-25. La
recomendacion general es no iniciar modulos grandes nuevos hasta cerrar ciclos
administrativos incompletos, reforzar controles y automatizar tareas repetitivas
en los modulos ya existentes.

### Multi-Iglesia, Roles Y Alcance

Sentido funcional: alto. La separacion por `iglesia`, roles, permisos y filtros
obligatorios permite supervision nacional sin mezclar la operacion local.

Procesos faltantes:

- flujo operativo completo para soporte nacional excepcional;
- revision periodica de accesos especiales;
- manejo de usuarios con responsabilidad temporal en mas de una filial.

Casos no contemplados:

- pastor o encargado que atiende dos filiales;
- apoyo regional temporal;
- intervencion nacional solo por una ventana de tiempo.

Errores posibles:

- asignar usuario a una iglesia incorrecta;
- confundir cargo eclesiastico con rol de sistema;
- operar datos de una filial desde una sesion nacional sin advertirlo.

Controles recomendados:

- alerta visual cuando un usuario nacional consulta o gestiona datos de una
  filial;
- motivo obligatorio y ventana de vigencia para soporte nacional;
- reporte de accesos funcionales vigentes por filial.

Automatizaciones recomendadas:

- revision programada de cuentas inactivas, cargos vencidos y permisos
  funcionales heredados.

### Filiales

Sentido funcional: alto. Crear filial, autoridad inicial y acceso temporal en
una misma operacion reduce altas incompletas.

Procesos faltantes:

- apertura institucional aprobada;
- cierre, fusion, reactivacion o cambio de zona de una filial;
- checklist de preparacion operativa de una nueva filial.

Casos no contemplados:

- filial sin autoridad titular;
- cambio de nombre;
- fusion de dos filiales con miembros, inventario y saldos.

Errores posibles:

- crear filiales duplicadas;
- asignar autoridad inicial equivocada;
- desactivar una filial con procesos abiertos.

Controles recomendados:

- validacion de codigo/nombre unico;
- motivo obligatorio para desactivacion;
- bloqueo o advertencia si existen miembros, activos, cierres o aportes
  pendientes.

Automatizaciones recomendadas:

- checklist automatico de alta: autoridad, usuarios minimos, periodo,
  conceptos financieros base, niveles de Escuela Dominical y parametros.

### Usuarios

Sentido funcional: alto. La gestion delegada por nacional/local y el cambio
obligatorio de contrasena temporal son coherentes.

Procesos faltantes:

- baja formal por salida de cargo;
- suspension temporal;
- recuperacion de cuenta sin crear duplicados.

Casos no contemplados:

- usuario que cambia de iglesia;
- usuario con dos funciones simultaneas;
- cuenta local que queda activa despues de finalizar una asignacion.

Errores posibles:

- crear una segunda cuenta para la misma persona;
- asignar un rol excesivo;
- olvidar desactivar cuentas antiguas.

Controles recomendados:

- deteccion de duplicados por identificacion o correo;
- caducidad de contrasenas temporales;
- revision de permisos efectivos.

Automatizaciones recomendadas:

- degradar o retirar permisos cuando finaliza el cargo o asignacion que los
  justificaba.

### Miembros

Sentido funcional: alto. Listado, busqueda, detalle, creacion, edicion y
acciones pastorales ampliadas cubren la base de membresia.

Estado: el ciclo pastoral ampliado registra bautismo, admision formal, baja
voluntaria, restauracion, disciplina, suspension y fallecimiento. Cada evento
conserva historial pastoral con motivo, usuario, estado anterior/nuevo y
auditoria. El fallecimiento cierra relaciones locales activas del miembro.

Procesos faltantes:

- bautismo u otras acciones con soporte documental obligatorio;
- visitantes o simpatizantes antes de membresia;
- seguimiento pastoral periodico.

Casos no contemplados:

- visitantes o simpatizantes;
- menores sin representante;
- miembros sin identificacion;
- duplicados entre filiales.

Errores posibles:

- duplicar miembros;
- editar datos historicos como si fueran actuales;
- registrar estado de membresia incorrecto sin revisar historial.

Controles recomendados:

- busqueda preventiva de duplicados antes de crear;
- documentos obligatorios para acciones pastorales sensibles;
- motivo obligatorio para cambios pastorales.

Automatizaciones recomendadas:

- alertas de datos incompletos, cumpleanos, miembros sin familia y miembros sin
  actividad reciente.

### Familias Y Matrimonios

Sentido funcional: alto. Los vinculos desactivables sin borrar historial son
adecuados para la realidad pastoral.

Procesos faltantes:

- separacion, divorcio, viudez y recomposicion familiar;
- cambio formal de jefe de hogar.

Casos no contemplados:

- tutores legales;
- hogares extendidos;
- matrimonios donde solo una persona es miembro;
- conyuges de distintas filiales.

Errores posibles:

- duplicar familias;
- dejar dos jefes de hogar activos;
- vincular miembros a la familia equivocada.

Controles recomendados:

- una sola jefatura activa;
- advertencia si un miembro ya pertenece a otra familia activa;
- motivo al desactivar vinculos.

Automatizaciones recomendadas:

- sugerir creacion o actualizacion de familia al registrar matrimonio;
- sugerir revision familiar cuando se traslada un jefe de hogar.

### Cargos Y Directivas

Sentido funcional: alto. Modelar cargos como asignaciones y no como roles base
es una decision solida.

Estado: corregido funcionalmente para nombramiento, posesion, renuncia,
reemplazo, cargos titulares/interinos/suplentes, historial formal, auditoria,
incompatibilidades para cargos sensibles y documentos obligatorios de posesion
cuando el cargo lo requiere.

Procesos faltantes:

- autoridades nacionales o regionales como asignaciones organizacionales;
- constancias de cargo generadas desde la asignacion;
- alertas de vencimiento de cargos.

Casos no contemplados:

- autoridades nacionales o regionales como asignaciones organizacionales.

Errores posibles:

- no finalizar una asignacion previa;
- asignar cargos solapados;
- otorgar acceso funcional a quien no corresponde.

Controles recomendados:

- ampliar matriz de incompatibilidades si se definen cargos incompatibles por
  reglamento interno;
- revisar periodicamente cargos sensibles nombrados o vigentes.

Automatizaciones recomendadas:

- alertas de vencimiento;
- recalculo periodico de accesos;
- constancias de cargo generadas desde la asignacion.

### Ministerios

Sentido funcional: medio-alto. La base de ministerios, responsables y
participaciones esta bien iniciada.

Procesos faltantes:

- planificacion de actividades;
- responsables suplentes;
- informes periodicos;
- presupuesto o necesidades del ministerio.

Casos no contemplados:

- ministerios temporales;
- ministerios compartidos entre filiales;
- equipos con funciones internas.

Errores posibles:

- dejar ministerios sin responsable;
- olvidar finalizar participaciones;
- confundir lider con participante.

Controles recomendados:

- responsable vigente obligatorio;
- historial de liderazgo;
- motivo al finalizar participacion.

Automatizaciones recomendadas:

- alertas de ministerios sin responsable y reportes de integrantes activos.

### Escuela Dominical

Sentido funcional: alto. Es un flujo completo: niveles, clases, matriculas,
asistencia, cierre, promocion, revision y egreso.

Estado: corregido el control preventivo de doble matricula activa. Un alumno no
puede tener dos matriculas activas en la misma iglesia y periodo, aunque sean
clases diferentes.

Procesos faltantes:

- inscripcion inicial masiva;
- retiro durante el anio;
- cambio de clase;
- suplencias de maestros;
- reportes pedagogicos.

Casos no contemplados:

- alumnos visitantes;
- alumnos que repiten por criterio pastoral;
- necesidades especiales;
- asistencia parcial.

Errores posibles:

- matricular en nivel incorrecto;
- intentar matricular dos veces al mismo alumno en el mismo periodo;
- cerrar sesiones incompletas;
- olvidar confirmar promociones;
- superar cupo sin justificacion.

Controles recomendados:

- advertencia por edad fuera de rango;
- justificacion para cupo excedido;
- control de sesiones pendientes antes del cierre anual.

Automatizaciones recomendadas:

- matricula sugerida por edad;
- alertas de ausentismo;
- reportes por clase, maestro y periodo.

### Certificados

Sentido funcional: alto. Numeracion transaccional, firmas historicas, emision
por lote y anulacion sin reutilizar numero son controles correctos.

Estado: corregido el orden funcional de emision. Los firmantes vigentes se
validan antes de reservar el secuencial, evitando consumir numeracion cuando no
existen firmas requeridas.

Procesos faltantes:

- reimpresion controlada;
- duplicado oficial;
- correccion por error de datos;
- plantillas por tipo institucional.

Casos no contemplados:

- solicitud por terceros;
- cambio de firmantes despues de emitir;
- certificados institucionales distintos de Escuela Dominical.

Errores posibles:

- emitir con datos desactualizados;
- generar un lote equivocado;
- anular cuando corresponde corregir el dato fuente.

Controles recomendados:

- vista previa obligatoria;
- motivo de anulacion;
- marca de reimpresion;
- bloqueo si faltan firmantes vigentes.

Automatizaciones recomendadas:

- emision sugerida tras promocion confirmada;
- listado de certificados pendientes;
- catalogo futuro para membresia, bautismo, traslado, cargo y constancia
  pastoral.

### Traslados

Sentido funcional: alto. El cierre de relaciones locales en origen al aceptar
un traslado evita inconsistencias importantes.

Estado: recepcion pastoral en destino implementada para traslados aceptados,
con observacion, permisos por iglesia destino, filtro de pendientes y auditoria.
Tambien existe checklist de integracion en destino para revision familiar y
revision de Escuela Dominical cuando aplica, con filtros y auditoria. El
checklist permite vincular al miembro a una familia existente del destino y
matricularlo en una clase existente de Escuela Dominical del destino. El
traslado familiar completo permite seleccionar integrantes adicionales de la
familia origen, moverlos a destino al aceptar y cerrar sus relaciones locales
activas en origen. La recepcion en destino genera tareas pastorales de
seguimiento, que pueden crearse, completarse y auditarse.

Procesos faltantes:

- integracion a ministerios en destino;
- constancia de traslado.

Casos no contemplados:

- traslado temporal;
- retorno a iglesia de origen;
- traslado con pendientes financieros, documentales o pastorales.

Errores posibles:

- solicitar traslado al destino equivocado;
- aceptar sin revisar documentos;
- trasladar una persona cuando debia trasladarse la familia.

Controles recomendados:

- confirmacion reforzada antes de aceptar;
- resumen de relaciones que se cerraran;
- documentos obligatorios segun tipo de traslado.

Automatizaciones recomendadas:

- generar certificado o constancia de traslado.

### Finanzas Locales

Sentido funcional: alto. Movimientos, conceptos, adjuntos, anulaciones y cierres
mensuales congelados son una base administrativa fuerte.

Procesos faltantes:

- presupuesto;
- cajas o cuentas bancarias;
- conciliacion bancaria;
- aprobacion de egresos;
- arqueos.

Casos no contemplados:

- pagos parciales;
- transferencias entre cajas;
- donaciones con destino especifico;
- comprobantes tardios.

Errores posibles:

- registrar ingreso como egreso;
- usar concepto incorrecto;
- cerrar el mes antes de revisar;
- intentar corregir fuera del sistema.

Controles recomendados:

- numeracion de comprobantes locales;
- doble aprobacion para egresos altos;
- motivo obligatorio de anulacion;
- validacion fuerte contra meses cerrados.

Automatizaciones recomendadas:

- alertas de cierre pendiente;
- resumen mensual automatico;
- conciliacion asistida en un bloque futuro.

### Aportes Nacionales

Sentido funcional: alto. Generar aportes desde cierres congelados protege la
cuenta corriente nacional.

Procesos faltantes:

- exoneraciones aprobadas.

Casos no contemplados:

- pago agrupado de varios meses;
- reverso de pago;
- cambio de porcentaje nacional;
- aplicacion de un abono como compensacion contra periodos futuros.

Errores posibles:

- registrar pago al aporte incorrecto;
- generar aporte antes de revisar el cierre;
- confundir saldo local con saldo nacional.

Controles recomendados:

- soporte obligatorio de pago;
- registro de pagos parciales sin emitir recibo final hasta cubrir el saldo;
- acuerdos de pago vigentes sobre aportes pendientes;
- identificacion de mora por fecha de vencimiento;
- tablero consolidado de pendientes y morosidad;
- autorizacion para ajustes;
- anulacion formal del aporte pendiente antes de abrir el cierre origen;
- ajuste por cargo o abono cuando el aporte ya fue pagado con recibo.

Automatizaciones recomendadas:

- alertas de vencimiento;
- estado de cuenta automatico por filial;
- tablero nacional de morosidad.

### Inventario

Sentido funcional: alto. Activos por iglesia, codigo unico, responsable,
ubicacion, movimientos y baja logica cubren el control basico.

Estado documental: el siguiente bloque esta definido en `docs/inventario.md`,
con alcance para inventario fisico periodico, actas de entrega/devolucion y
aprobaciones de baja.

Procesos faltantes:

- inventario fisico periodico;
- acta de entrega y devolucion;
- aprobaciones de baja;
- mantenimiento preventivo avanzado;
- tratamiento completo de perdida, robo o venta.

Casos no contemplados:

- activos compartidos;
- prestamos entre filiales;
- garantias;
- seguros;
- activos sin valor conocido.

Errores posibles:

- duplicar codigos;
- cambiar ubicacion sin soporte;
- dar de baja sin autorizacion;
- asignar responsable incorrecto.

Controles recomendados:

- acta obligatoria para baja;
- aprobacion para activos de alto valor;
- historial no editable;
- conteo fisico con diferencias.

Automatizaciones recomendadas:

- alertas de mantenimiento, garantias e inventario anual pendiente.

### Documentos Adjuntos

Sentido funcional: alto. El modelo reusable con validacion por modulo reduce
duplicidad y errores.

Procesos faltantes:

- vigencia documental;
- versionamiento;
- revision o aprobacion;
- clasificacion de sensibilidad.

Casos no contemplados:

- documentos vencidos;
- reemplazos;
- duplicados;
- documentos mas sensibles que el registro padre.

Errores posibles:

- subir documentos al registro equivocado;
- seleccionar tipo documental incorrecto;
- conservar archivos ilegibles.

Controles recomendados:

- vista previa;
- descripcion obligatoria;
- motivo de anulacion;
- deteccion de duplicados.

Automatizaciones recomendadas:

- alertas de vencimiento;
- checklist documental por proceso.

### Reportes

Sentido funcional: medio-alto. Los reportes nacionales de traslados, finanzas e
inventario responden a necesidades reales de supervision.

Procesos faltantes:

- reportes locales operativos;
- exportacion oficial;
- programacion de reportes;
- reportes comparativos.

Casos no contemplados:

- membresia por estado, edad y filial;
- asistencia de Escuela Dominical;
- cargos vencidos;
- auditoria por filial;
- ministerios activos.

Errores posibles:

- comparar meses abiertos con cerrados;
- interpretar datos preliminares como oficiales;
- olvidar filtros aplicados.

Controles recomendados:

- mostrar fecha de generacion, filtros y estado de cierre;
- distinguir reportes preliminares de oficiales;
- totales calculados sobre todo el conjunto filtrado.

Automatizaciones recomendadas:

- envio mensual a autoridades;
- exportacion PDF/Excel;
- tablero nacional con alertas.

### Auditoria

Sentido funcional: alto. La auditoria es indispensable para soporte nacional,
finanzas, traslados, documentos y cambios de autoridad.

Procesos faltantes:

- interfaz de revision;
- severidad de eventos;
- seguimiento y cierre de hallazgos;
- auditoria de lectura para informacion sensible.

Casos no contemplados:

- descargas de documentos sensibles;
- consultas nacionales sin modificacion;
- cambios masivos;
- accesos fallidos relevantes.

Errores posibles:

- no revisar auditoria periodicamente;
- confundir auditoria tecnica con revision administrativa;
- no cerrar hallazgos detectados.

Controles recomendados:

- filtros por modulo, usuario, filial y fecha;
- exportacion protegida;
- retencion minima;
- alertas ante eventos criticos.

Automatizaciones recomendadas:

- resumen semanal de eventos criticos;
- alertas por intervencion nacional;
- deteccion de patrones inusuales.

### Infraestructura Y Operacion

Sentido funcional: medio-alto. Docker, PostgreSQL, Redis, Celery, healthcheck,
seeds y validaciones dan buena base de operacion.

Procesos faltantes:

- backups y restauracion probada;
- monitoreo;
- revision de logs;
- respuesta a incidentes;
- verificacion de tareas Celery.

Casos no contemplados:

- perdida de archivos `media`;
- falla de generacion PDF;
- caida de tareas programadas;
- restauracion parcial por filial.

Errores posibles:

- operar sin respaldo probado;
- no detectar procesos automaticos fallidos;
- mezclar datos de desarrollo y produccion.

Controles recomendados:

- backups automaticos con prueba de restauracion;
- logs centralizados;
- estado visible de servicios criticos;
- separacion clara entre ambientes.

Automatizaciones recomendadas:

- alertas de servicios caidos;
- verificacion programada de integridad;
- pruebas periodicas de restauracion.

## Recomendaciones Priorizadas

### Prioridad 1: cerrar ciclos administrativos existentes

Antes de crear modulos grandes nuevos, conviene completar los procesos que ya
empezaron y que hoy dependen de pasos manuales o decisiones fuera del sistema:

- cierre familiar completo cuando hay cambio de jefe de hogar;
- inventario fisico, actas y aprobaciones de baja.

### Prioridad 2: reforzar controles preventivos

Los modulos ya implementados deben ayudar a evitar errores de captura y
operacion:

- busqueda preventiva de duplicados;
- motivos obligatorios en anulaciones y cambios sensibles;
- documentos obligatorios en procesos criticos;
- advertencias por acciones inter-iglesia;
- validaciones de solapamiento en cargos, familias y participaciones;
- distincion entre datos preliminares y datos oficiales cerrados.

### Prioridad 3: automatizar seguimiento operativo

El sistema debe reducir tareas manuales recurrentes:

- alertas de cargos, documentos y garantias por vencer;
- reportes mensuales automaticos;
- tareas de integracion en destino tras confirmar recepcion;
- revision de cuentas inactivas;
- recordatorios de cierre financiero y aporte pendiente;
- resumen semanal de auditoria critica.

### Prioridad 4: mantener mejoras visuales y documentales

Quedan como mejoras necesarias, pero no deben desplazar los cierres de proceso:

- validar diseno PDF con plantilla institucional y logotipo oficial;
- aplicar las convenciones HTMX documentadas antes de crecer pantallas con
  interacciones parciales;
- mantener sincronizados `estado_actual.md`, `pendientes.md` y este documento.

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
- auditoria con resumen de cierres aplicados;
- traslado familiar con integrantes adicionales;
- tareas pastorales posteriores a recepcion.

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

Estado: corregido para cierres sin aporte nacional generado y para cierres con
aporte nacional pendiente anulado previamente. Los aportes ya pagados con recibo
se corrigen mediante ajustes formales de cargo o abono.

Resultado esperado:

- anulacion controlada de cierres cerrados sin aporte nacional generado;
- anulacion controlada de aportes pendientes para permitir correccion del cierre
  origen;
- apertura del mes para registrar o anular movimientos correctivos;
- regeneracion del cierre sobre el mismo periodo con totales recalculados;
- regeneracion del aporte anulado con los nuevos totales del cierre;
- ajuste formal de cargo o abono cuando el aporte ya fue pagado, para no alterar
  recibos emitidos.

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

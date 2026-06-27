# Inventario Fisico, Actas Y Aprobaciones

Ultima actualizacion: 2026-06-27.

## Objetivo

Cerrar el ciclo administrativo de inventario ya iniciado, agregando controles
para verificacion fisica, entregas, devoluciones y bajas aprobadas.

El modulo actual ya registra activos, movimientos, documentos adjuntos, historial
y baja logica. El siguiente bloque debe reforzar evidencia, aprobacion y
seguimiento operativo sin crear un modulo nuevo separado.

## Alcance Del Siguiente Bloque

### Inventario fisico periodico

Debe permitir registrar conteos o revisiones fisicas por iglesia filial.

Datos minimos:

- iglesia;
- fecha de inventario;
- usuario responsable;
- estado del proceso;
- observacion general;
- activos revisados;
- resultado por activo: encontrado, no encontrado, con diferencia o pendiente;
- observacion por activo.

Reglas:

- un inventario fisico pertenece a una sola iglesia;
- usuarios de filial solo revisan activos de su iglesia;
- no debe modificar automaticamente responsable, ubicacion o estado del activo;
- las diferencias deben quedar registradas para revision posterior;
- el cierre del inventario debe congelar sus resultados.

### Actas de entrega y devolucion

Debe formalizar movimientos de responsable o ubicacion cuando exista entrega o
devolucion.

Datos minimos:

- activo;
- responsable anterior y nuevo cuando aplique;
- ubicacion anterior y nueva cuando aplique;
- tipo de acta: entrega o devolucion;
- fecha;
- usuario que registra;
- observacion;
- documento adjunto tipo `Acta` cuando sea requerido.

Reglas:

- no reemplaza el historial de movimientos; lo complementa;
- el acta debe quedar vinculada al activo o movimiento;
- el cambio operativo debe conservar el antes y despues;
- documentos adjuntos deben respetar los tipos permitidos de Inventario.

### Aprobaciones de baja

La baja de activos debe pasar de una accion directa a un flujo controlado para
casos sensibles.

Flujo recomendado:

1. Solicitud de baja con motivo.
2. Revision por autoridad autorizada.
3. Aprobacion o rechazo.
4. Si se aprueba, baja logica del activo.
5. Registro de auditoria y documento de soporte cuando aplique.

Datos minimos:

- activo;
- motivo de baja;
- tipo de baja: dano, perdida, robo, venta, donacion, obsolescencia u otro;
- usuario solicitante;
- usuario aprobador;
- fecha de solicitud;
- fecha de aprobacion o rechazo;
- estado;
- observacion;
- documento de respaldo cuando aplique.

Reglas:

- activos de alto valor deben requerir aprobacion antes de baja;
- la baja aprobada no elimina fisicamente el activo;
- una baja rechazada conserva historial;
- no se debe permitir baja directa si el activo requiere aprobacion;
- la aprobacion debe auditarse.

## Permisos

Gestion local:

- `SUPERADMIN`;
- `PASTOR_FILIAL`;
- `ENCARGADO_FILIAL`;
- `TESORERO_FILIAL`.

Lectura:

- roles con lectura permitida por la matriz funcional vigente.

Reglas:

- usuarios de filial solo ven activos e inventarios de su iglesia;
- `ADMIN_NACIONAL` supervisa por reportes, no opera inventario local ordinario;
- cualquier soporte nacional directo debe seguir `docs/soporte_nacional.md`.

## Auditoria

Auditar explicitamente:

- cierre de inventario fisico;
- diferencias relevantes;
- solicitud, aprobacion, rechazo y ejecucion de baja;
- cambio de responsable con acta;
- anulacion de documentos sensibles.

Datos minimos:

- activo o inventario afectado;
- iglesia;
- usuario;
- accion;
- estado anterior y nuevo;
- motivo;
- fecha;
- documento asociado cuando exista.

## Reportes Y Seguimiento

El bloque debe preparar informacion para:

- activos con diferencias de inventario;
- bajas solicitadas, aprobadas o rechazadas;
- activos sin responsable;
- activos sin ubicacion clara;
- garantias o mantenimientos futuros.

No es obligatorio implementar todos estos reportes en el primer bloque, pero los
modelos y estados deben permitirlos.

## Fuera De Alcance Inicial

Quedan para bloques posteriores:

- prestamos entre filiales;
- seguros;
- depreciacion contable;
- ventas con flujo financiero completo;
- mantenimiento preventivo avanzado;
- alertas automaticas por garantia o mantenimiento.

## Criterios De Validacion

El bloque debe validarse con pruebas de:

- permisos y aislamiento por iglesia;
- creacion y cierre de inventario fisico;
- registro de diferencias;
- actas de entrega/devolucion;
- solicitud y aprobacion o rechazo de baja;
- bloqueo de baja directa cuando requiere aprobacion;
- documentos adjuntos permitidos;
- auditoria de acciones sensibles;
- `python manage.py check`;
- `python manage.py makemigrations --check --dry-run`.

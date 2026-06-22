# Corte y Promocion de Escuela Dominical

## Distributivo

| Nivel | Edad durante el ciclo |
| --- | --- |
| 1 | 1 a 3 anos |
| 2 | 4 a 6 anos |
| 3 | 7 a 9 anos |
| 4 | 10 a 12 anos |
| 5 | 13 a 17 anos despues del corte |

El nivel 5 se describe institucionalmente como 13 a 18 anos porque un alumno
puede cumplir 18 despues del corte y permanece matriculado hasta la graduacion
del enero siguiente.

## Regla de corte

- La graduacion se realiza una vez al ano, en enero.
- El corte es una fecha completa y exacta, por ejemplo `2027-01-10`.
- La edad se calcula en esa fecha.
- Un cumpleanos ocurrido exactamente el dia del corte se considera cumplido.
- Un cumpleanos posterior al corte se considera en la graduacion del siguiente ano.
- La promocion depende de la edad; asistencia y calificaciones no la bloquean.
- La asistencia cerrada se muestra como informacion para la revision.

## Transiciones

- Al cumplir 4 anos al corte: nivel 1 a nivel 2.
- Al cumplir 7 anos al corte: nivel 2 a nivel 3.
- Al cumplir 10 anos al corte: nivel 3 a nivel 4.
- Al cumplir 13 anos al corte: nivel 4 a nivel 5.
- Al cumplir 18 anos al corte: egreso de Escuela Dominical hacia Jovenes.

Las edades se obtienen de los rangos configurados por iglesia: la promocion
interna usa la edad minima del nivel siguiente y el egreso usa la edad maxima
del ultimo nivel.

## Flujo de confirmacion

1. Pastor, encargado o `SUPERADMIN` prepara el proceso con iglesia, periodo
   origen, periodo destino y fecha de corte.
2. El sistema calcula los candidatos y muestra edad, asistencia y destino.
3. Para promociones internas se selecciona una clase del nivel y periodo
   destino con cupo disponible.
4. La autoridad confirma el lote.
5. La matricula origen se marca como promovida y se crea la matricula destino.
6. Para el egreso a Jovenes solo se cierra la matricula; no se crea otro registro.

Cada resultado confirmado, incluido el egreso a Jovenes, queda disponible para
la emision posterior de un certificado. La confirmacion de la promocion no
emite documentos automaticamente.

La confirmacion es transaccional y conserva usuario y fecha. Un maestro puede
operar sus clases y asistencias, pero no confirmar promociones.

# Bitácora TDD y BDD — HU-02

## Alcance y criterio de evidencia

HU-02 permite cancelar una reservación propia vigente con más de 60 minutos de anticipación, conservarla en el historial y liberar el horario. Este documento toma como base `08fdc26` y registra los 29 commits posteriores hasta `77d75c3`. Los mensajes de Git identifican la intención y el resultado declarado de cada cambio; no sustituyen una salida de prueba. No se incluyen pruebas de carga con JMeter.

## Ciclos en el historial

| Prueba o cambio | RED / prueba en Git | GREEN o continuación en Git | Lectura del historial |
|---|---|---|---|
| UT-13: cancelación propia vigente | `7ad9504` | `c11e1d5` | Prueba declarada fallida; implementación mínima declarada exitosa. |
| UT-14: propiedad | `09fee34` | `bd82fd9` | Prueba declarada fallida; validación del propietario declarada exitosa. |
| UT-15: exactamente 60 minutos | `c8bf03c` | `1d4e0d8` | Prueba declarada fallida; límite estricto declarado exitoso. |
| UT-16: menos de 60 minutos | `5025df5` | — | Prueba declarada exitosa al incorporarse; no se documenta un RED nuevo. |
| UT-17: segunda cancelación | `356eaa0` | `1c8c9fb` | Prueba declarada fallida; rechazo declarado exitoso. |
| UT-20: reutilizar el horario | `9c52603` | — | Prueba declarada exitosa al incorporarse. |
| Reservación inexistente | `2be3c6e` | `cd0b419` | Prueba declarada fallida; rechazo declarado exitoso. |
| Refactor del servicio | — | `602b8f4` | Centraliza anticipación y protege la actualización; el commit declara pruebas exitosas. |
| UT-18: acceso anónimo | `0ab90cc` | `edfa7f1` | Prueba declarada fallida; vista y URL declaradas exitosas. |
| UT-19: cancelación ajena manipulada | `98ef68e` | — | Prueba declarada exitosa al incorporarse. |
| POST y CSRF | `3c39b1e` | — | Pruebas declaradas exitosas al incorporarse. |
| Acción de cancelar e historial | `6e30c74` | `b83ebc6` | Pruebas declaradas fallidas; interfaz declarada exitosa. |
| Visibilidad e historial | `d5b6486` | — | Pruebas declaradas exitosas al incorporarse. |

### Aceptación y cierre técnico

- CA-07: feature en `b32ac49` y pasos declarados exitosos en `4726d0b`.
- CA-08 a CA-11: `77b32ce`, `c0fa31b`, `25606c8` y `ba97ce2`, respectivamente; sus mensajes declaran los escenarios exitosos, sin demostrar por sí solos una regresión final completa.
- `67e2c3c`: configuración de flake8 y ajuste de prueba. `ef3a0ed`: casos de medianoche y sala inexistente para CA-09, y configuración de cobertura. `77d75c3`: README de HU-02 y su verificación.

## Resultados observados y reportados

- **UT-13:** la corrida completa de MariaDB del usuario mostró 91 pruebas descubiertas y un `ImportError` por la ausencia de `cancelar_reservacion`; al resolverse, la suite mostró **101 pruebas, OK**. El log `logs/01_UT13_RED.log` de V2 es una corrida separada en SQLite.
- **UT-14 RED:** la salida de MariaDB mostró **103 pruebas y dos fallos**: no se lanzó `ValidationError` y una reservación ajena cambió a `CANCELADA` en vez de quedar `VIGENTE`.
- **Regresión SQLite:** la verificación local ejecutó **132 pruebas sin concurrencia**, con cobertura de **227/227 sentencias**. No sustituye a la suite completa en MariaDB.
- **Regresión MariaDB:** `python -m coverage run manage.py test` ejecutó **133 pruebas en 19.311 s, OK**, incluida la prueba de concurrencia de HU-01. `python -m coverage report -m` reportó **227 sentencias, 0 sin cubrir, 100 %**. `makemigrations --check --dry-run` indicó `No changes detected`.
- **Regresión Behave en Docker/MariaDB:** **18 escenarios aprobados, 1 fallido**; 178 pasos aprobados, 1 fallido y 9 omitidos. Pasaron los 14 escenarios de HU-01, incluido el de concurrencia, y CA-07, CA-08, CA-10 y CA-11. CA-09 se detuvo antes de abrir el navegador: `sudo -n` no pudo ejecutar el comando de datos (`sudo: a password is required`).
- **Repetición de CA-09:** `sudo -v && HEADLESS=1 behave -f plain -n CA-09` aprobó **1 escenario y 10 pasos** en 23.391 s. Los otros 18 escenarios quedaron omitidos por el filtro. En conjunto, quedaron verificados **los 19 escenarios y sus 188 pasos en dos corridas**, no en una sola corrida verde.
- **Calidad:** flake8 terminó sin hallazgos y Radon midió una complejidad máxima de 7 por función o método. Los reportes están en `reportes/flake8.txt` y `reportes/radon_cc.txt` de V2.
- **CA-07:** el ODT contiene la salida de terminal de una corrida con 11 pasos aprobados, correspondiente al escenario antes de que se añadiera un paso de captura explícito.
- **Capturas:** se verificó la existencia de siete PNG en `~/Salvada/Investigacion/Testing/Evidencia_HU02_TDD_V2/capturas/`: dos de CA-07, dos de CA-08 y una de cada uno de CA-09, CA-10 y CA-11.

## Evidencia externa

El ODT del usuario `~/Salvada/pruebas.odt` y las capturas V2 se conservan fuera de Git.

Los comandos reproducibles y las precauciones están en `README.md` y en [Demo_HU02.md](Demo_HU02.md). Los escenarios por interfaz pueden dejar reservaciones de prueba en la base de aceptación.

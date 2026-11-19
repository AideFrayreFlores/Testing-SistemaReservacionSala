# Resultados de rendimiento: MariaDB local

Corridas del 18 de noviembre de 2026, reportadas por el usuario para Django
local con MariaDB. Las métricas siguientes proceden de los JTL y reportes
guardados; no son una nueva ejecución. Los planes, criterios y preparación
están en [README.md](README.md). La evidencia externa está en
`~/Salvada/Investigacion/Testing/Evidencia_JMeter/` (en adelante, `EVIDENCIA`),
fuera del repositorio.

## Métricas observadas

Promedio, p90, p95 y throughput provienen de `reportes/PERF-0N/statistics.json`
de JMeter; tiempos en milisegundos y throughput en muestras/segundo.

| Escenario y alcance | Muestras | Promedio | p90 | p95 HTML | Throughput | Errores |
|---|---:|---:|---:|---:|---:|---:|
| PERF-01, consultas medidas | 250 | 8.44 | 10 | 11.45 | 8.60 | 0 (0 %) |
| PERF-02, POST medidos | 90 | 47.44 | 49 | 49.45 | 3.12 | 0 (0 %) |
| PERF-03, **total integral**, incluidos auxiliares | 44 | 33.57 | 50 | 350 | 43.22 | 0 (0 %) |

Los dashboards de PERF-01 y PERF-02 usan JTL filtrados por su etiqueta;
el de PERF-03 usa el JTL completo: 20 POST, 20 GET de formulario y cuatro
peticiones de login. Por ello sus métricas totales **no son métricas de los
20 POST** ni directamente comparables con las otras filas. El rechazo por
traslape esperado en PERF-03 se clasifica como éxito funcional, no como error.
El throughput depende de la ventana y del patrón de carga de cada reporte;
no representa capacidad máxima demostrada.

Para aceptación, `reportes/PERF-01.txt` y `PERF-02.txt` usan p95 por
**rango más cercano**: 11 y 49 ms, respectivamente, frente a 11.45 y
49.45 ms del HTML de JMeter, calculados con otra convención de percentil.
El evaluador confirma para PERF-01 250 muestras, errores < 1 % y p95
≤ 1500 ms; para PERF-02, 90 muestras, errores < 1 % y p95 ≤ 2000 ms:
ambos **cumplen**. En PERF-03 no se establece umbral de latencia; el criterio
es funcional y de persistencia.

## Concurrencia y auditoría

`reportes/PERF-03.txt` verifica 10 rondas, cada una con dos POST para el
mismo horario: una aceptación HTTP 302 y un rechazo esperado HTTP 200,
ambos con `success=true`. En total son **20 POST, 10 aceptaciones y 10
rechazos esperados**, sin errores inesperados en los auxiliares.

La salida SQL guardada en `logs/04_perf03_mariadb_20261118_225523.sql.txt`
(también en `reportes/PERF-03-auditoria.txt`) muestra **una fila vigente por
ronda** para el 14–23 de septiembre de 2027 y **cero pares vigentes
traslapados en toda la base** al auditarla. El JTL acredita respuestas; la
salida SQL aporta la comprobación de persistencia, no una auditoría nueva.

## Fuentes y entrega

Rutas relativas a `EVIDENCIA`:

| Escenario | JTL original y log | Evaluación / HTML |
|---|---|---|
| PERF-01 | `logs/02_perf01_mariadb_20261118_221922.jtl` y `.log` del mismo nombre | `reportes/PERF-01.txt`, `reportes/PERF-01.jtl`, `reportes/PERF-01/index.html` |
| PERF-02 | `logs/03_perf02_mariadb_20261118_224037.jtl` y `.log` del mismo nombre | `reportes/PERF-02.txt`, `reportes/PERF-02.jtl`, `reportes/PERF-02/index.html` |
| PERF-03 | `logs/04_perf03_mariadb_20261118_225523.jtl`, `.log` y `.sql.txt` del mismo nombre | `reportes/PERF-03.txt`, `reportes/PERF-03-auditoria.txt`, `reportes/PERF-03/index.html` |

El paquete local `EVIDENCIA/Evidencia_JMeter.zip` contiene el índice, los
JTL originales, las evaluaciones TXT, la auditoría SQL y las carpetas
completas de los tres dashboards. Los logs de ejecución quedan aparte.
Extrae el ZIP entero antes de abrir cada `reportes/PERF-0N/index.html` en
un navegador: cada dashboard necesita sus recursos.

## Regenerar desde los JTL guardados

Desde la raíz del repositorio, con Python 3, JMeter 5.6.3 y Java 21
instalados. Se crea una carpeta temporal nueva; no se toca la evidencia
original ni se vuelve a ejecutar carga contra el servidor:

```bash
export EVIDENCIA="$HOME/Salvada/Investigacion/Testing/Evidencia_JMeter"
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
SALIDA=$(mktemp -d /tmp/opencode/jmeter-reportes-XXXXXX)
python3 pruebas_rendimiento/evaluar_jtl.py \
  --jtl "$EVIDENCIA/logs/02_perf01_mariadb_20261118_221922.jtl" \
  --jtl-filtrado "$SALIDA/PERF-01.jtl"
python3 pruebas_rendimiento/evaluar_jtl.py \
  --jtl "$EVIDENCIA/logs/03_perf02_mariadb_20261118_224037.jtl" \
  --etiqueta '^PERF-02' --min-muestras 90 --p95 2000 \
  --escenario PERF-02 --jtl-filtrado "$SALIDA/PERF-02.jtl"
python3 pruebas_rendimiento/verificar_perf03.py \
  --jtl "$EVIDENCIA/logs/04_perf03_mariadb_20261118_225523.jtl"
jmeter -g "$SALIDA/PERF-01.jtl" -o "$SALIDA/PERF-01"
jmeter -g "$SALIDA/PERF-02.jtl" -o "$SALIDA/PERF-02"
jmeter -g "$EVIDENCIA/logs/04_perf03_mariadb_20261118_225523.jtl" \
  -o "$SALIDA/PERF-03"
printf 'Reportes: %s\n' "$SALIDA"
```

La auditoría SQL de solo lectura y sus requisitos están en la sección
«Cruzar con la base de datos» del [README](README.md); repetirla consulta el
estado actual, que podría haber cambiado, y requiere `FECHA_BASE=2027-09-14`.

## Alcance y límites

Son corridas locales puntuales con los patrones y datos de los planes; no
establecen rendimiento de producción, capacidad máxima ni comportamiento
bajo otras cargas. Los GET auxiliares de PERF-02 generan carga aunque no
entren en sus KPI. No se identificó ni midió un cuello de botella; cualquier
hipótesis sobre consultas, bloqueos o servidor requiere instrumentación
adicional. No se confirmó aquí la configuración efectiva del entorno ni la
cantidad de reservas iniciales de PERF-01.

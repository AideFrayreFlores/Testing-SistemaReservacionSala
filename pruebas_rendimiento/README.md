# Pruebas de rendimiento (JMeter)

Planes de **Apache JMeter 5.6.3** para el Sistema de Reservación de Salas,
ejecutados **solo contra el Django local** (sin destinos remotos y sin
pruebas ofensivas). Cubren:

- **Commit 1/5 — humo de login:** autenticación real contra el formulario
  de Django (CSRF + sesión). No mide carga ni forma parte de PERF-01.
- **Commit 2/5 — PERF-01:** consulta del listado de reservaciones después
  de autenticar, con 50 usuarios virtuales, subida gradual de 30 s y 5
  consultas por usuario (250 muestras medidas).

El resto de PERF (registro sin conflicto y concurrencia) no está
implementado en este README.

## Requisitos

- **Apache JMeter 5.6.3** en el equipo que ejecuta las pruebas. Versión
  fijada para que el resultado sea reproducible; no se instala desde este
  repo y no se requieren plugins.
- **Java 17 o 21**. Usa `/usr/lib/jvm/java-21-openjdk` (verificado con
  OpenJDK 21.0.13). JMeter 5.6.3 trae Groovy 3, que no carga clases de
  Java 25 y aborta con `Unsupported class file major version 69`; no
  ejecutes los planes con el JVM del sistema si es más nuevo que 21.
- **Python 3.11+** únicamente para el evaluador de JTL
  (`evaluar_jtl.py`, solo biblioteca estándar).
- Servidor Django **local** ya levantado, sobre una base **aislada y
  migrada**, de modo que existan los usuarios iniciales de
  `usuarios/migrations/0001_usuarios_iniciales.py` (`alumno1`).
- La medición de PERF-01 debe hacerse sobre la instancia con MariaDB
  (Docker Compose del proyecto). SQLite sirve **solo** para el humo
  funcional del plan: con 50 hilos concurrentes SQLite responde
  `database is locked` y el resultado no representa a la aplicación.

## Archivos

```text
pruebas_rendimiento/
├── README.md                                 # este documento
├── evaluar_jtl.py                            # evaluación de umbrales
└── jmeter/
    ├── plan_humo_login.jmx                   # commit 1/5 (1 hilo, 1 vuelta)
    ├── plan_perf01_consulta_reservaciones.jmx # commit 2/5 (PERF-01)
    ├── usuarios_smoke.csv                    # usuario del humo
    └── usuarios_perf01.csv                   # usuario de PERF-01
```

`*.jtl`, `jmeter.log` y `reporte*/` están en `.gitignore`: los resultados
se generan y se guardan fuera de Git (por ejemplo en `/tmp/opencode/`).

## Usuarios sintéticos

Ambos CSV contienen **solo un nombre de usuario ya existente** creado por
la migración inicial; no se crean cuentas nuevas (ni 50 ni ninguna):

```csv
usuario
alumno1
```

En PERF-01 los 50 hilos usan ese mismo usuario, pero cada hilo tiene su
**propia sesión**: el `HTTP Cookie Manager` está configurado con
`controlledByThreadGroup=true`, así que cada hilo mantiene su propio
`sessionid`/`csrftoken` y hace su propio login (una vez) con el formulario
real. Esto es autenticación legítima y no depende de compartir cookies
entre hilos.

El CSV tiene una sola fila y el plan lo recicla (`recycle=true`,
`shareMode=all`), por lo que todos los hilos leen `alumno1`. Para usar otro
usuario local, edita `usuarios_perf01.csv` y exporta su clave en
`JMETER_CLAVE`; el `.jmx` no se toca.

La contraseña **no** está en el repositorio: se lee de la variable de
entorno `JMETER_CLAVE` en tiempo de ejecución.

## Datos de consulta (recomendado antes de medir)

El listado renderiza una fila por reservación del usuario. Con un usuario
sin reservaciones la vista solo pinta el estado vacío y el tiempo medido
no representa una consulta con filas. Antes de la medición, siembra datos
deterministas en la instancia de prueba (10 reservaciones de `alumno1`) y
**anota cuántas usaste** en el reporte de resultados:

```bash
docker compose exec app python manage.py shell -c "
from datetime import date, time, timedelta
from django.contrib.auth.models import User
from salas.models import Sala
from reservaciones.models import Reservacion
usuario = User.objects.get(username='alumno1')
sala, _ = Sala.objects.get_or_create(
    nombre='Sala PERF-01',
    defaults={'capacidad': 10, 'ubicacion': 'Edificio A'},
)
inicio = date.today() + timedelta(days=30)
for i in range(10):
    Reservacion.objects.get_or_create(
        usuario=usuario, sala=sala,
        fecha=inicio + timedelta(days=i),
        hora_inicio=time(9, 0), hora_fin=time(10, 0),
        defaults={'asistentes': 5, 'proposito': 'Datos sinteticos PERF-01'},
    )
print('reservaciones de alumno1:', Reservacion.objects.filter(usuario=usuario).count())
"
```

Es idempotente (`get_or_create`); repetirlo no duplica filas. No modifica
código de la aplicación: usa el ORM desde `manage.py shell`.

---

## Plan 1/5: humo de login

`plan_humo_login.jmx`: 1 hilo, 1 iteración, sin scheduler. Verifica que un
usuario sintético puede iniciar sesión con el formulario real de Django y
que la sesión sigue válida al pedir `/reservaciones/`.

| # | Petición | Qué comprueba |
|---|---|---|
| 01 | `GET /usuarios/login` | HTTP 200 y `name="csrfmiddlewaretoken"` en el HTML; el token se extrae a `CSRF_TOKEN`. |
| 02 | `POST /usuarios/login` | HTTP **302** y `Location` con `/reservaciones/`. |
| 03 | `GET /reservaciones/` | HTTP 200, `<title>Mis reservaciones</title>` y `id="btn-logout"`. |

No es PERF-01: el paso 03 solo comprueba sesión, no se mide ni se exige
ningún tiempo.

Ejecución (desde la carpeta del plan, porque los CSV se resuelven por ruta
relativa al directorio de trabajo):

```bash
cd pruebas_rendimiento/jmeter
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
read -rs JMETER_CLAVE
export JMETER_CLAVE
jmeter -n -t plan_humo_login.jmx \
  -l /tmp/opencode/jmeter-humo-login.jtl \
  -j /tmp/opencode/jmeter-humo-login.log
unset JMETER_CLAVE
```

Resultado esperado en consola: `summary = 3`, `Err: 0` (una muestra por
petición). `-Jpuerto=8016` (opcional) usa otro puerto del mismo equipo.

## Plan 2/5: PERF-01 (consulta de reservaciones)

`plan_perf01_consulta_reservaciones.jmx` implementa el escenario del
enunciado:

| Parámetro | Default de examen | Override CLI |
|---|---|---|
| Hilos (usuarios virtuales) | 50 | `-Jusuarios=1` |
| Subida gradual (ramp) | 30 s | `-Jramp=1` |
| Consultas por usuario | 5 | `-Jiteraciones=5` |
| Puerto | 8000 | `-Jpuerto=8016` |

Con los defaults se esperan **250 muestras medidas** (50 × 5). La rampa de
30 s reparte el arranque (≈1.7 hilos/s), de modo que el login inicial de
cada hilo no ocurre todo en el mismo instante.

### Estructura del plan

1. `HTTP Request Defaults`: `http://${HOST}:${PORT}`, timeouts de conexión
   5 s y de respuesta 15 s.
2. `CSV Data Set Config`: `usuarios_perf01.csv` → `${usuario}`.
3. `HTTP Cookie Manager`: sesión independiente por hilo.
4. `Once Only Controller` — **login una sola vez por hilo, fuera de los
   KPI**: `GET /usuarios/login` (extrae CSRF, exige 200 y el token) y
   `POST /usuarios/login` (exige 302 y `Location` con `/reservaciones/`).
5. `Loop Controller` (5 iteraciones) — **la medición**: `GET
   /reservaciones/` con aserción de página autenticada.

### Etiquetas discriminables

| Etiqueta en el JTL | Muestras | ¿Cuenta en los KPI? |
|---|---|---|
| `00 login GET /usuarios/login (no medido)` | 50 | No |
| `00 login POST /usuarios/login (no medido)` | 50 | No |
| `PERF-01 GET /reservaciones/ (consulta medida)` | 250 | **Sí** |

El evaluador filtra por la etiqueta `^PERF-01`, así que el login (coste de
hashing de contraseña, escritura de sesión) no contamina el conteo ni los
percentiles. No se usa `Transaction Controller` para no duplicar muestras.

### Aserción de página autenticada

Cada consulta medida exige HTTP 200, `<title>Mis reservaciones</title>` y
`id="btn-logout"`. Si la sesión del hilo se perdiera, Django redirige al
login (200 con el formulario) y la aserción la marca como **fallida**, no
como consulta válida. El plan **no** incluye `Duration Assertion`: así la
tasa de errores mide fallos funcionales y el criterio de latencia se
evalúa aparte (ver más abajo). Un timeout de 15 s sí cuenta como error y
sigue siendo visible porque 15 s > 1500 ms.

### Comandos

Humo funcional del plan (SQLite local, puerto 8016, 1 hilo × 5 vueltas =
5 consultas). Sirve para comprobar CSRF, sesión, etiquetas y aserciones;
**no** es la medición de examen:

```bash
cd pruebas_rendimiento/jmeter
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
read -rs JMETER_CLAVE
export JMETER_CLAVE
jmeter -n -t plan_perf01_consulta_reservaciones.jmx \
  -Jusuarios=1 -Jramp=1 -Jiteraciones=5 -Jpuerto=8016 \
  -l /tmp/opencode/perf01-humo.jtl \
  -j /tmp/opencode/perf01-humo.log
unset JMETER_CLAVE
```

Esperado en consola: `summary = 7` (2 login + 5 consultas), `Err: 0`.

Medición de PERF-01 con los defaults (Django local sobre MariaDB, puerto
8000; ajusta `-Jpuerto` si tu instancia usa otro):

```bash
cd pruebas_rendimiento/jmeter
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
read -rs JMETER_CLAVE
export JMETER_CLAVE
jmeter -n -t plan_perf01_consulta_reservaciones.jmx \
  -l /tmp/opencode/perf01.jtl \
  -j /tmp/opencode/perf01.log
unset JMETER_CLAVE
```

Esperado en consola: `summary = 350`, `Err: 0`; la duración ronda los
35–60 s (30 s de rampa + consultas). Los `00 login …` deben ser 100 y los
`PERF-01 …` 250. `-l` debe apuntar a un archivo que **no exista**: JMeter
añade líneas a un JTL previo.

### Semántica del percentil y criterios

El criterio del enunciado es "percentil 95 <= 1500 ms" sobre las consultas
medidas. Definición usada (y única válida para aceptar la prueba):

- Se ordenan los `elapsed` de las 250 muestras medidas, **incluidas las
  fallidas**, igual que el reporte agregado de JMeter.
- Percentil por **rango más cercano**: el valor reportado es un tiempo
  realmente observado, el menor `elapsed` tal que al menos el 95 % de las
  muestras son menores o iguales a él. Con 250 muestras el índice 1-based
  es `ceil(0.95 × 250) = 238`.
- JMeter puede diferir en una muestra por su redondeo interno; el valor
  de aceptación es el que imprime `evaluar_jtl.py`, y su fórmula está
  documentada en el propio script.

| Criterio | Umbral | Cómo se verifica |
|---|---|---|
| Volumen suficiente | ≥ 250 muestras medidas | `evaluar_jtl.py` |
| Tasa de errores | < 1 % (estricto) | `evaluar_jtl.py` |
| Percentil 95 | ≤ 1500 ms | `evaluar_jtl.py` |
| Página autenticada | 200 + título + botón de logout | aserciones del `.jmx` |

El mínimo de 250 muestras evita declarar "CUMPLE" con una corrida
incompleta: si un hilo aborta o el plan se corta, el evaluador falla
aunque el p95 sea bajo.

### Evaluación

```bash
cd pruebas_rendimiento
python3 evaluar_jtl.py --jtl /tmp/opencode/perf01.jtl
```

Salida esperada (valores ilustrativos):

```text
JTL evaluado: /tmp/opencode/perf01.jtl
Etiqueta:     ^PERF-01
Muestras:     250
Errores:      0 (0.00 %)
Tiempos (ms): p50=180 p90=420 p95=610 max=900
Criterios:
  [CUMPLE] muestras medidas >= 250 (observado: 250)
  [CUMPLE] tasa de errores < 1 % (observado: 0.00 %)
  [CUMPLE] percentil 95 <= 1500 ms (observado: 610 ms)
Resultado PERF-01: CUMPLE
```

- Código de salida `0` = cumple; `1` = algún criterio falla; `2` = JTL
  ilegible o sin muestras de la etiqueta.
- Para el humo 1×5 (5 muestras) usa `--min-muestras 5`; los demás
  umbrales siguen aplicando.
- Opciones: `--etiqueta`, `--min-muestras`, `--max-errores`, `--p95`,
  `--jtl-filtrado`. `python3 evaluar_jtl.py --help` lista todo.
- `--jtl-filtrado` escribe un JTL solo con las muestras medidas, útil
  para que el reporte HTML no mezcle el login.

### Reporte HTML

JMeter exige un directorio de salida **inexistente o vacío**:

```bash
cd pruebas_rendimiento/jmeter
jmeter -g /tmp/opencode/perf01-filtrado.jtl \
  -o /tmp/opencode/perf01-reporte
```

Genera antes `perf01-filtrado.jtl` con:

```bash
python3 evaluar_jtl.py --jtl /tmp/opencode/perf01.jtl \
  --jtl-filtrado /tmp/opencode/perf01-filtrado.jtl
```

En el reporte, la tabla de etiquetas debe mostrar una sola fila
`PERF-01 GET /reservaciones/ (consulta medida)` con 250 muestras. Si se
genera desde el JTL completo, la tabla incluye además los `00 login …`;
en ese caso cita el p95 por etiqueta, no el total del plan.

### Interpretación esperada y cuello de botella a revisar

- Este plan mide **el stack servido**: Django + base + servidor de
  aplicación. Un p95 alto con `alumno1` sin datos apunta a sobrecarga del
  servidor; con 10 reservaciones sembradas apunta además al renderizado.
- `reservaciones/views.py::listar_reservaciones` recorre el queryset y
  accede a `r.sala.nombre` sin `select_related('sala')`: con N filas se
  emiten N+1 consultas. Es el primer sospechoso si el p95 crece al sembrar
  datos; **no se corrige aquí** (este commit solo agrega el plan) y debe
  confirmarse con `connection.queries` o `django-debug-toolbar` antes de
  afirmarlo en el reporte.
- `DEBUG=True` en `settings.py` añade trabajo por petición; se mide tal
  como está desplegada la instancia de prueba y se declara esa condición
  en el reporte.
- El contenedor `app` sirve con Apache + mod_wsgi. Si el MPM atiende
  menos peticiones que los 50 hilos, la latencia incluye cola del
  servidor: repórtalo como hallazgo, no subas hilos para "mejorar" el
  número.

## Riesgos y límites

- Las aserciones dependen de textos del template (`Mis reservaciones`,
  `id="btn-logout"`). Un rediseño de la vista obliga a actualizar ambos
  planes.
- Requiere servidor y base **aislados** ya migrados; si `alumno1` no
  existe o la clave no coincide, el login no redirige y las consultas
  medidas fallan de forma explícita (no hay falso positivo).
- El login de cada hilo crea 50 sesiones del mismo usuario en
  `django_session`. Es el comportamiento legítimo de 50 clientes
  concurrentes; no se reutilizan cookies entre hilos.
- No se valida concurrencia de reservaciones ni reglas de negocio: eso
  pertenece a PERF-02/PERF-03.
- HTTP plano en localhost. Con cookies `Secure` o HTTPS, el Cookie Manager
  no reenviaría `csrftoken`/`sessionid`.
- SQLite no soporta 50 escritores concurrentes (login/sesiones): úsalo
  solo con `-Jusuarios=1`.
- Los defaults 50/30/5 se resuelven en tiempo de ejecución desde variables
  del plan que leen `-J`; el mismo patrón anidado está confirmado para
  `${PORT}` por el JTL del humo previo (`localhost:8016`), pero este plan
  no se ejecutó en el entorno de autoría. Comprueba en la primera corrida
  que la consola diga `summary = 7` (humo) o `350` (medición).
- Los números del README son ilustrativos. Los resultados reales deben
  generarse en la instancia del equipo y adjuntarse como evidencia.

## Verificación realizada

Validación **estática**, sin ejecutar JMeter contra un servidor:

```bash
xmllint --noout \
  pruebas_rendimiento/jmeter/plan_perf01_consulta_reservaciones.jmx
python3 -m py_compile pruebas_rendimiento/evaluar_jtl.py
flake8 pruebas_rendimiento/evaluar_jtl.py
radon cc pruebas_rendimiento/evaluar_jtl.py -s
```

- El `.jmx` pasa `xmllint` y se revisó su árbol con un recorrido de XML:
  `Once Only` contiene solo los dos login, el `Loop Controller` contiene
  solo la consulta medida y el `Thread Group` toma
  `${USUARIOS}`/`${RAMP}`/`${ITERACIONES}`, con defaults 50/30/5.
- `flake8` sin hallazgos y `radon` con complejidad máxima 9 (≤ 10).
- El evaluador se probó con JTL sintéticos (no versionados): 250 muestras
  que cumplen, 250 con 1.2 % de errores, 250 con p95 de 2237 ms y 5
  muestras. Devolvió `0` solo en el caso que cumple, `1` en los tres que
  deben fallar y `2` con un JTL inexistente o sin la etiqueta. También se
  leyó el JTL de la corrida de humo previa, que no se versiona.

Los planes **no** se ejecutaron al crear este commit (JMeter no está
instalado en el entorno de autoría): la corrida de humo y la medición las
realiza quien tenga JMeter y el servidor local.

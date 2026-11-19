# Pruebas de rendimiento (JMeter)

Planes de **Apache JMeter 5.6.3** para el Sistema de Reservación de Salas,
ejecutados **solo contra el Django local** (sin destinos remotos y sin
pruebas ofensivas). Cubren:

- **Commit 1/5 — humo de login:** autenticación real contra el formulario
  de Django (CSRF + sesión). No mide carga ni forma parte de PERF-01.
- **Commit 2/5 — PERF-01:** consulta del listado de reservaciones después
  de autenticar, con 50 usuarios virtuales, subida gradual de 30 s y 5
  consultas por usuario (250 muestras medidas).
- **Commit 3/5 — PERF-02:** registro de reservaciones sin conflicto, con
  30 usuarios virtuales, subida gradual de 30 s y 3 registros por usuario
  (90 muestras medidas) sobre 90 slots únicos del dataset.

El plan de **PERF-03** (concurrencia sobre el mismo slot) se documenta en
la sección del commit 4/5, más abajo.

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
- La medición de PERF-01 (50 hilos) y PERF-02 (30 hilos) debe hacerse
  sobre la instancia con MariaDB (Docker Compose del proyecto). SQLite
  sirve **solo** para el humo funcional de los planes: con decenas de
  hilos concurrentes responde `database is locked` y el resultado no
  representa a la aplicación.
- Para PERF-02, la base debe tener las salas 1, 2 y 3 activas (IDs de la
  migración inicial) y los 90 slots de la fecha base libres; revisa el
  plan 3/5 antes de medir.

## Archivos

```text
pruebas_rendimiento/
├── README.md                                 # este documento
├── evaluar_jtl.py                            # evaluación de umbrales
└── jmeter/
    ├── plan_humo_login.jmx                   # commit 1/5 (1 hilo, 1 vuelta)
    ├── plan_perf01_consulta_reservaciones.jmx # commit 2/5 (PERF-01)
    ├── plan_perf02_registro_reservaciones.jmx # commit 3/5 (PERF-02)
    ├── usuarios_smoke.csv                    # usuario del humo
    ├── usuarios_perf01.csv                   # usuario de PERF-01
    ├── usuarios_perf02.csv                   # usuario de PERF-02
    └── reservas_perf02.csv                   # 90 slots únicos de PERF-02
```

`*.jtl`, `jmeter.log` y `reporte*/` están en `.gitignore`: los resultados
se generan y se guardan fuera de Git (por ejemplo en `/tmp/opencode/`).

## Usuarios sintéticos

Los tres CSV de usuarios contienen **solo un nombre de usuario ya
existente** creado por la migración inicial; no se crean cuentas nuevas
(ni 50 ni ninguna):

```csv
usuario
alumno1
```

En PERF-01 los 50 hilos y en PERF-02 los 30 hilos usan ese mismo usuario,
pero cada hilo tiene su **propia sesión**: el `HTTP Cookie Manager` está
configurado con `controlledByThreadGroup=true`, así que cada hilo mantiene
su propio `sessionid`/`csrftoken` y hace su propio login (una vez) con el
formulario real. Esto es autenticación legítima y no depende de compartir
cookies entre hilos.

Cada CSV de usuarios tiene una sola fila y el plan la recicla
(`recycle=true`, `shareMode=all`), por lo que todos los hilos leen
`alumno1`. Para usar otro usuario local, edita el CSV del plan y exporta su
clave en `JMETER_CLAVE`; el `.jmx` no se toca.

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

## Plan 3/5: PERF-02 (registro de reservaciones sin conflicto)

`plan_perf02_registro_reservaciones.jmx` implementa el escenario del
enunciado: 30 usuarios virtuales, subida gradual de 30 s y 3 registros por
usuario, con 90 muestras medidas.

| Parámetro | Default de examen | Override CLI |
|---|---|---|
| Hilos (usuarios virtuales) | 30 | `-Jusuarios=1` |
| Subida gradual (ramp) | 30 s | `-Jramp=1` |
| Registros por usuario | 3 | `-Jiteraciones=3` |
| Puerto | 8000 | `-Jpuerto=8016` |
| Fecha base | hoy + 30 días | `-Jfecha_base=2027-01-15` |

Con los defaults se esperan **90 muestras medidas** (30 × 3). La rampa
reparte el arranque de los 30 hilos; cada hilo hace su login una vez y
luego 3 registros.

### Dataset: 90 slots únicos

`reservas_perf02.csv` tiene 90 filas y se consume una por registro
(`shareMode=all`, `recycle=false`). Las columnas son:

| Columna | Uso |
|---|---|
| `sala_id` | PK de una sala activa (por defecto 1, 2 y 3). |
| `dias_offset` | Días que se suman a la fecha base (0, 1 y 2). |
| `hora_inicio` / `hora_fin` | Bloques de 1 h entre 08:00 y 18:00. |
| `asistentes` | 2 (cabe en la sala de menor capacidad, 4). |
| `proposito` | Texto único de 30 caracteres (`Reserva PERF-02 slot NNN de 90`). |

La combinación `(sala_id, dias_offset, hora_inicio)` es única en las 90
filas: 3 salas × 3 fechas × 10 horarios. Como cada fila se usa una sola
vez, **no puede haber traslape** aunque dos hilos registren al mismo
tiempo; no se depende del orden de ejecución. El Thread Group usa
`${ITERACIONES}` (3) como loop, de modo que cada iteración consume
exactamente una fila del CSV; no se usa un bucle anidado.

Las horas respetan las reglas del formulario: inicio entre 08:00 y 19:00,
fin <= 20:00 y duración de 60 minutos (mínimo 30, máximo 120).

### Fecha base y repetición no destructiva

El CSV **no** guarda fechas absolutas: guarda `dias_offset`. Un
`JSR223PreProcessor` (Groovy, Java 21) calcula
`fecha = fecha_base + dias_offset` antes del GET del formulario:

- `-Jfecha_base=YYYY-MM-DD` fija la primera fecha.
- Sin la propiedad, la base es `LocalDate.now() + 30 días` (zona del JVM;
  el margen de 30 días evita cualquier diferencia con
  `America/Mexico_City`).
- El valor se envía en ISO `YYYY-MM-DD`, formato que el `DateField` de
  Django acepta; el formulario no requiere `dd/mm/yyyy`.

Para repetir la prueba **no borres filas**: pasa una `fecha_base` nueva
(por ejemplo, hoy + 60) y el dataset vuelve a caer en fechas libres. Si
repites con la misma base sobre una base de datos que ya tiene esos 90
slots, el POST devuelve 200 con "La sala no está disponible en el horario
solicitado" y la aserción de 302 falla: la prueba lo reporta, no lo oculta.
La base usada es desechable; puedes recrear la instancia aislada si lo
prefieres. Si una corrida se aborta a medias, también conviene una base
nueva: las filas ya consumidas quedaron reservadas en la base de datos.

Los `sala_id` por defecto son los de
`salas/migrations/0002_salas_iniciales.py` (Sala A=1, Sala B=2, Sala C=3).
Comprueba los IDs de tu instancia antes de medir:

```bash
docker compose exec app python manage.py shell -c "
from salas.models import Sala
print(list(Sala.objects.filter(activa=True).values_list('id', 'nombre', 'capacidad')))
"
```

Si tu base tiene otros IDs, edita la columna `sala_id` del CSV manteniendo
3 salas activas distintas y capacidad >= 2. Un ID inexistente o inactivo
hace que el POST no redirija y la muestra medida cuente como error.

### Estructura del plan

1. `HTTP Request Defaults`: `http://${HOST}:${PORT}` con `HOST=127.0.0.1`;
   timeouts de conexión 5 s y de respuesta 15 s.
2. Dos `CSV Data Set Config`: un usuario preexistente (una fila reciclada)
   y los 90 slots (sin reciclar).
3. `HTTP Cookie Manager`: sesión independiente por hilo.
4. `Once Only Controller` — login real una vez por hilo, **fuera de los
   KPI**: `GET /usuarios/login` (extrae CSRF) y `POST /usuarios/login`
   (exige 302 y `Location` con `/reservaciones/`).
5. En cada iteración del Thread Group:
   - `00 formulario GET /reservaciones/nueva (no medido)`: exige 200, el
     bloque `id="reservacion-form"` y el CSRF; extrae
     `csrfmiddlewaretoken` a `CSRF_FORM` y calcula `${fecha}`.
   - `PERF-02 POST /reservaciones/nueva (registro medido)`: envía
     `csrfmiddlewaretoken`, `sala`, `fecha`, `hora_inicio`, `hora_fin`,
     `asistentes` y `proposito`; exige **302** y `Location` con
     `/reservaciones/`.
   - `00 verificacion GET /reservaciones/ (no medido)`: comprueba en una
     petición separada el mensaje de éxito y la tabla con una fila del
     dataset.

### Etiquetas y conteo (30 × 3)

| Etiqueta en el JTL | Muestras | ¿Cuenta en los KPI? |
|---|---|---|
| `00 login GET /usuarios/login (no medido)` | 30 | No |
| `00 login POST /usuarios/login (no medido)` | 30 | No |
| `00 formulario GET /reservaciones/nueva (no medido)` | 90 | No |
| `PERF-02 POST /reservaciones/nueva (registro medido)` | 90 | **Sí** |
| `00 verificacion GET /reservaciones/ (no medido)` | 90 | No |

El total del plan es 330 muestras; el evaluador filtra `^PERF-02` y solo
cuenta las 90. El POST usa `follow_redirects=false`, así que el 302
produce **una** muestra y no se duplica con el GET de verificación. No se
usa `Transaction Controller`.

### Verificación del éxito sin doble conteo

El POST se considera exitoso solo si devuelve 302 con `Location` hacia
`/reservaciones/`: la vista redirige únicamente después de que
`registrar_reservacion` persistió la fila. El GET de verificación es una
petición aparte, con la cookie del mismo hilo, y exige
`id="mensaje-confirmacion"`, el texto `registrada exitosamente`, la tabla
`id="tabla-reservaciones"` y una fila `Reserva PERF-02 slot`. El mensaje
flash se guarda en la sesión del hilo y solo se crea en la rama de éxito;
como cada hilo tiene su propia sesión, no puede provenir del POST de otro
hilo. Login, formulario y verificación llevan etiqueta `00 …`, por lo que
no contaminan muestras, errores ni percentiles.

### Comandos

Humo funcional en SQLite (puerto 8016, 1 hilo × 1 registro = 1 muestra
medida). **No** es la medición de examen: SQLite no soporta 30 escritores
concurrentes.

```bash
cd pruebas_rendimiento/jmeter
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
read -rs JMETER_CLAVE
export JMETER_CLAVE
jmeter -n -t plan_perf02_registro_reservaciones.jmx \
  -Jusuarios=1 -Jramp=1 -Jiteraciones=1 -Jpuerto=8016 \
  -Jfecha_base="$(date -d '+29 days' +%F)" \
  -l /tmp/opencode/perf02-humo.jtl \
  -j /tmp/opencode/perf02-humo.log
unset JMETER_CLAVE
```

Esperado: `summary = 5` (2 login + 1 formulario + 1 POST + 1
verificación) y `Err: 0`. La fecha `+29` evita el primer slot del default
`+30` si después mides sobre la misma base; en una base desechable
cualquier fecha libre sirve. Si `date -d` no está disponible, pasa una
fecha ISO explícita.

Medición de PERF-02 con los defaults (Django local sobre MariaDB, puerto
8000; ajusta `-Jpuerto` si tu instancia usa otro):

```bash
cd pruebas_rendimiento/jmeter
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
read -rs JMETER_CLAVE
export JMETER_CLAVE
jmeter -n -t plan_perf02_registro_reservaciones.jmx \
  -l /tmp/opencode/perf02.jtl \
  -j /tmp/opencode/perf02.log
unset JMETER_CLAVE
```

Esperado: `summary = 330`, `Err: 0`; duración aproximada 35–60 s (30 s de
rampa + 90 registros). `-l` debe apuntar a un archivo que **no exista**:
JMeter añade líneas a un JTL previo. Para una repetición, agrega
`-Jfecha_base=YYYY-MM-DD` con una base nueva (o recrea la instancia
aislada).

### Evaluación

El mismo `evaluar_jtl.py` sirve para PERF-02 cambiando etiqueta, volumen
y percentil. `--escenario` solo cambia el nombre del resumen final; su
default sigue siendo `PERF-01`, así que los comandos anteriores no cambian.

```bash
cd pruebas_rendimiento   # desde la raíz del repositorio
python3 evaluar_jtl.py --jtl /tmp/opencode/perf02.jtl \
  --etiqueta '^PERF-02' --min-muestras 90 --p95 2000 \
  --escenario PERF-02
```

Salida esperada (valores ilustrativos):

```text
JTL evaluado: /tmp/opencode/perf02.jtl
Etiqueta:     ^PERF-02
Muestras:     90
Errores:      0 (0.00 %)
Tiempos (ms): p50=120 p90=340 p95=510 max=980
Criterios:
  [CUMPLE] muestras medidas >= 90 (observado: 90)
  [CUMPLE] tasa de errores < 1 % (observado: 0.00 %)
  [CUMPLE] percentil 95 <= 2000 ms (observado: 510 ms)
Resultado PERF-02: CUMPLE
```

Con 90 muestras, **un solo error** da 1.11 % y el criterio `< 1 %` falla:
la corrida debe quedar en cero errores. El mínimo de 90 evita aceptar una
corrida incompleta. Para el humo, el mismo evaluador con volumen relajado
(el humo no demuestra el criterio de volumen):

```bash
python3 evaluar_jtl.py --jtl /tmp/opencode/perf02-humo.jtl \
  --etiqueta '^PERF-02' --min-muestras 1 --p95 2000 \
  --escenario PERF-02
```

### Reporte HTML

```bash
cd pruebas_rendimiento
python3 evaluar_jtl.py --jtl /tmp/opencode/perf02.jtl \
  --etiqueta '^PERF-02' --min-muestras 90 --p95 2000 \
  --jtl-filtrado /tmp/opencode/perf02-filtrado.jtl
cd jmeter
jmeter -g /tmp/opencode/perf02-filtrado.jtl \
  -o /tmp/opencode/perf02-reporte
```

La tabla de etiquetas del reporte debe mostrar una sola fila
`PERF-02 POST /reservaciones/nueva (registro medido)` con 90 muestras. El
reporte HTML (y su `statistics.json`) aporta promedio, p90, p95, throughput
y porcentaje de errores; el script aporta la aceptación con la fórmula
documentada. Los valores de ejemplo no son evidencia: adjunta el JTL o el
reporte de tu corrida y una breve interpretación del cuello de botella
observado.

### Interpretación esperada y cuello de botella a revisar

- Cada POST escribe una fila y, dentro de `transaction.atomic()`, hace
  `select_for_update()` sobre la sala. Con 30 hilos repartidos en 3 salas
  hay serialización por sala: si el p95 crece, revisa esperas de lock y la
  concurrencia del servidor (Apache + mod_wsgi) antes de culpar al plan.
- `DEBUG=True` y el servidor de aplicación se miden tal como está
  desplegada la instancia; decláralo en el reporte.
- La verificación posterior a cada POST renderiza el listado, que crece
  hasta 90 filas y tiene N+1 consultas por `r.sala.nombre` (ver PERF-01).
  Esa carga **no** se mide, pero compite con los POST; si necesitas aislar
  el costo del registro, documenta ese efecto. No la elimines sin perder
  la verificación funcional del éxito.
- No hay `Duration Assertion`: la tasa de errores refleja fallos
  funcionales y el criterio de latencia se evalúa con el script. Un
  timeout de 15 s sí cuenta como error y sigue siendo visible porque
  15 s > 2000 ms.
- El percentil usa rango más cercano sobre las 90 muestras medidas,
  incluidas las fallidas, igual que el reporte de JMeter. La fórmula está
  documentada en `evaluar_jtl.py`.

## Plan 4/5: PERF-03 (concurrencia legítima sobre el mismo horario)

`plan_perf03_concurrencia_mismo_horario.jmx` implementa el escenario del
enunciado: **10 repeticiones controladas** en las que **dos solicitudes
normales y autenticadas** piden **el mismo horario**. El sistema debe
aceptar exactamente una y rechazar la otra por traslape, sin persistir
duplicados. No es un exploit ni un ataque: son dos clientes legítimos con
su propia sesión, el mismo usuario sintético y el formulario real, con un
`Synchronizing Timer` que las hace salir juntas para que la carrera sea
real.

Archivos nuevos de este commit:

```text
pruebas_rendimiento/
├── verificar_perf03.py                     # validación de pares en el JTL
└── jmeter/
    ├── plan_perf03_concurrencia_mismo_horario.jmx
    ├── usuarios_perf03.csv                  # usuario de PERF-03
    └── rondas_perf03.csv                    # 20 filas = 2 idénticas por ronda
```

| Parámetro | Default de examen | Override CLI |
|---|---|---|
| Hilos | **2, fijo** | no se parametriza |
| Rondas | 10 | `-Jrondas=1` (humo; el CSV alcanza hasta 10) |
| Subida gradual | 0 s | `-Jramp=0` |
| Barrera | 2 hilos, timeout 30 s | fijo en el plan |
| Puerto | 8000 | `-Jpuerto=8016` |
| Fecha base | hoy + 60 días | `-Jfecha_base=2027-01-15` |

Los hilos son **2 fijos** porque el `Synchronizing Timer` usa
`groupSize=2`: con un hilo la barrera esperaría el timeout en cada ronda
y la pareja se perdería. El loop del Thread Group es `${RONDAS}` y el CSV
tiene 20 filas (2 por ronda), así que `-Jrondas` no debe pasar de 10.

### Ranuras, fecha y propósito (cómo cruzar JTL y base)

`rondas_perf03.csv` tiene 10 pares de filas **idénticas**; cada hilo
consume una fila por ronda (`shareMode=all`), de modo que ambos piden la
misma ranura sin depender del orden de lectura:

| Columna | Valor |
|---|---|
| `ronda` | `01` … `10` |
| `sala_id` | `1` (Sala A de la migración inicial) |
| `dias_offset` | `0` … `9`, una fecha distinta por ronda |
| `hora_inicio` / `hora_fin` | `08:00` / `09:00` (60 min) |
| `asistentes` | `2` |

Formatos exactos para cruzar el JTL, la base y la auditoría de la
corrida:

- **Fecha enviada y persistida**: ISO `YYYY-MM-DD`, calculada como
  `fecha_base + dias_offset`. Con los defaults del examen, la corrida
  ocupa 10 días consecutivos a partir de hoy + 60.
- **Propósito persistido**:
  `Reserva PERF-03 ronda RR de NN AAAA-MM-DD 08:00-09:00`, con `RR` =
  ronda (`01`…`10`), `NN` = valor de `-Jrondas` (`10` por defecto) y la
  fecha ISO. Los dos POST de una ronda calculan el **mismo** propósito;
  solo el aceptado queda en la base, así que cada corrida deja
  exactamente **10 propósitos distintos**, uno por ronda.
- **Etiqueta del JTL**:
  `PERF-03 POST ronda RR AAAA-MM-DD 08:00-09:00 (medido)`. Hay 2
  muestras por etiqueta (la aceptada y la rechazada), con la misma fecha
  y horario: eso evidencia que ambas pidieron la misma ranura.

La fecha se calcula con un `JSR223PreProcessor` (Groovy, Java 21) antes
del GET del formulario; el `DateField` de Django acepta ISO. Sin
`-Jfecha_base`, la base es `LocalDate.now() + 60 días` (zona del JVM; el
margen evita diferencias con `America/Mexico_City`).

### Sincronización

- El `Synchronizing Timer` es **hijo únicamente del POST medido**: login
  y GET del formulario quedan fuera de la barrera y no se serializan.
- `groupSize=2` y `timeoutInMs=30000` van como literales: JMeter parsea
  los `longProp`/`intProp` al cargar el plan y no resuelve `${...}` ahí
  (falla con `NumberFormatException`). Si cambias la barrera, hazlo en el
  `.jmx`.
- Las dos filas idénticas por ronda son las que garantizan la misma
  ranura aunque el orden de lectura del CSV varíe. La barrera mantiene
  las rondas alineadas: cada hilo lee una fila por iteración, así que en
  la ronda `r` se consumen las filas `2r-1` y `2r`.
- Si el timeout de la barrera expira (un hilo no llega, login fallido,
  error inesperado), la ronda queda con una sola solicitud y
  `verificar_perf03.py` la reporta como pareja incompleta. No hay
  reintentos que oculten el problema.

### Outcomes: el rechazo esperado no es error

El POST medido lleva una aserción `JSR223` que clasifica la respuesta:

| HTTP | Texto / cabecera | Resultado | `success` | `responseMessage` |
|---|---|---|---|---|
| 302 | `Location` con `/reservaciones/` | aceptada | `true` | `ACEPTADA_302` |
| 200 | contiene `disponible en el horario solicitado` | rechazo por traslape | `true` | `RECHAZO_TRASLAPE_200` |
| otro | — | **error inesperado** | `false` | `INESPERADA_<código>` |

Así, el rechazo controlado **no** cuenta como error (es el resultado
correcto de la segunda solicitud) y sí se marcan los fallos reales:
HTTP 500, timeout de 15 s, 200 sin el mensaje de traslape (por ejemplo un
formulario inválido), 302 a otra ruta o sesión perdida. Login y
formulario conservan las aserciones de los planes anteriores (200, CSRF,
302 a `/reservaciones/`).

La aserción reescribe `responseMessage`, de modo que el JTL distingue el
outcome sin columnas extra; el `responseCode` conserva el HTTP y la
etiqueta conserva ronda y fecha. No se usa `Duration Assertion` ni
`Transaction Controller`.

### Etiquetas y conteo (2 × 10)

| Etiqueta en el JTL | Muestras | ¿Cuenta como medida? |
|---|---|---|
| `00 login GET /usuarios/login (no medido)` | 2 | No |
| `00 login POST /usuarios/login (no medido)` | 2 | No |
| `00 formulario GET /reservaciones/nueva (no medido)` | 20 | No |
| `PERF-03 POST ronda RR AAAA-MM-DD 08:00-09:00 (medido)` | 20 | **Sí (10 parejas)** |

Total del plan: 44 muestras, 20 medidas. Cada hilo hace su login una vez
(`Once Only Controller`) y reutiliza su sesión/cookie durante las 10
rondas; son 2 sesiones del mismo `alumno1`, no cookies compartidas.

### Comandos

Humo funcional (2 hilos × 1 ronda = 8 muestras, 2 medidas). Sirve para
comprobar login, CSRF, barrera y aserciones; **no** demuestra las 10
rondas:

```bash
cd pruebas_rendimiento/jmeter
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
read -rs JMETER_CLAVE
export JMETER_CLAVE
jmeter -n -t plan_perf03_concurrencia_mismo_horario.jmx \
  -Jrondas=1 -Jpuerto=8016 -Jfecha_base="$(date -d '+59 days' +%F)" \
  -l /tmp/opencode/perf03-humo.jtl \
  -j /tmp/opencode/perf03-humo.log
unset JMETER_CLAVE
```

Esperado: `summary = 8`, `Err: 0` (2 login + 2 formularios + 2 POST). Si
`date -d` no está disponible, pasa una fecha ISO explícita.

Corrida de examen (Django local, puerto 8000; ajusta `-Jpuerto` si tu
instancia usa otro):

```bash
cd pruebas_rendimiento/jmeter
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk
export PATH="$JAVA_HOME/bin:$PATH"
read -rs JMETER_CLAVE
export JMETER_CLAVE
jmeter -n -t plan_perf03_concurrencia_mismo_horario.jmx \
  -l /tmp/opencode/perf03.jtl \
  -j /tmp/opencode/perf03.log
unset JMETER_CLAVE
```

Esperado: `summary = 44`, `Err: 0`; duración de pocos segundos (sin
rampa). `-l` debe apuntar a un archivo que **no exista**: JMeter añade
líneas a un JTL previo. Si repites la corrida, usa otra `-Jfecha_base`
(por ejemplo, hoy + 70) o una base limpia; no borres filas.

### Evaluación de las parejas (script propio)

`evaluar_jtl.py` no aplica a PERF-03 (no hay umbral de latencia ni de
volumen, y su filtro por etiqueta no valida parejas); **no se modificó**.
La validación usa `verificar_perf03.py`, que comprueba, por ronda:
2 muestras de hilos distintos, misma fecha y horario, 1 aceptación (302)
y 1 rechazo (200) con sus marcadores, ambas `success=true`; además exige
10 rondas con fechas distintas y consecutivas y ningún fallo en login o
formulario.

```bash
cd pruebas_rendimiento
python3 verificar_perf03.py --jtl /tmp/opencode/perf03.jtl
```

Salida esperada (valores ilustrativos):

```text
JTL evaluado: /tmp/opencode/perf03.jtl
Rondas encontradas: 10 (esperadas: 10)
  ronda 01 2027-01-18 08:00-09:00: 2 POST, 1 aceptada(s), 1 rechazo(s)
  ...
  ronda 10 2027-01-27 08:00-09:00: 2 POST, 1 aceptada(s), 1 rechazo(s)
Errores inesperados fuera del POST: 0
Comprobaciones:
  [CUMPLE] una aceptacion (302) y un rechazo (200) por ronda, ambos success=true
  [CUMPLE] 10 rondas con ranuras distintas y fechas consecutivas
  [CUMPLE] sin errores inesperados en el resto del plan
Resultado PERF-03 en JTL: CUMPLE
```

- Código de salida `0` = cumple; `1` = alguna comprobación falla (por
  ejemplo dos 302 en una ronda); `2` = JTL ilegible o sin muestras
  PERF-03.
- Para el humo usa `--rondas 1`.
- `Err: 0` de JMeter **no basta**: dos aceptaciones también dan `Err: 0`
  porque ambos 302 son respuestas HTTP válidas. La detección de
  duplicados es la comparación 1×302/1×200 por ronda de este script; se
  comprobó con un stub que acepta siempre las dos solicitudes: JMeter
  reportó 0 errores y el script falló las dos rondas.

### Cruzar con la base de datos (solo lectura)

El JTL demuestra el resultado HTTP; que **no** queden duplicados se
confirma en MariaDB con dos consultas de solo lectura: una por corrida y
otra global. Desde la raíz del repositorio, usa la misma `FECHA_BASE` de
JMeter o asígnala antes de ejecutar:

```bash
{
  printf "SET @fecha_base = '%s';\n" "${FECHA_BASE:?Falta la fecha base}"
  cat pruebas_rendimiento/jmeter/auditar_{perf03,traslapes}.sql
} | docker compose exec -T db sh -c \
    'MYSQL_PWD="$MYSQL_PASSWORD" mariadb -u "$MYSQL_USER" "$MYSQL_DATABASE"'
```

Si Docker requiere `sudo`, úsalo antes de `docker compose`. Se esperan
**10 rondas con una fila vigente cada una y 0 pares vigentes traslapados**.
La consulta por corrida limita por fecha, sala, horario, estado y propósito,
de modo que no cuenta reservaciones de corridas con fechas distintas.

### Verificación realizada (stub local, no Django)

La mecánica del plan se validó con **JMeter 5.6.3 + Java 21** contra un
servidor HTTP mínimo local en `127.0.0.1:8023` (no versionado, **no**
Django) que emula login con CSRF, formulario autenticado y POST con
aceptación de la primera solicitud y rechazo por traslape de la segunda:

- `xmllint --noout` sobre el `.jmx` y recorrido con `ElementTree`: un solo
  Thread Group de 2 hilos, loop `${RONDAS}`, un único `Synchronizing
  Timer` hijo del POST medido (`groupSize=2`, `timeoutInMs=30000`), sin
  `Duration Assertion` ni `Transaction Controller`, y todos los samplers
  contra `${HOST}` (`127.0.0.1`).
- `rondas_perf03.csv`: 20 filas, 10 pares idénticos, 10 rondas y
  `dias_offset` consecutivos de 0 a 9.
- Corrida completa: `summary = 44`, `Err: 0`; 10 rondas con 1×302 y 1×200
  cada una, ambas `success=true`, y `verificar_perf03.py` en `0`. Los dos
  POST de cada ronda arrancaron en el mismo milisegundo (diferencia 0 ms)
  y la traza del stub registró exactamente 10 aceptaciones y 10 rechazos,
  una por ranura.
- Humo `-Jrondas=1`: `summary = 8`, `Err: 0`, verificador con
  `--rondas 1` en `0`.
- Detección de fallos: con un stub que **acepta siempre** las dos
  solicitudes, JMeter reportó `Err: 0` pero el verificador falló las dos
  rondas (`2 aceptaciones`). También se probaron JTL sintéticos con pareja
  incompleta, login fallido y marcador de rechazo ausente: exit `1` en
  todos; JTL inexistente: exit `2`.
- `flake8` sin hallazgos y `radon` con complejidad máxima 9 (≤ 10) en
  `verificar_perf03.py`.

Esto valida XML, CSV, sincronización, etiquetas, aserciones, outcomes y
el verificador. **No** valida el control de concurrencia real: la corrida
contra Django sobre MariaDB (puerto 8000) queda para la instancia del
equipo y es la que confirma que no se persisten duplicados.

### Límites de este plan

- La barrera garantiza salida simultánea, **no** el orden de llegada al
  servidor ni el resultado de la base. El control real es
  `transaction.atomic()` + `select_for_update()` en
  `registrar_reservacion`; si esa protección fallara, la ronda mostraría
  dos 302 y el script fallaría. Esa validación pertenece a la corrida en
  MariaDB.
- Dos hilos son suficientes para el criterio; con más hilos o más rondas
  cambia el CSV y deja de ser el escenario del enunciado.
- Con `-Jrondas=1` solo hay una pareja: no se puede concluir nada sobre
  las 10 repeticiones.
- Las 10 filas aceptadas **no se borran**; la base es desechable y cada
  repetición usa una `fecha_base` nueva. Si una corrida se corta, las
  filas ya aceptadas siguen ocupando su ranura.
- La auditoría SQL global cuenta parejas traslapadas vigentes en toda la
  base; úsala junto con el conteo por propósito para no atribuir a
  PERF-03 traslapes de otros datos.

## Riesgos y límites

- Las aserciones dependen de textos del template (`Mis reservaciones`,
  `id="btn-logout"`, `id="reservacion-form"`, `id="mensaje-confirmacion"`,
  `Reserva PERF-02 slot`). Un rediseño de las vistas obliga a actualizar
  los planes.
- Requiere servidor y base **aislados** ya migrados; si `alumno1` no
  existe o la clave no coincide, el login no redirige y las consultas
  medidas fallan de forma explícita (no hay falso positivo).
- El login de cada hilo crea 50 sesiones en PERF-01 y 30 en PERF-02 del
  mismo usuario en `django_session`. Es el comportamiento legítimo de
  clientes concurrentes; no se reutilizan cookies entre hilos.
- PERF-02 no prueba el control de concurrencia sobre el mismo slot: su
  dataset usa 90 slots distintos. La concurrencia real (dos POST al mismo
  horario) pertenece a PERF-03.
- PERF-02 supone que las salas 1, 2 y 3 existen, están activas y tienen
  capacidad >= 2. Si tu base tiene otros IDs, actualiza el CSV; un ID
  inválido produce errores medidos, no un falso positivo.
- PERF-02 supone que los 90 slots de la fecha base están libres. Repite
  con una `fecha_base` nueva (o una base limpia); si una corrida se corta,
  las filas ya consumidas quedaron reservadas.
- HTTP plano en loopback. Con cookies `Secure` o HTTPS, el Cookie Manager
  no reenviaría `csrftoken`/`sessionid`.
- SQLite no soporta 50 escritores concurrentes de PERF-01 ni 30 de
  PERF-02: úsalo solo con `-Jusuarios=1`.
- Los defaults 50/30/5 (PERF-01) y 30/30/3 (PERF-02) se resuelven en
  tiempo de ejecución desde variables del plan que leen `-J`; el patrón
  anidado está confirmado para `${PORT}` por el JTL del humo previo
  (`localhost:8016`). Comprueba en la primera corrida que la consola diga
  `summary = 7`/`350` (PERF-01) o `5`/`330` (PERF-02).
- La verificación de PERF-02 agrega un GET no medido por registro que
  renderiza el listado; es carga real sobre el servidor aunque no cuente
  en los KPI. Decláralo al interpretar el p95.
- Los números del README son ilustrativos. Los resultados reales deben
  generarse en la instancia del equipo y adjuntarse como evidencia.

## Verificación realizada

Validación **estática y mecánica**. La corrida funcional contra Django
queda para la instancia local del equipo.

```bash
xmllint --noout \
  pruebas_rendimiento/jmeter/plan_perf01_consulta_reservaciones.jmx \
  pruebas_rendimiento/jmeter/plan_perf02_registro_reservaciones.jmx
python3 -m py_compile pruebas_rendimiento/evaluar_jtl.py
flake8 pruebas_rendimiento/evaluar_jtl.py
radon cc pruebas_rendimiento/evaluar_jtl.py -s
```

- Ambos `.jmx` pasan `xmllint`. El árbol de PERF-02 se recorrió con
  `ElementTree`: el `Once Only` contiene solo los dos login; el Thread
  Group toma `${USUARIOS}`/`${RAMP}`/`${ITERACIONES}` con defaults 30/30/3;
  el CSV de 90 filas está fuera del `Once Only`; el POST medido está en el
  cuerpo de la iteración y no hay `Duration Assertion` ni
  `Transaction Controller`.
- `reservas_perf02.csv` se verificó con Python: 90 filas, 90 combinaciones
  `(sala_id, dias_offset, hora_inicio)` únicas, 90 propósitos únicos, 30
  filas por sala y por día, horas dentro de 08:00–20:00 y asistentes (2)
  dentro de la capacidad mínima (4).
- `flake8` sin hallazgos y `radon` con complejidad máxima 9 (≤ 10).
- El evaluador se probó con JTL sintéticos (no versionados): 90 muestras
  que cumplen, 90 con 1 error (1.11 %, debe fallar), 90 con p95 de
  2500 ms (debe fallar), 1 muestra de humo y 250 muestras de PERF-01 con
  los defaults. Devolvió `0` solo en los casos que cumplen, `1` en los que
  deben fallar y conserva el texto `Resultado PERF-01` cuando no se pasa
  `--escenario`.
- **Mecánica del plan:** con JMeter 5.6.3 + Java 21 se ejecutó el `.jmx`
  contra un servidor HTTP mínimo local (no versionado, **no Django**) que
  devuelve el HTML/302 que esperan las aserciones. Resultados:
  - 1 hilo × 11 iteraciones: 35 muestras (2 login + 11 formulario + 11
    POST + 11 verificación), 11 medidas, 0 errores. Los cuerpos POST
    mostraron `sala=1`, `fecha=2027-01-15` y los horarios 08:00→09:00 …
    17:00→18:00; la fila 11 cambió a `fecha=2027-01-16`, confirmando la
    suma de `dias_offset`.
  - 30 hilos × 3 iteraciones (ramp 30 s): 330 muestras, 90 medidas, 0
    errores; 30 login, 90 formularios, 90 POST, 90 verificaciones. Los 90
    cuerpos POST fueron **90 slots distintos** (30 por sala y por fecha),
    sin filas repetidas ni agotamiento del CSV.
  - Sin `-Jfecha_base`, la fecha enviada fue la de hoy + 30 días
    (`2026-12-18` al crear este commit).
  - En una corrida 1×1 el stub exigió la cookie `sessionid` para el
    formulario y el listado: la petición pasó, así que el Cookie Manager
    conserva la sesión creada por el 302 del login.

Lo anterior valida XML, CSV, variables, CSRF extraído, fecha calculada,
etiquetas y conteo. **No** valida contra Django: el humo real en SQLite
(8016) confirma el formulario y las reglas de negocio; la medición en
MariaDB confirma los umbrales. El humo debe hacerse con 1 hilo; SQLite no
soporta los 30 escritores concurrentes.

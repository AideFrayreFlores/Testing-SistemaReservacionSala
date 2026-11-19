# Pruebas de rendimiento (JMeter)

Documentación técnica del plan de **humo** de JMeter para el Sistema de
Reservación de Salas. Corresponde al commit **1/5** del trabajo de
rendimiento compartido: solo autenticación real contra un Django local.
No mide ningún escenario de carga ni implementa PERF-01, PERF-02 o PERF-03.

## Alcance de este plan

- Verifica que un usuario sintético puede iniciar sesión con el formulario
  real de Django, usando sesión y CSRF legítimos (cookie + token del HTML).
- Verifica que la sesión sigue válida al pedir `/reservaciones/`, cuya
  página autenticada es la única evidencia aceptada.
- **No** es PERF-01: el listado de reservaciones aquí solo comprueba sesión;
  no se mide ni se exige ningún tiempo, y no se generan datos de carga.

## Requisitos

- **Apache JMeter 5.6.3** en el equipo que ejecuta la prueba (versión fijada
  para que el resultado sea reproducible; no se instala desde este repo).
- **Java 17 o 21**. Usa `/usr/lib/jvm/java-21-openjdk` (verificado con
  OpenJDK 21.0.13). JMeter 5.6.3 trae Groovy 3, que no carga clases de Java
  25 y aborta con `Unsupported class file major version 69`; no ejecutes el
  plan con el JVM del sistema si es más nuevo que 21.
- Servidor Django **local** ya levantado (por ejemplo `runserver` en
  `localhost:8000`) sobre una base **aislada y migrada**, de modo que exista
  el usuario inicial `alumno1` (`usuarios/migrations/0001_usuarios_iniciales.py`).
- No se requieren plugins de JMeter ni destinos remotos.

## Archivos

```text
pruebas_rendimiento/
├── README.md                      # este documento
└── jmeter/
    ├── plan_humo_login.jmx        # plan base (1 hilo, 1 iteración)
    └── usuarios_smoke.csv         # nombre de usuario sintético
```

## Ejecución

Ejecuta **desde la carpeta del plan**, porque el CSV se resuelve por ruta
relativa al directorio de trabajo:

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

- `JAVA_HOME` debe apuntar a Java 21 (o 17) **antes** de invocar `jmeter`;
  con Java 25 la prueba ni arranca (ver Requisitos). Las mismas variables
  aplican al comando de reporte de más abajo.
- En `read`, escribe la contraseña del usuario sintético `alumno1` del
  README principal y pulsa Enter. No se muestra ni se guarda en Git.
- `-Jpuerto=8016` (opcional) usa otro puerto del mismo equipo.
- `-n` modo consola (sin GUI). No se abre ninguna interfaz.
- `-l` archivo de resultados; debe **no existir** o se añadirán líneas.
- `-j` log de JMeter.

Resultado esperado en consola: `summary = 3` y `Err: 0` (una muestra por
petición, sin errores). Reporte HTML opcional a partir del JTL ya generado,
con directorio de salida vacío:

```bash
jmeter -g /tmp/opencode/jmeter-humo-login.jtl \
  -o /tmp/opencode/jmeter-humo-reporte
```

## Flujo y aserciones

| # | Petición | Qué comprueba |
|---|---|---|
| 01 | `GET /usuarios/login` | HTTP 200 y que el formulario incluye `name="csrfmiddlewaretoken"`. Un extractor de expresión regular guarda el token en `CSRF_TOKEN`. |
| 02 | `POST /usuarios/login` (form, sin seguir redirección) | HTTP **302** y cabecera `Location` con `/reservaciones/`. Un login inválido o un rechazo CSRF no produce esa redirección. |
| 03 | `GET /reservaciones/` | HTTP 200, `<title>Mis reservaciones</title>` y `id="btn-logout"`. El formulario de login no pasa las aserciones del contenido. |

Detalles de implementación:

- `HTTP Cookie Manager` (sin limpiar entre iteraciones) conserva
  `csrftoken` y `sessionid`; no se envía ninguna cookie escrita a mano.
- El token CSRF se toma del campo oculto del formulario y se reenvía en el
  cuerpo del POST; corresponde a la cookie `csrftoken` que envió el
  Cookie Manager. Django rota el token al autenticar y el Cookie Manager
  toma el nuevo valor automáticamente.
- `HTTP Request Defaults` fija `http://localhost:8000`; no hay valores de
  producción ni destinos externos. El puerto es configurable con `-Jpuerto`.
- `ThreadGroup`: 1 hilo, 1 iteración, sin *scheduler*: no es una prueba de
  carga.
- Timeouts: conexión 5 s, respuesta 15 s (valores de humo, no umbrales).

## Usuarios sintéticos

`usuarios_smoke.csv` contiene solo el nombre de un usuario de desarrollo
creado por la migración inicial:

```csv
usuario
alumno1
```

El `CSV Data Set Config` usa `usuarios_smoke.csv`, delimitador `,`,
codificación UTF-8, salta la cabecera, comparte filas entre hilos
(`shareMode.all`) y recicla al llegar al final. Con 1 hilo y 1 iteración se
consume únicamente la primera fila, por lo que la prueba es determinista.
Para otro usuario local, edita el CSV y suministra su clave mediante
`JMETER_CLAVE`; no hace falta tocar el `.jmx`.

## Riesgos y límites

- La aserción depende de textos del template (`Mis reservaciones`,
  `id="btn-logout"`). Un rediseño de la vista obliga a actualizar el plan.
- Requiere el servidor y la base **aislados** ya migrados; si `alumno1` no
  existe, el paso 02 falla con 200 en lugar de 302 (falla explícita, no
  falso positivo).
- Asume HTTP plano en localhost. Si se activan cookies `Secure` o HTTPS, el
  Cookie Manager no reenviará `csrftoken`/`sessionid` y el plan fallará.
- No valida permisos ajenos ni reglas de negocio de reservaciones: eso
  pertenece a las pruebas funcionales y a los siguientes commits de PERF.
- El plan no se ejecutó al crear este commit (JMeter no está instalado en
  el entorno de autoría); solo se validó la sintaxis XML del `.jmx`.

## Verificación realizada

```bash
xmllint --noout pruebas_rendimiento/jmeter/plan_humo_login.jmx
```

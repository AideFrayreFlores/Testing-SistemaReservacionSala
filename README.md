# Sistema de Reservación de Salas de Estudio

Aplicación web desarrollada en **Python / Django** y **MariaDB** para la gestión de reservaciones de salas de estudio académicas, aplicando **Desarrollo Guiado por Pruebas (TDD)** y **Desarrollo Guiado por Comportamiento (BDD)** con **Behave y Selenium**.

---

## 1. Requisitos previos

- **Docker**  (para los contenedores de la aplicación Django y base de datos MariaDB).
- **Python 3.11+** en el equipo anfitrión (únicamente para ejecutar las pruebas de aceptación con Behave + Selenium en navegador Chrome).
- **Google Chrome** instalado en el equipo anfitrión.

---

## 2. Configuración del entorno (`.env`)

Al clonar el repositorio, crea el archivo `.env` en la raíz del proyecto (`SistemaReservacionSala/`) copiando la plantilla `.env.example`:

- **Windows (CMD / PowerShell):**

```bash
copy .env.example .env
```

- **Linux / macOS:**

```bash
cp .env.example .env
```

Contenido base de `.env.example`:

```env
DB_NAME=reservacion
DB_USER=reservacion-user
DB_USER_ADMIN=admin
DB_PASSWORD=admin1234
DB_ROOT_PASSWORD=admin1234
DB_HOST=db

DEBUG=False
SECRET_KEY='cambia-esta-clave'
```


---

## 3. Instalación, base de datos y ejecución de la aplicación

### 3.1 Levantar los contenedores con Docker Compose

Desde la raíz del proyecto (`SistemaReservacionSala/`):

```bash
docker compose up -d --build
```

### 3.2 Otorgar permisos de creación de base de datos de pruebas en MariaDB

Para que Django pueda crear y destruir la base de datos temporal `test_reservacion` al ejecutar la suite de pruebas:

```bash
docker compose exec db mariadb -u root -p
```

Dentro de la consola de MariaDB (ingresar el `DB_ROOT_PASSWORD` configurado en `.env`):

```sql
GRANT ALL PRIVILEGES ON *.* TO 'reservacion-user'@'%';
FLUSH PRIVILEGES;
EXIT;
```

### 3.3 Aplicar migraciones y cargar datos iniciales

Entrar al contenedor de la aplicación (desde `SistemaReservacionSala/`):

```bash
docker compose exec app bash
```

Aplicar las migraciones (esto crea las tablas y **carga automáticamente los datos iniciales** de salas y usuarios de prueba mediante migraciones de datos):

```bash
python manage.py migrate
```

### 3.4 Iniciar el servidor de desarrollo

Dentro del contenedor (`reservacion-app`):

```bash
python manage.py runserver 0.0.0.0:8000
```

La aplicación estará disponible en:
- **Inicio de sesión:** `http://localhost:8000/usuarios/login`
- **Mis reservaciones:** `http://localhost:8000/reservaciones/`
- **Nueva reservación:** `http://localhost:8000/reservaciones/nueva`

---

## 4. Datos iniciales precargados (Reproducibilidad)

Al ejecutar `python manage.py migrate` (y también de forma automática al correr `python manage.py test`), las migraciones cargan los siguientes datos:

### Salas de estudio (`salas/migrations/0002_salas_iniciales.py`)

- **Sala A:** capacidad para 4 personas, ubicada en *Biblioteca, planta baja* (activa).
- **Sala B:** capacidad para 8 personas, ubicada en *Biblioteca, planta baja* (activa).
- **Sala C:** capacidad para 12 personas, ubicada en *Biblioteca, planta alta* (activa).
- **Sala de mantenimiento:** capacidad para 6 personas, ubicada en *Biblioteca, planta alta* (inactiva).

### Usuarios de prueba (`usuarios/migrations/0001_usuarios_iniciales.py`)

- **`alumno1`** — contraseña: **`alumno123`** (`alumno1@correo.com`)
- **`alumno2`** — contraseña: **`alumno567`** (`alumno2@correo.com`)

---



### 5 Pruebas de aceptación BDD (`Behave` + `Selenium`)

Con el servidor corriendo en `http://localhost:8000`, abrir una terminal en la máquina anfitriona (donde se encuentra instalado Google Chrome):

1. Instalar dependencias en el entorno local (si no están instaladas):
   ```bash
   pip install behave selenium
   ```
2. Limpiar reservaciones previas de prueba en el contenedor (desde `SistemaReservacionSala/`):
   ```bash
   echo Reservacion.objects.all().delete() | docker exec -i reservacion-app python manage.py shell
   ```
3. Ejecutar las pruebas de aceptación de registro y cancelación de reservaciones desde `pruebas_aceptacion`:
   - Con navegador Chrome visible (por defecto):
     ```cmd
     cd pruebas_aceptacion
     behave
     ```
   - En modo *headless* (sin abrir ventanas, ideal para revisión automatizada en Windows CMD):
     ```cmd
     set HEADLESS=1
     behave
     ```

#### 5.1 Datos de apoyo del escenario CA-09

El escenario `CA-09 Impedir la cancelación fuera del periodo permitido`
necesita una reservación de `alumno1` que inicie ~30 minutos después del
momento de la ejecución. No se congela el reloj: Behave ejecuta el comando
`preparar_reserva_ca09` al comenzar el escenario y `--limpiar ID` al
terminar, que elimina únicamente esa fila.

- **Con Docker** (desde `SistemaReservacionSala/`):
  ```bash
  export COMANDO_DJANGO="docker compose exec -T app python manage.py"
  export DJANGO_DIR="$PWD"
  cd pruebas_aceptacion
  HEADLESS=1 behave --name "CA-09"
  ```
  Si Docker requiere `sudo`, ejecuta `sudo -v` en la misma terminal y usa
  `sudo -n docker compose` en `COMANDO_DJANGO`.
- **Con SQLite aislado**: el servidor y el comando de datos deben usar el
  mismo archivo de base de datos, no `:memory:`. Exporta `PYTHONPATH` y
  `DJANGO_SETTINGS_MODULE` del módulo de settings temporal y, si Django está
  en otro entorno virtual, configura también `COMANDO_DJANGO`:
  ```bash
  export PYTHONPATH=/tmp/opencode
  export DJANGO_SETTINGS_MODULE=settings_hu02_archivo
  cd pruebas_aceptacion
  HEADLESS=1 behave --name "CA-09"
  ```
- **Ejecución manual del comando**:
  ```bash
  # Docker
  docker compose exec app python manage.py preparar_reserva_ca09
  docker compose exec app python manage.py preparar_reserva_ca09 --limpiar 12
  # SQLite
  cd app
  PYTHONPATH=/tmp/opencode DJANGO_SETTINGS_MODULE=settings_hu02_archivo \
    python manage.py preparar_reserva_ca09
  ```
  El comando imprime un JSON con el `id`. `--limpiar ID` solo borra la fila
  con el propósito de CA-09 de `alumno1`; ante cualquier otra reservación
  falla sin eliminarla.
- Evidencia opcional: con `EVIDENCIA_HU02` apuntando a un directorio, el
  escenario guarda `CA09_rechazo_periodo_concluido.png`.

---

## 6. Estructura del proyecto

```text
SistemaReservacionSala/
├── app/
│   ├── manage.py
│   ├── sistemaReservacionSala/   # Configuración principal del proyecto Django
│   ├── salas/                    # Modelo Sala, migraciones iniciales y pruebas (16 tests)
│   ├── usuarios/                 # Autenticación (login/logout), usuarios iniciales y pruebas (9 tests)
│   └── reservaciones/            # Modelo Reservacion, ReservacionForm, servicio transaccional,
│                                 # vistas, templates y pruebas unitarias/concurrencia (74 tests)
│       └── management/commands/  # preparar_reserva_ca09: fixture aislado del escenario CA-09
├── pruebas_aceptacion/
│   ├── .behaverc                 # Configuración de Behave en español (lang:es)
│   └── features/
│       ├── environment.py        # Driver Chrome (visible/headless), URL base y limpieza de CA-09
│       ├── fixture_ca09.py       # Invocación del comando de datos de CA-09
│       ├── registrar_reservacion.feature
│       ├── cancelar_reservacion.feature
│       └── steps/
│           ├── autenticacion.py
│           ├── registrar_reservacion.py
│           └── cancelar_reservacion.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

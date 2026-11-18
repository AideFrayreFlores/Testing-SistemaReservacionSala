# Demo breve — HU-02: cancelar reservación

## Preparación

Usar una base de aceptación **desechable**: los escenarios por interfaz pueden dejar reservaciones de prueba. El fixture de CA-09 limpia su propia fila, no necesariamente las creadas por otros escenarios. No ejecutar una limpieza general sobre datos que se quieran conservar.

Desde la raíz del repositorio, preparar `.env` y levantar Docker según `README.md` (secciones 2 y 3):

```bash
docker compose up -d --build
docker compose exec app bash
# Dentro del contenedor:
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Mantener el servidor activo. En el anfitrión se necesitan Chrome, Behave y Selenium; consultar el README para dependencias y permisos de la base de pruebas. Abrir `http://localhost:8000/usuarios/login`.

## Recorrido manual

1. Ingresar con el usuario de prueba `alumno1` / `alumno123` y registrar una sala en un horario que empiece en más de 60 minutos.
2. En **Mis reservaciones**, seleccionar **Cancelar** y confirmar. Mostrar el aviso y la fila cancelada con fecha y hora.
3. Registrar otra reservación para la misma sala y horario: debe quedar vigente. Mostrar que se liberó el horario.
4. Como complemento, mostrar el rechazo de una reservación ajena, el límite de cancelación y la conservación del historial; los escenarios CA-08 a CA-11 detallan los pasos reproducibles.

## Ejecución de aceptación

Con el servidor activo, desde otra terminal en el anfitrión y la raíz del repositorio:

```bash
export COMANDO_DJANGO="docker compose exec -T app python manage.py"
export DJANGO_DIR="$PWD"
cd pruebas_aceptacion
HEADLESS=1 behave --name "CA-07"
```

Para mostrar Chrome, omitir `HEADLESS=1`. Para la regresión completa, desde `pruebas_aceptacion`, usar `HEADLESS=1 behave -f plain`. Si Docker requiere sudo, seguir la sección 8 del README. Para guardar capturas, definir `EVIDENCIA_HU02` antes de correr Behave. Para CA-09, mantener configurados `COMANDO_DJANGO` y `DJANGO_DIR` como indica el README.

## Evidencia y estado

Las siete capturas V2 están en `~/Salvada/Investigacion/Testing/Evidencia_HU02_TDD_V2/capturas/`. En MariaDB pasaron las 133 pruebas de Django, incluida concurrencia. Los 19 escenarios de Behave quedaron verificados en dos corridas: 18 en la suite general y CA-09 en una repetición con la autorización de `sudo` renovada. Consulta [la bitácora](Bitacora_TDD_HU02.md) para el detalle. No se incluyen pruebas JMeter.

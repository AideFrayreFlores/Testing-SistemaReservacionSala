"""Invocación del fixture de CA-09 desde Behave.

El comando se ejecuta con el mismo intérprete de Behave por defecto, de modo
que basta exportar PYTHONPATH y DJANGO_SETTINGS_MODULE al usar un SQLite
aislado. Para Docker se configura COMANDO_DJANGO y DJANGO_DIR (ver README).

La preparación crea una única reservación y `limpiar` elimina esa misma fila
por su identificador al concluir el escenario.
"""

import json
import os
import subprocess
import sys

COMANDO = 'preparar_reserva_ca09'


def _directorio_django():
    return os.getenv(
        'DJANGO_DIR',
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'app')
        )
    )


def _comando_django():
    configurado = os.getenv('COMANDO_DJANGO')
    if configurado:
        return configurado.split()
    return [sys.executable, 'manage.py']


def _ejecutar(argumentos):
    resultado = subprocess.run(
        [*_comando_django(), *argumentos],
        cwd=_directorio_django(),
        capture_output=True,
        text=True,
        check=False
    )
    if resultado.returncode != 0:
        raise AssertionError(
            f'Falló {" ".join(argumentos)}: {resultado.stderr.strip()}'
        )
    return resultado.stdout


def preparar():
    salida = _ejecutar([COMANDO])
    return json.loads(salida.strip().splitlines()[-1])


def limpiar(reservacion_id):
    _ejecutar([COMANDO, '--limpiar', str(reservacion_id)])

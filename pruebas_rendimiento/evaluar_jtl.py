#!/usr/bin/env python3
"""Evalua un JTL CSV de JMeter contra los criterios de PERF-01.

Uso tipico (medicion completa, 50 usuarios x 5 consultas = 250 muestras):

    python3 evaluar_jtl.py --jtl /tmp/opencode/perf01.jtl

Humo con SQLite (1 usuario x 5 consultas), donde el volumen de examen
no aplica y se relaja solo el minimo de muestras:

    python3 evaluar_jtl.py --jtl /tmp/opencode/perf01-humo.jtl \
        --min-muestras 5

Criterios (por defecto, los del enunciado para PERF-01):

* Muestras medidas: al menos 250. 50 usuarios x 5 iteraciones = 250;
  si hay menos, el percentil 95 se calcula con poco volumen y el
  resultado no es representativo, por eso se rechaza.
* Tasa de errores < 1 % de las muestras medidas.
* Percentil 95 del tiempo transcurrido (``elapsed``) <= 1500 ms.

Solo se evaluan las muestras cuya etiqueta coincide con ``--etiqueta``
(por defecto ``^PERF-01``), de modo que el login de cada hilo, que el
plan ejecuta una sola vez y no forma parte del KPI, no contamina el
conteo ni los percentiles.

Semantica del percentil: rango mas cercano (nearest rank) sobre los
tiempos ``elapsed`` de todas las muestras medidas, incluidas las
fallidas, igual que el reporte agregado de JMeter. El valor reportado
es un tiempo realmente observado: el menor ``elapsed`` tal que al menos
el 95 % de las muestras son menores o iguales a el. Con 250 muestras el
indice 1-based es ``ceil(0.95 * 250) = 238``. JMeter puede diferir en
una muestra por su redondeo interno; para la aceptacion se usa el
calculo de este script, que queda documentado aqui.

Exit codes: 0 si cumple todos los criterios, 1 si alguno falla,
2 si el JTL no se puede leer o no tiene las columnas esperadas.
"""

import argparse
import csv
import math
import re
import sys

COLUMNAS_REQUERIDAS = ("elapsed", "label", "success")
ETIQUETA_POR_DEFECTO = r"^PERF-01"
MIN_MUESTRAS_POR_DEFECTO = 250
MAX_ERRORES_POR_DEFECTO = 1.0
P95_MS_POR_DEFECTO = 1500


def leer_jtl(ruta, patron):
    """Devuelve (cabecera, filas_crudas, muestras) del JTL filtrado."""
    with open(ruta, newline="", encoding="utf-8") as archivo:
        lector = csv.reader(archivo)
        cabecera = next(lector, None)
        if cabecera is None:
            raise ValueError("el JTL esta vacio")
        faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in cabecera]
        if faltantes:
            raise ValueError(
                "faltan columnas en el JTL: " + ", ".join(faltantes)
            )
        i_elapsed = cabecera.index("elapsed")
        i_label = cabecera.index("label")
        i_success = cabecera.index("success")
        filas = []
        muestras = []
        for numero, fila in enumerate(lector, start=2):
            if not fila:
                continue
            if len(fila) <= max(i_elapsed, i_label, i_success):
                raise ValueError(
                    f"fila {numero} incompleta: se esperaban al menos "
                    f"{len(cabecera)} columnas"
                )
            if not patron.search(fila[i_label]):
                continue
            filas.append(fila)
            muestras.append({
                "elapsed": float(fila[i_elapsed]),
                "exitosa": fila[i_success].strip().lower() == "true",
            })
    return cabecera, filas, muestras


def percentil(valores, p):
    """Percentil por rango mas cercano; devuelve un valor observado."""
    ordenados = sorted(valores)
    if not ordenados:
        raise ValueError("no hay muestras para calcular percentiles")
    indice = max(math.ceil(p / 100.0 * len(ordenados)) - 1, 0)
    return ordenados[indice]


def escribir_jtl_filtrado(destino, cabecera, filas):
    """Guarda solo las muestras medidas para el reporte HTML de JMeter."""
    with open(destino, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        escritor.writerow(cabecera)
        escritor.writerows(filas)


def metricas_de(muestras):
    """Resume las muestras medidas; sin muestras todo queda en cero."""
    total = len(muestras)
    if total == 0:
        return {
            "muestras": 0,
            "errores": 0,
            "errores_pct": 0.0,
            "p50": 0.0,
            "p90": 0.0,
            "p95": 0.0,
            "max": 0.0,
        }
    tiempos = [m["elapsed"] for m in muestras]
    errores = sum(1 for m in muestras if not m["exitosa"])
    return {
        "muestras": total,
        "errores": errores,
        "errores_pct": 100.0 * errores / total,
        "p50": percentil(tiempos, 50),
        "p90": percentil(tiempos, 90),
        "p95": percentil(tiempos, 95),
        "max": max(tiempos),
    }


def criterios_de(metricas, min_muestras, max_errores, p95_limite):
    """Compara las metricas con los umbrales de PERF-01."""
    total = metricas["muestras"]
    hay_muestras = total > 0
    return [
        (
            f"muestras medidas >= {min_muestras}",
            total >= min_muestras,
            f"{total}",
        ),
        (
            f"tasa de errores < {max_errores:g} %",
            hay_muestras and metricas["errores_pct"] < max_errores,
            f"{metricas['errores_pct']:.2f} %",
        ),
        (
            f"percentil 95 <= {p95_limite:g} ms",
            hay_muestras and metricas["p95"] <= p95_limite,
            f"{metricas['p95']:.0f} ms",
        ),
    ]


def construir_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Evalua el JTL de JMeter contra los criterios de PERF-01 "
            "(consulta de reservaciones)."
        )
    )
    parser.add_argument(
        "--jtl", required=True, help="JTL CSV generado con -l en JMeter"
    )
    parser.add_argument(
        "--etiqueta",
        default=ETIQUETA_POR_DEFECTO,
        help=(
            "regex de la etiqueta de las muestras medidas "
            f"(por defecto {ETIQUETA_POR_DEFECTO})"
        ),
    )
    parser.add_argument(
        "--min-muestras",
        type=int,
        default=MIN_MUESTRAS_POR_DEFECTO,
        help=(
            "minimo de muestras medidas; usa 5 para el humo 1x5 "
            f"(por defecto {MIN_MUESTRAS_POR_DEFECTO})"
        ),
    )
    parser.add_argument(
        "--max-errores",
        type=float,
        default=MAX_ERRORES_POR_DEFECTO,
        help=(
            "tasa de errores maxima en porcentaje, exclusiva "
            f"(por defecto {MAX_ERRORES_POR_DEFECTO:g})"
        ),
    )
    parser.add_argument(
        "--p95",
        type=float,
        default=P95_MS_POR_DEFECTO,
        help=(
            "percentil 95 maximo en milisegundos "
            f"(por defecto {P95_MS_POR_DEFECTO:g})"
        ),
    )
    parser.add_argument(
        "--jtl-filtrado",
        help=(
            "escribe un JTL solo con las muestras medidas, para generar "
            "el reporte HTML sin el login"
        ),
    )
    return parser


def main(argv=None):
    args = construir_parser().parse_args(argv)
    try:
        patron = re.compile(args.etiqueta)
    except re.error as error:
        print(f"ERROR: regex de etiqueta invalida: {error}")
        return 2
    try:
        cabecera, filas, muestras = leer_jtl(args.jtl, patron)
    except (OSError, ValueError) as error:
        print(f"ERROR: no se pudo leer {args.jtl}: {error}")
        return 2
    if args.jtl_filtrado:
        escribir_jtl_filtrado(args.jtl_filtrado, cabecera, filas)
        print(f"JTL filtrado: {args.jtl_filtrado}")
    if not muestras:
        print(
            f"ERROR: ninguna muestra coincide con la etiqueta "
            f"{args.etiqueta!r} en {args.jtl}"
        )
        return 2

    metricas = metricas_de(muestras)
    criterios = criterios_de(
        metricas, args.min_muestras, args.max_errores, args.p95
    )
    print(f"JTL evaluado: {args.jtl}")
    print(f"Etiqueta:     {args.etiqueta}")
    print(f"Muestras:     {metricas['muestras']}")
    print(
        f"Errores:      {metricas['errores']} "
        f"({metricas['errores_pct']:.2f} %)"
    )
    print(
        "Tiempos (ms): "
        f"p50={metricas['p50']:.0f} "
        f"p90={metricas['p90']:.0f} "
        f"p95={metricas['p95']:.0f} "
        f"max={metricas['max']:.0f}"
    )
    print("Criterios:")
    for descripcion, cumple, valor in criterios:
        estado = "CUMPLE" if cumple else "NO CUMPLE"
        print(f"  [{estado}] {descripcion} (observado: {valor})")
    if all(cumple for _, cumple, _ in criterios):
        print("Resultado PERF-01: CUMPLE")
        return 0
    print("Resultado PERF-01: NO CUMPLE")
    return 1


if __name__ == "__main__":
    sys.exit(main())

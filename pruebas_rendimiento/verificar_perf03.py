#!/usr/bin/env python3
"""Verifica el JTL de PERF-03: una aceptacion y un rechazo por ronda.

PERF-03 hace 10 rondas controladas. En cada ronda dos solicitudes
normales y autenticadas piden el mismo horario; el plan las sincroniza
con un Synchronizing Timer (solo el POST medido) y espera exactamente
una aceptacion (HTTP 302 hacia /reservaciones/) y un rechazo controlado
por traslape (HTTP 200 con el mensaje de sala no disponible). El rechazo
esperado NO es un error: el plan lo valida por texto y le deja
`success=true`; cualquier otro HTTP o texto si falla.

El JTL no demuestra por si solo que no se persistieron duplicados: eso
lo responde la auditoria SQL de la base (cuenta de traslapes y filas por
proposito). Este script comprueba la parte observable en el JTL:

* Hay una entrada por ronda con las dos muestras del POST medido.
* Las dos muestras de la ronda usan hilos distintos y la MISMA fecha y
  horario (la etiqueta incluye la ranura pedida).
* Por ronda: exactamente un 302 ACEPTADA_302 y un 200
  RECHAZO_TRASLAPE_200, ambos con success=true.
* Las fechas de las rondas son distintas y consecutivas (10 ranuras
  distintas, una por ronda).
* Ninguna otra muestra del plan (login, formulario) fallo: si el login
  o el CSRF fallaran, las rondas no serian solicitudes legitimas.

Uso:

    python3 verificar_perf03.py --jtl /tmp/opencode/perf03.jtl

Exit codes: 0 si el JTL cumple, 1 si alguna comprobacion falla,
2 si el JTL no se puede leer o no tiene muestras PERF-03.
"""

import argparse
import csv
import datetime
import re
import sys

COLUMNAS_REQUERIDAS = (
    "label", "responseCode", "responseMessage", "success", "threadName",
)
ETIQUETA_POR_DEFECTO = (
    r"^PERF-03 POST ronda (\d{2}) (\d{4}-\d{2}-\d{2}) 08:00-09:00 \(medido\)$"
)
RONDAS_POR_DEFECTO = 10


def leer_muestras(ruta):
    """Devuelve todas las filas del JTL como diccionarios."""
    with open(ruta, newline="", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        if lector.fieldnames is None:
            raise ValueError("el JTL esta vacio")
        faltantes = [c for c in COLUMNAS_REQUERIDAS
                     if c not in lector.fieldnames]
        if faltantes:
            raise ValueError(
                "faltan columnas en el JTL: " + ", ".join(faltantes)
            )
        return [
            {clave: (valor or "").strip() for clave, valor in fila.items()}
            for fila in lector if fila
        ]


def agrupar_rondas(muestras, patron):
    """Agrupa las muestras del POST medido por (ronda, fecha)."""
    rondas = {}
    for muestra in muestras:
        coincidencia = patron.match(muestra["label"])
        if coincidencia:
            clave = (coincidencia.group(1), coincidencia.group(2))
            rondas.setdefault(clave, []).append(muestra)
    return rondas


def problemas_de_pareja(muestras):
    """Comprueba que hay dos hilos pidiendo la misma ranura."""
    if len(muestras) != 2:
        return [
            f"se esperaban 2 muestras y hay {len(muestras)}: una pareja "
            "incompleta indica que el Synchronizing Timer expiro o que un "
            "hilo no llego al POST"
        ]
    problemas = []
    if len({m["threadName"] for m in muestras}) != 2:
        problemas.append("las dos muestras no provienen de hilos distintos")
    if len({m["label"] for m in muestras}) != 1:
        problemas.append(
            "las dos muestras no piden la misma ranura (etiquetas distintas)"
        )
    return problemas


def problemas_de_conteo(aceptadas, rechazos):
    """Comprueba un solo 302 y un solo 200 con sus marcadores."""
    problemas = []
    if len(aceptadas) != 1 or len(rechazos) != 1:
        problemas.append(
            "se esperaba 1 aceptacion (302) y 1 rechazo (200) y hay "
            f"{len(aceptadas)} aceptaciones y {len(rechazos)} rechazos; "
            "dos aceptaciones sugieren que se persistieron solicitudes "
            "traslapadas"
        )
    if aceptadas and aceptadas[0]["responseMessage"] != "ACEPTADA_302":
        problemas.append(
            "la aceptacion no esta marcada como ACEPTADA_302: "
            f"{aceptadas[0]['responseMessage']!r}"
        )
    if rechazos and rechazos[0]["responseMessage"] != "RECHAZO_TRASLAPE_200":
        problemas.append(
            "el rechazo no esta marcado como RECHAZO_TRASLAPE_200: "
            f"{rechazos[0]['responseMessage']!r}"
        )
    return problemas


def problemas_de_exito(muestras):
    """Ninguna muestra de la ronda debe quedar con success=false."""
    fallidas = [m for m in muestras if m["success"].lower() != "true"]
    if not fallidas:
        return []
    return [
        f"{len(fallidas)} muestra(s) de la ronda con success=false; "
        "una aceptacion y un rechazo esperados deben ser success=true"
    ]


def problemas_de_outcome(muestras):
    """Comprueba un 302 aceptado y un 200 rechazado, ambos exitosos."""
    aceptadas = [m for m in muestras if m["responseCode"] == "302"]
    rechazos = [m for m in muestras if m["responseCode"] == "200"]
    return (
        problemas_de_conteo(aceptadas, rechazos)
        + problemas_de_exito(muestras)
    )


def revisar_ronda(muestras):
    """Devuelve los problemas de una ronda; vacia si cumple."""
    problemas = problemas_de_pareja(muestras)
    if problemas:
        return problemas
    return problemas_de_outcome(muestras)


def revisar_fechas(rondas, total):
    """Comprueba que hay una fecha distinta y consecutiva por ronda."""
    fechas = sorted({fecha for _, fecha in rondas})
    if len(fechas) != total:
        return [
            f"se esperaban {total} fechas distintas y hay {len(fechas)}"
        ]
    dias = [datetime.date.fromisoformat(f) for f in fechas]
    for anterior, siguiente in zip(dias, dias[1:]):
        if (siguiente - anterior).days != 1:
            return [
                "las fechas de las rondas no son consecutivas: "
                f"{anterior} y {siguiente}"
            ]
    return []


def errores_fuera_del_post(muestras, patron):
    """Devuelve las muestras fallidas que no son el POST medido."""
    return [
        muestra for muestra in muestras
        if muestra["success"].lower() != "true"
        and not patron.match(muestra["label"])
    ]


def reportar_rondas(rondas, esperadas, problemas):
    """Imprime una linea por ronda y acumula sus problemas."""
    for clave in sorted(rondas):
        ronda, fecha = clave
        grupo = rondas[clave]
        aceptadas = sum(1 for m in grupo if m["responseCode"] == "302")
        rechazos = sum(1 for m in grupo if m["responseCode"] == "200")
        print(
            f"  ronda {ronda} {fecha} 08:00-09:00: "
            f"{len(grupo)} POST, {aceptadas} aceptada(s), "
            f"{rechazos} rechazo(s)"
        )
        problemas.extend(
            f"ronda {ronda} {fecha}: {problema}"
            for problema in revisar_ronda(grupo)
        )
    problemas.extend(revisar_fechas(rondas, esperadas))


def construir_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Verifica el JTL de PERF-03: 10 rondas con una aceptacion y un "
            "rechazo por traslape sobre el mismo horario."
        )
    )
    parser.add_argument(
        "--jtl", required=True,
        help="JTL CSV generado por el plan PERF-03 con -l",
    )
    parser.add_argument(
        "--rondas", type=int, default=RONDAS_POR_DEFECTO,
        help=f"rondas esperadas (por defecto {RONDAS_POR_DEFECTO})",
    )
    parser.add_argument(
        "--etiqueta", default=ETIQUETA_POR_DEFECTO,
        help="regex de la etiqueta del POST medido",
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
        muestras = leer_muestras(args.jtl)
    except (OSError, ValueError) as error:
        print(f"ERROR: no se pudo leer {args.jtl}: {error}")
        return 2

    rondas = agrupar_rondas(muestras, patron)
    if not rondas:
        print(
            f"ERROR: ninguna muestra coincide con la etiqueta "
            f"{args.etiqueta!r} en {args.jtl}"
        )
        return 2

    problemas = []
    print(f"JTL evaluado: {args.jtl}")
    print(f"Rondas encontradas: {len(rondas)} (esperadas: {args.rondas})")
    if len(rondas) != args.rondas:
        problemas.append(
            f"rondas incompletas: {len(rondas)} de {args.rondas}"
        )
    reportar_rondas(rondas, args.rondas, problemas)

    inesperadas = errores_fuera_del_post(muestras, patron)
    print(f"Errores inesperados fuera del POST: {len(inesperadas)}")
    problemas.extend(
        f"muestra fallida ajena al POST: {muestra['label']!r}"
        for muestra in inesperadas
    )

    print("Comprobaciones:")
    if problemas:
        for problema in problemas:
            print(f"  [FALLA] {problema}")
        print("Resultado PERF-03 en JTL: NO CUMPLE")
        return 1
    print(
        "  [CUMPLE] una aceptacion (302) y un rechazo (200) por ronda, "
        "ambos success=true"
    )
    print(
        f"  [CUMPLE] {args.rondas} rondas con ranuras distintas y fechas "
        "consecutivas"
    )
    print("  [CUMPLE] sin errores inesperados en el resto del plan")
    print("Resultado PERF-03 en JTL: CUMPLE")
    print(
        "Recuerda: la ausencia de duplicados persistidos se confirma con "
        "la auditoria SQL de la base, no con este JTL."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

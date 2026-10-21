"""ERP simulado de Distribuciones Brétema: envía extractos de ventas a la capa bronce.

    from herramientas.erp_simulado import enviar_remesa_enero, reenviar_remesa_enero

Cada envío deja un fichero CSV en lakehouse/bronce/erp_ventas/fecha_carga=AAAA-MM-DD/,
como haría una exportación diaria del ERP. La remesa de enero llega con los problemas
típicos de un fichero real; el reenvío corrige los que el ERP puede corregir.
"""
import csv
import random
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRONCE = RAIZ / "lakehouse" / "bronce" / "erp_ventas"
HISTORICO = BRONCE / "fecha_carga=2026-10-15" / "ventas_2024-2025.csv"
ARCHIVO = "ventas_2026-01.csv"


def _base():
    with open(HISTORICO, encoding="utf-8", newline="") as f:
        filas = [r for r in csv.DictReader(f) if r["fecha"].startswith("2025-01")]
    for r in filas:
        r["fecha"] = "2026" + r["fecha"][4:]
    return filas


def _ensuciar(filas, corregido):
    rnd = random.Random(2026)
    idx = list(range(len(filas)))
    rnd.shuffle(idx)
    trozos = {k: [idx.pop() for _ in range(n)] for k, n in
              [("delegacion", 12), ("coma", 20), ("fecha_es", 8), ("sin_unidades", 3), ("fecha_mala", 2), ("ourense", 1)]}
    for i in trozos["delegacion"]:
        filas[i]["delegacion"] = rnd.choice([" lugo", "CORUÑA", "santiago ", "Coruña"])
    for i in trozos["coma"]:
        filas[i]["precio_unitario"] = filas[i]["precio_unitario"].replace(".", ",")
    for i in trozos["fecha_es"]:
        a, m, d = filas[i]["fecha"].split("-")
        filas[i]["fecha"] = f"{d}/{m}/{a}"
    for i in trozos["fecha_mala"]:
        filas[i]["fecha"] = "31/02/2026"
    if not corregido:
        for i in trozos["sin_unidades"]:
            filas[i]["unidades"] = ""
        for i in trozos["ourense"]:
            filas[i]["delegacion"] = "Ourense"
    return filas


def _escribir(filas, fecha_carga):
    carpeta = BRONCE / f"fecha_carga={fecha_carga}"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / ARCHIVO
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)
    print(f"📨 El ERP ha dejado {ruta.relative_to(RAIZ)} ({len(filas)} filas)")
    return ruta


def enviar_remesa_enero():
    """Primera entrega de enero de 2026: llega sucia."""
    return _escribir(_ensuciar(_base(), corregido=False), "2026-10-16")


def reenviar_remesa_enero():
    """Reenvío del mismo fichero, corregido en origen por el equipo del ERP."""
    return _escribir(_ensuciar(_base(), corregido=True), "2026-10-17")

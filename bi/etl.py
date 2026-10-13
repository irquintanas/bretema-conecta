#!/usr/bin/env python3
"""
Brétema Pulso · ETL básico del equipo de datos (pieza BI de Brétema Conecta)

    python bi/etl.py

  1. EXTRAER     lee el extracto del ERP: datos/ventas.csv (el mismo fichero que usa el portal)
  2. TRANSFORMAR comprueba cada fila, convierte tipos y calcula importe y coste
  3. CARGAR      guarda un modelo en estrella en bi/bretema.db (SQLite)

El modelo: una tabla de hechos (hechos_ventas, una fila por línea de venta) y cinco
dimensiones (dim_fecha, dim_producto, dim_cliente, dim_comercial, dim_delegacion).

Definición común con el portal (diccionario del proyecto):
  ventas netas = unidades × precio_unitario, y las devoluciones (unidades < 0) restan.

Solo usa la biblioteca estándar de Python. bi/bretema.db es un resultado: no se sube a git.
"""
import csv
import sqlite3
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "datos" / "ventas.csv"
DESTINO = RAIZ / "bi" / "bretema.db"
COLUMNAS = ["fecha", "delegacion", "comercial", "cliente_id", "canal", "familia", "producto",
            "unidades", "precio_unitario", "coste_unitario"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


# ───────────────────────────── 1 · EXTRAER ─────────────────────────────
def extraer():
    with open(ORIGEN, encoding="utf-8", newline="") as f:
        lector = csv.DictReader(f)
        if lector.fieldnames != COLUMNAS:
            sys.exit(f"❌ datos/ventas.csv no tiene las columnas acordadas: {', '.join(COLUMNAS)}")
        return list(lector)


# ───────────────────────────── 2 · TRANSFORMAR ─────────────────────────────
def transformar(filas):
    buenas, rechazadas = [], []
    for n, r in enumerate(filas, start=2):
        try:
            if any(not r[c].strip() for c in COLUMNAS):
                raise ValueError("hay campos vacíos")
            f = date.fromisoformat(r["fecha"])
            u = int(r["unidades"])
            p, c = float(r["precio_unitario"]), float(r["coste_unitario"])
            if u == 0 or p <= 0 or c < 0:
                raise ValueError("unidades, precio o coste fuera de rango")
        except ValueError as ex:
            rechazadas.append((n, str(ex)))
            continue
        buenas.append({**{k: r[k].strip() for k in COLUMNAS}, "fecha": f, "unidades": u,
                       "precio": p, "coste": c, "importe": round(u * p, 2), "coste_total": round(u * c, 2)})
    return buenas, rechazadas


# ───────────────────────────── 3 · CARGAR ─────────────────────────────
ESQUEMA = """
CREATE TABLE dim_fecha      (fecha_id INTEGER PRIMARY KEY, fecha TEXT, anio INTEGER, trimestre INTEGER,
                             mes INTEGER, nombre_mes TEXT);
CREATE TABLE dim_delegacion (delegacion_id INTEGER PRIMARY KEY, delegacion TEXT UNIQUE);
CREATE TABLE dim_producto   (producto_id INTEGER PRIMARY KEY, producto TEXT UNIQUE, familia TEXT);
CREATE TABLE dim_cliente    (cliente_id TEXT PRIMARY KEY, canal TEXT, delegacion TEXT);
CREATE TABLE dim_comercial  (comercial_id INTEGER PRIMARY KEY, comercial TEXT UNIQUE, delegacion TEXT);
CREATE TABLE hechos_ventas  (fecha_id INTEGER REFERENCES dim_fecha, delegacion_id INTEGER REFERENCES dim_delegacion,
                             producto_id INTEGER REFERENCES dim_producto, cliente_id TEXT REFERENCES dim_cliente,
                             comercial_id INTEGER REFERENCES dim_comercial,
                             unidades INTEGER, precio REAL, importe REAL, coste REAL);
"""


def cargar(filas):
    DESTINO.unlink(missing_ok=True)
    con = sqlite3.connect(DESTINO)
    con.executescript(ESQUEMA)

    def clave(tabla, columna, valor, extra=()):
        """Devuelve la clave de un valor en su dimensión; si no existe, lo da de alta."""
        fila = con.execute(f"SELECT rowid FROM {tabla} WHERE {columna} = ?", (valor,)).fetchone()
        if fila:
            return fila[0]
        return con.execute(f"INSERT INTO {tabla} VALUES (NULL, ?{', ?' * len(extra)})", (valor, *extra)).lastrowid

    for r in filas:
        f = r["fecha"]
        fecha_id = int(f.strftime("%Y%m%d"))
        con.execute("INSERT OR IGNORE INTO dim_fecha VALUES (?, ?, ?, ?, ?, ?)",
                    (fecha_id, f.isoformat(), f.year, (f.month - 1) // 3 + 1, f.month, MESES[f.month - 1]))
        con.execute("INSERT OR IGNORE INTO dim_cliente VALUES (?, ?, ?)", (r["cliente_id"], r["canal"], r["delegacion"]))
        con.execute("INSERT INTO hechos_ventas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            fecha_id,
            clave("dim_delegacion", "delegacion", r["delegacion"]),
            clave("dim_producto", "producto", r["producto"], (r["familia"],)),
            r["cliente_id"],
            clave("dim_comercial", "comercial", r["comercial"], (r["delegacion"],)),
            r["unidades"], r["precio"], r["importe"], r["coste_total"]))
    con.commit()
    resumen = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
               for t in ["hechos_ventas", "dim_fecha", "dim_producto", "dim_cliente", "dim_comercial", "dim_delegacion"]}
    con.close()
    return resumen


if __name__ == "__main__":
    filas = extraer()
    print(f"1 · Extraer      {len(filas):>6} filas leídas de datos/ventas.csv")
    buenas, rechazadas = transformar(filas)
    print(f"2 · Transformar  {len(buenas):>6} filas válidas · {len(rechazadas)} rechazadas")
    for n, motivo in rechazadas[:10]:
        print(f"      ⚠️  línea {n}: {motivo}")
    resumen = cargar(buenas)
    print(f"3 · Cargar       {resumen.pop('hechos_ventas'):>6} filas en hechos_ventas (bi/bretema.db)")
    print("                 dimensiones: " + " · ".join(f"{t[4:]} {n}" for t, n in resumen.items()))
    print("✅ ETL terminado.")

#!/usr/bin/env python3
"""
Brétema Pulso · consultas del cuadro de mando interno

    python bi/cuadro.py

Lee el modelo en estrella de bi/bretema.db (lo crea bi/etl.py) con consultas SQL y deja
el resultado en bi/cuadro.json. El portal (web/build.py) lo usa para generar el área interna.

Cada «ámbito» es lo que puede ver un usuario: «Brétema» (toda la empresa, para Dirección)
o una delegación (para su jefe de delegación).
"""
import json
import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BD = RAIZ / "bi" / "bretema.db"
SALIDA = RAIZ / "bi" / "cuadro.json"

# Todas las consultas parten de la tabla de hechos y se unen a las dimensiones que necesitan.
BASE = """
FROM hechos_ventas h
JOIN dim_fecha f        USING (fecha_id)
JOIN dim_delegacion d   USING (delegacion_id)
JOIN dim_producto p     USING (producto_id)
JOIN dim_cliente c      USING (cliente_id)
JOIN dim_comercial m    USING (comercial_id)
WHERE (:delegacion IS NULL OR d.delegacion = :delegacion)
"""

KPIS = """
SELECT SUM(CASE WHEN f.anio = :anio THEN h.importe END)                         AS ventas,
       SUM(CASE WHEN f.anio = :anterior THEN h.importe END)                     AS ventas_anterior,
       SUM(CASE WHEN f.anio = :anio THEN h.coste END)                           AS coste,
       COUNT(DISTINCT CASE WHEN f.anio = :anio THEN h.cliente_id END)           AS clientes,
       -SUM(CASE WHEN f.anio = :anio AND h.unidades < 0 THEN h.importe END)     AS devoluciones
""" + BASE

POR_MES = """
SELECT f.mes,
       SUM(CASE WHEN f.anio = :anterior THEN h.importe ELSE 0 END) AS anterior,
       SUM(CASE WHEN f.anio = :anio THEN h.importe ELSE 0 END)     AS actual
""" + BASE + " GROUP BY f.mes ORDER BY f.mes"

POR = """
SELECT {campo} AS nombre,
       SUM(CASE WHEN f.anio = :anio THEN h.importe ELSE 0 END)     AS ventas,
       SUM(CASE WHEN f.anio = :anterior THEN h.importe ELSE 0 END) AS anterior,
       SUM(CASE WHEN f.anio = :anio THEN h.coste ELSE 0 END)       AS coste,
       COUNT(DISTINCT CASE WHEN f.anio = :anio THEN h.cliente_id END) AS clientes
""" + BASE + " GROUP BY {campo} ORDER BY ventas DESC"


def consultar(con, delegacion, anio):
    p = {"delegacion": delegacion, "anio": anio, "anterior": anio - 1}
    k = con.execute(KPIS, p).fetchone()

    def lista(campo, limite=None):
        filas = con.execute(POR.format(campo=campo), p).fetchall()[:limite]
        return [{"nombre": r[0], "ventas": round(r[1]), "anterior": round(r[2]),
                 "margen": round(100 * (1 - r[3] / r[1]), 1) if r[1] else 0, "clientes": r[4]} for r in filas]

    return {
        "kpis": {"ventas": round(k[0]), "anterior": round(k[1]), "margen": round(100 * (1 - k[2] / k[0]), 1),
                 "clientes": k[3], "devoluciones": round(k[4] or 0)},
        "meses": [{"mes": r[0], "anterior": round(r[1]), "actual": round(r[2])} for r in con.execute(POR_MES, p)],
        "familias": lista("p.familia"),
        "canales": lista("c.canal"),
        "comerciales": lista("m.comercial", 10),
        "delegaciones": lista("d.delegacion") if delegacion is None else [],
    }


if __name__ == "__main__":
    if not BD.exists():
        sys.exit("❌ No existe bi/bretema.db: ejecuta antes python bi/etl.py")
    con = sqlite3.connect(BD)
    anio = con.execute("SELECT MAX(anio) FROM dim_fecha").fetchone()[0]
    delegaciones = [r[0] for r in con.execute("SELECT delegacion FROM dim_delegacion ORDER BY delegacion")]
    cuadro = {"anio": anio, "anterior": anio - 1,
              "ambitos": {"Brétema": consultar(con, None, anio),
                          **{d: consultar(con, d, anio) for d in delegaciones}}}
    con.close()
    SALIDA.write_text(json.dumps(cuadro, ensure_ascii=False, indent=1), encoding="utf-8")
    t = cuadro["ambitos"]["Brétema"]["kpis"]
    ventas = f"{t['ventas']:,}".replace(",", ".")
    margen = str(t["margen"]).replace(".", ",")
    print(f"📊 bi/cuadro.json · {len(cuadro['ambitos'])} ámbitos · ventas netas {anio}: {ventas} € · margen bruto {margen} %")

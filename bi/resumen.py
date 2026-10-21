#!/usr/bin/env python3
"""
Brétema Pulso · resumen del lakehouse en Markdown

    python bi/resumen.py >> "$GITHUB_STEP_SUMMARY"

Lee el resultado de la última ejecución de dbt (dbt/target/run_results.json) y la capa plata y oro
(lakehouse/), y escribe tres tablas: los tests con PASS o FAIL, las filas en cuarentena y las ventas
por mes del oro. GitHub Actions lo enseña en la página de la ejecución, sin descargar nada.
"""
import json
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "dbt" / "target" / "run_results.json"
PLATA = RAIZ / "lakehouse" / "plata"
ORO = RAIZ / "lakehouse" / "oro"
ESTADOS = {"pass": "✅ PASS", "fail": "❌ FAIL", "error": "❌ ERROR", "skipped": "⏭️ SKIP", "success": "✅ OK",
           "warn": "⚠️ WARN"}


def tabla(cabecera, filas):
    lineas = ["| " + " | ".join(cabecera) + " |", "|" + "---|" * len(cabecera)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


def euros(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def tests():
    print("## Tests de dbt\n")
    if not RESULTADOS.exists():
        print("No hay resultado de dbt: `dbt build` no llegó a ejecutarse.\n")
        return
    resultados = json.loads(RESULTADOS.read_text(encoding="utf-8"))["results"]
    rango = {"fail": 0, "error": 0, "warn": 1, "skipped": 2}      # primero lo que falla
    resultados.sort(key=lambda r: (rango.get(r["status"], 3), r["unique_id"]))
    filas = []
    for r in resultados:
        fallos = f" ({r['failures']} filas)" if r.get("failures") else ""
        filas.append((r["unique_id"].split(".")[0], f"`{r['unique_id'].split('.')[2]}`",
                      ESTADOS.get(r["status"], r["status"]) + fallos))
    malos = sum(1 for r in resultados if r["status"] in ("fail", "error"))
    saltados = sum(1 for r in resultados if r["status"] == "skipped")
    print(f"**{len(resultados)} pasos:** {len(resultados) - malos - saltados} correctos, {malos} con error, {saltados} saltados.\n")
    print(tabla(["Tipo", "Nombre", "Resultado"], filas) + "\n")


def cuarentena():
    print("## Filas en cuarentena\n")
    ruta = PLATA / "stg_ventas_cuarentena.parquet"
    if not ruta.exists():
        print("La capa plata no se ha construido.\n")
        return
    filas = duckdb.sql(f"""
        select archivo, fecha_carga, motivo_rechazo, delegacion, cliente_id, unidades
        from read_parquet('{ruta.as_posix()}') order by archivo, motivo_rechazo limit 50""").fetchall()
    total = duckdb.sql(f"select count(*) from read_parquet('{ruta.as_posix()}')").fetchone()[0]
    if not total:
        print("Ninguna: todas las líneas de la última entrega eran válidas.\n")
        return
    print(f"**{total} filas** apartadas de plata para revisarlas con quien las envió"
          f"{' (se muestran las 50 primeras)' if total > 50 else ''}.\n")
    print(tabla(["Fichero", "Entrega", "Motivo", "Delegación", "Cliente", "Unidades"],
                [tuple("" if c is None else c for c in f) for f in filas]) + "\n")


def ventas():
    print("## Ventas por mes del oro\n")
    ruta = ORO / "ventas_mes.parquet"
    if not ruta.exists():
        print("El oro no se ha construido: si un test falla, dbt no construye lo que depende de él.\n")
        return
    filas = duckdb.sql(f"""
        select anio, mes, sum(ventas_netas)
        from read_parquet('{ruta.as_posix()}') group by anio, mes order by anio, mes""").fetchall()
    print(tabla(["Año", "Mes", "Ventas netas"], [(a, f"{m:02d}", euros(float(v))) for a, m, v in filas]) + "\n")


if __name__ == "__main__":
    tests()
    cuarentena()
    ventas()

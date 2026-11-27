"""Índice navegable del lakehouse: copia plata y oro (Parquet) a _site/lakehouse/ y genera su index.html.

GitHub Pages no lista carpetas. Esta página enseña qué Parquet se han generado, cuántas filas y columnas
tiene cada uno y desde dónde se pueden leer. La llama web/build.py cuando el oro está construido.
"""
import html
import os
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LAKE = RAIZ / "lakehouse"
CAPAS = {"oro": "Listo para analizar: dimensiones, hechos y tablas agregadas.",
         "plata": "Datos tipados y validados, incluidas las filas en cuarentena."}
e = html.escape


def disponible():
    """Hay índice si el oro está construido y DuckDB está instalado."""
    try:
        import duckdb  # noqa: F401
    except ImportError:
        return False
    return any((LAKE / "oro").glob("*.parquet"))


def aviso_interno():
    return ('<p class="aviso-lakehouse"><a href="../lakehouse/index.html">Ver el lakehouse →</a> '
            '<span>los ficheros Parquet de plata y oro que genera dbt</span></p>')


def _miles(n):
    return f"{n:,}".replace(",", ".")


def _tamano(n):
    return f"{n / 1024:,.1f} KB".replace(",", "X").replace(".", ",").replace("X", ".")


def _url_publica():
    """URL del lakehouse en GitHub Pages; en local no hay (devuelve None)."""
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return None
    propietario, nombre = repo.split("/", 1)
    return f"https://{propietario.lower()}.github.io/{nombre}/lakehouse"


def _ejecucion():
    """Enlace a la ejecución de GitHub Actions que ha generado los ficheros."""
    repo, run = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_RUN_ID")
    if not (repo and run):
        return "Generado en un equipo local."
    url = f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{run}"
    return f'Generado por <a href="{e(url)}">esta ejecución de GitHub Actions</a>.'


def generar(salida, pagina, nav):
    """Escribe salida/lakehouse/ (Parquet e index.html). Devuelve el número de ficheros publicados."""
    import duckdb

    destino = salida / "lakehouse"
    con = duckdb.connect()
    secciones, total, ejemplo = [], 0, None
    for capa, descripcion in CAPAS.items():
        (destino / capa).mkdir(parents=True, exist_ok=True)
        filas = []
        for origen in sorted((LAKE / capa).glob("*.parquet")):
            copia = destino / capa / origen.name
            shutil.copy(origen, copia)
            vacia = con.execute("select * from read_parquet(?) limit 0", [str(copia)])
            columnas = [c[0] for c in vacia.description]
            n = con.execute("select count(*) from read_parquet(?)", [str(copia)]).fetchone()[0]
            # Si un modelo no devuelve filas, dbt-duckdb escribe una con todo nulo para conservar las columnas
            relleno = n == 1 and all(v is None for v in
                                     con.execute("select * from read_parquet(?)", [str(copia)]).fetchone())
            cuenta = '0 <small>(el fichero lleva una fila de nulos)</small>' if relleno else _miles(n)
            ruta = f"{capa}/{origen.name}"
            ejemplo = ejemplo or ruta
            filas.append(f'<tr><td><a href="{e(ruta)}" download>{e(origen.name)}</a></td>'
                         f'<td class="num">{cuenta}</td>'
                         f'<td><details><summary>{len(columnas)}</summary>{e(", ".join(columnas))}</details></td>'
                         f'<td class="num">{_tamano(copia.stat().st_size)}</td></tr>')
        total += len(filas)
        if filas:
            secciones.append(f'<section><h2>{capa.capitalize()} <span class="fuente">{len(filas)} ficheros</span></h2>'
                             f'<p>{descripcion}</p><div class="scroll"><table><tr><th>Fichero</th><th>Filas</th>'
                             f'<th>Columnas</th><th>Tamaño</th></tr>{"".join(filas)}</table></div></section>')
    con.close()

    base = _url_publica()
    consulta = f"select * from '{base}/{ejemplo}';" if base else f"select * from '_site/lakehouse/{ejemplo}';"
    cuerpo = (f'<div class="lakehouse"><p class="volver"><a href="../interno/index.html">← Volver al área interna</a></p>'
              f'<h1>Lakehouse de Brétema</h1>'
              f'<p>bronce (CSV del ERP) → dbt → <b>plata y oro (Parquet)</b>. {_ejecucion()} '
              f'La fecha y el commit figuran al pie de la página.</p>'
              f'{"".join(secciones)}'
              f'<section><h2>Cómo leer un fichero</h2><p>Con DuckDB:</p>'
              f'<pre><code>{e(consulta)}</code></pre></section></div>')
    (destino / "index.html").write_text(pagina("Lakehouse · Brétema Conecta", cuerpo, nav, "../"), encoding="utf-8")
    return total

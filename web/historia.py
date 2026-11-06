"""Jornada 7 · La historia: las páginas de paginas/historia/ en el área interna de Brétema Conecta.

    paginas/historia/historia.md         → _site/interno/historia.html          (la historia para la dirección)
    paginas/historia/historia-pasos.md   → _site/interno/historia-pasos.html    (cómo se construyó)

Es el ejemplo resuelto de la Jornada 7, con los mismos bloques que los portales de los casos individuales:

- Marcas {{ modelo.columna[i] }} y {{ modelo.filas }}: valor de la columna (fila i) de un modelo del lakehouse
  (lakehouse/oro/ y, si no está, lakehouse/plata/). Ninguna cifra se escribe a mano.
- ```grafico: cinco tipos (barras, linea, histograma, calor y eje), dibujados por web/graficos.py.
- ```cifras: tarjetas de cifras, una línea «cifra | qué es» por tarjeta.

Las cifras salen del oro, así que hace falta haber ejecutado dbt build y tener DuckDB instalado
(pip install -r requirements.txt). Si no, el portal público se genera igual y la historia se salta.
"""
import html
import re
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graficos  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CARPETA = RAIZ / "paginas" / "historia"
LAKE = RAIZ / "lakehouse"
PAGINAS = [("historia", "La historia"), ("historia-pasos", "Cómo se construyó la historia")]
MARCA = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)(?:\[(\d+)\])?\s*\}\}")
e = html.escape


def disponible():
    """(sí o no, motivo): la historia necesita sus páginas, DuckDB y el oro construido."""
    if not any((CARPETA / f"{n}.md").exists() for n, _ in PAGINAS):
        return False, "no hay páginas en paginas/historia/"
    try:
        import duckdb  # noqa: F401
    except ImportError:
        return False, "falta DuckDB (pip install -r requirements.txt)"
    if not any((LAKE / "oro").glob("*.parquet")):
        return False, "el oro no está construido (dbt build --project-dir dbt --profiles-dir dbt)"
    return True, ""


# ─────────────────────────── datos del lakehouse ───────────────────────────
def parquet(modelo):
    for capa in ("oro", "plata"):
        ruta = LAKE / capa / f"{modelo}.parquet"
        if ruta.exists():
            return ruta
    return None


def leer(modelo, limite=None):
    """Columnas y filas de un modelo, o None si no existe."""
    import duckdb
    ruta = parquet(modelo)
    if ruta is None:
        return None
    rel = duckdb.sql(f"select * from read_parquet('{ruta.as_posix()}')")
    filas = (rel.limit(limite) if limite else rel).fetchall()
    if len(filas) == 1 and all(v is None for v in filas[0]):
        filas = []
    return rel.columns, filas


def formato(v):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "sí" if v else "no"
    if isinstance(v, Decimal):
        v = int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    if isinstance(v, float):
        if v.is_integer() and abs(v) < 1e15:
            return f"{int(v):,}".replace(",", ".")
        decimales = 2 if abs(v) >= 1 else 3
        texto = f"{v:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return texto.rstrip("0").rstrip(",") if "," in texto else texto
    return str(v)


def valor_marca(m):
    modelo, columna, i = m.group(1), m.group(2), int(m.group(3) or 0)
    datos = leer(modelo)
    if datos is None:
        return None, f"el modelo {modelo} no existe (¿has ejecutado dbt build?)"
    if columna == "filas" and m.group(3) is None:
        return formato(len(datos[1])), None
    cols, filas = datos
    if columna not in cols:
        return None, f"{modelo} no tiene la columna {columna} (tiene: {', '.join(cols)})"
    if i >= len(filas):
        return None, f"{modelo} solo tiene {len(filas)} filas: no hay fila {i}"
    return formato(filas[i][cols.index(columna)]), None


def con_marcas(texto):
    return MARCA.sub(lambda m: valor_marca(m)[0] or f"⚠️ {m.group(0)}", texto)


# ─────────────────────────── bloques y Markdown ───────────────────────────
def bloques(texto, tipo):
    lineas, out, i = texto.splitlines(), [], 0
    while i < len(lineas):
        if lineas[i].strip() == f"```{tipo}":
            j = i + 1
            while j < len(lineas) and not lineas[j].startswith("```"):
                j += 1
            out.append((i + 1, lineas[i + 1:j]))
            i = j
        i += 1
    return out


def cifras_html(cuerpo):
    tarjetas = []
    for l in cuerpo:
        if "|" in l:
            valor, _, etiqueta = l.partition("|")
            tarjetas.append(f'<div class="cifra"><span class="v">{e(valor.strip())}</span><span class="t">{e(etiqueta.strip())}</span></div>')
    return f'<div class="cifras">{"".join(tarjetas)}</div>'


def md_a_html(texto):
    """Markdown sencillo: títulos, párrafos, listas, tablas, citas, **negrita**, *cursiva*, `código` y [enlaces](url)."""
    def enlinea(t):
        out = []
        for p in re.split(r"(`[^`]+`)", t):
            if p.startswith("`") and p.endswith("`") and len(p) > 1:
                out.append(f"<code>{e(p[1:-1])}</code>")
                continue
            p = e(p)
            p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
            p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
            p = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', p)
            out.append(p)
        return "".join(out)

    out, lineas, i = [], texto.splitlines(), 0
    while i < len(lineas):
        l = lineas[i]
        if not l.strip():
            i += 1
            continue
        if l.startswith("```"):
            j = i + 1
            while j < len(lineas) and not lineas[j].startswith("```"):
                j += 1
            cuerpo = lineas[i + 1:j]
            if l.strip() == "```grafico":
                out.append(graficos.dibujar(cuerpo, leer, formato)[0])
            elif l.strip() == "```cifras":
                out.append(cifras_html(cuerpo))
            else:
                out.append("<pre><code>" + e("\n".join(cuerpo)) + "</code></pre>")
            i = j + 1
            continue
        if l.startswith("#"):
            nivel = min(len(l) - len(l.lstrip("#")), 3)
            out.append(f"<h{nivel}>{enlinea(l.lstrip('#').strip())}</h{nivel}>")
            i += 1
            continue
        bloque = []
        while i < len(lineas) and lineas[i].strip() and not lineas[i].startswith(("#", "```")):
            bloque.append(lineas[i])
            i += 1
        if all(b.lstrip().startswith("|") for b in bloque) and len(bloque) >= 2:
            celdas = [[c.strip() for c in b.strip().strip("|").split("|")] for b in bloque]
            filas = [c for c in celdas[1:] if not all(re.fullmatch(r":?-{2,}:?", x) for x in c)]
            out.append('<div class="scroll"><table><tr>' + "".join(f"<th>{enlinea(c)}</th>" for c in celdas[0]) + "</tr>" +
                       "".join("<tr>" + "".join(f"<td>{enlinea(c)}</td>" for c in f) + "</tr>" for f in filas) + "</table></div>")
        elif all(re.match(r"\s*[-*] ", b) for b in bloque):
            items = [enlinea(re.sub(r"^\s*[-*] ", "", b)) for b in bloque]
            out.append("<ul>" + "".join("<li>" + x + "</li>" for x in items) + "</ul>")
        elif all(re.match(r"\s*\d+\. ", b) for b in bloque):
            items = [enlinea(re.sub(r"^\s*\d+\. ", "", b)) for b in bloque]
            out.append("<ol>" + "".join("<li>" + x + "</li>" for x in items) + "</ol>")
        elif all(b.startswith(">") for b in bloque):
            out.append("<blockquote>" + enlinea(" ".join(b.lstrip(">").strip() for b in bloque)) + "</blockquote>")
        else:
            out.append(f"<p>{enlinea(' '.join(b.strip() for b in bloque))}</p>")
    return "\n".join(out)


# ─────────────────────────── comprobación y páginas ───────────────────────────
def comprobar():
    """(errores, tipos de gráfico usados). Solo se llama si disponible()."""
    errores, tipos = [], set()
    for nombre, _ in PAGINAS:
        ruta = CARPETA / f"{nombre}.md"
        sitio = f"paginas/historia/{nombre}.md"
        if not ruta.exists():
            errores.append(f"{sitio}: falta la página")
            continue
        texto = ruta.read_text(encoding="utf-8")
        for m in MARCA.finditer(texto):
            _, motivo = valor_marca(m)
            if motivo:
                errores.append(f"{sitio}, línea {texto[:m.start()].count(chr(10)) + 1}: la marca {m.group(0)} no tiene valor: {motivo}")
        for linea, cuerpo in bloques(texto, "grafico"):
            g, fallos = graficos.preparar([MARCA.sub(lambda m: valor_marca(m)[0] or "", l) for l in cuerpo], leer, formato)
            if g:
                tipos.add(g["tipo"])
            errores += [f"{sitio}, gráfico de la línea {linea}: {f}" for f in fallos]
        if nombre == "historia":
            primera = next((l for l in texto.splitlines() if l.strip()), "")
            if not primera.startswith("# ") or not MARCA.search(primera):
                errores.append(f"{sitio}: la primera línea es el titular («# …») y lleva al menos una marca {{{{ … }}}}")
    return errores, tipos


def submenu(activa):
    enlaces = [("index", "Cuadro de mando")] + PAGINAS
    return ('<nav class="sub-interno">' + "".join(
        f'<a href="{n}.html"{" class=activa" if n == activa else ""}>{e(t)}</a>' for n, t in enlaces) + "</nav>")


def generar(salida, pagina, nav):
    """Escribe las dos páginas en salida/ (la carpeta del área interna) con el envoltorio del portal."""
    for nombre, titulo in PAGINAS:
        texto = con_marcas((CARPETA / f"{nombre}.md").read_text(encoding="utf-8"))
        cuerpo = f'{submenu(nombre)}<article class="historia">{md_a_html(texto)}</article>'
        (salida / f"{nombre}.html").write_text(pagina(f"{titulo} · Brétema Pulso", cuerpo, nav, "../"), encoding="utf-8")


def aviso_interno():
    """El acceso a la historia desde la portada del área interna."""
    return (f'{submenu("index")}<section class="aviso-historia"><span class="num">Jornada 7 · La historia</span>'
            '<a href="historia.html"><strong>La historia para la dirección</strong>: cuándo se juega la campaña de Vinos</a>'
            '<a href="historia-pasos.html">Cómo se construyó la historia</a></section>')

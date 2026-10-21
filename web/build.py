#!/usr/bin/env python3
"""
Brétema Conecta · portal web de Distribuciones Brétema (proyecto del MTIDE 3.1)

Comprueba el contenido y genera la web en la carpeta _site/.

    python web/build.py --check   # solo comprueba (lo que hace GitHub en cada pull request)
    python web/build.py           # comprueba y genera _site/ (abre _site/index.html en el navegador)

Solo usa la biblioteca estándar de Python: no hay que instalar nada.

Las páginas (paginas/familias/*.md y paginas/delegaciones/*.md) llevan el texto que escribe
cada persona del equipo. Las cifras las calcula este script a partir de lakehouse/bronce/erp_ventas/,
lo que entrega el ERP: nadie las teclea.

Si existe bi/cuadro.json (lo genera el equipo de datos con dbt build y bi/cuadro.py), genera también
el área interna _site/interno/ y comprueba que portal y cuadro de mando dan las mismas ventas.
"""
import csv
import html
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINAS = RAIZ / "paginas"
BRONCE = RAIZ / "lakehouse" / "bronce" / "erp_ventas"   # lo que entrega el ERP: una carpeta por fecha de carga
PLAN = RAIZ / "web" / "plan.csv"
SECCIONES = RAIZ / "secciones.csv"
CUADRO = RAIZ / "bi" / "cuadro.json"     # lo genera el equipo de datos (dbt build + bi/cuadro.py)
SALIDA = RAIZ / "_site"
CABECERA_SECCIONES = ["orden", "tarea", "titulo"]
CARPETA = {"familia": "familias", "delegacion": "delegaciones"}
MARCAS = ("<<<<<<<", "=======", ">>>>>>>")
e = html.escape


# ─────────────────────────── lectura ───────────────────────────
def leer_csv(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def plan():
    filas = leer_csv(PLAN)
    return {f[0]: {"tipo": f[1], "nombre": f[2], "archivo": f[3]} for f in filas[1:] if f}


def leer_pagina(ruta):
    """Devuelve (datos, texto) de una página con cabecera entre líneas '---'."""
    lineas = ruta.read_text(encoding="utf-8").splitlines()
    if not lineas or lineas[0].strip() != "---":
        raise ValueError("la página debe empezar con una línea '---'")
    try:
        fin = lineas.index("---", 1)
    except ValueError:
        raise ValueError("falta la línea '---' que cierra la cabecera")
    datos = {}
    for n, linea in enumerate(lineas[1:fin], start=2):
        if not linea.strip():
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", linea)
        if not m:
            raise ValueError(f"línea {n} de la cabecera no se entiende: «{linea.strip()}»")
        datos[m.group(1)] = m.group(2).strip()
    texto = "\n".join(lineas[fin + 1:])
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.S).strip()
    return datos, texto


def paginas():
    """Lista de (tipo, ruta) de todas las páginas escritas por el equipo."""
    out = []
    for tipo, carpeta in CARPETA.items():
        out += [(tipo, p) for p in sorted((PAGINAS / carpeta).glob("*.md"))]
    return out


# ─────────────────────────── datos (la pieza de datos del proyecto) ───────────────────────────
def ventas_erp():
    """Líneas de venta del ERP, con la misma regla que la capa plata del lakehouse (dbt).

    Del bronce se queda, de cada fichero, con la entrega más reciente (el ERP reenvía los ficheros
    corregidos); acepta fechas dd/mm/aaaa y precios con coma, unifica las formas de escribir la delegación
    y descarta las líneas ilegibles (en el lakehouse van a la cuarentena de plata).
    """
    entregas = {}
    for ruta in sorted(BRONCE.glob("fecha_carga=*/*.csv")):
        entregas[ruta.name] = ruta                    # el orden alfabético de las fechas deja la última
    delegaciones = {"a coruña": "A Coruña", "coruña": "A Coruña", "santiago": "Santiago", "lugo": "Lugo"}
    filas = []
    for ruta in entregas.values():
        with open(ruta, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                try:
                    texto = r["fecha"].strip()
                    fecha = (datetime.strptime(texto, "%d/%m/%Y") if "/" in texto else datetime.strptime(texto, "%Y-%m-%d"))
                    unidades = int(r["unidades"])
                    precio = float(r["precio_unitario"].replace(",", "."))
                except ValueError:
                    continue
                filas.append({**{k: v.strip() for k, v in r.items()}, "fecha": fecha.strftime("%Y-%m-%d"),
                              "delegacion": delegaciones.get(r["delegacion"].strip().lower(), r["delegacion"].strip()),
                              "cliente_id": r["cliente_id"].strip().upper(),
                              "unidades": str(unidades), "precio_unitario": str(precio)})
    return filas


def cifras():
    """Calcula las cifras de la web a partir del extracto del ERP."""
    filas = ventas_erp()
    anio = max(r["fecha"][:4] for r in filas)
    fam = defaultdict(lambda: {"productos": set(), "precio_min": None, "unidades": defaultdict(int), "ventas": 0.0})
    dele = defaultdict(lambda: {"clientes": set(), "comerciales": set(), "ventas": 0.0, "hosteleria": 0.0,
                                "familias": defaultdict(float)})
    total, clientes = 0.0, set()
    for r in filas:
        u, p = int(r["unidades"]), float(r["precio_unitario"])
        f = fam[r["familia"]]
        f["productos"].add(r["producto"])
        f["precio_min"] = p if f["precio_min"] is None else min(f["precio_min"], p)
        clientes.add(r["cliente_id"])
        d = dele[r["delegacion"]]
        d["clientes"].add(r["cliente_id"])
        d["comerciales"].add(r["comercial"])
        if r["fecha"][:4] == anio:
            importe = u * p                      # las devoluciones (unidades < 0) restan
            f["unidades"][r["producto"]] += u
            f["ventas"] += importe
            d["ventas"] += importe
            d["familias"][r["familia"]] += importe
            if r["canal"] == "Hostelería":
                d["hosteleria"] += importe
            total += importe
    return {"anio": anio, "familias": fam, "delegaciones": dele, "total": total,
            "n_clientes": len(clientes), "n_productos": len({r["producto"] for r in filas})}


def euros(x):
    return f"{x:,.0f} €".replace(",", ".")


def euros2(x):
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# ─────────────────────────── comprobación ───────────────────────────
def comprobar():
    errores, avisos = [], []
    pl = plan()
    datos = cifras()

    # 1 · restos de un conflicto mal resuelto
    for ruta in [SECCIONES] + [r for _, r in paginas()]:
        for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), start=1):
            if linea.startswith(MARCAS[0]) or linea.startswith(MARCAS[2]) or linea.strip() == MARCAS[1]:
                errores.append(f"{ruta.relative_to(RAIZ)}, línea {n}: quedan marcas de conflicto («{linea.strip()[:12]}»). "
                               "Borra las líneas <<<<<<<, ======= y >>>>>>> y deja el contenido bueno.")

    # 2 · páginas
    vistas = {}
    for tipo, ruta in paginas():
        sitio = ruta.relative_to(RAIZ)
        try:
            d, texto = leer_pagina(ruta)
        except ValueError as ex:
            errores.append(f"{sitio}: {ex}")
            continue
        tarea = d.get("tarea", "")
        if tarea not in pl:
            errores.append(f"{sitio}: «tarea: {tarea}» no está en el plan (T-01 … T-11).")
            continue
        t = pl[tarea]
        if t["tipo"] != tipo:
            errores.append(f"{sitio}: la tarea {tarea} es una página de {t['tipo']}; va en paginas/{CARPETA[t['tipo']]}/.")
        if ruta.stem != t["archivo"]:
            errores.append(f"{sitio}: para la tarea {tarea} el fichero debe llamarse {t['archivo']}.md.")
        clave = d.get(tipo, "")
        if clave != t["nombre"]:
            errores.append(f"{sitio}: «{tipo}: {clave}» debe ser exactamente «{t['nombre']}», como en los datos.")
        elif clave not in datos["familias" if tipo == "familia" else "delegaciones"]:
            errores.append(f"{sitio}: «{clave}» no aparece en los datos del ERP (lakehouse/bronce/erp_ventas/).")
        if not re.match(r"^[a-z0-9._-]+$", d.get("autor", "")) or d.get("autor") == "tu.alias":
            errores.append(f"{sitio}: «autor» debe ser tu alias en minúsculas, sin espacios (ej.: ana.r).")
        if not d.get("lema") or d.get("lema", "").startswith("Una frase corta"):
            errores.append(f"{sitio}: falta el «lema» (o sigue el texto de la plantilla).")
        if tarea in vistas:
            errores.append(f"{sitio}: la tarea {tarea} ya tiene página en {vistas[tarea]}.")
        vistas[tarea] = sitio
        if len(texto) < 80:
            avisos.append(f"{sitio}: el texto es muy corto.")

    # 3 · menú del sitio
    filas = leer_csv(SECCIONES)
    if not filas or filas[0] != CABECERA_SECCIONES:
        errores.append(f"secciones.csv: la primera línea debe ser exactamente «{','.join(CABECERA_SECCIONES)}».")
    en_menu = {}
    for n, fila in enumerate(filas[1:], start=2):
        if not fila or not "".join(fila).strip():
            continue
        if fila[0].startswith(MARCAS[0]) or fila[0].startswith(MARCAS[2]) or fila[0].strip() == MARCAS[1]:
            continue
        if len(fila) != 3:
            errores.append(f"secciones.csv, línea {n}: debe tener 3 columnas y tiene {len(fila)}.")
            continue
        if not fila[0].isdigit():
            errores.append(f"secciones.csv, línea {n}: «orden» debe ser un número (el de tu tarea: 5 para T-05).")
        if fila[1] not in pl:
            errores.append(f"secciones.csv, línea {n}: la tarea «{fila[1]}» no está en el plan.")
        if fila[1] in en_menu:
            errores.append(f"secciones.csv, línea {n}: la tarea {fila[1]} ya está en la línea {en_menu[fila[1]]}.")
        en_menu[fila[1]] = n

    # 4 · una sola verdad: el portal y el cuadro de mando interno deben dar las mismas ventas
    cuadra = None
    if CUADRO.exists():
        bi = json.loads(CUADRO.read_text(encoding="utf-8"))["ambitos"]
        pares = [("Brétema", datos["total"])] + [(d, v["ventas"]) for d, v in datos["delegaciones"].items()]
        for nombre, portal in pares:
            interno = bi.get(nombre, {}).get("kpis", {}).get("ventas")
            if interno is None or abs(interno - portal) > 1:
                errores.append(f"Las ventas netas de {nombre} no cuadran: portal {euros(portal)} · cuadro de mando "
                               f"{euros(interno) if interno is not None else 'sin dato'}. Revisad la definición común.")
        cuadra = euros(datos["total"])

    lineas = [f"⚠️  {a}" for a in avisos] + [f"❌ {er}" for er in errores]
    if not errores:
        lineas.append(f"✅ Todo correcto: {len(vistas)} páginas y {len(en_menu)} entradas en el menú.")
        if cuadra:
            lineas.append(f"🔗 Portal y cuadro de mando cuadran: ventas netas {datos['anio']} = {cuadra} en los dos.")
    print("\n".join(lineas))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("## Comprobación de Brétema Conecta\n\n" + "\n".join(f"- {l}" for l in lineas) + "\n")
    return not errores


# ─────────────────────────── git ───────────────────────────
def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ""


def ultimos_cambios(n=12):
    """Historial de main «de primer nivel»: un elemento por pull request fusionado."""
    salida = git("log", f"-n{n}", "--first-parent", "--date=format:%d/%m/%Y %H:%M",
                 "--pretty=format:%h\x1f%an\x1f%ad\x1f%s\x1f%b\x1e")
    cambios = []
    for registro in salida.split("\x1e"):
        partes = registro.strip("\n").split("\x1f")
        if len(partes) != 5:
            continue
        sha, autor, fecha, asunto, cuerpo = partes
        m = re.match(r"^Merge pull request #(\d+) from [^/]+/(.+)$", asunto)
        titulo = cuerpo.strip().splitlines()[0] if cuerpo.strip() else ""
        cambios.append(dict(sha=sha, autor=autor, fecha=fecha, pr=m.group(1) if m else None,
                            rama=m.group(2) if m else None, mensaje=titulo or asunto))
    return cambios


def enlace_repo():
    repo = os.environ.get("GITHUB_REPOSITORY")
    return f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}" if repo else None


# ─────────────────────────── HTML ───────────────────────────
def md_a_html(texto):
    """Markdown mínimo: títulos ##, listas con guion, párrafos, **negrita** y `código`."""
    def enlinea(t):
        t = e(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        return re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    out = []
    for bloque in re.split(r"\n\s*\n", texto):
        lineas = [l for l in bloque.splitlines() if l.strip()]
        if not lineas:
            continue
        if all(l.lstrip().startswith("- ") for l in lineas):
            out.append("<ul>" + "".join(f"<li>{enlinea(l.lstrip()[2:])}</li>" for l in lineas) + "</ul>")
        elif lineas[0].startswith("#"):
            out.append(f"<h2>{enlinea(lineas[0].lstrip('#').strip())}</h2>")
            if lineas[1:]:
                out.append(f"<p>{enlinea(' '.join(lineas[1:]))}</p>")
        else:
            out.append(f"<p>{enlinea(' '.join(lineas))}</p>")
    return "\n".join(out)


def menu(pl, publicadas, prefijo):
    filas = [f for f in leer_csv(SECCIONES)[1:] if len(f) == 3 and f[1] in pl and f[0].isdigit()]
    items = [f'<a href="{prefijo}index.html">Inicio</a>']
    for orden, tarea, titulo in sorted(filas, key=lambda f: int(f[0])):
        t = pl[tarea]
        if tarea in publicadas:
            items.append(f'<a href="{prefijo}{CARPETA[t["tipo"]]}/{t["archivo"]}.html">{e(titulo)}</a>')
        else:
            items.append(f'<span class="off" title="Página aún no publicada">{e(titulo)}</span>')
    return "<nav>" + "".join(items) + "</nav>"


def pagina(titulo, cuerpo, nav, prefijo=""):
    version = git("describe", "--tags", "--abbrev=0") or "sin versión publicada"
    commit = git("rev-parse", "--short", "HEAD") or "—"
    ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title><link rel="stylesheet" href="{prefijo}estilo.css"></head>
<body>
<header><a href="{prefijo}index.html" class="marca">Brétema <b>Conecta</b></a>
<span class="sub">Distribuciones Brétema · bebidas y alimentación para hostelería y comercio</span>
<a class="acceso" href="{prefijo}interno/index.html">Acceso empleados</a></header>
{nav}
<main>{cuerpo}</main>
<footer>Proyecto del MTIDE 3.1 · empresa ficticia · <span class="ver">{e(version)}</span> · commit <code>{e(commit)}</code> · publicado el {ahora}</footer>
</body></html>"""


def dato(valor, etiqueta):
    return f'<div class="dato"><b>{valor}</b><span>{etiqueta}</span></div>'


def interno():
    """Área interna: cuadro de mando con los datos de bi/cuadro.json."""
    if not CUADRO.exists():
        return ('<section class="pulso"><h1>Brétema <b>Pulso</b></h1><p class="vacio">El cuadro de mando aún no se ha '
                'generado. Lo prepara el equipo de datos: <code>python bi/etl.py</code> y <code>python bi/cuadro.py</code>.</p></section>')
    datos = CUADRO.read_text(encoding="utf-8").replace("</", "<\\/")
    return (RAIZ / "web" / "interno.html").read_text(encoding="utf-8").replace("/*CUADRO*/null", datos)


def generar():
    pl = plan()
    c = cifras()
    publicadas = {}
    for tipo, ruta in paginas():
        d, texto = leer_pagina(ruta)
        publicadas[d["tarea"]] = (d, texto)

    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    for carpeta in CARPETA.values():
        (SALIDA / carpeta).mkdir(parents=True)
    shutil.copy(RAIZ / "web" / "estilo.css", SALIDA / "estilo.css")

    # portada
    tarjetas = {"familia": [], "delegacion": []}
    for tarea, t in pl.items():
        if tarea in publicadas:
            d, _ = publicadas[tarea]
            tarjetas[t["tipo"]].append(
                f'<a class="tarjeta hecha" href="{CARPETA[t["tipo"]]}/{t["archivo"]}.html"><span class="num">{tarea}</span>'
                f'<span class="emp">{e(t["nombre"])}</span><span class="q">{e(d["lema"])}</span>'
                f'<span class="por">por {e(d["autor"])}</span></a>')
        else:
            tarjetas[t["tipo"]].append(
                f'<div class="tarjeta pendiente"><span class="num">{tarea}</span><span class="emp">{e(t["nombre"])}</span>'
                f'<span class="estado">en desarrollo</span></div>')
    n, total = len(publicadas), len(pl)

    items = []
    base = enlace_repo()
    for ch in ultimos_cambios():
        if ch["pr"]:
            et = f'<a href="{base}/pull/{ch["pr"]}">PR #{ch["pr"]}</a>' if base else f"PR #{ch['pr']}"
            tx = f'{e(ch["mensaje"])} <span class="rama">{e(ch["rama"])}</span>'
        else:
            et = f'<a href="{base}/commit/{ch["sha"]}"><code>{ch["sha"]}</code></a>' if base else f"<code>{ch['sha']}</code>"
            tx = e(ch["mensaje"])
        items.append(f'<li><span class="pr">{et}</span> <span class="msg">{tx}</span>'
                     f'<span class="meta">{e(ch["autor"])} · {e(ch["fecha"])}</span></li>')
    cambios = '<ul class="cambios">' + "".join(items) + "</ul>" if items else '<p class="vacio">Sin historial de git.</p>'

    cuerpo = f"""
<section class="hero"><h1>Todo lo que tu local necesita, en un solo distribuidor</h1>
<p>Bebidas, alimentación y limpieza para hostelería y comercio en A Coruña, Santiago y Lugo.</p></section>
<section><h2>Brétema en cifras <span class="fuente">calculado a partir del ERP</span></h2>
<div class="datos">{dato(len(c['familias']), 'familias de producto')}{dato(c['n_productos'], 'productos')}
{dato(c['n_clientes'], 'clientes')}{dato(len(c['delegaciones']), 'delegaciones')}{dato(euros(c['total']), f"ventas netas {c['anio']}")}</div></section>
<section><h2>Nuestras familias de producto</h2><div class="rejilla">{''.join(tarjetas['familia'])}</div></section>
<section><h2>Nuestras delegaciones</h2><div class="rejilla">{''.join(tarjetas['delegacion'])}</div></section>
<section class="proyecto"><h2>Estado del proyecto</h2>
<div class="progreso"><div class="barra" style="width:{n / total * 100:.0f}%"></div></div>
<p class="cuenta"><strong>{n}</strong> de {total} páginas publicadas</p>
<h3>Últimos cambios en <code>main</code></h3>{cambios}</section>"""
    (SALIDA / "index.html").write_text(pagina("Brétema Conecta", cuerpo, menu(pl, publicadas, "")), encoding="utf-8")

    # páginas
    for tarea, (d, texto) in publicadas.items():
        t = pl[tarea]
        if t["tipo"] == "familia":
            f = c["familias"][t["nombre"]]
            top = sorted(f["unidades"].items(), key=lambda x: -x[1])[:3]
            panel = (f'<div class="datos">{dato(len(f["productos"]), "productos")}'
                     f'{dato(euros2(f["precio_min"]), "precio desde")}'
                     f'{dato(euros(f["ventas"]), "ventas netas " + c["anio"])}</div>'
                     f'<h3>Los más pedidos en {c["anio"]}</h3><ol class="top">'
                     + "".join(f"<li>{e(p)} <span>{u:,} uds.</span></li>".replace(",", ".") for p, u in top) + "</ol>")
        else:
            dl = c["delegaciones"][t["nombre"]]
            fam_top = max(dl["familias"].items(), key=lambda x: x[1])[0] if dl["familias"] else "—"
            pct = dl["hosteleria"] / dl["ventas"] * 100 if dl["ventas"] else 0
            panel = (f'<div class="datos">{dato(len(dl["clientes"]), "clientes")}'
                     f'{dato(len(dl["comerciales"]), "comerciales")}'
                     f'{dato(euros(dl["ventas"]), "ventas netas " + c["anio"])}'
                     f'{dato(f"{pct:.0f} %".replace(".", ","), "de las ventas, a hostelería")}</div>'
                     f'<p class="nota">Familia más vendida en {c["anio"]}: <strong>{e(fam_top)}</strong></p>')
        cuerpo = f"""<p class="volver"><a href="../index.html">← Volver al inicio</a></p>
<article class="ficha"><span class="num">{tarea} · {'Familia' if t['tipo'] == 'familia' else 'Delegación'}</span><h1>{e(t['nombre'])}</h1>
<p class="lema">{e(d['lema'])}</p>
<div class="panel"><span class="fuente">cifras calculadas a partir del ERP</span>{panel}</div>
{md_a_html(texto)}
<p class="autor">Página de <strong>{e(d['autor'])}</strong></p></article>"""
        (SALIDA / CARPETA[t["tipo"]] / f"{t['archivo']}.html").write_text(
            pagina(f"{t['nombre']} · Brétema Conecta", cuerpo, menu(pl, publicadas, "../"), "../"), encoding="utf-8")
    # área interna (Brétema Pulso)
    (SALIDA / "interno").mkdir()
    (SALIDA / "interno" / "index.html").write_text(
        pagina("Brétema Pulso · acceso empleados", interno(), menu(pl, publicadas, "../"), "../"), encoding="utf-8")
    print(f"🌐 Web generada en _site/ ({n} de {total} páginas publicadas"
          f"{', con el área interna' if CUADRO.exists() else ''}).")


if __name__ == "__main__":
    ok = comprobar()
    if not ok:
        print("\nCorrige los errores marcados con ❌ y vuelve a subir los cambios.")
        sys.exit(1)
    if "--check" not in sys.argv:
        generar()

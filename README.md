# Brétema Conecta

Portal web de **Distribuciones Brétema** (empresa ficticia): catálogo de familias de producto y páginas de delegación,
más un **área interna para empleados** con el cuadro de mando comercial (**Brétema Pulso**, prototipo del equipo de datos).
Proyecto colaborativo del MTIDE 3.1.

Cada cambio que llega a `main` se comprueba y se publica solo en GitHub Pages.

## El plan de la v1.0

| Tarea | Página | Fichero |
|---|---|---|
| T-01 … T-08 | Una por familia de producto | `paginas/familias/<familia>.md` |
| T-09 … T-11 | Una por delegación | `paginas/delegaciones/<delegacion>.md` |

La lista exacta (tarea, nombre y nombre de fichero) está en `web/plan.csv`. Cada tarea es una **issue** asignada a una persona.

## Normas del proyecto

1. **Nunca se trabaja en `main`.** Cada tarea va en su rama: `t05-cervezas`, `menu-t05`, `issue-38`…
2. **Todo entra por pull request**, revisado y aprobado por la persona de la tarea siguiente (a T-01 la revisa T-02, a T-02 la revisa T-03 … y a T-11, T-01).
3. **La comprobación automática tiene que salir en verde (✅).** Si sale ❌, el detalle dice qué falla y en qué línea.
4. **Mensajes de commit claros**, en presente: «Añade la página de Cervezas», «Corrige el lema de Lugo».
5. **Solo tocas tus ficheros**, salvo `secciones.csv` (el menú), que es de todos.
6. **Las cifras no se escriben a mano**: las calcula la web a partir de `datos/ventas.csv`.

## Qué hay en el repositorio

| Ruta | Qué es |
|---|---|
| `paginas/_plantillas/` | Plantillas de página de familia y de delegación |
| `paginas/familias/`, `paginas/delegaciones/` | Las páginas que escribe el equipo |
| `secciones.csv` | El menú del sitio: `orden,tarea,titulo` |
| `datos/ventas.csv` | Extracto del ERP (ventas 2024–2025): de aquí salen todas las cifras |
| `web/build.py` | Comprueba el contenido, calcula las cifras y genera la web |
| `web/plan.csv` | Las 11 tareas de la v1.0 (no se toca) |
| `web/interno.html` | Plantilla del área interna (cuadro de mando sin inicio de sesión) |
| `bi/etl.py` | ETL del equipo de datos: extrae `datos/ventas.csv`, transforma y carga un modelo en estrella en `bi/bretema.db` (SQLite) |
| `bi/cuadro.py` | Consultas SQL del cuadro de mando: deja el resultado en `bi/cuadro.json` |
| `.github/workflows/publicar.yml` | Comprobar en cada pull request, publicar en cada cambio de `main` |

## Ver la web en tu ordenador antes de subir nada

```bash
python web/build.py          # comprueba y genera _site/
# abre _site/index.html en el navegador
```

`python web/build.py --check` solo comprueba: es exactamente lo que hará GitHub con tu pull request.

## La pieza de datos: Brétema Pulso (área interna)

```bash
python bi/etl.py       # 1 extraer · 2 transformar · 3 cargar → bi/bretema.db
python bi/cuadro.py    # consultas SQL → bi/cuadro.json
python web/build.py    # genera también _site/interno/
```

- **Una sola verdad.** «Ventas netas» = unidades × precio unitario; las devoluciones restan. El portal y el cuadro
  de mando usan la misma definición, y la comprobación automática falla si sus cifras no cuadran.
- **Público e interno.** El portal muestra cifras agregadas; el margen, los comerciales y el detalle mensual solo
  aparecen en el área interna.
- **Sin autenticación.** El área interna es de acceso libre: no pide usuario ni contraseña. Es un prototipo: en
  GitHub Pages no hay servidor y los datos van dentro de la página. En un proyecto real, el cuadro de mando estaría en
  una herramienta de BI o detrás de un servidor con autenticación, nunca en una web pública.
- `bi/bretema.db` y `bi/cuadro.json` son resultados: no se suben a git. GitHub los genera en cada publicación.

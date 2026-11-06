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
6. **Las cifras no se escriben a mano**: las calcula la web a partir de los datos del ERP (`lakehouse/bronce/`).

## Qué hay en el repositorio

| Ruta | Qué es |
|---|---|
| `paginas/_plantillas/` | Plantillas de página de familia y de delegación |
| `paginas/familias/`, `paginas/delegaciones/` | Las páginas que escribe el equipo |
| `secciones.csv` | El menú del sitio: `orden,tarea,titulo` |
| `lakehouse/bronce/erp_ventas/` | Lo que entrega el ERP, una carpeta `fecha_carga=AAAA-MM-DD` por entrega: de aquí salen todas las cifras. Plata y oro los escribe dbt y no se suben |
| `web/build.py` | Comprueba el contenido, calcula las cifras y genera la web |
| `web/plan.csv` | Las 11 tareas de la v1.0 (no se toca) |
| `web/interno.html` | Plantilla del área interna (cuadro de mando sin inicio de sesión) |
| `dbt/` | Proyecto dbt del equipo de datos: modelos de plata y oro (estrella de cinco dimensiones), tests y macros |
| `herramientas/erp_simulado.py` | El ERP simulado de la demostración: envía la remesa de enero y su reenvío |
| `bi/cuadro.py` | Consultas SQL (DuckDB) sobre el oro: deja el resultado en `bi/cuadro.json` |
| `bi/resumen.py` | Resumen en Markdown del lakehouse (tests, cuarentena, ventas por mes) para la página de cada ejecución |
| `paginas/historia/` | Jornada 7 · La historia: la historia para la dirección y cómo se construyó (ejemplo resuelto) |
| `web/historia.py`, `web/graficos.py` | Generan esas dos páginas en el área interna, con cifras y gráficos sacados del oro |
| `.github/workflows/publicar.yml` | Comprobar en cada pull request, publicar en cada cambio de `main` |

## Ver la web en tu ordenador antes de subir nada

```bash
python web/build.py          # comprueba y genera _site/
# abre _site/index.html en el navegador
```

`python web/build.py --check` solo comprueba: es exactamente lo que hará GitHub con tu pull request.

## La pieza de datos: Brétema Pulso (área interna)

```bash
pip install -r requirements.txt                    # una vez: dbt y DuckDB
dbt build --project-dir dbt --profiles-dir dbt     # bronce → plata → oro, con sus tests → lakehouse/
python bi/cuadro.py                                # consultas SQL sobre el oro → bi/cuadro.json
python web/build.py                                # genera también _site/interno/
```

Es opcional: GitHub hace lo mismo en cada pull request y en cada cambio de `main`. En la página de cada ejecución
(pestaña Actions) queda un resumen con los tests, las filas en cuarentena y las ventas por mes, y un zip
`lakehouse-<PR>` con plata y oro en Parquet (`select * from 'oro/ventas_mes.parquet'` con DuckDB).
Tras cada cambio de `main`, plata y oro quedan también publicados en la web, y DuckDB los lee por URL:
`select * from 'https://irquintanas.github.io/bretema-conecta/lakehouse/oro/ventas_mes.parquet'`.

- **Una sola verdad.** «Ventas netas» = unidades × precio unitario; las devoluciones restan. El portal y el cuadro
  de mando usan la misma definición, y la comprobación automática falla si sus cifras no cuadran.
- **Público e interno.** El portal muestra cifras agregadas; el margen, los comerciales y el detalle mensual solo
  aparecen en el área interna.
- **Sin autenticación.** El área interna es de acceso libre: no pide usuario ni contraseña. Es un prototipo: en
  GitHub Pages no hay servidor y los datos van dentro de la página. En un proyecto real, el cuadro de mando estaría en
  una herramienta de BI o detrás de un servidor con autenticación, nunca en una web pública.
- `lakehouse/plata/`, `lakehouse/oro/` y `bi/cuadro.json` son resultados: no se suben a git. GitHub los reconstruye en
  cada ejecución y lo único que perdura es la web publicada (más la documentación de dbt en `/dbt-docs/`).
- **Si un test falla**, dbt no construye lo que depende de él, el pull request sale en ❌ y nada llega a `main`: la web
  sigue con las cifras anteriores.

## Jornada 7 · La historia

El ejemplo resuelto de la Jornada 7: los cuatro pasos de «Del dato a la decisión» aplicados a Brétema. Pasa del cuadro
de mando (un informe) a una historia para la dirección: **1 de cada 4 € de Vinos se vende en noviembre y diciembre, y la
campaña se decide en septiembre**.

| Pieza | Dónde |
|---|---|
| La historia (la portada para la dirección) | `paginas/historia/historia.md` → área interna, «La historia» |
| Cómo se construyó: decidir, analizar, elegir los datos y las cinco comprobaciones | `paginas/historia/historia-pasos.md` → área interna |
| Las cifras que necesita la historia, con sus tests | `dbt/models/oro/historia_*.sql` y `_oro.yml` |

Las páginas no llevan ninguna cifra escrita a mano: una marca como `{{ historia_vinos.nov_dic_pct[0] }}` toma el valor
del oro, y los bloques `grafico` dibujan con los datos de un modelo los cinco tipos de gráfico de la presentación
(`barras`, `linea`, `histograma`, `calor` y `eje`). Es la misma sintaxis que usan los portales de los casos
individuales; su README explica cada tipo.

```bash
dbt build --project-dir dbt --profiles-dir dbt     # construye también los modelos historia_*
python bi/cuadro.py
python web/build.py                                # genera _site/interno/historia.html y historia-pasos.html
```

`python web/build.py --check` comprueba que cada marca tiene valor y que cada gráfico apunta a un modelo y unas
columnas que existen. Si el oro no está construido o no tienes DuckDB, el portal público se genera igual y la historia
se salta con un aviso.

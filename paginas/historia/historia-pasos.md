# Cómo se construyó la historia

La portada cuenta el destino. Aquí queda el viaje: la decisión que hay detrás, lo que buscamos en los datos y lo que dejamos fuera.

## Paso 1 · De tema a decisión

| Nivel | En Brétema | Qué obliga a hacer |
|---|---|---|
| Tema | «Las ventas de Vinos y licores» | Nada: admite cualquier gráfico |
| Pregunta | «¿Cuándo se vende Vinos y licores?» | Una serie mes a mes y una base de comparación: el mes medio |
| Decisión | «¿Reservamos stock de Vinos con los proveedores en septiembre?» | Quién (Compras), cuándo (septiembre) y qué (un pedido anticipado) |

**La prueba:** después de leer la portada, Compras adelanta o no el pedido de Vinos a septiembre.

## Paso 2 · Qué se mueve en los datos

### 2a · El terreno: Brétema en dos años

```cifras
{{ historia_terreno.lineas[0] }} | líneas de pedido
{{ historia_terreno.clientes[0] }} | clientes
{{ historia_terreno.familias[0] }} | familias de producto
{{ historia_terreno.facturacion[0] }} | euros facturados en 2024 y 2025
```

```grafico
titular: Facturación por familia, 2024–2025
modelo: historia_familias
barras: familia → importe
orden: desc
```

Una familia, Vinos y licores, factura casi la mitad del negocio: el {{ historia_familias.pct[0] }} %.

```grafico
tipo: linea
titular: Vinos y licores, mes a mes, 2024–2025
modelo: historia_vinos_mes
x: mes
y: importe
referencia: historia_vinos.media_mes · mes medio
```

Los dos diciembres destacan muy por encima del mes medio de la familia ({{ historia_vinos.media_mes[0] }} €).

```grafico
tipo: histograma
titular: Importe por línea de pedido, 2024–2025
modelo: fact_ventas
columna: importe
escala: log
```

La media de una línea son {{ historia_terreno.media_linea[0] }} €, pero la mitad está por debajo de {{ historia_terreno.mediana_linea[0] }} €: la media no describe a ningún cliente, así que en la historia no usamos medias por línea.

### 2b · El disparador: diciembre, frente al mes medio

```grafico
tipo: linea
titular: El pico de diciembre de 2024: un {{ historia_vinos.pico_sobre_media_pct[0] }} % por encima del mes medio
modelo: historia_vinos_mes
x: mes
y: importe
destacar: {{ historia_vinos.pico_mes[0] }}
referencia: historia_vinos.media_mes · mes medio
```

```grafico
tipo: calor
titular: ¿Es la Navidad de todo el negocio? Cada familia frente a su propio mes medio
modelo: historia_familia_mes
filas: familia
columnas: mes
valor: importe
normalizar: fila
destacar: Vinos y licores
```

**El hallazgo:** noviembre y diciembre suman {{ historia_vinos.nov_dic_eur[0] }} €, el {{ historia_vinos.nov_dic_pct[0] }} % de lo que Vinos factura en dos años, cuando un reparto uniforme daría el 16,7 %. Conservas también sube en diciembre, pero factura casi cinco veces menos; Cervezas y Bebidas frías tienen su pico en verano.

### 2c · Qué lo puede explicar

- **Anomalía:** sí. Los dos diciembres se separan del resto del año.
- **Cambio significativo:** no. El patrón se repite igual en 2024 y en 2025.
- **Fuerzas del mercado:** la campaña de Navidad y las compras de la hostelería. Es una hipótesis: no tenemos datos de la hostelería.
- **Iniciativas propias:** las promociones de noviembre y diciembre coinciden en el calendario con la Navidad; con estos datos no se pueden separar.

## Paso 3 · Qué datos entran y cuáles se quedan fuera

| Dato candidato | ¿Pasa el filtro? | Dónde se usa |
|---|---|---|
| Importe mensual de Vinos | Sí: es la serie de la estacionalidad | Portada, gráfico principal |
| Importe por familia y mes | Sí: demuestra que es de Vinos, no de todo el negocio | Portada, segunda prueba |
| Importe por delegación | No para la decisión, pero sirve para auditar el eje | Aquí, en el eje cortado |
| Censo de clientes por provincia | No: describe, no explica la Navidad | Fuera |
| Margen por delegación | No: no cambia la decisión de stock | Fuera, por mucho que interese |

```grafico
tipo: eje
titular: Mismos datos, dos lecturas: el eje manda
modelo: historia_delegaciones
barras: delegacion → importe
corte: 280000
```

Con el eje cortado, A Coruña parece aplastar a Lugo. Por eso todos los gráficos de barras de la portada empiezan en cero.

> **Alcance.** Extracto de ventas del ERP de Brétema, enero de 2024 a diciembre de 2025: {{ historia_terreno.lineas[0] }} líneas, devoluciones incluidas como importes negativos.

## Las cinco comprobaciones

- **Hay una decisión detrás:** adelantar a septiembre el pedido de Vinos (Compras).
- **El titular afirma:** leído sin gráficos, dice cuándo se juega la campaña.
- **Cada cifra tiene fuente:** modelo y filtros al pie de cada gráfico.
- **La evidencia es diversa:** la serie de Vinos y el mapa de calor de todas las familias apuntan a lo mismo.
- **Lo que no cuadra se dice:** Conservas también sube en diciembre, y las promociones no se pueden separar de la Navidad.

# 1 de cada 4 € de Vinos se vende en noviembre y diciembre: el {{ historia_vinos.nov_dic_pct[0] }} %, y la campaña se decide en septiembre

Vinos y licores es casi la mitad del negocio y concentra en dos meses {{ historia_vinos.nov_dic_eur[0] }} € de sus {{ historia_vinos.total_familia[0] }} €. Diciembre de 2024 vendió un {{ historia_vinos.pico_sobre_media_pct[0] }} % más que un mes medio. Proponemos cerrar en septiembre la reserva de stock con los proveedores.

```grafico
tipo: linea
titular: Cada diciembre, Vinos se dispara por encima de su mes medio
modelo: historia_vinos_mes
x: mes
y: importe
destacar: {{ historia_vinos.pico_mes[0] }}
referencia: historia_vinos.media_mes · mes medio
```

```grafico
tipo: calor
titular: La Navidad no es de todo el negocio: es sobre todo de Vinos
modelo: historia_familia_mes
filas: familia
columnas: mes
valor: importe
normalizar: fila
destacar: Vinos y licores
```

## Qué proponemos

1. **Reservar en septiembre el stock de Vinos para noviembre y diciembre** (Compras, antes del 30 de septiembre).
2. **Reforzar las visitas a la hostelería en noviembre y diciembre** (Comercial).

## Qué no sabemos todavía

- Cuánto del pico es Navidad y cuánto son nuestras promociones: coinciden en el calendario.
- Que la hostelería sea el motor es una hipótesis: no tenemos sus datos de compra.
- Son dos años: 2024 y 2025.

## La misma historia para cada audiencia

- **Comité de dirección (5 segundos):** «1 de cada 4 € de Vinos se vende en noviembre y diciembre».
- **Compras y Comercial (1 minuto):** «Diciembre vende un {{ historia_vinos.pico_sobre_media_pct[0] }} % más que un mes medio». Acción 1: reservar stock en septiembre. Acción 2: reforzar la hostelería en noviembre y diciembre.
- **Equipo de datos (5 minutos):** «Estacionalidad por familia, 2024–2025»: importe neto del extracto del ERP, devoluciones incluidas, {{ historia_terreno.lineas[0] }} líneas.

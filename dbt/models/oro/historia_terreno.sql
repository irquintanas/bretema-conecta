-- ORO · historia: las cifras de contexto del terreno (una fila)
select count(*)                          as lineas,
       count(distinct cliente_id)        as clientes,
       count(distinct delegacion)        as delegaciones,
       count(distinct familia)           as familias,
       round(sum(importe), 0)            as facturacion,
       round(avg(importe), 2)            as media_linea,
       round(median(importe), 2)         as mediana_linea
from {{ ref('stg_ventas') }}

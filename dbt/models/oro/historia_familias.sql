-- ORO · historia: lo que pesa cada familia en la facturación
select familia,
       round(sum(importe), 0)                                    as importe,
       round(100 * sum(importe) / sum(sum(importe)) over (), 1)  as pct
from {{ ref('stg_ventas') }}
group by familia
order by importe desc

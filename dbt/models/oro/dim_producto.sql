-- ORO · dimensión producto
select row_number() over (order by producto) as producto_id, producto, familia
from (select producto, any_value(familia) as familia from {{ ref('stg_ventas') }} group by producto)

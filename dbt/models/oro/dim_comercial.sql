-- ORO · dimensión comercial
select row_number() over (order by comercial) as comercial_id, comercial, any_value(delegacion) as delegacion
from {{ ref('stg_ventas') }}
group by comercial

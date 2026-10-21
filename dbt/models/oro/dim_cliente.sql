-- ORO · dimensión cliente
select cliente_id, any_value(canal) as canal, any_value(delegacion) as delegacion
from {{ ref('stg_ventas') }}
group by cliente_id

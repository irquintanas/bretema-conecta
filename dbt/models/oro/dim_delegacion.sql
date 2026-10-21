-- ORO · dimensión delegación
select row_number() over (order by delegacion) as delegacion_id, delegacion
from (select distinct delegacion from {{ ref('stg_ventas') }})

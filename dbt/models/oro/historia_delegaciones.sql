-- ORO · historia: facturación por delegación
select delegacion, round(sum(importe), 0) as importe
from {{ ref('stg_ventas') }}
group by delegacion

-- ORO · historia: Vinos y licores, mes a mes
select strftime(fecha, '%Y-%m') as mes, round(sum(importe), 0) as importe
from {{ ref('stg_ventas') }}
where familia = 'Vinos y licores'
group by mes

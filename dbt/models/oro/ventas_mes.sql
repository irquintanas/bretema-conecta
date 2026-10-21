-- ORO · ventas netas y margen por delegación y mes
select d.delegacion,
       f.anio,
       f.mes,
       round(sum(h.importe), 2)                                  as ventas_netas,
       round(100 * (1 - sum(h.coste) / sum(h.importe)), 1)       as margen_pct
from {{ ref('fact_ventas') }} h
join {{ ref('dim_fecha') }} f using (fecha_id)
join {{ ref('dim_delegacion') }} d using (delegacion_id)
group by all
order by f.anio, f.mes, d.delegacion

-- ORO · tabla de hechos: una fila por línea de venta, con la clave de cada dimensión
select
    cast(strftime(v.fecha, '%Y%m%d') as integer) as fecha_id,
    d.delegacion_id,
    p.producto_id,
    v.cliente_id,
    m.comercial_id,
    v.unidades,
    v.precio_unitario as precio,
    v.importe,
    v.coste
from {{ ref('stg_ventas') }} v
join {{ ref('dim_delegacion') }} d using (delegacion)
join {{ ref('dim_producto') }} p using (producto)
join {{ ref('dim_comercial') }} m using (comercial)

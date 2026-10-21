-- PLATA · filas que no se pueden usar: se apartan para revisarlas con quien las envía
select * from {{ ref('stg_ventas_tipado') }}
where motivo_rechazo is not null

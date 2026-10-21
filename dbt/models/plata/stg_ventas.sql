-- PLATA · ventas válidas, listas para usar
select
    fecha, delegacion, comercial, cliente_id, canal, familia, producto,
    unidades, precio_unitario, coste_unitario,
    unidades * precio_unitario as importe,
    unidades * coste_unitario  as coste,
    archivo, fecha_carga
from {{ ref('stg_ventas_tipado') }}
where motivo_rechazo is null

-- Regla de negocio: ningún precio puede ser cero o negativo.
select * from {{ ref('stg_ventas') }} where precio_unitario <= 0

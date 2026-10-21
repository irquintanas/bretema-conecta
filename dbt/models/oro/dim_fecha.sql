-- ORO · dimensión fecha: un día por fila, con la clave AAAAMMDD
select
    cast(strftime(fecha, '%Y%m%d') as integer) as fecha_id,
    fecha,
    year(fecha)                                as anio,
    quarter(fecha)                             as trimestre,
    month(fecha)                               as mes,
    list_value('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
               'septiembre', 'octubre', 'noviembre', 'diciembre')[month(fecha)] as nombre_mes
from (select distinct fecha from {{ ref('stg_ventas') }})

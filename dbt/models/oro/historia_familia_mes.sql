-- ORO · historia: importe por familia y mes del año (dos años juntos), una fila por celda
select familia,
       printf('%02d', month(fecha)) as mes,
       round(sum(importe), 0)       as importe
from {{ ref('stg_ventas') }}
group by all

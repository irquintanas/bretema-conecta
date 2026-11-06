-- ORO · historia: las cifras del hallazgo de Vinos y licores (una fila)
with mes as (
    select strftime(fecha, '%Y-%m') as mes, month(fecha) as m, sum(importe) as importe
    from {{ ref('stg_ventas') }} where familia = 'Vinos y licores' group by all
)
select round(avg(importe), 0)                                                       as media_mes,
       arg_max(mes, importe)                                                        as pico_mes,
       round(max(importe), 0)                                                       as pico_eur,
       round(100 * (max(importe) / avg(importe) - 1), 0)                            as pico_sobre_media_pct,
       round(sum(importe) filter (where m in (11, 12)), 0)                          as nov_dic_eur,
       round(100 * sum(importe) filter (where m in (11, 12)) / sum(importe), 1)     as nov_dic_pct,
       round(sum(importe), 0)                                                       as total_familia
from mes

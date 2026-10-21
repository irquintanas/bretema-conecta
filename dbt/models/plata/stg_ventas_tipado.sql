-- PLATA · todas las filas, con tipos y texto normalizado, y el motivo si alguna no vale
with bruto as (
    select *, parse_filename(filename) as archivo
    from {{ source('bronce', 'erp_ventas') }}
),
ultima_entrega as (
    -- si el ERP reenvía un fichero, nos quedamos con la entrega más reciente
    select * from bruto
    qualify fecha_carga = max(fecha_carga) over (partition by archivo)
),
tipado as (
    select
        coalesce(try_cast(fecha as date), try_strptime(fecha, '%d/%m/%Y')::date) as fecha,
        case lower(trim(delegacion))
            when 'a coruña' then 'A Coruña'
            when 'coruña'   then 'A Coruña'
            when 'santiago' then 'Santiago'
            when 'lugo'     then 'Lugo'
            else trim(delegacion)
        end                                                              as delegacion,
        trim(comercial)                                                  as comercial,
        upper(trim(cliente_id))                                          as cliente_id,
        trim(canal)                                                      as canal,
        trim(familia)                                                    as familia,
        trim(producto)                                                   as producto,
        try_cast(unidades as integer)                                    as unidades,
        try_cast(replace(precio_unitario, ',', '.') as decimal(10, 2))   as precio_unitario,
        try_cast(replace(coste_unitario, ',', '.') as decimal(10, 2))    as coste_unitario,
        archivo,
        fecha_carga
    from ultima_entrega
)
select
    *,
    case
        when fecha is null           then 'fecha ilegible'
        when unidades is null        then 'sin unidades'
        when precio_unitario is null then 'precio ilegible'
        when coste_unitario is null  then 'coste ilegible'
    end as motivo_rechazo
from tipado

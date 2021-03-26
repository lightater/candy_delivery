from sqlalchemy import and_, func, select

from distributor.db.schema import couriers_table, orders_table


COURIERS_QUERY = select([
    couriers_table.c.courier_id,
    couriers_table.c.courier_type,
    couriers_table.c.regions,
    couriers_table.c.working_hours,
    couriers_table.c.rating,
    couriers_table.c.earnings,
]).select_from(couriers_table)

ORDERS_QUERY = select([
    orders_table.c.order_id,
    orders_table.c.weight,
    orders_table.c.region,
    orders_table.c.delivery_hours,
]).select_from(orders_table)

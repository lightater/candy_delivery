from enum import Enum, unique

from sqlalchemy import (
    Column, Date, Enum as PgEnum, ForeignKey, ForeignKeyConstraint, Integer,
    MetaData, String, Table, ARRAY, Float, DateTime
)


# SQLAlchemy рекомендует использовать единый формат для генерации названий для
# индексов и внешних ключей.
# https://docs.sqlalchemy.org/en/13/core/constraints.html#configuring-constraint-naming-conventions
convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),
    'ix': 'ix__%(table_name)s__%(all_column_names)s',
    'uq': 'uq__%(table_name)s__%(all_column_names)s',
    'ck': 'ck__%(table_name)s__%(constraint_name)s',
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)


@unique
class TransportType(Enum):
    foot = 'foot'
    bike = 'bike'
    car = 'car'


couriers_table = Table(
    'couriers',
    metadata,
    Column('courier_id', Integer, primary_key=True),
    Column('courier_type', PgEnum(TransportType, name='courier_type'),
           nullable=False),
    Column('regions', ARRAY(Integer), nullable=False),
    Column('working_hours', ARRAY(String), nullable=False),
    Column('rating', Float, nullable=True),
    Column('earnings', Integer, nullable=True),

)


orders_table = Table(
    'orders',
    metadata,
    Column('order_id', Integer, primary_key=True),
    Column('weight', Float, nullable=False),
    Column('region', Integer, nullable=False),
    Column('delivery_hours', ARRAY(String), nullable=False),
)


assigned_orders_table = Table(
    'assigned_orders',
    metadata,
    Column('order_id', Integer, ForeignKey('orders.order_id'),
           primary_key=True),
    Column('courier_id', Integer, ForeignKey('couriers.courier_id'),
           primary_key=True),
    Column('assign_time', DateTime, nullable=False),
)

completed_orders_table = Table(
    'completed_orders',
    metadata,
    Column('order_id', Integer, ForeignKey('orders.order_id'),
           primary_key=True),
    Column('courier_id', Integer, ForeignKey('couriers.courier_id'),
           primary_key=True),
    Column('complete_time', DateTime, nullable=False),
)

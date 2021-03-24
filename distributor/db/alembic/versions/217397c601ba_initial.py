"""Initial

Revision ID: 217397c601ba
Revises: 
Create Date: 2021-03-24 07:59:32.752905

"""
from alembic import op
from sqlalchemy import (
    ARRAY, Column, DateTime, Enum, ForeignKeyConstraint, Float, Integer,
    PrimaryKeyConstraint, String,
)

# revision identifiers, used by Alembic.
revision = '217397c601ba'
down_revision = None
branch_labels = None
depends_on = None


TransportType = Enum('female', 'male', name='type')


def upgrade():
    op.create_table(
        'couriers',
        Column('courier_id', Integer(), nullable=False),
        Column('courier_type', TransportType,
               nullable=False),
        Column('regions', ARRAY(Integer()), nullable=False),
        Column('working_hours', ARRAY(String()),
               nullable=False),
        Column('rating', Float(), nullable=True),
        Column('earnings', Integer(), nullable=True),
        PrimaryKeyConstraint('courier_id',
                             name=op.f('pk__couriers'))
    )
    op.create_table(
        'orders',
        Column('order_id', Integer(), nullable=False),
        Column('weight', Float(), nullable=False),
        Column('region', Integer(), nullable=False),
        Column('delivery_hours', ARRAY(String()),
               nullable=False),
        PrimaryKeyConstraint('order_id', name=op.f('pk__orders'))
    )
    op.create_table(
        'assigned_orders',
        Column('order_id', Integer(), nullable=False),
        Column('courier_id', Integer(), nullable=False),
        Column('assign_time', DateTime(), nullable=False),
        ForeignKeyConstraint(['courier_id'],
                             ['couriers.courier_id'], name=op.f(
                'fk__assigned_orders__courier_id__couriers')),
        ForeignKeyConstraint(['order_id'], ['orders.order_id'],
                             name=op.f(
                                 'fk__assigned_orders__order_id__orders')),
        PrimaryKeyConstraint('order_id', 'courier_id',
                             name=op.f('pk__assigned_orders'))
    )
    op.create_table(
        'completed_orders',
        Column('order_id', Integer(), nullable=False),
        Column('courier_id', Integer(), nullable=False),
        Column('complete_time', DateTime(), nullable=False),
        ForeignKeyConstraint(['courier_id'],
                             ['couriers.courier_id'], name=op.f(
                'fk__completed_orders__courier_id__couriers')),
        ForeignKeyConstraint(['order_id'], ['orders.order_id'],
                             name=op.f(
                                 'fk__completed_orders__order_id__orders')),
        PrimaryKeyConstraint('order_id', 'courier_id',
                             name=op.f('pk__completed_orders'))
    )


def downgrade():
    op.drop_table('completed_orders')
    op.drop_table('assigned_orders')
    op.drop_table('orders')
    op.drop_table('couriers')
    TransportType.drop(op.get_bind(), checkfirst=False)

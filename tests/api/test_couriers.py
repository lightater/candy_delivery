from datetime import datetime
from http import HTTPStatus

import pytest

from distributor.db.schema import couriers_table
from distributor.utils.testing import (
    compare_courier_groups, generate_courier, get_courier,
)


datasets = [
    # Выгрузка с курьерами.
    # Обработчик должен вернуть список с {'id':...}
    [
        generate_courier(courier_id=1),
        generate_courier(courier_id=2),
        generate_courier(courier_id=4),
        generate_courier(courier_id=17)
    ],

    # Пустой курьер
    [
        generate_courier()
    ],

    # Выгрузка с жителем, который сам себе родственник.
    # Обработчик должен возвращать идентификатор жителя в списке родственников.
    [
        generate_courier(courier_id=10, courier_type='bike', regions=[1, 17],
                         working_hours=['13:45-14:00', '22:50-00:10'])
    ],

    # Пустая выгрузка.
    # Обработчик не должен падать на пустой выгрузке.
    [],
]


def post_couriers(connection, couriers) -> list:
    courier_rows, courier_ids = [], []
    for courier in couriers:
        courier_ids.append({'id': courier['courier_id']})
        courier_rows.append({
            'courier_id': courier['courier_id'],
            'courier_type': courier['courier_type'],
            'regions': courier['regions'],
            'working_hours': courier['working_hours'],
        })

    if courier_rows:
        query = couriers_table.insert().values(courier_rows)
        connection.execute(query)

    return courier_ids


@pytest.mark.parametrize('dataset', datasets)
async def test_get_citizens(api_client, migrated_postgres_connection, dataset):
    # Перед прогоном каждого теста добавляем в БД дополнительную выгрузку с
    # одним курьером, чтобы убедиться, что обработчик различает жителей разных
    # выгрузок.
    post_couriers(migrated_postgres_connection, [generate_courier()])

    # Проверяем обработчик на указанных данных
    courier_ids = post_couriers(migrated_postgres_connection, dataset)
    actual_couriers = []
    for courier_id in courier_ids:
        actual_courier = await get_courier(api_client, courier_id)
        actual_couriers.append(actual_courier)
    assert compare_courier_groups(actual_couriers, dataset)


async def test_get_non_existing_import(api_client):
    await get_courier(api_client, 999, HTTPStatus.NOT_FOUND)

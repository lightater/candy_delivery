from datetime import date, timedelta
from http import HTTPStatus

import pytest

from distributor.utils.pg import MAX_INTEGER
from distributor.utils.testing import (
    compare_courier_groups, generate_courier, generate_couriers, get_courier,
    post_couriers,
)


CASES = (
    # Один курьер
    (
        [
            generate_courier()
        ],
        HTTPStatus.CREATED
    ),

    # Несколько курьеров
    (
        [
            generate_courier(courier_id=1),
            generate_courier(courier_id=2),
            generate_courier(courier_id=3)
        ],
        HTTPStatus.CREATED
    ),

    # Выгрузка с максимально длинными/большими значениями.
    # aiohttp должен разрешать запросы такого размера, а обработчик не должен
    # на них падать.
    (
        generate_couriers(
            couriers_num=10000,
            start_courier_id=MAX_INTEGER - 10000,
            courier_type='bike',
        ),
        HTTPStatus.CREATED
    ),

    # Пустая выгрузка
    # Обработчик не должен падать на таких данных.
    (
        [],
        HTTPStatus.CREATED
    ),

    # courier_id не уникален в рамках выгрузки
    (
        [
            generate_courier(courier_id=1),
            generate_courier(courier_id=1),
        ],
        HTTPStatus.BAD_REQUEST
    ),
)


@pytest.mark.parametrize('couriers,expected_status', CASES)
async def test_import(api_client, couriers, expected_status):
    courier_ids = await post_couriers(api_client, couriers, expected_status)

    if len(courier_ids) < 10:
        print(courier_ids)

    # Проверяем, что данные успешно импортированы
    if expected_status == HTTPStatus.CREATED:
        imported_couriers = []
        for courier_id in courier_ids:
            imported_courier = await get_courier(api_client, courier_id)
            imported_couriers.append(imported_courier)
        assert compare_courier_groups(couriers, imported_couriers)

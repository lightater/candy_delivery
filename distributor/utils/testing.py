from enum import EnumMeta
from http import HTTPStatus
from random import choice, randint, randrange, shuffle
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union

import faker
from aiohttp.test_utils import TestClient
from aiohttp.typedefs import StrOrURL
from aiohttp.web_urldispatcher import DynamicResource

from distributor.api.handlers import (
    CourierView, PostCouriersView
)
from distributor.api.schema import (
    CourierSchema,
    CourierResponseSchema, PostCouriersResponseSchema,
    PatchCourierResponseSchema
)
from distributor.utils.pg import MAX_INTEGER


fake = faker.Faker('ru_RU')


def url_for(path: str, **kwargs) -> str:
    """
    Генерирует URL для динамического aiohttp маршрута с параметрами.
    """
    kwargs = {
        key: str(value)  # Все значения должны быть str (для DynamicResource)
        for key, value in kwargs.items()
    }
    return str(DynamicResource(path).url_for(**kwargs))


def generate_courier(
        courier_id: Optional[int] = None,
        courier_type: Optional[str] = None,
        regions: Optional[List[int]] = None,
        working_hours: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Создает и возвращает курьера, автоматически генерируя данные для не
    указанных полей.
    """
    if courier_id is None:
        courier_id = randint(0, MAX_INTEGER)

    if courier_type is None:
        courier_type = choice(('foot', 'bike', 'car'))

    if regions is None:
        reg = set()
        for i in range(randint(1, 5)):
            reg.add(randint(0, 20))
        regions = list(reg)

    if working_hours is None:
        w_hours = set()
        for i in range(randint(1, 5)):
            start, end = fake.date_time(), fake.date_time()
            if start > end:
                start, end = end, start
            w_hours.add(start.strftime('%H:%M') + '-' + end.strftime('%H:%M'))
        working_hours = list(w_hours)

    return {
        'courier_id': courier_id,
        'courier_type': courier_type,
        'regions': regions,
        'working_hours': working_hours,
    }


def generate_couriers(
        couriers_num: int,
        unique_regions: int = 20,
        start_courier_id: int = 0,
        **courier_kwargs
) -> List[Dict[str, Any]]:
    """
    Генерирует список курьеров.
    :param couriers_num: Количество курьеров
    :param unique_regions: Кол-во уникальных регионов в выгрузке
    :param start_courier_id: С какого courier_id начинать
    :param courier_kwargs: Аргументы для функции generate_couriers
    """
    # Ограничнный набор городов
    regions = [range(unique_regions)]
    types = ['foot', 'bike', 'car']

    # Создаем жителей
    max_courier_id = start_courier_id + couriers_num - 1
    couriers = {}
    for courier_id in range(start_courier_id, max_courier_id + 1):
        courier_kwargs['courier_type'] = courier_kwargs.get('courier_type',
                                                            choice(types))
        couriers[courier_id] = generate_courier(courier_id=courier_id,
                                                **courier_kwargs)

    return list(couriers.values())


def normalize_courier(courier):
    """
    Преобразует объект с курьером для сравнения с другими.
    """
    return {**courier,
            'regions': sorted(courier['regions']),
            'working_hours': sorted(courier['working_hours'])}


def compare_couriers(left: Mapping, right: Mapping) -> bool:
    return normalize_courier(left) == normalize_courier(right)


def compare_courier_groups(left: Iterable, right: Iterable) -> bool:
    left = [normalize_courier(courier) for courier in left]
    left.sort(key=lambda courier: courier['courier_id'])

    right = [normalize_courier(courier) for courier in right]
    right.sort(key=lambda courier: courier['courier_id'])
    return left == right


async def post_couriers(
        client: TestClient,
        couriers: List[Mapping[str, Any]],
        expected_status: Union[int, EnumMeta] = HTTPStatus.CREATED,
        **request_kwargs
) -> dict:
    response = await client.post(
        PostCouriersView.URL_PATH, json={'data': couriers},
        **request_kwargs
    )
    assert response.status == expected_status

    if response.status == HTTPStatus.CREATED:
        data = await response.json()
        errors = PostCouriersResponseSchema().validate(data)
        assert errors == {}
        return data['couriers']


async def get_courier(
        client: TestClient,
        courier_id: int,
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        **request_kwargs
) -> dict:
    response = await client.get(
        url_for(CourierView.URL_PATH, courier_id=courier_id),
        **request_kwargs
    )
    assert response.status == expected_status

    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = CourierSchema().validate(data)
        assert errors == {}
        return data


async def patch_courier(
        client: TestClient,
        courier_id: int,
        data: Mapping[str, Any],
        expected_status: Union[int, EnumMeta] = HTTPStatus.OK,
        str_or_url: StrOrURL = CourierView.URL_PATH,
        **request_kwargs
):
    response = await client.patch(
        url_for(str_or_url, courier_id=courier_id),
        json=data,
        **request_kwargs
    )
    assert response.status == expected_status
    if response.status == HTTPStatus.OK:
        data = await response.json()
        errors = PatchCourierResponseSchema().validate(data)
        assert errors == {}
        return data['data']

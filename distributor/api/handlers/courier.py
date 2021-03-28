from http import HTTPStatus
from typing import Generator

from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_response import Response
from aiohttp_apispec import docs, request_schema, response_schema
from aiomisc import chunk_list
from sqlalchemy import and_, or_

from distributor.api.schema import CourierSchema, \
    PatchCourierResponseSchema, PatchCourierSchema, PostCouriersSchema, \
    PostCouriersResponseSchema

from distributor.db.schema import assigned_orders_table, couriers_table, \
    orders_table
from distributor.utils.helpers_func import calc_courier_carrying, overlap
from distributor.utils.pg import MAX_QUERY_ARGS, SelectQuery

from .base import BaseCourierView, BaseView
from .query import COURIERS_QUERY


class PostCouriersView(BaseView):
    URL_PATH = '/couriers'
    # Так как данных может быть много, а postgres поддерживает только
    # MAX_QUERY_ARGS аргументов в одном запросе, писать в БД необходимо
    # частями.
    # Максимальное кол-во строк для вставки можно рассчитать как отношение
    # MAX_QUERY_ARGS к кол-ву вставляемых в таблицу столбцов.
    MAX_COURIERS_PER_INSERT = MAX_QUERY_ARGS // len(couriers_table.columns)

    @classmethod
    def make_couriers_table_rows(cls, couriers) -> Generator:
        """
        Генерирует данные готовые для вставки в таблицу couriers (с ключом
        earnings).
        """
        for courier in couriers:
            yield {
                'courier_id': courier['courier_id'],
                'courier_type': courier['courier_type'],
                'regions': courier['regions'],
                'working_hours': courier['working_hours'],
                # 'earnings': 0
            }

    @docs(summary='Добавить выгрузку с информацией о курьерах')
    @request_schema(PostCouriersSchema())
    @response_schema(PostCouriersResponseSchema(),
                     code=HTTPStatus.CREATED.value)
    async def post(self):
        # Транзакция требуется чтобы в случае ошибки (или отключения клиента,
        # не дождавшегося ответа) откатить частично добавленные изменения.
        async with self.pg.transaction() as conn:
            # Генераторы make_citizens_table_rows и make_relations_table_rows
            # лениво генерируют данные, готовые для вставки в таблицы citizens
            # и relations на основе данных отправленных клиентом.
            couriers = self.request['data']['data']
            courier_rows = self.make_couriers_table_rows(couriers)

            # Чтобы уложиться в ограничение кол-ва аргументов в запросе к
            # postgres, а также сэкономить память и избежать создания полной
            # копии данных присланных клиентом во время подготовки - используем
            # генератор chunk_list.
            # Он будет получать из генератора make_citizens_table_rows только
            # необходимый для 1 запроса объем данных.
            chunked_courier_rows = chunk_list(courier_rows,
                                              self.MAX_COURIERS_PER_INSERT)

            query = couriers_table.insert()
            for chunk in chunked_courier_rows:
                await conn.execute(query.values(list(chunk)))
            courier_ids = []
            for courier in couriers:
                courier_ids.append({'courier_id': courier['courier_id']})

        return Response(body={'couriers': courier_ids},
                        status=HTTPStatus.CREATED)


class CourierView(BaseCourierView):
    URL_PATH = r'/couriers/{courier_id:\d+}'

    @property
    def courier_id(self):
        return int(self.request.match_info.get('courier_id'))

    @staticmethod
    async def acquire_lock(conn, courier_id):
        await conn.execute('SELECT pg_advisory_xact_lock($1)', courier_id)

    @staticmethod
    async def get_courier(conn, courier_id):
        query = COURIERS_QUERY.where(couriers_table.c.courier_id == courier_id)
        result = await conn.execute(query)
        print(result)
        return result.fetchone

    @staticmethod
    async def get_assigned_orders(conn, courier_id):
        query = assigned_orders_table.select().where(
            assigned_orders_table.c.courier_id == courier_id)
        return await conn.fetchall(query)

    @staticmethod
    async def move_orders(conn, order_ids):
        if not order_ids:
            return

        conditions = []
        for order_id in order_ids:
            conditions.append(assigned_orders_table.c.order_id == order_id)
        query_del = assigned_orders_table.delete().returning(or_(*conditions))
        orders = await conn.execute(query_del).fetchall()
        query_ins = orders_table.insert().values(orders)
        await conn.execute(query_ins)

    @classmethod
    async def update_courier(cls, conn, courier_id, data):
        values = {k: v for k, v in data.items()}
        if values:
            query = couriers_table.update().values(values).where(
                couriers_table.c.courier_id == courier_id
            )
            await conn.execute(query)

    @docs(summary='Обновить указанного курьера')
    @request_schema(PatchCourierSchema())
    @response_schema(PatchCourierResponseSchema(), code=HTTPStatus.OK.value)
    async def patch(self):
        # Транзакция требуется чтобы в случае ошибки (или отключения клиента,
        # не дождавшегося ответа) откатить частично добавленные изменения, а
        # также для получения транзакционной advisory-блокировки.
        async with self.pg.transaction() as conn:

            # Блокировка позволит избежать состояние гонки между конкурентными
            # запросами на изменение родственников.
            await self.acquire_lock(conn, self.courier_id)

            # Получаю информацию о курьере
            courier = await self.get_courier(conn, self.courier_id)
            if not courier:
                raise HTTPNotFound()

            # Обновляю assigned orders и orders
            orders = await self.get_assigned_orders(conn, self.courier_id)
            orders_to_remove = []
            for order in orders:
                if (order['weight'] > calc_courier_carrying(
                        self.request['data']['courier_type'])) or (overlap(
                    order['delivery_hours'],
                    self.request['data']['delivery_hours'])):
                    orders_to_remove.append(order)
            await self.move_orders(conn, orders_to_remove)

            # Обновляю таблицу couriers
            await self.update_courier(conn, self.courier_id,
                                      self.request['data'])

            # Получаю актуальную информацию о курьере
            courier = await self.get_courier(conn, self.courier_id)
        return Response(body={'data': courier})

    @docs(summary='Отобразить указанного курьера')
    @response_schema(CourierSchema())
    async def get(self):
        #query = COURIERS_QUERY.where(
        #    couriers_table.c.courier_id == self.courier_id
        #)
        #for itr in SelectQuery(query, self.pg.transaction()):
        #    print(itr)
        #courier = SelectQuery(query, self.pg.transaction())
        async with self.pg.transaction() as conn:
            await self.acquire_lock(conn, self.courier_id)
            courier = await self.get_courier(conn, self.courier_id)
            if not courier:
                raise HTTPNotFound()
            return Response(body=courier)

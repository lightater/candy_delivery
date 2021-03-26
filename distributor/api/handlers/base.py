from aiohttp.web_exceptions import HTTPNotFound
from aiohttp.web_urldispatcher import View
from asyncpgsa import PG
from sqlalchemy import exists, select

from distributor.db.schema import couriers_table


class BaseView(View):
    URL_PATH: str

    @property
    def pg(self) -> PG:
        return self.request.app['pg']


class BaseCourierView(BaseView):
    @property
    def courier_id(self):
        return int(self.request.match_info.get('courier_id'))

    async def check_courier_exists(self):
        print("HERE")
        query = select([
            exists().where(couriers_table.c.courier_id == self.courier_id)
        ])
        if not await self.pg.fetchval(query):
            raise HTTPNotFound()

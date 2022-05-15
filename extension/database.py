from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, Float
import asyncio
import asyncpg
import sqlalchemy.exc
import sqlalchemy

Base = declarative_base()


class AsyncDatabaseSession:
    def __init__(self):
        self._session = None
        self._engine = None

    def __getattr__(self, name):
        return getattr(self._session, name)

    async def init(self):
        self._engine = create_async_engine("postgresql+asyncpg://", echo=True)

        self._session = sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession)()

    async def create_all(self):
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async_db_session = AsyncDatabaseSession()


class ModelAdmin:
    @classmethod
    async def create(cls, people_or_order):
        async_db_session.add(people_or_order)
        await async_db_session.commit()

    @classmethod
    async def update(cls, id_tg, **kwargs):
        query = (
            sqlalchemy.sql.update(cls)
            .where(cls.telegram_id == id_tg)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await async_db_session.execute(query)
        await async_db_session.commit()

    @classmethod
    async def update_order(cls, id_order, **kwargs):
        query = (
            sqlalchemy.sql.update(cls)
            .where(cls.id == id_order)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await async_db_session.execute(query)
        await async_db_session.commit()

    @classmethod
    async def update_admin(cls, id_temp, **kwargs):
        query = (
            sqlalchemy.sql.update(cls)
            .where(cls.id == id_temp)
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await async_db_session.execute(query)
        await async_db_session.commit()

    @classmethod
    async def get_history(cls, id_tg, order: str = "Исполнено"):
        query = select(cls).where(cls.oper_id == id_tg, cls.state == order)
        result = await async_db_session.execute(query)
        return result.fetchall()

    @classmethod
    async def get_account(cls, id_tg):
        query = select(cls).where(cls.telegram_id == id_tg)
        result = await async_db_session.execute(query)
        try:
            (result,) = result.one()
        except sqlalchemy.exc.NoResultFound:
            result = None
        return result

    @classmethod
    async def get_db_admin(cls, id_temp):
        query = select(cls).where(cls.id == id_temp)
        result = await async_db_session.execute(query)
        try:
            (result,) = result.one()
        except sqlalchemy.exc.NoResultFound:
            result = None
        return result

    @classmethod
    async def get_db(cls):
        query = select(cls)
        result = await async_db_session.execute(query)
        return result.scalars()

    @classmethod
    async def delete(cls, id_tg):
        query = sqlalchemy.delete(cls).where(cls.telegram_id == id_tg)
        await async_db_session.execute(query)
        await async_db_session.commit()


class Account(Base, ModelAdmin):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger)
    name = Column(String)
    wallet_number = Column(String)
    language = Column(String)
    telegram_name = Column(String)
    refer_user = Column(String)
    date_born = Column(String)

    def __init__(self, telegram_id: int = None, name: str = None, wallet_number: str = None, language: str = None,
                 telegram_name: str = None, refer_user: str = None, date_born: str = None):
        super().__init__()
        self.telegram_id = telegram_id
        self.name = name
        self.wallet_number = wallet_number
        self.language = language
        self.telegram_name = telegram_name
        self.refer_user = refer_user
        self.date_born = date_born

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}("
            f"id={self.id}, "
            f"full_name={self.telegram_name}, "
            f"telegram_id={self.telegram_id}"
            ")>"
        )


class Order(Base, ModelAdmin):
    __tablename__ = 'orders'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    oper_id = Column(BigInteger)
    owner_id = Column(BigInteger)
    title = Column(String)
    state = Column(String)
    give = Column(String)
    get = Column(String)
    name_oper = Column(String)
    name_owner = Column(String)
    date_time = Column(String)

    def __init__(self,
                 oper_id: int = None,
                 owner_id: int = None,
                 title: str = None,
                 give: str = None,
                 get: str = None,
                 name_oper: str = None,
                 name_owner: str = None,
                 date_time: str = None,
                 state: str = None
                 ):
        super().__init__()
        self.oper_id = oper_id
        self.owner_id = owner_id
        self.title = title
        self.give = give
        self.get = get
        self.name_oper = name_oper
        self.name_owner = name_owner
        self.date_time = date_time
        self.state = state

    def __repr__(self):
        return f"📜Id обмена: {self.id}\n" + f"Название: {self.title}\n" + f"Номер ордера: {self.id}\n" \
                                                                           f"Вы: {self.name_oper}\n" \
                                                                           f"Обменник: {self.name_owner}\n" \
                                                                           f"Отдавали: {self.give}\n" \
                                                                           f"Получали: {self.get}\n" \
                                                                           f"{self.date_time}"


class PercentDB(Base, ModelAdmin):
    __tablename__ = 'admin_settings'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    percent = Column(Float)
    place = Column(String)
    time = Column(String)

    def __init__(self,
                 percent: float = None,
                 place: str = place,
                 time: str = time
                 ):
        super().__init__()
        self.percent = percent
        self.place = place
        self.time = time

    def __repr__(self):
        return (
            f"{float(self.percent)}"
        )


class CurrencyWallet(Base, ModelAdmin):
    __tablename__ = 'Currency'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    USDT = Column(Float)
    USD = Column(Float)
    AED = Column(Float)

    def __init__(self,
                 USDT: float = None,
                 USD: float = None,
                 AED: float = None
                 ):
        super().__init__()
        self.USDT = USDT
        self.USD = USD
        self.AED = AED

    def __repr__(self):
        return (
            f"id={self.id}, "
            f"USD = {float(self.USD)}, "
            f"USDT = {float(self.USDT)}, "
            f"AED = {float(self.AED)}, "
        )

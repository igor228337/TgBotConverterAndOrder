from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Filter


class StateSave(StatesGroup):
    give = State()
    You_give = State()
    get = State()
    give_currency_name = State()
    get_currency_name = State()


class EditState(StatesGroup):
    percent = State()
    time = State()
    place = State()


class AccountState(StatesGroup):
    language = State()
    name = State()
    wallet_number = State()


class IsAdmin(Filter):
    key = "is_admin"

    async def check(self, message: types.Message):
        return message.from_user.id in BotClass.admins


class BotClass:
    Api: str = ""
    admin: str = "@"
    info_bot: int = 0
    admins: list = []
    bot: Bot = Bot(token=token)
    dp = Dispatcher(bot, storage=MemoryStorage())
    dp.middleware.setup(LoggingMiddleware())

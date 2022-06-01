from pycoingecko import CoinGeckoAPI
from aiogram import Bot, Dispatcher, executor, types
from extension.botclass import BotClass, AccountState, EditState, StateSave, IsAdmin
from extension.classmessage import Message, Language, Button, Currency, ButtonHistory
from extension.database import Order, Account, async_db_session, PercentDB, CurrencyWallet
from extension.load_sheets import load_sheets
from aiogram.utils.exceptions import BotBlocked
from aiogram.dispatcher import FSMContext
from aiogram.utils.deep_linking import get_start_link
from aiogram.dispatcher.filters import Text
from textblob import TextBlob
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from requests_html import HTMLSession
from bs4 import BeautifulSoup
import asyncio
import fake_useragent
import requests
import datetime
import random
import aiogram


dp = BotClass.dp
languages: list = [i.value for i in Language]


async def translate_language(text: str, country: str) -> str:
    if country != "ru":
        return TextBlob(text).translator.translate(text, from_lang="ru", to_lang=country)
    else:
        return text


async def get_course(give, get) -> tuple | None:
    give, get = give.lower().replace("usdt", "tether"), get.lower().replace("usdt", "tether")
    cg = CoinGeckoAPI()
    a = cg.get_price(ids=give, vs_currencies=get)
    try:
        return float(a[give][get]), False
    except KeyError:
        a = cg.get_price(ids=get, vs_currencies=give)
        return float(a[get][give]), True


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.reset_state(with_data=False)
    await message.reply(Message.CANCEL)


@dp.message_handler(commands="block")
async def cmd_block(message: types.Message) -> None:
    acc = await get_account(message.from_user.id)
    await asyncio.sleep(10.0)
    await message.reply(await translate_language("Вы заблокированы", acc.language))


@dp.errors_handler(exception=BotBlocked)
async def error_bot_blocked(update: types.Update, exception: BotBlocked) -> bool:
    await Account.delete(update.message.from_user.id)
    print(f"Меня заблокировал пользователь!\nСообщение: {update}\nОшибка: {exception}")
    return True


async def shutdown(dispatcher: Dispatcher) -> None:
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()


async def markup_language() -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup()
    mar_temp = []
    i = 0
    for mark in Language:
        if i % 3 == 0:
            markup.add(*mar_temp)
            mar_temp.clear()
        mar_temp.append(types.KeyboardButton(mark.value))
        i += 1
    markup.add(*mar_temp)
    mar_temp.clear()
    return markup


async def markup_button(language, message: types.Message) -> types.ReplyKeyboardMarkup:
    markup = types.ReplyKeyboardMarkup()
    if message.from_user.id in BotClass.admins:
        buttons = [types.KeyboardButton(await translate_language(i.value, language)) for i in Button]
    else:
        buttons = [types.KeyboardButton(await translate_language(i.value, language)) for i in
                   [v for k, v in enumerate(Button) if k < 4]]
    markup.add(*buttons)
    return markup


async def extract_unique_code(text):
    # Extracts the unique_code from the sent /start command.
    return text.split()[1] if len(text.split()) > 1 else None


@dp.message_handler(commands="start", state="*")
async def start(message: types.Message) -> None:
    acc = await Account.get_account(message.from_user.id)
    if not acc:
        unique_code = await extract_unique_code(message.text)
        if unique_code:
            try:
                username = message.from_user.username
            except:
                username = ""
            await Account.create(Account(telegram_id=message.from_user.id, wallet_number="", language="en",
                                         telegram_name=username, refer_user=unique_code,
                                         date_born=str(datetime.datetime.now().strftime("%d.%m.%Y"))))
        else:
            try:
                username = message.from_user.username
            except:
                username = ""
            await Account.create(Account(telegram_id=message.from_user.id, wallet_number="", language="en",
                                         telegram_name=username, refer_user="",
                                         date_born=str(datetime.datetime.now().strftime("%d.%m.%Y"))))
        await AccountState.language.set()
        await message.answer(await translate_language(Message.GREETING, "en"), reply_markup=await markup_language())
    else:
        markup = await markup_button(acc.language, message)
        await message.answer(await translate_language(Message.REPEAT_START, acc.language),
                             reply_markup=markup)


@dp.message_handler(lambda message: not message.text in languages, state=AccountState.language)
async def process_language_invalid(message: types.Message):
    return await message.reply(await translate_language(Message.NO_LANGUAGE, "en"))


@dp.message_handler(state=AccountState.language)
async def set_language(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["language"] = message.text
    await AccountState.next()
    await message.answer(await translate_language(Message.WHAT_NAME, message.text),
                         reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(lambda message: str(message.text).isdigit() or message.text.lower() in Message.BAD_SAY,
                    state=AccountState.name)
async def process_language_invalid(message: types.Message):
    return await message.reply(await translate_language(Message.NO_NAME, "en"))


@dp.message_handler(state=AccountState.name)
async def set_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["name"] = message.text

    user_data = await state.get_data()
    await Account.update(id_tg=message.from_user.id, name=message.text, language=user_data["language"])
    await state.reset_state(with_data=False)
    await message.answer(await translate_language(Message.SUCCESSFULLY, user_data["language"]),
                         reply_markup=await markup_button(language=user_data["language"], message=message))


async def result_money(give, message, state, list_cur, what) -> bool:
    percent = await PercentDB.get_db_admin(1)
    for i in Currency:
        i = i.value
        if give.lower() != i.lower():
            value, revers = await get_course(give, i)
            if not revers:
                data = value * float(message.text) * (1 - percent.percent)
            else:
                data = float(message.text) / value / (1 + percent.percent)
            list_cur.append(i + ": " + str(round(data, 3)))
        else:
            value = 1
            list_cur.append(i + ": " + str(round(value * float(message.text), 3)))
    async with state.proxy() as data:
        data[f"{what}"] = list_cur
    return True


@dp.message_handler(lambda message: valid_float(message.text) is False, state=StateSave.You_give)
async def process_currency_invalid(message: types.Message):
    acc = await Account.get_account(message.from_user.id)
    return await message.reply(await translate_language(Message.NO_CURRENCY, acc.language))


@dp.message_handler(state=StateSave.You_give)
async def set_you_give(message: types.Message, state: FSMContext) -> None:
    acc = await Account.get_account(message.from_user.id)
    async with state.proxy() as data:
        data["You_give"] = message.text
        give = data["give"].data.split("_")[0]
    await state.reset_state(with_data=False)
    language = acc.language
    list_cur = []
    a = await result_money(give, message, state, list_cur, "get")
    if a:
        await message.answer(await translate_language(Message.CALC_GIVE_SEND_PEOPLE + "\n" + "\n".join(list_cur),
                                                      language),
                             reply_markup=await gen_inline_calc(language, False, "get"))
    else:
        pass


@dp.callback_query_handler(lambda call: call.data.endswith("_you_get"))
async def currency_you_get(call: types.CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup(None)
    acc = await Account.get_account(call.from_user.id)
    language = acc.language
    async with state.proxy() as data:
        data["give_currency_name"] = data["give"].data.split("_")[0]
        data["get_currency_name"] = call.data.split("_")[0]
    await call.message.edit_reply_markup(reply_markup=await gen_inline_calc(language, True, "get"))


@dp.callback_query_handler(lambda call: call.data.endswith("_you_give"))
async def currency_you_give(call: types.CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup(None)
    acc = await Account.get_account(call.from_user.id)
    await StateSave.You_give.set()
    async with state.proxy() as data:
        data["give"] = call
    await call.message.answer(await translate_language(Message.MESSAGE_GIVE.format(currency=call.data.split("_")[0],
                                                                                   what=Message.YOU_GIVE),
                                                       acc.language))


@dp.callback_query_handler(lambda call: call.data.startswith("what_"))
async def what_give(call: types.CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup(None)
    what = call.data.split("_")[-1]
    acc = await Account.get_account(call.from_user.id)
    language = acc.language
    if what == "give":
        await call.message.answer(await translate_language(Message.CALC_GIVE, language),
                                  reply_markup=await gen_inline_calc(language, False, what))
    elif what == "get":
        await call.message.answer(await translate_language(Message.CALC_GET, language),
                                  reply_markup=await gen_inline_calc(language, False, "what_get"))
    else:
        print("GG 1")


async def gen_inline_what(language: str) -> types.InlineKeyboardMarkup:
    inline = types.InlineKeyboardMarkup()
    inline.add(types.InlineKeyboardButton(await translate_language(f"⬇{Message.YOU_GIVE}⬇", language),
                                          callback_data="what_give"))
    inline.add(types.InlineKeyboardButton(await translate_language(f"⬇{Message.YOU_GET}⬇", language),
                                          callback_data="what_get"))
    return inline


async def gen_inline_calc(language: str, no_push: bool = True, give_get: str | None = None) -> \
        types.InlineKeyboardMarkup:
    inline = types.InlineKeyboardMarkup()
    if give_get == "give":
        inline.add(types.InlineKeyboardButton(await translate_language(f"⬇{Message.YOU_GIVE}⬇", language),
                                              callback_data="0"))
        inline.add(
            *[types.InlineKeyboardButton(await translate_language(i.value, language),
                                         callback_data=i.value + "_you_give")
              for i in Currency])

    elif give_get == "get":
        inline.add(types.InlineKeyboardButton(await translate_language(f"⬇{Message.YOU_GET}⬇", language),
                                              callback_data="0"))
        inline.add(
            *[types.InlineKeyboardButton(await translate_language(i.value, language),
                                         callback_data=i.value + "_you_get")
              for i in Currency])
    elif give_get == "what_get":
        inline.add(types.InlineKeyboardButton(await translate_language(f"⬇{Message.YOU_GET}⬇", language),
                                              callback_data="0"))
        inline.add(
            *[types.InlineKeyboardButton(await translate_language(i.value, language),
                                         callback_data=i.value + "_will_i_get")
              for i in Currency])
    elif give_get == "what_give":
        inline.add(types.InlineKeyboardButton(await translate_language(f"⬇{Message.YOU_GIVE}⬇", language),
                                              callback_data="0"))
        inline.add(
            *[types.InlineKeyboardButton(await translate_language(i.value, language),
                                         callback_data=i.value + "_will_i_give")
              for i in Currency])
    if no_push:
        inline.add(types.InlineKeyboardButton(await translate_language(Message.SEND_ORDER, language),
                                              callback_data="create_order"))
    return inline


async def init() -> None:
    await async_db_session.init()
    # await async_db_session.create_all()


def valid_float(text) -> float | None:
    try:
        return float(text)
    except ValueError:
        return False


@dp.message_handler(lambda message: valid_float(message.text) is False, state=EditState.percent)
async def process_currency_invalid(message: types.Message):
    acc = await Account.get_account(message.from_user.id)
    return await message.reply(await translate_language(Message.NO_CURRENCY, acc.language))


@dp.message_handler(state=EditState.percent)
async def set_percent(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["percent"] = message.text
    await state.reset_state(with_data=False)
    await PercentDB.update_admin(1, percent=float(message.text))
    acc = await Account.get_account(message.from_user.id)

    await message.answer(await translate_language(Message.EDIT_PERCENT_SUCCESS, acc.language))


@dp.message_handler(state=EditState.time)
async def set_time(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["time"] = message.text
    await state.reset_state(with_data=False)
    await PercentDB.update_admin(1, time=message.text)
    acc = await Account.get_account(message.from_user.id)
    await message.answer(await translate_language(Message.EDIT_TIME_SUCCESS, acc.language))


@dp.message_handler(state=EditState.place)
async def set_place(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["place"] = message.text
    await state.reset_state(with_data=False)
    await PercentDB.update_admin(1, place=message.text)
    acc = await Account.get_account(message.from_user.id)
    await message.answer(await translate_language(Message.EDIT_PLACE_SUCCESS, acc.language))


async def gen_inline_button(names, calls, language) -> types.InlineKeyboardMarkup:
    markup = types.InlineKeyboardMarkup()
    for n, c in zip(names, calls):
        markup.add(types.InlineKeyboardButton(text=await translate_language(n, language), callback_data=c))
    return markup


@dp.callback_query_handler(lambda call: call.data == "Yes_send")
async def create_order_yes(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(None)
    acc = await Account.get_account(call.from_user)
    language = acc.language
    async with state.proxy() as data:
        if data["get_currency_name"] != "USDT" and data["get"] != "":
            await send_order_admin(call=call, state=state)

        elif data["get"] != "":
            wallet = acc.wallet_number
            if wallet == "":
                await call.message.answer(await translate_language(Message.WHAT_WALLET.format(wallet=wallet), language),
                                          reply_markup=await gen_inline_button(["Другой"], ["Another"],
                                                                               language))
            else:
                await call.message.answer(await translate_language(Message.WHAT_WALLET.format(wallet=wallet), language),
                                          reply_markup=await gen_inline_button(["Да", "Другой"], ["Yes", "Another"],
                                                                               language))
        else:
            await call.message.answer(await translate_language(Message.NO_SEND, language))


@dp.message_handler(state=AccountState.wallet_number)
async def set_state_reg_finish(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data["wallet_number"] = message.text
    await Account.update(message.from_user.id, wallet_number=message.text)
    await send_order_admin(message=message, state=state)


@dp.callback_query_handler(lambda call: call.data == "Another")
async def create_order_another(call: types.CallbackQuery) -> None:
    await call.message.edit_reply_markup(None)
    acc = await Account.get_account(call.from_user.id)
    language = acc.language
    await call.message.answer(await translate_language(Message.WALLET_NUMBER, language))
    await AccountState.wallet_number.set()


@dp.callback_query_handler(lambda call: call.data == "Success_order" or call.data == "Cancel_order")
async def success_order(call: types.CallbackQuery) -> None:
    await call.message.edit_reply_markup(None)
    id_orders = int(call.message.text.split("\n")[2].split(": ")[-1])
    order = await Order.get_db_admin(id_orders)
    if order.state == "Исполнено" or order.state == "Отменено":
        pass
    else:
        try:
            acc = await Account.get_account(call.from_user.id)
            language = acc.language
        except:
            language = "ru"

        if call.data == "Success_order":
            await Order.update_order(id_orders, state="Исполнено")
            await call.message.answer(await translate_language(Message.SUCCESS_ORDER, language))
        elif call.data == "Cancel_order":
            await Order.update_order(id_orders, state="Отменено")
            await call.message.answer(await translate_language(Message.CANCEL_ORDER, language))


@dp.message_handler(lambda message: valid_float(message.text) is False, state=StateSave.get)
async def process_currency_invalid(message: types.Message):
    acc = await Account.get_account(message.from_user.id)
    return await message.reply(await translate_language(Message.NO_CURRENCY, acc.language))


@dp.message_handler(state=StateSave.get)
async def set_state_get(message: types.Message, state: FSMContext) -> None:
    acc = await Account.get_account(message.from_user.id)
    async with state.proxy() as data:
        data["get_currency_name"] = data["get"]
        get = data["get"]
        data["get"] = message.text + " " + get
    await state.reset_state(with_data=False)
    list_cur = []
    language = acc.language
    a = await result_money(get, message, state, list_cur, "give")
    if a:
        await message.answer(await translate_language(Message.CALC_GET_SEND_PEOPLE + "\n" + "\n".join(list_cur),
                                                      language),
                             reply_markup=await gen_inline_calc(language, False, "what_give"))
    else:
        pass


@dp.callback_query_handler(lambda call: call.data.endswith("_will_i_give"))
async def end_get(call: types.CallbackQuery, state: FSMContext) -> None:
    acc = await Account.get_account(call.from_user.id)
    language = acc.language
    async with state.proxy() as data:
        data["give_currency_name"] = call.data.split("_")[0]
        data["get_currency_name"], data["give_currency_name"] = data["give_currency_name"], data["get_currency_name"]
        data["get"], data["give"] = data["give"], data["get"]
        data["You_give"] = data["give"]
    await call.message.edit_reply_markup(reply_markup=await gen_inline_calc(language, True, "what_get"))


@dp.callback_query_handler(lambda call: call.data.endswith("_will_i_get"))
async def will_i_get(call: types.CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup(None)
    async with state.proxy() as data:
        data["get"] = call.data.split("_")[0]
    await StateSave.get.set()
    acc = await Account.get_account(call.from_user.id)
    await call.message.answer(await translate_language(
        Message.CALC_GET_PEOPLE.format(what=call.data.split("_")[0]), acc.language))


async def find_and_return_get(all_cur, name) -> str:
    for i in all_cur:
        if name in i:
            n, v = i.split(": ")
            return v + " " + n


async def send_order_admin(state: FSMContext, message=None, call=None) -> None:
    if call is not None:
        id_tg = call.from_user.id
        username = call.from_user.username
    else:
        id_tg = message.from_user.id
        username = message.from_user.username

    acc = await Account.get_account(id_tg)
    language = acc.language
    wallet = acc.wallet_number
    admin = await PercentDB.get_db_admin(1)
    async with state.proxy() as data:
        try:
            give = str(float(data["You_give"])) + " " + data["give_currency_name"]
            get = await find_and_return_get(data["get"], data["get_currency_name"])
        except ValueError:
            get = data["You_give"]
            give = await find_and_return_get(data["get"], data["get_currency_name"])

    order = Order(id_tg, BotClass.info_bot, "Обмен", give,
                  get, name_oper=username, name_owner=BotClass.admin,
                  date_time=str(datetime.datetime.now().strftime("Дата: %d.%m.%Y\nВремя: %H:%M")),
                  state="Открытый")

    await Order.create(order)

    message_send = await translate_language(Message.CANCEL_CREATE_ORDER.format(
        id_order=order.id,
        date=datetime.datetime.now().date(),
        time=admin.time,
        place=admin.place,
        wallet=wallet,
        username="@" + username,
        give=give,
        get=get,
        rnd=f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
            f"-{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}",
        admin_username=BotClass.admin
    ), language)
    if call is not None:
        await call.message.answer(await translate_language(Message.THANK_SEND_ORDER, language))
        await call.message.answer(await translate_language(message_send, language))
        await dp.bot.send_message(chat_id=BotClass.info_bot, text=message_send,
                                  reply_markup=await gen_inline_button(['Завершено', 'Отмена'],
                                                                       ['Success_order', 'Cancel_order'], "ru"))
    else:
        await message.answer(await translate_language(Message.THANK_SEND_ORDER, language))
        await message.answer(await translate_language(message_send, language))
        await dp.bot.send_message(chat_id=BotClass.info_bot, text=message_send,
                                  reply_markup=await gen_inline_button(['Завершено', 'Отмена'],
                                                                       ['Success_order', 'Cancel_order'], "ru"))
    await state.reset_state(with_data=False)


@dp.callback_query_handler(lambda call: call.data == "Yes")
async def created_order_yes_yes(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(None)
    await send_order_admin(call=call, state=state)


@dp.callback_query_handler(lambda call: call.data == "No_send")
async def create_order_no(call: types.CallbackQuery) -> None:
    await call.message.edit_reply_markup(None)


@dp.callback_query_handler(lambda call: call.data == "create_order")
async def create_order(call: types.CallbackQuery, state: FSMContext) -> None:
    await call.message.edit_reply_markup(None)
    acc = await Account.get_account(call.from_user.id)
    await call.message.answer(await translate_language(Message.CONFIRMATION_ORDER, acc.language),
                              reply_markup=await gen_inline_button(["Да", "Нет"], ["Yes_send", "No_send"],
                                                                   acc.language))


@dp.message_handler(commands="GetId")
async def get_id(message: types.Message):
    await message.answer(message.from_user.id)


@dp.message_handler(IsAdmin(), commands=["updateSheets"])
async def save_sheets(message: types.Message) -> None:
    while 1:
        data = await Account.get_db()
        data_order = await Order.get_db()
        close_order = []
        for i in data_order:
            if i.state == "Открытый" and int(i.date_time.split("\n")[0].split(": ")[-1].split(".")[0]) < int(
                    datetime.datetime.now().strftime("%d")):
                close_order.append(i.id)
        for id_temp in close_order:
            await Order.update_order(id_temp, state="Отменено")
        data_order = await Order.get_db()
        data_post = []
        for i in data:
            tg_username = i.telegram_name
            if "@" not in i.telegram_name:
                tg_username = "@" + tg_username

            data_post.append([i.id, i.telegram_id, i.name, i.wallet_number, i.language, tg_username, i.refer_user,
                              i.date_born])
        data_order_t = []

        for i in data_order:
            tg_username = i.name_oper
            if "@" not in tg_username:
                tg_username = "@" + tg_username
            data_order_t.append(
                [i.id, i.oper_id, i.owner_id, i.title, i.give, i.get, tg_username, i.name_owner, i.date_time, i.state])
        await load_sheets(data_user=data_post, data_order=data_order_t)
        await message.answer("Обновил гугл таблицу")

        await asyncio.sleep(3600)


@dp.callback_query_handler(lambda call: call.data == "history")
async def pul_all_history(call: types.CallbackQuery) -> None:
    acc = await Account.get_account(call.from_user.id)
    history = await Order.get_history(call.from_user.id)
    for i in history:
        await call.message.answer(await translate_language(str(i).replace(",)", "").replace("(", ""), acc.language))


async def gen_markup_history(language):
    markup = types.ReplyKeyboardMarkup()
    markup.add(await translate_language(ButtonHistory.OPEN_HISTORY.value, language),
               await translate_language(ButtonHistory.HISTORY_HISTORY.value, language))
    return markup


@dp.message_handler()
async def message_up(msg: types.Message) -> None:
    try:
        acc = await Account.get_account(msg.from_user.id)
        language = acc.language
    except Exception as e:
        print(e)
        await msg.answer(await translate_language(Message.HELP, "en"))
        await msg.answer(await translate_language(Message.NO_ACCOUNT, "en"))
        return
    if msg.text == await translate_language(Button.CALC.value, language):
        await msg.answer(await translate_language(Message.CALC_MESSAGE, language),
                         reply_markup=await gen_inline_what(language))

    elif msg.text == await translate_language(Button.ACCOUNT.value, acc.language):
        markup = await markup_button(language, message=msg)
        await msg.answer(await translate_language(Message.PROFILE.format(telegram_name=acc.telegram_name,
                                                                         name=acc.name,
                                                                         language=acc.language,
                                                                         wallet=acc.wallet_number,
                                                                         referral=acc.refer_user),
                                                  language), reply_markup=markup)
    elif msg.text == await translate_language(Button.HISTORY.value, language):
        await msg.answer(await translate_language(Message.HISTORY_WHAT, language),
                         reply_markup=await gen_markup_history(language))

    elif msg.text == await translate_language(ButtonHistory.HISTORY_HISTORY.value, language):
        await msg.answer(await translate_language(Message.HISTORY_WHAT, language),
                         reply_markup=await markup_button(acc.language, msg))
        history = await Order.get_history(msg.from_user.id)
        if history:
            history_slice = history[-5:]
            for i in history_slice:
                await msg.answer(await translate_language(str(i).replace(",)", "").replace("(", ""), language))
            try:
                await msg.answer(await translate_language(str(history[4]).replace(",)", "").replace("(", ""), language),
                                 reply_markup=await gen_inline_button(names=["Вся история"],
                                                                      calls=["history"],
                                                                      language=language))
            except IndexError:
                pass
        else:
            await msg.answer(await translate_language(Message.NO_HISTORY, language))

    elif msg.text == await translate_language(ButtonHistory.OPEN_HISTORY.value, language):
        await msg.answer(await translate_language(Message.HISTORY_WHAT, language),
                         reply_markup=await markup_button(acc.language, msg))
        history = await Order.get_history(msg.from_user.id, order="Открытый")
        if history:
            for i in history:
                await msg.answer(await translate_language(str(i).replace(",)", "").replace("(", ""), language),
                                 reply_markup=await gen_inline_button(['Отмена'],
                                                                      ['Cancel_order'], language))
        else:
            await msg.answer(await translate_language(Message.NO_HISTORY_OPEN, language))

    elif msg.text == await translate_language(Button.PERCENT.value,
                                              language) and msg.from_user.id in BotClass.admins:
        percent = await PercentDB.get_db_admin(1)
        await msg.answer(await translate_language(Message.EDIT_PERCENT.format(percent=percent.percent), language))
        await EditState.percent.set()

    elif msg.text == await translate_language(Button.TIME.value,
                                              language) and msg.from_user.id in BotClass.admins:
        time = await PercentDB.get_db_admin(1)
        await msg.answer(await translate_language(Message.EDIT_TIME.format(time=time.time), language))
        await EditState.time.set()

    elif msg.text == await translate_language(Button.PLACE.value,
                                              language) and msg.from_user.id in BotClass.admins:
        place = await PercentDB.get_db_admin(1)
        await msg.answer(await translate_language(Message.EDIT_PLACE.format(place=place.place), language))
        await EditState.place.set()

    elif msg.text == await translate_language(Button.CREATE_REFER.value, language):
        await msg.answer(
            await translate_language(Message.SEND_REFER.format(ref=await get_start_link(msg.from_user.id)), language))
    else:
        await msg.answer(await translate_language(Message.HELP, language))


if __name__ == '__main__':
    asyncio.run(init())
    from asyncio import new_event_loop, set_event_loop

    set_event_loop(new_event_loop())
    print("Бот запущен")
    dp.bind_filter(IsAdmin)
    executor.start_polling(BotClass.dp, on_shutdown=shutdown, skip_updates=True)

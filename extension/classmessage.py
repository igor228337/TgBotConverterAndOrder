from enum import Enum


class Language(Enum):
    RUS: str = "ru"
    ENG: str = "en"
    AR: str = "ar"
    FR: str = "fr"


class Currency(Enum):
    USD: str = "USD"
    USDT: str = "USDT"
    AED: str = "AED"


class ButtonHistory(Enum):
    OPEN_HISTORY: str = "🚗 Открытые сделки"
    HISTORY_HISTORY: str = "☑ История сделок"


class Button(Enum):
    CALC: str = "🖥 Открыть сделку"
    ACCOUNT: str = "💾 Мой профиль"
    HISTORY: str = "📒 Заявки"
    CREATE_REFER: str = "📩 Создать ссылку"
    PERCENT: str = "✍ Процент"
    TIME: str = "🌉 Время"
    PLACE: str = "🛐 Место"


class Message:
    BAD_SAY: list = []
    NO_ACCOUNT: str = "У вас нет аккаунта пожалуйста зарегистрируйтесь введя /start"
    GREETING: str = "✋ Добро пожаловать на наш бот, выберите пожалуйста язык: "
    HELP: str = "😥 Я не знаю что случилось обратись к @Usdt_admin_dubai, описав ошибку в боте"
    CANCEL: str = "😐 Отмена состояния"
    REPEAT_START: str = "😄 У вас уже есть аккаунт"
    NO_LANGUAGE: str = "😔 Извините, я ещё не знаю такого языка, выбирите из списка ниже"
    WHAT_NAME: str = "🔑 Как вас зовут?"
    NO_NAME: str = "⌚ Попробуйте другое имя"
    WALLET_NUMBER: str = "💼 Введите номер кошелька"
    NO_WALLET: str = "🛎 Не существует таких кошельков введите другой"
    SUCCESSFULLY: str = "🔒 Регистрация прошла успешно!"
    PROFILE: str = "📁 Ваш профиль: {telegram_name}\n"\
                   "Ваше имя: {name}\n"\
                   "Ваш язык: {language}\n"\
                   "Ваш кошелёк: {wallet}\n"\
                   "Вас пригласил: {referral}"
    CALC_MESSAGE: str = "👨‍💻 Доброго времени суток!\nВыберите валюту"
    MESSAGE_GIVE: str = "📩 Введите сколько хотите {currency} {what}"
    YOU_GET: str = "Вы получаете"
    YOU_GIVE: str = "Вы отдаёте"
    NO_CURRENCY: str = "☣Вы не правильно ввели число попробуйте ещё раз, для отмены введите /cancel"
    NO_EDIT: str = "❗Вызовите заново калькулятор"
    EDIT_PERCENT: str = "💵 Введите процент, где 1 это 100%\nСейчас процент: {percent}\nПример: 0.08"
    EDIT_PERCENT_SUCCESS: str = "💸 Процент по калькулятору изменён"
    FUCK_REPLU: str = "👁 Бот активно разрабатывается, по этому выберите ту же валюты и введите число"
    SEND_ORDER: str = "🏆 Отправить"
    EDIT_TIME: str = "👀Введите как будет выведено время пользователю\nСейчас время: {time}"
    EDIT_TIME_SUCCESS: str = "🕺Время изменено"
    EDIT_PLACE: str = "🗣Введите место встречи\nСейчас: {place}"
    EDIT_PLACE_SUCCESS: str = "👥Место встречи изменено"
    CONFIRMATION_ORDER: str = "👨‍🏫Подтвердите действие"
    CANCEL_CREATE_ORDER: str = "#Дубай #Выдать #Принять\n\n" \
                               "Id: {id_order} \n"                          \
                               "🕛Дата: {date} {time}\n" \
                               "🗺Локация: {place}\n" \
                               "👛Кошелёк: {wallet}\n"\
                               "🤵Клиент: {username}\n" \
                               "💷Клиент отдаёт: {give}\n" \
                               "💷Клиент получает: {get}\n" \
                               "🔓Кодовое слово: {rnd}\n" \
                               "📱Контакт: {admin_username}\n"
    THANK_SEND_ORDER: str = "🍫Заявка была отправлена"
    NO_HISTORY: str = "✖У вас ещё нет истории"
    WHAT_WALLET: str = "👼Использовать этот кошелёк: {wallet}"
    NO_SEND: str = '🌚 Вы не выбрали в какую валюту конвертировать'
    HISTORY_WHAT: str = "🔴 Выберите из списка ниже"
    NO_HISTORY_OPEN: str = "✖У вас нет открытых сделок"
    CANCEL_ORDER: str = "✖ Вы отменили сделку"
    SUCCESS_ORDER: str = "🗣 Ордер исполнен"
    SEND_MESSAGE_CALC: str = "👁 К получению {price} {what}, для продолжение нажмите ⬆ \n🏆 Отправить"
    SEND_REFER: str = "👁 Вот ваша ссылка для рефералов: {ref}"
    CALC_GIVE: str = "👁 Выберите сколько вы хотите отдать"
    CALC_GET: str = "👁 Выберите сколько вы хотите получить"
    CALC_GIVE_SEND_PEOPLE: str = "👛 Вы получаете: "
    CALC_GET_SEND_PEOPLE: str = "👛 Вы должны будете отдать: "
    CALC_GET_PEOPLE: str = "🗣 Введите сколько хотите получить {what}: "
    BOT_SLEEP: str = "Бот устал обратитесь к нему позднее"


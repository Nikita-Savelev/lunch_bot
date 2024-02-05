from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
import connector
import re
import datetime

conn = connector.Connector()
def menu_button():
    button1 = KeyboardButton('Заказать🍽')
    button2 = KeyboardButton('Узнать свой заказ👀')
    button3 = KeyboardButton('Жми меня если забываешь сделать заказ')
    button4 = KeyboardButton('🆕Свободные заказы🆕')
    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    greet_kb.row(button1, button2)
    greet_kb.row(button4)
    greet_kb.row(button3)
    return greet_kb

def binar():
    button1 = KeyboardButton('Нет')
    button2 = KeyboardButton('Да')
    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    greet_kb.row(button1, button2)
    return greet_kb

def get_closeF(button):
    if re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', button):
        close = conn.is_close(button)
        if close:
            button += "🔒"
    return button

def get_weekday(date):
    week_days = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
    day = datetime.datetime.strptime(date, "%Y-%m-%d")
    return week_days[datetime.datetime.weekday(day)]

def get_refuse_order(day, user_id):
    inline_btn = InlineKeyboardButton('Забрать заказ', callback_data=f"get_refuse_order/{str(day)}/{user_id}")
    inline_kb = InlineKeyboardMarkup().add(inline_btn)
    return inline_kb


def convert_day(days):
    if type(days) is not list:
        days = [days]
    res = []
    now = datetime.datetime.now()
    tomorrow = str(now + datetime.timedelta(1))[:10]
    now = str(now)[:10]
    today = False
    for day in days:
        if re.sub("🔒", "", day) == now:
            res_day = "Сегодня"
            today = True
        elif re.sub("🔒", "", day) == tomorrow:
            res_day = "Завтра"
        else:
            m = re.findall("[0-9]{4}-([0-9]{2})-[0-9]{2}", day)[0]
            d = re.findall("[0-9]{4}-[0-9]{2}-([0-9]{2})", day)[0]
            res_day = f"""{get_weekday(re.sub("🔒", "", day))} {d}.{m}"""
        if "🔒" in day:
            res_day += "🔒"
        if "Завтра" in res_day and res:
            res.insert(0, res_day)
            continue
        if "Сегодня" in res_day and len(res) > 1 and "Завтра" in res[0]:
            res.insert(1, res_day)
        elif "Сегодня" in res_day and len(res) > 1:
            res.insert(0, res_day)
        else:
            res.append(res_day)
    return res, today

def convert_day_revers(days):
    if type(days) is not list:
        days = [days]
    res = []
    now = datetime.datetime.now()
    tomorrow = str(now + datetime.timedelta(1))[:10]
    now = str(now)[:10]
    y = now[:4]
    for day in days:
        if "🔒" in day:
            day = re.sub("🔒", "", day)
        if day == "Сегодня":
            res_day = now
        elif day == "Завтра":
            res_day = tomorrow
        else:
            d = re.findall("([0-9]{2})-[0-9]{2}", day)[0]
            m = re.findall("[0-9]{2}-([0-9]{2})", day)[0]
            res_day = f"{y}-{m}-{d}"
        res.append(res_day)
    return res


def get_keyboard(some_positions, days=False):
    if days:
        some_positions, today = convert_day([get_closeF(str(day)) for day in some_positions])
    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    if (len(some_positions) // 2) > 0 and len(some_positions) > 3:
        greet_kb.row(KeyboardButton(get_closeF(str(some_positions.pop(-1)))), KeyboardButton(get_closeF(str(some_positions.pop(-1)))), KeyboardButton(get_closeF(str(some_positions.pop(-1)))))
    while some_positions:
        bt1 = KeyboardButton(get_closeF(str(some_positions.pop(-1))))
        if some_positions:
            bt2 = KeyboardButton(get_closeF(str(some_positions.pop(-1))))
            greet_kb.row(bt1, bt2)
            continue
        greet_kb.row(bt1)
    button = KeyboardButton("Назад")
    if not days:
        button1 = KeyboardButton("Пропустить")
        greet_kb.row(button, button1)
    else:
        if not today:
            greet_kb.row(KeyboardButton("Сегодня"), button)
        else:
            greet_kb.row(button)
    return greet_kb

def back():
    button1 = KeyboardButton('Назад')
    greet_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    greet_kb.add(button1)
    return greet_kb

def admin():
    inline_btn1 = InlineKeyboardButton('Добавить админа', callback_data='add_admin')
    inline_btn2 = InlineKeyboardButton('Добавить/Изменить меню', callback_data='add_menu')
    inline_btn3 = InlineKeyboardButton('Получить все заказы', callback_data='get_orders')
    inline_btn4 = InlineKeyboardButton('Загрузить меню из файла', callback_data='load_menu')
    inline_btn5 = InlineKeyboardButton('Открыть/Закрыть меню', callback_data='close_open')
    inline_btn6 = InlineKeyboardButton('Добавить пользователя', callback_data='add_user')
    inline_btn7 = InlineKeyboardButton('Получить заказ по имени', callback_data='get_orders_for_user')
    inline_kb = InlineKeyboardMarkup().row(inline_btn7, inline_btn3).row(inline_btn2, inline_btn4).add(inline_btn1, inline_btn6).add(inline_btn5)
    return inline_kb

def refusal_kb(day, user_id):
    print(f"{str(day)}/{user_id}")
    inline_btn = InlineKeyboardButton('Отдать заказ', callback_data=f"{str(day)}/{user_id}")
    inline_kb = InlineKeyboardMarkup().add(inline_btn)
    return inline_kb

def dop_option(user_id):
    option = conn.get_dop_option(user_id)
    if option[0]:
        inline_btn2 = InlineKeyboardButton('🔴Выключить', callback_data='dop_option')
    else:
        inline_btn2 = InlineKeyboardButton('🟢Включить', callback_data='dop_option')
    inline_kb = InlineKeyboardMarkup().add(inline_btn2)
    return inline_kb

#bot.py
# @dp.message_handler(commands=['1'])
# async def process_command_1(message: types.Message):
#     await message.reply("Первая инлайн кнопка", reply_markup=kb.inline_kb1)
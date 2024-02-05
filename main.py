import re

from aiogram import Bot, Dispatcher, executor, types
import keyboard as kb
import connector
import pandas as pd

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.dispatcher.filters import Text
import urllib
from multiprocessing import Pool
import datetime

conn = connector.Connector()
API_TOKEN = ''

from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

def get_first(array):
    return array[0] if len(array) > 0 else None

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
            try:
                d = re.findall("([0-9]{2}).[0-9]{2}", day)[0]
                m = re.findall("[0-9]{2}.([0-9]{2})", day)[0]
                res_day = f"{y}-{m}-{d}"
            except:
                res_day = day
        res.append(res_day)
    return res
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user = conn.get_user_info(message.from_user.id)
    if not user:
        await add_user(message)
    else:
        user = user[1] if user else f"{message.from_user.first_name} {message.from_user.last_name}"
        keyboard = kb.menu_button()
        await message.answer(f"👋Приветствую {user}!", reply_markup=keyboard)


@dp.message_handler(Text(equals="Назад"))
async def back_to_start(message: types.Message):
    user = conn.get_user_info(message.from_user.id)
    if not user:
        await add_user(message)
    else:
        user = user[1] if user else f"{message.from_user.first_name} {message.from_user.last_name}"
        keyboard = kb.menu_button()
        await message.answer(f"👋Приветствую, {user}!", reply_markup=keyboard)


class AddUser(StatesGroup):
    full_name = State()

async def add_user(message: types.Message):
    await message.answer(f"""Приветствую, {message.from_user.first_name} {message.from_user.last_name}! \nКажется я вижу вас впервые👀. Введите свои фамилию и имя, для того чтобы я внес вас в базу """)
    await AddUser.full_name.set()


@dp.message_handler(state=AddUser.full_name)
async def get_username(message: types.Message, state: FSMContext):
    keyboard = kb.menu_button()
    if re.fullmatch('[А-Яа-я]+ [А-Яа-я]+', message.text) and len(message.text) < 300:
        user_exist = conn.get_office_worker(message.text)[0]
        if user_exist:
            if not user_exist[0]:
                conn.add_user(message.from_user.id, message.text)
                conn.update_office_worker(message.text, message.from_user.id)
                await message.answer(f"Приятно познакомиться {message.text}, теперь вы можете делать заказы!", reply_markup=keyboard)
                await state.finish()
            else:
                await message.answer("""Этот пользователь уже есть в базе""")
        else:
            await message.answer("""Работника с таким именем нет в базе. Если вы уверены в правильности написания своих ФИ, обратитесь к офис менеджеру""")
    else:
        await message.answer("""Я ожидал получить ответ в формате "Фамилия Имя" попробуйте еще раз""")


@dp.message_handler(Text(equals="Жми меня если забываешь сделать заказ"))
async def for_forgetful(message: types.Message):
    keyboard = kb.dop_option(message.from_user.id)
    await bot.send_message(message.from_user.id, 'В очередной раз забыли заказать обед на понедельник? \nНе беда! Включите опцию авто заказов, и я сделаю заказ за вас в случае его отсутствия перед закрытием меню\n(Позиции из меню выбираются случайным образом)', reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'dop_option')
async def dop_option(callback_query: types.CallbackQuery):
    conn.set_dop_option(callback_query.from_user.id)
    keyboard = kb.menu_button()
    await bot.send_message(callback_query.from_user.id, 'Готово!', reply_markup=keyboard)



class GetOrder(StatesGroup):
    order = State()

@dp.message_handler(Text(equals="Узнать свой заказ👀"))
async def get_order(message: types.Message):
    days = [str(menu[0]) for menu in conn.select_menu(closeF=None)]
    keyboard = kb.get_keyboard(days, days=True)
    await bot.send_message(message.from_user.id, 'Выберите день из списка или пришлите свой вариант', reply_markup=keyboard)
    await GetOrder.order.set()

@dp.message_handler(state=GetOrder.order)
async def lalalala(message: types.Message, state: FSMContext):
    is_now_date = False
    if not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text):
        if "Сегодня" in message.text:
            is_now_date = True
        message.text = convert_day_revers(message.text)[0]
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text): #04.25
        data = conn.select_order(message.text, message.from_user.id)
        if data:
            if is_now_date:
                keyboard = kb.refusal_kb(data[2], message.from_user.id)
                await message.answer(f"""Ваш заказ на {data[2]}:\nСалат: {data[3]}\nПервое: {data[4]}\nВторое: {data[5]}\nГарнир: {data[6]}\nВыпечка: {data[7]}\n""", reply_markup=keyboard)
                keyboard = kb.menu_button()
                await message.answer("Приятного аппетита!", reply_markup=keyboard)
                await state.finish()
                return
            keyboard = kb.menu_button()
            await message.answer(f"""Ваш заказ на {data[2]}:\nСалат: {data[3]}\nПервое: {data[4]}\nВторое: {data[5]}\nГарнир: {data[6]}\nВыпечка: {data[7]}\n""", reply_markup=keyboard)
            await state.finish()
        else:
            await message.answer("Не могу найти ваш заказ на этот день")
            return
    else:
        await message.answer("""Я ожидал получить ответ в формате "DD.MM" например 23.05 попробуйте еще раз""")
        return

@dp.callback_query_handler(lambda c: re.fullmatch("[0-9]{4}-[0-9]{2}-[0-9]{2}/[0-9]+", c.data))
async def refuse_orders(callback_query: types.CallbackQuery):
    day, user_id = re.split("/", callback_query.data)
    now = str(datetime.datetime.now())[:10]
    keyboard = kb.menu_button()
    if day == now:
        if conn.refusal_order(day, user_id):
            await bot.send_message(callback_query.from_user.id, 'Готово!', reply_markup=keyboard)
            name = conn.get_office_worker(user_id=callback_query.from_user.id)[0]
            user = name[0].upper() + re.sub(" [а-яё]", f"{re.findall(' [а-яё]', name)[0].upper()}", name[1:])
            await conn.send_refuse_notif(user, bot, callback_query.from_user.id)
        else:
            await bot.send_message(callback_query.from_user.id, 'Заказ не найден', reply_markup=keyboard)
    else:
        await bot.send_message(callback_query.from_user.id, 'Отдать можно только сегодняшние заказы', reply_markup=keyboard)

@dp.callback_query_handler(lambda c: re.fullmatch("get_refuse_order/[0-9]{4}-[0-9]{2}-[0-9]{2}/[0-9]+", c.data))
async def refuse_orders(callback_query: types.CallbackQuery):
    _, day, user_id = re.split("/", callback_query.data)
    now = str(datetime.datetime.now())[:10]
    keyboard = kb.menu_button()
    order = conn.select_order(now, callback_query.from_user.id)
    if order:
        await bot.send_message(callback_query.from_user.id, 'У вас уже есть заказ на сегодня')
        return
    if day == now:
        if conn.refusal_order(day, user_id, this_user_id=callback_query.from_user.id, reverse=True):
            await bot.send_message(callback_query.from_user.id, 'Готово!', reply_markup=keyboard)
        else:
            await bot.send_message(callback_query.from_user.id, 'Заказ не найден', reply_markup=keyboard)
    else:
        await bot.send_message(callback_query.from_user.id, 'Забрать можно только сегодняшние заказы', reply_markup=keyboard)

@dp.message_handler(Text(equals="🆕Свободные заказы🆕"))
async def open_orders(message: types.Message):
    none_orders = True
    for order in conn.get_refusal_orders(str(datetime.datetime.now())[:10]):
        none_orders = False
        name = conn.get_office_worker(user_id=order[1])[0]
        user = name[0].upper() + re.sub(" [а-яё]", f"{re.findall(' [а-яё]', name)[0].upper()}", name[1:])
        keyboard = kb.get_refuse_order(str(order[2]), order[1])
        await message.answer(f"""Заказ от пользователя "{user}":\nСалат: {order[3]}\nПервое: {order[4]}\nВторое: {order[5]}\nГарнир: {order[6]}\nВыпечка: {order[7]}\n""", reply_markup=keyboard)
        print(order, user)
    if none_orders:
        await message.answer("На сегодня свободных заказов нет")


class AddOrder(StatesGroup):
    menu = State()
    question = State()
    binar = State()
    date = State()
    salat = State()
    first = State()
    second = State()
    garneer = State()
    bakery = State()
    dubl_bakery = State()
    fin = State()

@dp.message_handler(Text(equals="Заказать🍽"))
async def make_an_order(message: types.Message):
    days = [str(menu[0]) for menu in conn.select_menu(closeF=None)]
    keyboard = kb.get_keyboard(days, days=True)
    await bot.send_message(message.from_user.id, 'Выберите день из списка или пришлите свой вариант', reply_markup=keyboard)
    await AddOrder.question.set()

@dp.message_handler(state=AddOrder.question)
async def ask_question(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if "🔒" in message.text:
        keyboard = kb.menu_button()
        await message.answer("Меню на этот день уже закрыто", reply_markup=keyboard)
        await state.finish()
        return
    if not re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text):
        message.text = convert_day_revers(message.text)[0]
    if re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text):  # 2023-04-25
        menu = conn.select_menu(message.text)
        if menu:
            await state.update_data(menu=menu)
            await state.update_data(date=message.text)
        else:
            await message.answer("Не могу найти меню на этот день")
            return
        order = conn.select_order(message.text, message.from_user.id)
        if order:
            await state.update_data(question=True)
            keyboard = kb.binar()
            await message.answer(f"На этот день у вас уже есть заказ, хотите перезаписать его?", reply_markup=keyboard)
            await AddOrder.next()
        else:
            await state.update_data(question=False)
            salats = menu[1].split("/")
            keyboard = kb.get_keyboard(salats)
            await message.answer(f"Выберите салат", reply_markup=keyboard)
            await AddOrder.next()
    else:
        await message.answer("""Я ожидал получить ответ в формате "DD.MM" например 23.05 попробуйте еще раз""")
        return

@dp.message_handler(state=AddOrder.binar)
async def get_binar(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    data = await state.get_data()
    menu = data["menu"]
    if data["question"]:
        if message.text in ["Да", "Нет"]:
            if message.text == "Да":
                await state.update_data(binar="pass")
                await state.update_data(question=False)
                salats = menu[1].split("/")
                keyboard = kb.get_keyboard(salats)
                await message.answer(f"Выберите салат", reply_markup=keyboard)
                await AddOrder.salat.set()
            else:
                await state.finish()
                await start(message)
                return
        else:
            await bot.send_message(message.from_user.id, 'Я ожидал ответ в формате Да/Нет')
            return
    else:
        await state.update_data(binar="pass")
        salat = [doc.strip() for doc in menu[1].split("/")]
        if message.text in salat or message.text == "Пропустить":
            first = menu[2].split("/")
            keyboard = kb.get_keyboard(first)
            await state.update_data(salat=message.text)
            if conn.is_security(message.from_user.id):
                salat_selection = data["salat"] if "salat" in data else None
                if salat_selection:
                    await state.update_data(salat=f"{message.text}/{salat_selection}")
                    await message.answer(f"Выберите первое", reply_markup=keyboard)
                    await AddOrder.first.set()
                else:
                    men = menu[1].split("/")
                    keyboard = kb.get_keyboard(men)
                    await message.answer(f"Выберите второй салат", reply_markup=keyboard)
                    return
            else:
                await message.answer(f"Выберите первое", reply_markup=keyboard)
                await AddOrder.first.set()
        else:
            await message.answer("""Кажется этого салата нет в меню на этот день""")
            return


@dp.message_handler(state=AddOrder.salat)
async def get_salat(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    menu = await state.get_data()
    menu = menu['menu']
    salat = [doc.strip() for doc in menu[1].split("/")]
    if message.text in salat or message.text == "Пропустить":
        first = menu[2].split("/")
        keyboard = kb.get_keyboard(first)
        await state.update_data(salat=message.text)
        if conn.is_security(message.from_user.id):
            data = await state.get_data()
            salat_selection = data["salat"] if "salat" in data else None
            if salat_selection:
                await state.update_data(salat=f"{message.text}/{salat_selection}")
                await message.answer(f"Выберите первое", reply_markup=keyboard)
                await AddOrder.first.set()
            else:
                men = menu[1].split("/")
                keyboard = kb.get_keyboard(men)
                await message.answer(f"Выберите второй салат", reply_markup=keyboard)
                return
        else:
            await message.answer(f"Выберите первое", reply_markup=keyboard)
            await AddOrder.first.set()
    else:
        await message.answer("""Кажется этого салата нет в меню на этот день""")
        return

@dp.message_handler(state=AddOrder.first)
async def get_first(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    menu = await state.get_data()
    menu = menu['menu']
    first = [doc.strip() for doc in menu[2].split("/")]
    if message.text in first or message.text == "Пропустить":
        second = menu[3].split("/")
        keyboard = kb.get_keyboard(second)
        data = await state.get_data()
        await state.update_data(first=message.text)
        if conn.is_security(message.from_user.id):
            first_selection = data["first"] if "first" in data else None
            if first_selection:
                await state.update_data(first=f"{message.text}/{first_selection}")
                await message.answer(f"Выберите второе", reply_markup=keyboard)
                await AddOrder.second.set()
            else:
                men = menu[2].split("/")
                keyboard = kb.get_keyboard(men)
                await message.answer(f"Выберите второе первое", reply_markup=keyboard)
                return
        else:
            await message.answer(f"Выберите второе", reply_markup=keyboard)
            await AddOrder.second.set()
    else:
        await message.answer("""Кажется этого блюда нет в меню на этот день""")
        return

@dp.message_handler(state=AddOrder.second)
async def get_second(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    menu = await state.get_data()
    menu = menu['menu']
    second = [doc.strip() for doc in menu[3].split("/")]
    if message.text in second or message.text == "Пропустить":
        garneer = menu[4].split("/")
        keyboard = kb.get_keyboard(garneer)
        data = await state.get_data()
        await state.update_data(second=message.text)
        if conn.is_security(message.from_user.id):
            second_selection = data["second"] if "second" in data else None
            if second_selection:
                await state.update_data(second=f"{message.text}/{second_selection}")
                await message.answer(f"Выберите гарнир", reply_markup=keyboard)
                await AddOrder.garneer.set()
            else:
                men = menu[3].split("/")
                keyboard = kb.get_keyboard(men)
                await message.answer(f"Выберите второе второе", reply_markup=keyboard)
                return
        else:
            await message.answer(f"Выберите гарнир", reply_markup=keyboard)
            await AddOrder.garneer.set()
    else:
        await message.answer("""Кажется этого блюда нет в меню на этот день""")
        return

@dp.message_handler(state=AddOrder.garneer)
async def get_garneer(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    menu = await state.get_data()
    menu = menu['menu']
    garneer = [doc.strip() for doc in menu[4].split("/")]
    if message.text in garneer or message.text == "Пропустить":
        bakery = menu[5].split("/")
        keyboard = kb.get_keyboard(bakery)
        data = await state.get_data()
        await state.update_data(garneer=message.text)
        if conn.is_security(message.from_user.id):
            second_selection = data["garneer"] if "garneer" in data else None
            if second_selection:
                await state.update_data(garneer=f"{message.text}/{second_selection}")
                await message.answer(f"И последнее - выпечка", reply_markup=keyboard)
                await AddOrder.bakery.set()
            else:
                men = menu[4].split("/")
                keyboard = kb.get_keyboard(men)
                await message.answer(f"Выберите второй гарнир", reply_markup=keyboard)
                return
        else:
            await message.answer(f"И последнее - выпечка", reply_markup=keyboard)
            if conn.is_ml_team(message.from_user.id):
                await AddOrder.dubl_bakery.set()
            else:
                await AddOrder.bakery.set()
    else:
        await message.answer("""Кажется этого блюда нет в меню на этот день""")
        return

@dp.message_handler(state=AddOrder.bakery)
async def get_bakery(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    menu = await state.get_data()
    menu = menu['menu']
    bakery = [doc.strip() for doc in menu[5].split("/")]
    print(bakery, message.text)
    if message.text in bakery or message.text == "Пропустить":
        keyboard = kb.menu_button()
        data = await state.get_data()
        await state.update_data(bakery=message.text)
        print(conn.is_security(message.from_user.id))
        if conn.is_security(message.from_user.id):
            second_selection = data["bakery"] if "bakery" in data else None
            if second_selection:
                await state.update_data(bakery=f"{message.text}/{second_selection}")
            else:
                men = menu[5].split("/")
                keyboard = kb.get_keyboard(men)
                await message.answer(f"Выберите вторую булочку", reply_markup=keyboard)
                return
        data = await state.get_data()
        if not conn.select_order(data['date'], message.from_user.id):
            conn.add_order(data, message.from_user.id)
        else:
            conn.add_order(data, message.from_user.id, remove=True)
        data = conn.select_order(data['date'], message.from_user.id)
        await message.answer(f"""Записал! Ваш заказ на {data[2]}:\nСалат: {data[3]}\nПервое: {data[4]}\nВторое: {data[5]}\nГарнир: {data[6]}\nВыпечка: {data[7]}\n""", reply_markup=keyboard)
        await state.finish()
    else:
        await message.answer("""Кажется этого блюда нет в меню на этот день""")
        return


@dp.message_handler(state=AddOrder.dubl_bakery)
async def get_dubl_bakery(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    menu = await state.get_data()
    menu = menu['menu']
    bakery = [doc.strip() for doc in menu[5].split("/")]
    if message.text in bakery or message.text == "Пропустить":
        bakery = menu[5].split("/")
        keyboard = kb.get_keyboard(bakery)
        await state.update_data(bakery=message.text)
        # await bot.send_photo(message.from_user.id, types.InputFile('не болтай.jpg'))
        await message.answer(f"Пс, еще булочку?", reply_markup=keyboard)
        await AddOrder.fin.set()
    else:
        await message.answer("""Кажется этого блюда нет в меню на этот день""")
        return

@dp.message_handler(state=AddOrder.fin)
async def get_fin(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    menu = await state.get_data()
    menu = menu['menu']
    bakery = [doc.strip() for doc in menu[5].split("/")]
    if message.text in bakery or message.text == "Пропустить":
        keyboard = kb.menu_button()
        data = await state.get_data()
        data['bakery'] += f"/{message.text}"
        if not conn.select_order(data['date'], message.from_user.id):
            conn.add_order(data, message.from_user.id)
        else:
            conn.add_order(data, message.from_user.id, remove=True)
        data = conn.select_order(data['date'], message.from_user.id)
        await message.answer(f"""Записал! Ваш заказ на {data[2]}:\nСалат: {data[3]}\nПервое: {data[4]}\nВторое: {data[5]}\nГарнир: {data[6]}\nВыпечка: {data[7]}\n""", reply_markup=keyboard)
        await state.finish()
    else:
        await message.answer("""Кажется этого блюда нет в меню на этот день""")
        return

# ======================================================================================================================
#                                          ADMIN PANEL
# ======================================================================================================================

@dp.message_handler(commands=['admin'])
async def admin_start(message: types.Message):
    admins = conn.get_admins()
    print([admin[0] for admin in admins])
    print(str(message.from_user.id))
    if str(message.from_user.id) in [admin[0] for admin in admins]:
        keyboard = kb.admin()
        await message.answer(f"Вы вошли в админ панель", reply_markup=keyboard)

class AddAdmin(StatesGroup):
    admin_id = State()

@dp.callback_query_handler(lambda c: c.data == 'add_admin')
async def get_admin_id_adnin(callback_query: types.CallbackQuery):
    keyboard = kb.back()
    await bot.send_message(callback_query.from_user.id, 'Введите id пользователя которому хотите дать доступ к админ панели\nУзнать id можно в боте @JsonDumpBot \n(https://t.me/JsonDumpBot)', reply_markup=keyboard)
    await AddAdmin.admin_id.set()

@dp.message_handler(state=AddAdmin.admin_id)
async def lalalala_admin(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    conn.add_admin(message.text)
    keyboard = kb.menu_button()
    await bot.send_message(message.from_user.id, 'Готово! Теперь этот пользователь может войти в админ панель', reply_markup=keyboard)
    await state.finish()


class AddUsers(StatesGroup):
    user_name = State()

@dp.callback_query_handler(lambda c: c.data == 'add_user')
async def get_user_name_adnin(callback_query: types.CallbackQuery):
    keyboard = kb.back()
    await bot.send_message(callback_query.from_user.id, 'Введите фамилию и имя работника', reply_markup=keyboard)
    await AddUsers.user_name.set()

@dp.message_handler(state=AddUsers.user_name)
async def lalalala_user(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if re.fullmatch('[А-Яа-я]+ [А-Яа-я]+', message.text) and len(message.text) < 300:
        user_exist = conn.get_office_worker(message.text)[0]
        if not user_exist:
            keyboard = kb.menu_button()
            conn.insert_users_in_workers([message.text])
            await message.answer(f"Пользователь ```{message.text}``` добавлен в базу!", reply_markup=keyboard)
            await state.finish()
        else:
            await message.answer("""Этот пользователь уже есть в базе""")
            await state.finish()
    else:
        await message.answer("""Я ожидал получить ответ в формате "Фамилия Имя" попробуйте еще раз""")


class LoadMenu(StatesGroup):
    data = State()
    confirmation = State()

@dp.callback_query_handler(lambda c: c.data == 'load_menu')
async def get_data_adnin(callback_query: types.CallbackQuery):
    keyboard = kb.back()
    await bot.send_message(callback_query.from_user.id, 'Введите название загруженного файла', reply_markup=keyboard)
    await LoadMenu.data.set()

def cool_func(string):
    cool_string = ""
    count = 1
    for pos in re.split('/', string):
        cool_string += f"   {count}. {pos}\n"
        count += 1
    return cool_string

@dp.message_handler(state=LoadMenu.data)
async def lalalala_adminsss(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return

    data = load_menu(message.text)
    if not data:
        keyboard = kb.menu_button()
        await bot.send_message(message.from_user.id, "Файл не найден", reply_markup=keyboard)
        await state.finish()
        return
    full_menu = ""
    for pos in data:
        full_menu += f"День - {pos['date']}\nСалаты: \n{cool_func(pos['salat'])}Первое: \n{cool_func(pos['first'])}Второе: \n{cool_func(pos['second'])}Гарниры: \n{cool_func(pos['garneer'])}Выпечка: \n{cool_func(pos['bakery'])}\n\n"
    keyboard = kb.binar()
    await bot.send_message(message.from_user.id, full_menu)
    await bot.send_message(message.from_user.id, "Все верно?", reply_markup=keyboard)
    await state.update_data(confirmation=data)
    await LoadMenu.confirmation.set()

@dp.message_handler(state=LoadMenu.confirmation)
async def load_menues(message: types.Message, state: FSMContext):
    if message.text == "Назад" or message.text == "Нет":
        await state.finish()
        await start(message)
        return
    if message.text == "Да":
        data = await state.get_data()
        data = data['confirmation']
        for day in data:
            conn.add_menu(day, remove=True)
        keyboard = kb.menu_button()
        await bot.send_message(message.from_user.id, "Готово!", reply_markup=keyboard)
        await state.finish()
def load_menu(name_table):
    menu_load = pd.read_excel(f'./{name_table}.xlsx')
    menu = []
    keys = []
    positions = []
    days = []
    try:
        for key in menu_load:
            keys.append(key)
            if len(keys) == 1:
                continue
            menu_for_day = []
            for position in menu_load[key]:
                if str(position) != "nan":
                    menu_for_day.append(position)
                if len(menu_for_day) == 5:
                    positions.append(menu_for_day)
                    menu_for_day = []
            if len(keys) == 2:
                continue
            first = True
            for day in menu_load[key]:
                if first:
                    day = key
                    first = False
                if str(day) != "nan" and "Unnamed" not in str(day) and str(day).strip():
                    print(repr(day))
                    try:
                        Y = re.findall(".+?[0-9]{2}\.[0-9]{2}\.([0-9]{4})", day)[0]
                        M = re.findall(".+?[0-9]{2}\.([0-9]{2})\.[0-9]{4}", day)[0]
                        D = re.findall(".+?([0-9]{2})\.[0-9]{2}\.[0-9]{4}", day)[0]
                    except:
                        Y = re.findall(".*?([0-9]{4})\.[0-9]{2}\.[0-9]{2}", day)[0]
                        M = re.findall(".*?[0-9]{4}\.([0-9]{2})\.[0-9]{2}", day)[0]
                        D = re.findall(".*?[0-9]{4}\.[0-9]{2}\.([0-9]{2})", day)[0]
                    date = f"{Y}-{M}-{D}"
                    days.append(date)
        for index in range(0, len(days)):
            menu.append({
                "date": days[index],
                "salat": positions[index][0],
                "first": positions[index][1],
                "second": positions[index][2],
                "garneer": positions[index][3],
                "bakery": positions[index][4]
            })
        return menu
    except Exception as ex:
        print(ex)
        return None

class CloseOpen(StatesGroup):
    order = State()

@dp.callback_query_handler(lambda c: c.data == 'close_open')
async def close_open(callback_query: types.CallbackQuery):
    days = [str(menu[0]) for menu in conn.select_menu(closeF=None)]
    keyboard = kb.get_keyboard(days, days=True)
    await bot.send_message(callback_query.from_user.id, 'Выберите день из списка или пришлите свой вариант', reply_markup=keyboard)
    await CloseOpen.order.set()

@dp.message_handler(state=CloseOpen.order)
async def random_name(message: types.Message, state: FSMContext):
    message.text = convert_day_revers(message.text)[0]
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text): #2023-04-25
        close = conn.close_orders(message.text, revert=True)
        if close == "FOUND_ERROR":
            await message.answer("Не могу найти меню на этот день")
            return
        keyboard = kb.menu_button()
        if close:
            await message.answer(f"""Готово! \nТеперь меню {message.text} открыто""", reply_markup=keyboard)
            await state.finish()
        else:
            await message.answer(f"""Готово! \nТеперь меню {message.text} закрыто""", reply_markup=keyboard)
            await state.finish()
    else:
        await message.answer("""Я ожидал получить ответ в формате "DD.MM" например 24.03 попробуйте еще раз""")
        return


class GetUserOrder(StatesGroup):
    day = State()

@dp.callback_query_handler(lambda c: c.data == 'get_orders_for_user')
async def get_order_adnin(callback_query: types.CallbackQuery):
    keyboard = kb.back()
    await bot.send_message(callback_query.from_user.id, 'Введите дату в формате "2023-03-24", фамилию и имя пользователя через пробел', reply_markup=keyboard)
    await GetUserOrder.day.set()

@dp.message_handler(state=GetUserOrder.day)
async def lalalala_admin(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    keyboard = kb.menu_button()
    if len(re.findall('[а-яА-ЯЁё]+', message.text)) == 2 and len(re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text)) == 1: #2023-04-25
        name = f"{re.findall('[а-яА-ЯЁё]+', message.text)[0]} {re.findall('[а-яА-ЯЁё]+', message.text)[1]}"
        user_id = conn.get_office_worker(name)[0]
        print(user_id)
        if user_id:
            if user_id[0]:
                data = conn.select_order(re.findall('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text)[0], user_id[0])
                if data:
                    await message.answer(
                        f"""Заказ пользователя "{name}" на {data[2]}:\nСалат: {data[3]}\nПервое: {data[4]}\nВторое: {data[5]}\nГарнир: {data[6]}\nВыпечка: {data[7]}\n""", reply_markup=keyboard)
                    await state.finish()
                else:
                    await message.answer(f"Не могу найти заказ пользователя '{name}' на этот день", reply_markup=keyboard)
                    await state.finish()
            else:
                await message.answer("""Этот пользователь еще не авторизовался в боте""")
        else:
            await message.answer("""Работника с таким именем нет в базе""")
    else:
        await message.answer("""Я ожидал получить ответ в формате "YYYY-MM-DD Фамилия Имя" например "2023-03-24 Савельев Никита" попробуйте еще раз""")
        return


class GetAllOrders(StatesGroup):
    order = State()

@dp.callback_query_handler(lambda c: c.data == 'get_orders')
async def get_order_adnin(callback_query: types.CallbackQuery):
    days = [str(menu[0]) for menu in conn.select_menu(closeF=None)]
    keyboard = kb.get_keyboard(days, days=True)
    await bot.send_message(callback_query.from_user.id, 'Выберите день из списка или пришлите свой вариант', reply_markup=keyboard)
    await GetAllOrders.order.set()

@dp.message_handler(state=GetAllOrders.order)
async def lalalala_admin(message: types.Message, state: FSMContext):
    message.text = convert_day_revers(message.text)[0]
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text): #2023-04-25
        data = conn.select_orders(message.text)
        if data:
            keyboard = kb.menu_button()
            await message.answer(f"""Заказы {message.text}\n{data}""", reply_markup=keyboard)
            await state.finish()
        else:
            await message.answer("Не могу найти заказы на этот день")
            return
    else:
        await message.answer("""Я ожидал получить ответ в формате "DD.MM" например 24.05 попробуйте еще раз""")
        return

@dp.message_handler(content_types=['document'])
async def scan_message(message: types.Message):
    admins = conn.get_admins()
    if str(message.from_user.id) in [admin[0] for admin in admins]:
        document_id = message.document.file_id
        file_info = await bot.get_file(document_id)
        fi = file_info.file_path
        name = message.document.file_name
        urllib.request.urlretrieve(f'https://api.telegram.org/file/bot{API_TOKEN}/{fi}',f'./{name}')
        await bot.send_message(message.from_user.id, 'Файл успешно сохранён')


class AddMenu(StatesGroup):
    date = State()
    salat = State()
    first = State()
    second = State()
    garneer = State()
    bakery = State()


@dp.callback_query_handler(lambda c: c.data == 'add_menu')
async def add_menu(callback_query: types.CallbackQuery):
    keyboard = kb.back()
    await bot.send_message(callback_query.from_user.id, 'Введите дату в формате (YYYY-MM-DD)', reply_markup=keyboard)
    await AddMenu.date.set()

@dp.message_handler(state=AddMenu.date)
async def get_date(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', message.text):
        keyboard = kb.back()
        await state.update_data(date=message.text)
        await message.answer(f"Какие салаты будут в этот день? \nДалее я ожидаю получать ответы в формате \n(позиция 1/позиция 2/и тд)", reply_markup=keyboard)
        await AddMenu.next()
    else:
        keyboard = kb.back()
        await message.answer("""Я ожидал получить ответ в формате "YYYY-MM-DD" например 2023-04-24 попробуй еще раз""", reply_markup=keyboard)
        return

@dp.message_handler(state=AddMenu.salat)
async def get_salat(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if len(re.split('/', message.text)) > 0:
        keyboard = kb.back()
        await state.update_data(salat=message.text)
        await message.answer(f"Что в меню на первое?", reply_markup=keyboard)
        await AddMenu.next()
    else:
        keyboard = kb.back()
        await message.answer("""Я ожидал получить ответ в формате "позиция 1/позиция 2/и тд" например "суп лапша куринная/бощ/солянка сборная" попробуй еще раз""", reply_markup=keyboard)
        return

@dp.message_handler(state=AddMenu.first)
async def get_first(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if len(re.split('/', message.text)) > 0:
        keyboard = kb.back()
        await state.update_data(first=message.text)
        await message.answer(f"Что в меню на второе?", reply_markup=keyboard)
        await AddMenu.next()
    else:
        keyboard = kb.back()
        await message.answer("""Я ожидал получить ответ в формате "позиция 1/позиция 2/и тд" например "суп лапша куринная/бощ/солянка сборная" попробуй еще раз""", reply_markup=keyboard)
        return

@dp.message_handler(state=AddMenu.second)
async def get_second(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if len(re.split('/', message.text)) > 0:
        keyboard = kb.back()
        await state.update_data(second=message.text)
        await message.answer(f"Что по гарнирам?", reply_markup=keyboard)
        await AddMenu.next()
    else:
        keyboard = kb.back()
        await message.answer("""Я ожидал получить ответ в формате "позиция 1/позиция 2/и тд" например "суп лапша куринная/бощ/солянка сборная" попробуй еще раз""", reply_markup=keyboard)
        return

@dp.message_handler(state=AddMenu.garneer)
async def get_garneer(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if len(re.split('/', message.text)) > 0:
        keyboard = kb.back()
        await state.update_data(garneer=message.text)
        await message.answer(f"И последнее - выпечка", reply_markup=keyboard)
        await AddMenu.next()
    else:
        keyboard = kb.back()
        await message.answer("""Я ожидал получить ответ в формате "позиция 1/позиция 2/и тд" например "суп лапша куринная/бощ/солянка сборная" попробуй еще раз""", reply_markup=keyboard)
        return

@dp.message_handler(state=AddMenu.bakery)
async def get_bakery(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.finish()
        await start(message)
        return
    if len(re.split('/', message.text)) > 0:
        keyboard = kb.back()
        await state.update_data(bakery=message.text)
        data = await state.get_data()
        if not conn.select_menu(data['date']):
            conn.add_menu(data)
        else:
            conn.add_menu(data, remove=True)
        data = conn.select_menu(data['date'])
        await message.answer(f"""
Записал! Меню на {data[0]} будет выглядеть следующим образом:\n
Салаты: {re.split('/', data[1])}\n
Первое: {re.split('/', data[2])}\n
Второе: {re.split('/', data[3])}\n
Гарниры: {re.split('/', data[4])}\n
Выпечка: {re.split('/', data[5])}\n
                            """, reply_markup=keyboard)
        await state.finish()
    else:
        keyboard = kb.back()
        await message.answer("""Я ожидал получить ответ в формате "позиция 1/позиция 2/и тд" например "суп лапша куринная/бощ/солянка сборная" попробуй еще раз""", reply_markup=keyboard)
        return

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    # from datetime import datetime, timedelta
    #
    # now = datetime.now()
    # print(now.strftime("%m.%d"))  # 2017-05-03
    #
    # now = datetime.now()
    # two_days = timedelta(2)
    # in_two_days = now + two_days
    # print(in_two_days.strftime("%m.%d"))


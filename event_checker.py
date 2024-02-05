from aiogram import Bot, Dispatcher
import connector
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import asyncio
import random
import re
import datetime
import time

conn = connector.Connector()
API_TOKEN = ''

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

async def send_reminder():
    users = conn.get_who_did_not_order()
    if users:
        print(users)
        for user in users:
            try:
                print(f"send_reminder from user {user} SUCCESFUL")
                await bot.send_message(str(user), 'Вы не сделали заказ на следующий рабочий день.\nПоспешите, до закрытия меню осталось пол часа')
            except:
                print(f"send_reminder from user {user} FAILED")


async def set_random_orders():
    users = conn.get_who_did_not_order(options=True)
    if users:
        for user in users:
            next_day = conn.get_next_day()
            menu = conn.select_menu(next_day)
            order = {"date": next_day,
                     "salat": random.choice(re.split('/', menu[1])),
                     "first": random.choice(re.split('/', menu[2])),
                     "second": random.choice(re.split('/', menu[3])),
                     "garneer": random.choice(re.split('/', menu[4])),
                     "bakery": random.choice(re.split('/', menu[5]))
                     }
            conn.add_order(order, user)
            data = conn.select_order(next_day, user)
            await bot.send_message(str(user), f"""Вы не сделали заказ на следующий рабочий день.\nПоэтому я выбрал за вас:\nСалат: {data[3]}\nПервое: {data[4]}\nВторое: {data[5]}\nГарнир: {data[6]}\nВыпечка: {data[7]}\n""")
            print(f"send_reminder from user {user} Succesfuly")

async def close_orders():
    next_day = conn.get_next_day()
    conn.close_orders(next_day)

async def eternity():
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        print(now)
        if now == "16:00":
            print("start send_reminder event")
            await send_reminder()
        if now == "16:30":
            print("start close_orders event")
            await set_random_orders()
            await close_orders()
        time.sleep(60)

def start():
    asyncio.run(eternity())
start()
import re

import psycopg2
from datetime import datetime, timedelta

class Connector():
    def __init__(self):
        self.conn = psycopg2.connect(dbname="yarus_bot_db", user="postgres", password="qwerty", host="127.0.0.1")
        self.cursor = self.conn.cursor()
        self.conn.autocommit = True

    def add_user(self, id, full_name):
        insert_query = f""" INSERT INTO users (id, full_name, helper) VALUES (%s, %s, %s) """
        self.cursor.execute(insert_query, (id, full_name, False))

    def get_user_info(self, id):
        select_query = "select * from users where id = %s"
        self.cursor.execute(select_query, (str(id),))
        return self.cursor.fetchone()

    def get_next_day(self):
        now = '20' + datetime.now().strftime("%y-%m-%d")
        select_query = "SELECT day FROM menu WHERE day > %s ORDER BY day ASC LIMIT 1"
        self.cursor.execute(select_query, (now,))
        next_day = '20' + self.cursor.fetchone()[0].strftime("%y-%m-%d")
        return next_day

    def is_security(self, id):
        select_query = "select * from security where id = %s"
        self.cursor.execute(select_query, (str(id),))
        return self.cursor.fetchone()

    def get_who_did_not_order(self, options=False, day=None):
        try:
            if day:
                next_day = day
            else:
                next_day = self.get_next_day()
            if not options:
                select_query = "select id from users"
            else:
                select_query = "select id from users WHERE helper = True"
            self.cursor.execute(select_query)
            all_users = set([int(user[0]) for user in self.cursor.fetchall()])

            select_query = "SELECT user_id FROM orders WHERE day = %s"
            self.cursor.execute(select_query, (next_day,))
            all_users.difference_update(set([user[0] for user in self.cursor.fetchall()]))
            return all_users
        except:
            return None

    def add_menu(self, menu: dict, remove=False):
        if remove:
            delete_query = """  DELETE FROM menu WHERE day = %s  """
            self.cursor.execute(delete_query, (menu["date"],))
        insert_query = f""" INSERT INTO menu (day, salads, first, second, garnish, bakery, closeF) VALUES
                                                  (%s, %s, %s, %s, %s, %s, %s) """
        self.cursor.execute(insert_query, (menu['date'], menu['salat'], menu['first'], menu['second'], menu['garneer'], menu['bakery'], False))

    def delete_order(self, date=None, user_id=None, order_id=None, refuser=False):
        if order_id:
            delete_query = f"""  DELETE FROM {'orders' if not refuser else 'refusal_orders'} WHERE order_id = %s  """
            self.cursor.execute(delete_query, (order_id,))
            return
        delete_query = """  DELETE FROM orders WHERE day = %s AND user_id = %s  """
        self.cursor.execute(delete_query, (date, user_id))

    def add_order(self, order: [dict, tuple], user_id=None, remove=False):
        if remove:
            self.delete_order(order['date'], user_id)
        insert_query = f""" INSERT INTO orders (order_id, user_id, day, salads, first, second, garnish, bakery) VALUES
                                                  (%s, %s, %s, %s, %s, %s, %s, %s) """
        if type(order) == dict:
            order_id = str(user_id) + order['date']
            self.cursor.execute(insert_query, (order_id, user_id, order['date'], order['salat'], order['first'], order['second'], order['garneer'], order['bakery']))
        else:
            self.cursor.execute(insert_query, order)
    def add_admin(self, admin_id):
        insert_query = f""" INSERT INTO admins (id) VALUES (%s) """
        self.cursor.execute(insert_query, (admin_id,))

    def get_admins(self):
        select_query = "select * from admins"
        self.cursor.execute(select_query)
        return self.cursor.fetchall()

    def is_close(self, day):
        select_query = f"""SELECT closeF FROM menu WHERE day = %s"""
        self.cursor.execute(select_query, (day,))
        return self.cursor.fetchone()[0]

    def get_office_worker(self, name=None, user_id=None):
        if user_id:
            select_query = f"""SELECT name FROM office_workers WHERE user_id = %s"""
            self.cursor.execute(select_query, (user_id,))
            return self.cursor.fetchone()
        name = name.lower()
        select_query = f"""SELECT user_id FROM office_workers WHERE name = %s"""
        self.cursor.execute(select_query, (name,))
        res = self.cursor.fetchone()
        if not res:
            if re.fullmatch("[А-Яа-яЁё]+ [А-Яа-яЁё]+", name):
                name = re.sub("([А-Яа-яЁё]+) ([А-Яа-яЁё]+)", r"\2 \1", name)
                select_query = f"""SELECT user_id FROM office_workers WHERE name = %s"""
                self.cursor.execute(select_query, (name,))
                res = self.cursor.fetchone()
        return (res, name)

    def update_office_worker(self, name, id):
        name = name.lower()
        user_id, name = self.get_office_worker(name)
        user_id = user_id[0]
        if user_id:
            user_id = 0
        else:
            user_id = id
        update_query = f"""UPDATE office_workers SET user_id = {user_id} WHERE name = %s"""
        self.cursor.execute(update_query, (name,))

    def add_refusal_order(self, day, user_id, order):
        insert_query = f""" INSERT INTO refusal_orders (order_id, user_id, day, salads, first, second, garnish, bakery) VALUES
                                                  (%s, %s, %s, %s, %s, %s, %s, %s) """
        order_id = str(user_id) + day
        self.cursor.execute(insert_query, (order_id, user_id, day, order[3], order[4], order[5], order[6], order[7]))

    def refusal_order(self, day, user_id, this_user_id=None, reverse=False):
        if reverse:
            order = self.get_refusal_orders(order_id=f"{user_id}{day}")
            if order:
                order = list(order)
                order[1] = this_user_id
                order = tuple(order)
                self.add_order(order=order)
                self.delete_order(order_id=f"{user_id}{day}", refuser=True)
                return True
            else:
                return False
        order = self.select_order(day, user_id)
        if "/" in order[-1]:
            order = list(order)
            order[-1] = re.split("/", order[-1])[0]
            order = tuple(order)
        if order:
            self.add_refusal_order(day, user_id, order)
            self.delete_order(day, user_id)
            return True
        else:
            return False

    async def send_refuse_notif(self, user_name, bot, this_user):
        users = self.get_who_did_not_order(day=str(datetime.now())[:10])
        if users:
            for user in users:
                if user == this_user:
                    continue
                try:
                    await bot.send_message(str(user), f'Пользователь {user_name} отказался от своего заказа, вы можете его забрать!')
                except:
                    print(f"send_reminder from user {user} FAILED")

    def get_refusal_orders(self, day=str(datetime.now())[:10], order_id=None):
        if order_id:
            select_query = f"""SELECT * FROM refusal_orders WHERE order_id = %s"""
            self.cursor.execute(select_query, (order_id,))
            return self.cursor.fetchone()
        select_query = f"""SELECT * FROM refusal_orders WHERE day = %s"""
        self.cursor.execute(select_query, (day,))
        return self.cursor.fetchall()

    def close_orders(self, day, revert=False, closeF=True):
        close = None
        if revert:
            select_query = f"""SELECT * FROM menu WHERE day = %s"""
            self.cursor.execute(select_query, (day,))
            menu = self.cursor.fetchone()
            print(menu)
            if not menu:
                return "FOUND_ERROR"
            close = self.is_close(day)
            if close:
                closeF = False
        update_query = f"""UPDATE menu SET closeF = {closeF} WHERE day = %s"""
        self.cursor.execute(update_query, (day, ))
        return close

    def is_ml_team(self, id):
        select_query = "SELECT * FROM ml_team WHERE id = %s"
        self.cursor.execute(select_query, (str(id),))
        order = self.cursor.fetchone()
        return order

    def select_order(self, day, user_id):
        select_query = "SELECT * FROM orders WHERE day = %s AND user_id = %s"
        self.cursor.execute(select_query, (day, user_id))
        order = self.cursor.fetchone()
        return order

    def select_orders(self, day):
        all_positions = {}
        select_query = "SELECT * FROM orders WHERE day = %s"
        self.cursor.execute(select_query, (day, ))
        for order in self.cursor.fetchall():
            pass_index = 1
            for pos in order:
                pos = pos.split("/") if type(pos) is str else [pos]
                for positions in pos:
                    if pass_index < 3:
                        pass_index += 1
                        continue
                    if type(positions) is str:
                        positions = positions.strip()
                    if positions == "Пропустить":
                        continue
                    if positions in all_positions:
                        all_positions[positions] += 1
                    else:
                        all_positions[positions] = 1
        all_orders_string = ''
        for pos in all_positions:
            re_pos = pos
            if re.fullmatch('[0-9]{4}-[0-9]{2}-[0-9]{2}', str(pos)):
                re_pos = "Всего заказало человек"
            all_orders_string += f'\n{re_pos}: {all_positions[pos]}'
        return all_orders_string


    def get_dop_option(self, user_id):
        select_query = "select helper from users WHERE id = %s"
        self.cursor.execute(select_query, (str(user_id),))
        return self.cursor.fetchone()

    def set_dop_option(self, user_id):
        option = self.get_dop_option(user_id)[0]
        update_query = f"""UPDATE users SET helper = {True if not option else False} WHERE id = %s"""
        self.cursor.execute(update_query, (str(user_id),))

    def select_menu(self, day=None, closeF=True):
        if day:
            select_query = "SELECT * FROM menu WHERE day = %s AND closeF = False"
            self.cursor.execute(select_query, (day,))
            return self.cursor.fetchone()
        else:
            select_query = f"SELECT * FROM menu{' WHERE closeF = False' if closeF else ''} ORDER BY day DESC LIMIT 5"
            self.cursor.execute(select_query)
            return self.cursor.fetchall()


    def delete_user(self, user_id):
        delete_query = """Delete from users where id = %s"""
        self.cursor.execute(delete_query, (str(user_id),))

    def insert_users_in_workers(self, users):
        for user in users:
            user = user.lower()
            insert_query = f""" INSERT INTO office_workers (name, user_id) VALUES (%s, %s) """
            self.cursor.execute(insert_query, (user, 0))

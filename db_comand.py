import psycopg2

conn = psycopg2.connect(dbname="yarus_bot_db", user="postgres", password="qwerty", host="127.0.0.1")
cursor = conn.cursor()
#
# sql = "CREATE DATABASE yarus_bot_db"
# cursor.execute(sql)
conn.autocommit = True

# cursor.execute("""drop table office_workers""")
# cursor.execute('''
# CREATE TABLE office_workers (
# name text NOT NULL,
# user_id bigint
# );
# ''')

# cursor.execute("""drop table users""")
# cursor.execute('''
# CREATE TABLE users (
# id varchar(250) NOT NULL,
# full_name text NOT NULL,
# helper bool);
# ''')
#
# cursor.execute("""drop table security""")
# cursor.execute('''
# CREATE TABLE security (
# id text NOT NULL);
# ''')

# cursor.execute('''
# CREATE TABLE admins (
# id text NOT NULL);
# ''')

# cursor.execute("""drop table ml_team""")
# cursor.execute('''
# CREATE TABLE ml_team (
# id text NOT NULL);
# ''')

# cursor.execute("""drop table menu""")
#
# cursor.execute('''
# CREATE TABLE menu (
# day date NOT NULL,
# salads text NOT NULL,
# first text NOT NULL,
# second text NOT NULL,
# garnish text NOT NULL,
# bakery text NOT NULL,
# closeF bool);
# ''')

#
#
# cursor.execute("""drop table orders""")
# cursor.execute('''
# CREATE TABLE orders (
# order_id text NOT NULL UNIQUE,
# user_id bigint NOT NULL,
# day date NOT NULL,
# salads text NOT NULL,
# first text NOT NULL,
# second text NOT NULL,
# garnish text NOT NULL,
# bakery text NOT NULL);
# ''')

#
# cursor.execute('''
# CREATE TABLE orders (
# user_id varchar(250) NOT NULL,
# user_order varchar(4000) NOT NULL,
# day varchar(250) NOT NULL);
# ''')
#

# cursor.execute('''
# CREATE TABLE refusal_orders (
# order_id text NOT NULL UNIQUE,
# user_id bigint NOT NULL,
# day date NOT NULL,
# salads text NOT NULL,
# first text NOT NULL,
# second text NOT NULL,
# garnish text NOT NULL,
# bakery text NOT NULL);
# ''')


cursor.close()
conn.close()


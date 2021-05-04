import mysql.connector as mysql
import csv
from var_secrets import *

villager_data = None

db = mysql.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER_NAME,
    passwd=MYSQL_PASS,
    database=MYSQL_DATABASE
)

cursor = db.cursor()

villager_list = {}
cursor.execute("SELECT id, name from villagers")
for id, name in cursor.fetchall():
    villager_list[name] = id

user_list = {}
cursor.execute("SELECT id, discord_id from users")
for id, discord_id in cursor.fetchall():
    user_list[discord_id] = id

with open('import.csv', newline='') as f:
    reader = csv.reader(f)
    villager_data = list(reader)

for villager in villager_data:

    cursor.execute(f"SELECT captures.number from users "
                   f"INNER JOIN captures ON users.id = captures.user_id "
                   f"WHERE users.discord_id = {villager[1]} "
                   f"AND captures.villager_id = {villager_list[villager[0].title()]};")
    result = cursor.fetchone()
    print(result)
    if result is not None:
        cursor.execute(f"SELECT * FROM users WHERE discord_id = {villager[1]};")
        result = cursor.fetchone()
        id = result[0]
        print(f"{id}:{villager_list[villager[0].title()]}")
        cursor.execute(
            f"UPDATE captures "
            "SET number = number + 1 "
            f"WHERE user_id = {id} AND villager_id = {villager_list[villager[0].title()]};")
    else:
        cursor.execute(f"SELECT id FROM users WHERE discord_id = {villager[1]};")
        result = cursor.fetchone()
        if result is None:
            cursor.execute(f"INSERT INTO users (discord_id) VALUES ({villager[1]});")
            cursor.execute(f"SELECT * FROM users WHERE discord_id = {villager[1]};")
            result = cursor.fetchone()
            id = result[0]
        else:
            id = result[0]
        query = (
            "INSERT INTO captures (user_id , villager_id, shiny_number) "
            "VALUES (%s,%s, %s);"
        )
        values = (id, villager_list[villager[0].title()], 1)
        cursor.execute(query, values)
    db.commit()
    print(cursor.rowcount, "record inserted")

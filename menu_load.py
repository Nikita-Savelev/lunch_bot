import pandas as pd
import re

menu_load = pd.read_excel('./menu.xlsx')
menu = {}
keys = []
positions = []
days = []
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
        if str(day) != "nan":
            Y = re.findall(".+?[0-9]{2}\.[0-9]{2}\.([0-9]{4})", day)[0]
            M = re.findall(".+?[0-9]{2}\.([0-9]{2})\.[0-9]{4}", day)[0]
            D = re.findall(".+?([0-9]{2})\.[0-9]{2}\.[0-9]{4}", day)[0]
            date = f"{Y}-{M}-{D}"
            days.append(date)

print(len(positions))
print(len(days))

for index in range(0, len(days)):
    menu[days[index]] = positions[index]
print(menu)

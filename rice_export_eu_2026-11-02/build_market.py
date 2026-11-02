import csv
import json
from pathlib import Path

root = Path(__file__).parent
countries = [
    (40, 'Австрия'), (56, 'Бельгия'), (100, 'Болгария'), (191, 'Хорватия'),
    (196, 'Кипр'), (203, 'Чехия'), (208, 'Дания'), (233, 'Эстония'),
    (246, 'Финляндия'), (251, 'Франция'), (276, 'Германия'), (300, 'Греция'),
    (348, 'Венгрия'), (372, 'Ирландия'), (380, 'Италия'), (428, 'Латвия'),
    (440, 'Литва'), (442, 'Люксембург'), (470, 'Мальта'), (528, 'Нидерланды'),
    (616, 'Польша'), (620, 'Португалия'), (642, 'Румыния'), (703, 'Словакия'),
    (705, 'Словения'), (724, 'Испания'), (752, 'Швеция'),
]
records = {}
for year in (2024, 2025):
    source = root / 'sources' / f'comtrade_{year}_1006_world_imports.json'
    data = json.loads(source.read_text())
    records[year] = {int(r['reporterCode']): r for r in data['data']}
france = root / 'sources' / 'comtrade_2024_1006_france_all_partners.json'
if france.exists():
    fr_rows = json.loads(france.read_text())['data']
    records[2024][251] = next(r for r in fr_rows if r['partnerCode'] == 0)

with (root / 'data' / 'market_27.csv').open('w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['страна', 'код_ООН', 'год', 'импорт_HS1006_из_мира_т',
                'стоимость_USD', 'средняя_USD_т', 'вес_оценочный',
                'доля_extra_EU', 'потребление_т', 'примечание'])
    for code, name in countries:
        chosen = None
        year = None
        for y in (2025, 2024):
            r = records[y].get(code)
            if r and (r.get('netWgt') or 0) > 0 and (r.get('primaryValue') or 0) > 0:
                chosen, year = r, y
                break
        if chosen:
            tonnes = chosen['netWgt'] / 1000
            value = chosen['primaryValue']
            avg = value / tonnes
            note = 'Включает внутриесовский импорт; preview UN Comtrade'
            if year == 2024:
                note += '; 2025 отсутствует/нулевое'
            w.writerow([name, code, year, round(tonnes, 2), round(value, 2),
                        round(avg, 2), 'да' if chosen.get('isNetWgtEstimated') else 'нет',
                        'н/д', 'н/д', note])
        else:
            w.writerow([name, code, 'н/д', 'н/д', 'н/д', 'н/д', 'н/д',
                        'н/д', 'н/д', 'Нет строки в полученном публичном preview'])

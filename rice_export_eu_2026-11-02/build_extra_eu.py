import csv
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

root = Path(__file__).parent
countries = [(40,'Австрия'),(56,'Бельгия'),(100,'Болгария'),(191,'Хорватия'),
 (196,'Кипр'),(203,'Чехия'),(208,'Дания'),(233,'Эстония'),(246,'Финляндия'),
 (251,'Франция'),(276,'Германия'),(300,'Греция'),(348,'Венгрия'),(372,'Ирландия'),
 (380,'Италия'),(428,'Латвия'),(440,'Литва'),(442,'Люксембург'),(470,'Мальта'),
 (528,'Нидерланды'),(616,'Польша'),(620,'Португалия'),(642,'Румыния'),
 (703,'Словакия'),(705,'Словения'),(724,'Испания'),(752,'Швеция')]
codes = ','.join(str(c) for c,_ in countries)
world = {int(r['reporterCode']):r for r in json.loads(
    (root/'sources/comtrade_2024_1006_world_imports.json').read_text())['data']}

def fetch(item):
    code,name=item
    params={'period':'2024','reporterCode':str(code),'cmdCode':'1006','flowCode':'M',
            'partnerCode':codes,'partner2Code':'0','customsCode':'C00','motCode':'0',
            'maxRecords':'500'}
    url='https://comtradeapi.un.org/public/v1/preview/C/A/HS?'+urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url,timeout=25) as resp:
                data=json.load(resp)
            if isinstance(data.get('data'),list):
                return code,name,url,data,''
        except Exception as e:
            err=str(e)
            time.sleep(5*(attempt+1))
    return code,name,url,{},err

with ThreadPoolExecutor(max_workers=3) as pool:
    fetched=list(pool.map(fetch,countries))
raw={str(code):data for code,_,_,data,_ in fetched if data}
(root/'sources/comtrade_2024_1006_intra_eu_partner_rows.json').write_text(
    json.dumps(raw,ensure_ascii=False,indent=2))

with (root/'data/market_27_extra_eu_2024.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.writer(f)
    writer.writerow(['страна','код_ООН','год','импорт_из_мира_т','импорт_из_ЕС_т_сумма_партнёров',
        'расчёт_импорта_из_не_ЕС_т','качество','источник'])
    for code,name,url,data,err in fetched:
        wr=world.get(code)
        total=(wr or {}).get('netWgt') or 0
        intra=sum((r.get('netWgt') or 0) for r in data.get('data',[]) if r.get('partnerCode')!=code)
        if total>0 and data.get('data') is not None:
            extra=(total-intra)/1000
            status='оценка preview; расчёт world минус сумма EU-partners'
            if extra<0: status+='; ОТРИЦАТЕЛЬНОЕ — несопоставимые/оценочные данные'
            writer.writerow([name,code,2024,round(total/1000,2),round(intra/1000,2),
                             round(extra,2),status,url])
        else:
            writer.writerow([name,code,2024,'н/д','н/д','н/д',
                             'нет данных/ошибка: '+err,url])

import csv
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

root=Path(__file__).parent
market=list(csv.DictReader((root/'data/market_27_extra_eu_2024.csv').open(encoding='utf-8-sig')))
eucodes={int(r['код_ООН']) for r in market}

def fetch(r):
    country=int(r['код_ООН'])
    q={'period':'2024','reporterCode':country,'cmdCode':'1006','flowCode':'M',
       'partner2Code':'0','customsCode':'C00','motCode':'0','maxRecords':'500'}
    url='https://comtradeapi.un.org/public/v1/preview/C/A/HS?'+urllib.parse.urlencode(q)
    err=''
    for attempt in range(4):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(req,timeout=25) as h:data=json.load(h)
            if isinstance(data.get('data'),list):return country,url,data,''
            err=data.get('error','unknown API error')
        except Exception as e:err=str(e)
        time.sleep(6*(attempt+1))
    return country,url,{},err

cache=root/'sources/comtrade_2024_1006_all_partner_rows.json'
if cache.exists():
    raw=json.loads(cache.read_text())
    results=[]
    for r in market:
        code=int(r['код_ООН'])
        url='https://comtradeapi.un.org/public/v1/preview/C/A/HS?period=2024&reporterCode='+str(code)+'&cmdCode=1006&flowCode=M&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500'
        results.append((code,url,raw.get(str(code),{}),'нет кэшированной записи'))
else:
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(fetch,market))
    cache.write_text(json.dumps({str(c):data for c,_,data,_ in results if data},ensure_ascii=False,indent=2))

names={
 4:'Афганистан',32:'Аргентина',50:'Бангладеш',76:'Бразилия',104:'Мьянма',
 116:'Камбоджа',124:'Канада',144:'Шри-Ланка',156:'Китай',208:'Дания',
 251:'Франция',268:'Грузия',276:'Германия',300:'Греция',328:'Гайана',
 348:'Венгрия',699:'Индия',
 360:'Индонезия',364:'Иран',368:'Ирак',380:'Италия',398:'Казахстан',
 392:'Япония',418:'Лаос',458:'Малайзия',484:'Мексика',504:'Марокко',528:'Нидерланды',
 566:'Нигерия',586:'Пакистан',604:'Перу',608:'Филиппины',643:'Россия',
 688:'Сербия',704:'Вьетнам',710:'ЮАР',724:'Испания',764:'Таиланд',
 740:'Суринам',784:'ОАЭ',792:'Турция',804:'Украина',818:'Египет',826:'Великобритания',
 834:'Танзания',840:'США',858:'Уругвай',862:'Венесуэла',
}
bycode={int(r['код_ООН']):r for r in market}
with (root/'data/market_27_main_suppliers_2024.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['страна_импортёр','код_ООН','главные_внешние_поставщики_по_массе_HS1006_2024',
                'импорт_из_не_ЕС_т_по_партнёрам','статус','источник'])
    for code,url,data,err in results:
        partners=[r for r in data.get('data',[]) if (r.get('partnerCode') not in eucodes and
                    r.get('partnerCode')!=0 and (r.get('netWgt') or 0)>0)]
        partners.sort(key=lambda r:r.get('netWgt') or 0,reverse=True)
        tops=[]
        for p in partners[:4]:
            pc=int(p['partnerCode'])
            tops.append(f"{names.get(pc, 'код '+str(pc))}: {(p['netWgt']/1000):,.0f} т".replace(',',' '))
        w.writerow([bycode[code]['страна'],code,'; '.join(tops) if tops else 'н/д',
                    round(sum(r['netWgt'] for r in partners)/1000,2) if partners else 'н/д',
                    'публичный preview; партнёры могут быть неполными' if data else 'ошибка: '+err,url])

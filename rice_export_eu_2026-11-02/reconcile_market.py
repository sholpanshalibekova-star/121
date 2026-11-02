"""Rebuild 2024 intra/extra-EU estimates from cached UN Comtrade partner rows."""
import csv
import json
from pathlib import Path

root=Path(__file__).parent
market=list(csv.DictReader((root/'data/market_27.csv').open(encoding='utf-8-sig')))
eucodes={int(r['код_ООН']) for r in market}
all_rows=json.loads((root/'sources/comtrade_2024_1006_all_partner_rows.json').read_text())
with (root/'data/market_27_extra_eu_2024.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f)
    w.writerow(['страна','код_ООН','год','импорт_из_мира_т','импорт_из_ЕС_т_сумма_партнёров',
                'расчёт_импорта_из_не_ЕС_т','качество','источник'])
    for m in market:
        code=int(m['код_ООН'])
        records=all_rows.get(str(code),{}).get('data',[])
        world=next(((r.get('netWgt') or 0) for r in records if r.get('partnerCode')==0),0)
        intra=sum((r.get('netWgt') or 0) for r in records if r.get('partnerCode') in eucodes and r.get('partnerCode')!=code)
        extra=sum((r.get('netWgt') or 0) for r in records if r.get('partnerCode') not in eucodes and r.get('partnerCode')!=0)
        if records:
            quality='публичный preview; прямая сумма строк партнёров; могут быть неполные/оценочные данные'
            if world==0:quality+='; world-агрегат отсутствует'
            elif abs((intra+extra)-world)/world>0.05:quality+='; сумма партнёров отличается от world >5%'
            w.writerow([m['страна'],code,2024,round(world/1000,2) if world else 'н/д',
                        round(intra/1000,2),round(extra/1000,2),quality,
                        f'https://comtradeapi.un.org/public/v1/preview/C/A/HS?period=2024&reporterCode={code}&cmdCode=1006&flowCode=M&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500'])
        else:
            w.writerow([m['страна'],code,2024,'н/д','н/д','н/д','нет ответа API',''])

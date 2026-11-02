"""Find relevant official Kazakhstan services from the public gov.kz sitemap."""
import csv
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from lxml import etree

root=Path(__file__).parent
sitemap=etree.parse('/tmp/gov_services.xml')
ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}
urls=[u for u in sitemap.xpath('//s:loc/text()',namespaces=ns) if u.endswith('lang=ru')]
pattern=re.compile('фитосанитар|происхождени|деклар|карантин|экспорт|зерн|пищев',re.I)

def fetch(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=10) as response:
            data=response.read(40000).decode('utf-8','ignore')
        title=re.search(r'<title>(.*?)</title>',data,re.I|re.S)
        title=re.sub(r'<[^>]+>','',title.group(1)).strip() if title else ''
        return url,title
    except Exception:
        return url,''

with ThreadPoolExecutor(max_workers=8) as pool:
    results=list(pool.map(fetch,urls))
hits=[x for x in results if pattern.search(x[1])]
with (root/'data/kz_service_candidates.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['url','заголовок'])
    w.writerows(hits)
print('scanned',len(results),'titles',sum(bool(t) for _,t in results),'hits',len(hits))
for u,t in hits:print(t,u)

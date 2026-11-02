import csv
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from lxml import html

root = Path(__file__).parent
base = list(csv.DictReader((root / 'data' / 'buyer_candidates.csv').open(encoding='utf-8')))
extra = [
    ('Riso Zaccaria', 'IT', 'https://www.risozaccaria.it', 'producer_packer'),
    ('Principato di Lucedio', 'IT', 'https://www.principatodilucedio.it', 'producer_packer'),
    ('Cascina Belvedere', 'IT', 'https://www.cascinabelvedere.com', 'producer_packer'),
    ('Bosto (Ebro Foods)', 'BE', 'https://www.bosto.be', 'brand_distributor'),
    ('Raisio / Risella', 'FI', 'https://www.risella.fi', 'brand_distributor'),
    ('Reis-Fit (Ebro Foods)', 'DE', 'https://www.reis-fit.de', 'brand_distributor'),
    ('Riso Gemma', 'IT', 'https://www.risogemma.it', 'producer_packer'),
    ('Riseria Greppi', 'IT', 'https://www.riseriagreppi.it', 'producer_packer'),
    ('Riseria Re Carlo', 'IT', 'https://www.riseriarecarlo.it', 'producer_packer'),
    ('Riso Rancan', 'IT', 'https://www.risorancan.it', 'producer_packer'),
    ('Riso Margherita', 'IT', 'https://www.risomargherita.com', 'producer_packer'),
    ('Arroz Montsià', 'ES', 'https://www.montsia.es', 'producer_packer'),
]
base += [dict(zip(('company', 'country', 'website', 'category'), x)) for x in extra]

def check(row):
    out = row.copy()
    try:
        req = urllib.request.Request(row['website'], headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=13) as resp:
            page = resp.read(180000).decode('utf-8', 'ignore')
            out['final_url'] = resp.url
            out['status'] = str(resp.status)
        tree = html.fromstring(page)
        title = tree.xpath('//title/text()')
        out['title'] = ' '.join(title[0].split()) if title else ''
        out['rice_word_on_page'] = 'да' if re.search(
            r'\brice\b|riso|arroz|\bryż\b|\breis\b|\briz\b|\brijst\b', page, re.I) else 'нет'
        contacts = []
        for a in tree.xpath('//a[@href]'):
            href = a.get('href') or ''
            label = ' '.join(a.xpath('.//text()')).lower()
            if re.search(r'contact|kontakt|contatt|contacto|contato|yhteys', href + ' ' + label, re.I):
                url = urllib.parse.urljoin(out['final_url'], href)
                if urllib.parse.urlparse(url).netloc == urllib.parse.urlparse(out['final_url']).netloc:
                    contacts.append(url)
        out['contact_page'] = contacts[0] if contacts else ''
        out['public_email'] = ''  # A scraped email needs separate validation before use.
    except Exception as e:
        out.update(final_url='', status='ошибка: ' + str(e)[:75], title='',
                   rice_word_on_page='не проверено', contact_page='', public_email='')
    return out

with ThreadPoolExecutor(max_workers=8) as pool:
    checked = list(pool.map(check, base))

fields = ['company', 'country', 'website', 'final_url', 'category', 'status',
          'title', 'rice_word_on_page', 'contact_page', 'public_email']
with (root / 'data' / 'buyer_site_checks.csv').open('w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fields)
    w.writeheader()
    w.writerows(checked)

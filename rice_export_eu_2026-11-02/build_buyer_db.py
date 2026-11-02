import csv
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

root = Path(__file__).parent
checks = {r['company']: r for r in csv.DictReader((root / 'data' / 'buyer_site_checks.csv').open(encoding='utf-8-sig'))}

# One business lead per organisation/group. A trading name is kept when the legal name
# has not yet been checked; the legal-counterparty field explicitly records this.
names = [
    'Ebro Foods', 'Euricom', 'Riso Gallo', 'Riso Scotti', 'Riso Acquerello',
    'Riso Grazia', 'Dacsa Group', 'SanoRice', 'Muellers Muehle', 'Reishunger',
    'Davert', 'Rapunzel Naturkost', 'SONKO', 'Kupiec', 'Melvit', 'Sawex Foods',
    'Country Life', 'Novarroz', 'Markal', 'Smart Organic', 'Riso Zaccaria',
    'Principato di Lucedio', 'Cascina Belvedere', 'Raisio / Risella',
    'Riso Gemma', 'Riseria Greppi', 'Riseria Re Carlo', 'Riso Rancan',
    'Riso Margherita', 'Arroz Montsià',
]
assert len(names) == 30 and len(set(names)) == 30
assert all(checks[n]['status'] == '200' for n in names)

def priority(category):
    if category in ('ethnic_importer', 'importer_distributor', 'organic_distributor', 'retailer_distributor'):
        return 'A — запросить товарную матрицу'
    if category in ('producer_packer', 'food_manufacturer'):
        return 'B — предложить сырьё/контрактную фасовку'
    return 'C — проверить закупочную функцию'

rows = []
for name in names:
    c = checks[name]
    cat = c['category']
    evidence = ('Официальный сайт доступен; на странице есть упоминание риса/рисовых товаров'
                if c['rice_word_on_page'] == 'да' else
                'Официальный сайт доступен; ассортимент риса на стартовой странице не подтверждён')
    rows.append({
        'Компания / торговое имя': name,
        'Страна': c['country'],
        'Сегмент': cat,
        'Веб-сайт': c['final_url'],
        'Открытый канал связи': c['contact_page'] or c['final_url'],
        'Email': 'не найден/не проверен',
        'Основание включения': evidence,
        'Тип закупаемого риса': 'не подтверждён',
        'Интерес к казахстанскому рису': 'не подтверждён',
        'Юридическое лицо для договора': 'проверить в реестре перед KYC',
        'Приоритет': priority(cat),
        'Проверка сайта': '02.11.2026; HTTP 200',
        'Следующее действие': 'Отправить спецификацию и образец только после согласования продукта',
    })

csv_path = root / 'data' / 'buyers_30.csv'
with csv_path.open('w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

wb = Workbook()
ws = wb.active
ws.title = '30 потенциальных компаний'
ws.append(list(rows[0]))
for row in rows:
    ws.append(list(row.values()))
ws.freeze_panes = 'A2'
ws.auto_filter.ref = ws.dimensions
for cell in ws[1]:
    cell.font = Font(bold=True, color='FFFFFF')
    cell.fill = PatternFill('solid', fgColor='17365D')
    cell.alignment = Alignment(wrap_text=True)
for col in range(1, ws.max_column + 1):
    ws.column_dimensions[get_column_letter(col)].width = [31, 11, 23, 37, 44, 26, 66, 22, 25, 28, 37, 25, 55][col-1]
for row in ws.iter_rows(min_row=2):
    for cell in row:
        cell.alignment = Alignment(vertical='top', wrap_text=True)
    ws.row_dimensions[row[0].row].height = 45
    for idx in (4, 5):
        cell = row[idx-1]
        if str(cell.value).startswith('https://'):
            cell.hyperlink = cell.value
            cell.style = 'Hyperlink'

readme = wb.create_sheet('Пояснения')
for s in [
    '30 коммерческих организаций/торговых имён; факт сайта проверен 02.11.2026.',
    'Название в колонке A не гарантирует совпадение с зарегистрированным юридическим лицом; перед контрактом нужен KYC.',
    'Ни один участник не подтверждал интерес или готовность купить казахстанский рис.',
    'Рисовое предложение и закупочная функция требуют прямого контакта; сайт и контактная страница не означают согласие на сделку.',
    'Приоритет — гипотеза для очереди писем; не рейтинг кредитоспособности.',
    'Сырые результаты HTTP и ссылки на контакты: data/buyer_site_checks.csv.',
]:
    readme.append([s])
readme.column_dimensions['A'].width = 120
wb.save(root / '04_База_европейских_покупателей.xlsx')

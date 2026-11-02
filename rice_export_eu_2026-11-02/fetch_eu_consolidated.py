"""Fetch official consolidated EU law via Publications Office RDF links.

Usage: python fetch_eu_consolidated.py 32019R2072
"""
import re
import sys
import urllib.request
from pathlib import Path
from lxml import etree

root = Path(__file__).parent / 'sources'
R = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'

def fetch(url, accept='application/rdf+xml'):
    req = urllib.request.Request(url, headers={'Accept': accept, 'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()

def subject(root, uri):
    for node in root:
        if node.get(R+'about') == uri:
            return node
    raise ValueError('Subject missing: '+uri)

celex = sys.argv[1]
uri = 'http://publications.europa.eu/resource/celex/'+celex
tree = etree.fromstring(fetch(uri.replace('http:', 'https:')))
work = subject(tree, uri)
links = [c.get(R+'resource') for c in work if c.tag.endswith('consolidated_by') or c.tag.endswith('resource_legal_consolidated_by_act_consolidated')]
links = [x for x in links if x and re.search(r'%2F\d{8}$', x)]
links.sort(key=lambda u: u.rsplit('/',1)[1])
consolidated = links[-1]
expression = consolidated + '.ENG'
eng_tree = etree.fromstring(fetch(expression.replace('http:', 'https:')))
eng = subject(eng_tree, expression)
manifestation = next(c.get(R+'resource') for c in eng if c.tag.endswith('expression_manifested_by_manifestation') and c.get(R+'resource','').endswith('.xhtml'))
manifest_tree = etree.fromstring(fetch(manifestation.replace('http:', 'https:')))
manifest = subject(manifest_tree, manifestation)
cellar = next(c.get(R+'resource') for c in manifest if c.tag.endswith('manifestation_has_item')) if any(c.tag.endswith('manifestation_has_item') for c in manifest) else None
if not cellar:
    for node in manifest_tree:
        candidate = node.get(R+'about','')
        if '/DOC_1' in candidate:
            cellar = candidate
            break
if not cellar:
    raise ValueError('XHTML item missing')
body = fetch(cellar.replace('http:', 'https:'), 'application/xhtml+xml')
date = consolidated.rsplit('/',1)[1].split('%2F')[-1]
path = root / f'CELEX_{celex}_{date}_EN.xhtml'
path.write_bytes(body)
print(celex, date, len(body), cellar, path)

#!/usr/bin/env python3
"""Build one self-contained HTML page using the same published JSON as the live view."""
import json
from pathlib import Path
from refresh import validate_market
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'public/data/market.json').read_text(encoding='utf-8'))
validate_market(data)
template=(ROOT/'web/template.html').read_text(encoding='utf-8')
seed=json.dumps(data,ensure_ascii=True).replace('<','\\u003c')
html=template.replace('__APP_CSS__',(ROOT/'web/app.css').read_text()).replace('__MARKET_SEED__',seed).replace('__APP_JS__',(ROOT/'web/app.js').read_text())
(ROOT/'public/index.html').write_text(html,encoding='utf-8')
print('Built public/index.html with',len(data['records']),'source records')

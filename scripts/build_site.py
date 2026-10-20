#!/usr/bin/env python3
"""Build one self-contained HTML page using the same published JSON as the live view."""
import base64
import json
from pathlib import Path
from refresh import validate_market
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'public/data/market.json').read_text(encoding='utf-8'))
validate_market(data)
template=(ROOT/'web/template.html').read_text(encoding='utf-8')
seed=json.dumps(data,ensure_ascii=True).replace('<','\\u003c')
css=(ROOT/'web/app.css').read_text(encoding='utf-8')
# Embed locally bundled fonts so exported HTML remains usable offline.
for weight in ('Regular','Medium','SemiBold','Bold'):
 name=f'IBMPlexSansArabic-{weight}.woff2'
 encoded=base64.b64encode((ROOT/'web/fonts'/name).read_bytes()).decode('ascii')
 css=css.replace(f"url('fonts/{name}')",f"url('data:font/woff2;base64,{encoded}')")
license_text=(ROOT/'web/fonts/OFL.txt').read_text(encoding='utf-8')
css='/* IBM Plex Sans Arabic — bundled font license\n'+license_text+'\n*/\n'+css
html=template.replace('__APP_CSS__',css).replace('__MARKET_SEED__',seed).replace('__APP_JS__',(ROOT/'web/app.js').read_text(encoding='utf-8'))
(ROOT/'public/index.html').write_text(html,encoding='utf-8')
print('Built public/index.html with',len(data['records']),'source records')

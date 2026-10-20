"""Verify that a built dashboard retains its data, Arabic copy, and offline fonts."""
import base64
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BuildTests(unittest.TestCase):
    def test_dashboard_is_self_contained_and_preserves_utf8_and_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'web', root / 'web')
            (root / 'scripts').mkdir()
            for name in ('refresh.py', 'build_site.py'):
                shutil.copy2(ROOT / 'scripts' / name, root / 'scripts' / name)
            (root / 'public/data').mkdir(parents=True)
            shutil.copy2(ROOT / 'data/curated.json', root / 'public/data/market.json')

            subprocess.run(
                [sys.executable, '-B', str(root / 'scripts/build_site.py')],
                check=True, capture_output=True,
            )
            html = (root / 'public/index.html').read_text(encoding='utf-8')
            seed = re.search(
                r'<script type="application/json" id="seed-data">(.*?)</script>',
                html, re.S,
            )
            self.assertIsNotNone(seed)
            self.assertEqual(
                json.loads(seed.group(1)),
                json.loads((ROOT / 'data/curated.json').read_text(encoding='utf-8')),
            )
            fonts = re.findall(r'data:font/woff2;base64,([A-Za-z0-9+/=]+)', html)
            self.assertEqual(len(fonts), 4)
            self.assertEqual(
                {base64.b64decode(font) for font in fonts},
                {font.read_bytes() for font in (ROOT / 'web/fonts').glob('*.woff2')},
            )
            self.assertNotIn("url('fonts/", html)
            self.assertIn("font-src data:", html)
            self.assertIn('Copyright © 2017 IBM Corp.', html)
            self.assertIn('SIL OPEN FONT LICENSE Version 1.1', html)
            self.assertIn('اعرف السوق. واعرف قيمة تخصصك.', html)
            self.assertNotIn('__APP_CSS__', html)
            self.assertNotIn('__APP_JS__', html)
            self.assertNotIn('__MARKET_SEED__', html)


if __name__ == '__main__':
    unittest.main()

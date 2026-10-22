"""Local preview must reuse the existing builder without overwriting publication data."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location('preview_filters', ROOT / 'scripts/preview_filters.py')
preview = module_from_spec(spec)
spec.loader.exec_module(preview)


class PreviewTests(unittest.TestCase):
    def test_build_preserves_public_snapshot_and_contains_only_real_input_records(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / 'web', root / 'web')
            (root / 'scripts').mkdir()
            for name in ('refresh.py', 'build_site.py'):
                shutil.copy2(ROOT / 'scripts' / name, root / 'scripts' / name)
            (root / 'public/data').mkdir(parents=True)
            original = (ROOT / 'public/data/market.json').read_bytes()
            (root / 'public/data/market.json').write_bytes(original)
            (root / 'public/index.html').write_text('unchanged publication sentinel', encoding='utf-8')
            output = preview.build_preview(root)
            page = (output / 'index.html').read_text(encoding='utf-8')
            self.assertIn('data-local-preview="true"', page)
            seed = re.search(r'id="seed-data">(.*?)</script>', page, re.S)
            self.assertIsNotNone(seed)
            self.assertEqual(json.loads(seed.group(1)), json.loads(original))
            self.assertEqual((output / 'data/market.json').read_bytes(), original)
            self.assertEqual((root / 'public/data/market.json').read_bytes(), original)
            self.assertEqual((root / 'public/index.html').read_text(encoding='utf-8'), 'unchanged publication sentinel')
            self.assertIn('دليل المسؤوليات', page)
            self.assertNotIn("url('fonts/", page)


if __name__ == '__main__':
    unittest.main()

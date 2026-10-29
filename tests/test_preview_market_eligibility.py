"""Only saved Development decisions are projected; publication and sources stay untouched."""
from pathlib import Path
from unittest.mock import patch
import copy
import importlib.util
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('preview_market_eligibility', ROOT / 'scripts/preview_market_eligibility.py')
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)
RESULTS = ROOT / 'learning-local/market-eligibility-20261029-0dfbb5469d/market-eligibility.json'


@unittest.skipUnless(RESULTS.exists(), 'Private original Development results are not installed')
class DevelopmentPreviewTests(unittest.TestCase):
    def test_ten_generated_decisions_are_capture_bound_and_separate_from_pay_and_occupation(self):
        before = RESULTS.read_bytes()
        data = preview.development_dataset(ROOT, RESULTS)
        result = json.loads(before)
        originals = {r['case_id']: r for r in result['capture_decisions'] if r['primary_indexed_capture']}
        self.assertEqual(len(data['records']), 10)
        self.assertEqual(sum(r['marketEligibility']['decision'] == 'Accept' for r in data['records']), 1)
        self.assertEqual(len(data['reviewQueue']), 9)
        for row in data['records']:
            self.assertEqual(row['marketEligibility'], originals[row['id']])
            self.assertNotIn('keReview', row)
            self.assertNotIn('salaryReview', row)
            self.assertFalse(row['salaryEligible'])
        accepted = next(r for r in data['records'] if r['marketEligibility']['decision'] == 'Accept')
        self.assertEqual(accepted['city'], 'Jeddah')
        self.assertEqual(accepted['country'], 'Saudi Arabia')
        self.assertIsNone(accepted['salaryMin'])
        self.assertEqual(accepted['locationVariants'][0]['location']['country'], 'Egypt')
        self.assertEqual(accepted['locationVariants'][0]['decision'], 'Reject')
        lever = next(r for r in data['records'] if r['id'] == 'EVAL-4847917fd586d111')
        self.assertEqual((lever['salaryMin'], lever['salaryMax'], lever['currency'], lever['period']),
                         (165000, 185000, 'USD', 'Annual'))
        self.assertEqual(lever['originalStructuredSalary']['salaryRange']['interval'], 'per-year-salary')
        self.assertEqual(RESULTS.read_bytes(), before)

    def test_decisions_are_read_from_saved_results_not_human_comparison_or_case_ids(self):
        result = json.loads(RESULTS.read_bytes())
        changed = copy.deepcopy(result)
        row = next(r for r in changed['capture_decisions'] if r['primary_indexed_capture'] and r['decision'] == 'Accept')
        row.update(decision='Reject', job_market_eligible=False, rule='S0', reason='Synthetic test: decision changed upstream.')
        real_loads = preview.transport.loads
        def loads(raw):
            return copy.deepcopy(changed) if raw == RESULTS.read_bytes() else real_loads(raw)
        with patch.object(preview.transport, 'loads', side_effect=loads):
            data = preview.development_dataset(ROOT, RESULTS)
        self.assertEqual(len(data['reviewQueue']), 10)
        self.assertEqual(sum(r['marketEligibility']['decision'] == 'Accept' for r in data['records']), 0)

    def test_non_development_paths_and_existing_output_are_rejected(self):
        with self.assertRaises((ValueError, preview.transport.TransportError)):
            preview.development_dataset(ROOT, ROOT / 'public/data/market.json')
        with self.assertRaises(preview.transport.TransportError):
            preview.build_development_preview(RESULTS, RESULTS.parent)

    def test_wrong_capture_binding_fails_before_source_projection(self):
        result = json.loads(RESULTS.read_bytes())
        changed = copy.deepcopy(result)
        changed['capture_decisions'][0]['capture_sha256'] = '0' * 64
        real_loads = preview.transport.loads
        with patch.object(preview.transport, 'loads', side_effect=lambda raw: copy.deepcopy(changed) if raw == RESULTS.read_bytes() else real_loads(raw)):
            with self.assertRaisesRegex(preview.transport.TransportError, 'primary indexed capture'):
                preview.development_dataset(ROOT, RESULTS)


if __name__ == '__main__':
    unittest.main()

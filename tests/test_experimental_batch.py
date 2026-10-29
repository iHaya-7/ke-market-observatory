"""Saved new-batch fidelity and preview integration; no network or new decisions written."""
import base64
from collections import Counter
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import preview_market_eligibility as preview
import process_experimental_batch as batch

RESULTS = ROOT / 'learning-local/market-new-batch-20261029/processed/market-eligibility.json'


@unittest.skipUnless(RESULTS.exists(), 'Private new batch is not installed')
class SavedBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(RESULTS.read_bytes())
        cls.rows = cls.report['capture_decisions']

    def capture(self, row):
        raw = (ROOT / row['source_capture']).read_bytes()
        artifact = dict(path=row['source_capture'], sha256=batch.transport.digest(raw),
                        bytes_base64=base64.b64encode(raw).decode())
        return json.loads(raw), artifact

    def test_saved_results_stay_historical_and_only_two_penta_decisions_change(self):
        self.assertEqual(len(self.rows), 9)
        self.assertNotEqual(self.report['eligibility_implementation_sha256'], batch.transport.digest(
            (ROOT / 'tools/source-transport-vnext/market_eligibility_vnext.py').read_bytes()))
        self.assertEqual(Counter(r['decision'] for r in self.rows), {'Accept': 3, 'Reject': 5, 'Unresolved': 1})
        self.assertIsNone(self.report['human_reference'])
        for row in self.rows:
            capture, artifact = self.capture(row)
            self.assertEqual(artifact['sha256'], row['capture_sha256'])
            current = batch.eligibility.decide(capture['record'], capture['sourceType'], artifact)
            for key, value in current.items():
                if row['source_job_id'] in ('CR/030769', 'CR/030774') and key in (
                        'decision', 'job_market_eligible', 'responsibility_support', 'reason', 'rule'):
                    continue
                self.assertEqual(row[key], value, (row['case_id'], key))
            if row['source_job_id'] in ('CR/030769', 'CR/030774'):
                self.assertEqual((current['decision'], current['rule']), ('Accept', 'S1'))
            self.assertFalse(current['salary_evaluated'])
            self.assertFalse(current['occupational_classification_used'])

    def test_raw_sources_and_each_projected_field_are_exact_and_preview_is_isolated(self):
        data = preview.development_dataset(ROOT, RESULTS)
        self.assertEqual(len(data['records']), 9)
        self.assertEqual(Counter(r['marketEligibility']['decision'] for r in data['records']),
                         {'Accept': 3, 'Reject': 5, 'Unresolved': 1})
        self.assertEqual(len(data['reviewQueue']), 5)
        self.assertFalse(data['meta']['automationActivated'])
        self.assertEqual(data['sources'], [])
        self.assertTrue(all(r['id'].startswith('NEW-') for r in data['records']))
        self.assertTrue(all(r['salaryEligible'] is False and 'keReview' not in r and 'salaryReview' not in r
                            for r in data['records']))
        self.assertEqual(data['fx'], json.loads((ROOT / 'public/data/market.json').read_bytes())['fx'])

    def test_nothing_reuses_original_development_or_existing_public_postings(self):
        import refresh
        identities, urls = batch.known_postings(ROOT)
        for row in self.rows:
            self.assertNotIn((row['source_id'], row['source_job_id']), identities)
            self.assertNotIn(refresh.canonical(row['source_url']), urls)
            identities.add((row['source_id'], row['source_job_id']))
            urls.add(refresh.canonical(row['source_url']))

    def test_penta_coordinated_verbs_are_supported_without_rewriting_evidence(self):
        row = next(r for r in self.rows if r['source_job_id'] == 'CR/030769')
        capture, artifact = self.capture(row)
        packet = batch.eligibility.source_projection(capture['record'], capture['sourceType'], artifact)
        docs = batch.eligibility.consumer.document_views(packet)
        duties = batch.eligibility.consumer.extract_responsibilities(packet, docs)
        duty = next(d for d in duties if d['text'].startswith('Design, develop, and maintain Semantic Layer'))
        self.assertEqual(batch.eligibility.consumer.resolve_evidence(packet, duty['locator']), duty['text'])
        self.assertIsNotNone(batch.eligibility.DIRECT.match(duty['text']))
        self.assertEqual((row['decision'], row['rule'], row['location']['country']), ('Reject', 'S0', 'Saudi Arabia'))

    def test_penta_paragraph_bullets_are_handled_only_in_saudi_market_detection(self):
        row = next(r for r in self.rows if r['source_job_id'] == 'CR/030774')
        capture, artifact = self.capture(row)
        packet = batch.eligibility.source_projection(capture['record'], capture['sourceType'], artifact)
        docs = batch.eligibility.consumer.document_views(packet)
        self.assertIn('\u2022 Design Semantic and Data Mart layers from scratch', docs[0]['text'])
        self.assertEqual(batch.eligibility.consumer.extract_responsibilities(packet, docs), [])
        self.assertIsNotNone(batch.eligibility.DIRECT.match('Design Semantic and Data Mart layers from scratch.'))
        support = batch.eligibility.saudi_support(capture['record'], capture['sourceType'], artifact)
        self.assertEqual(len(support), 3)
        for evidence in support:
            self.assertEqual(batch.eligibility.consumer.resolve_evidence(packet, evidence['locator']), evidence['matched_clause'])
        self.assertEqual((row['decision'], row['rule']), ('Reject', 'S0'))

    def test_unknown_location_stays_unresolved_and_is_not_a_rejection(self):
        row = next(r for r in self.rows if r['source_job_id'] == 'CR/030761')
        capture, _ = self.capture(row)
        self.assertEqual(capture['originalRecord']['jobLocation']['address']['addressCountry'], '')
        self.assertIsNone(row['location']['country'])
        self.assertIsNone(row['job_market_eligible'])
        self.assertEqual((row['decision'], row['rule']), ('Unresolved', 'L0'))

    def test_original_batch_and_new_outputs_refuse_overwrite(self):
        with self.assertRaisesRegex(batch.transport.TransportError, 'no overwrites'):
            batch.process(ROOT / self.report['selection_path'])
        with self.assertRaisesRegex(batch.transport.TransportError, 'no overwrites'):
            preview.build_development_preview(RESULTS, RESULTS.parent)
        with self.assertRaisesRegex(batch.transport.TransportError, 'no overwrites'):
            batch.rerun_saved(RESULTS, RESULTS.parent)


class SourceProjectionTests(unittest.TestCase):
    def test_sourceflow_preserves_exact_html_span_with_unicode_and_nested_fields(self):
        ld = dict({'@type': 'JobPosting'}, title='Synthetic test only', description='Flattened text',
                  jobLocation={'address': {'addressCountry': 'SA', 'addressLocality': 'Riyadh'}})
        body = ('<html>\n<script type="application/ld+json">' + json.dumps(ld) + '</script>\n'
                '<div data-sourceflow-prop="content"><p>Responsibilities</p><ul><li>Maintain '
                'semantic models &amp; constraints — اختبار.</li></ul></div></html>').encode()
        record, mapping, original = batch.project({'format': 'sourceflow'}, body)
        span = mapping['html_fields']['description']
        self.assertEqual(body.decode()[span['start']:span['end']], record['description'])
        self.assertIn('&amp;', record['description'])
        self.assertEqual(original['description'], 'Flattened text')
        self.assertEqual(record['country'], 'SA')

    def test_modified_source_is_rejected_before_projection(self):
        if not RESULTS.exists(): self.skipTest('Private new batch is not installed')
        report = json.loads(RESULTS.read_bytes())
        target = ROOT / report['capture_decisions'][0]['source_capture']
        real_read = Path.read_bytes
        def read(path):
            return b'{}' if path == target else real_read(path)
        with patch.object(Path, 'read_bytes', read):
            with self.assertRaisesRegex(batch.transport.TransportError, 'hash mismatch'):
                preview.development_dataset(ROOT, RESULTS)


CORRECTED = ROOT / 'learning-local/saudi-s1-fix-20261029/results/market-eligibility.json'


@unittest.skipUnless(CORRECTED.exists(), 'Private corrected batch is not installed')
class CorrectedBatchTests(unittest.TestCase):
    def test_rerun_uses_same_captures_with_only_two_decision_changes(self):
        old = json.loads(RESULTS.read_bytes())
        new = json.loads(CORRECTED.read_bytes())
        self.assertEqual(new['previous_results_sha256'], batch.transport.digest(RESULTS.read_bytes()))
        self.assertEqual(new['responsibility_detection_version'], batch.eligibility.S1_IMPLEMENTATION_VERSION)
        self.assertEqual(new['eligibility_implementation_sha256'], batch.transport.digest(
            (ROOT / 'tools/source-transport-vnext/market_eligibility_vnext.py').read_bytes()))
        self.assertEqual(Counter(r['decision'] for r in new['capture_decisions']), {'Accept': 5, 'Reject': 3, 'Unresolved': 1})
        changed = []
        for before, after in zip(old['capture_decisions'], new['capture_decisions']):
            for key in ('case_id', 'source_capture', 'capture_sha256', 'source_url', 'location', 'salary_availability'):
                self.assertEqual(before[key], after[key])
            raw = (ROOT / after['source_capture']).read_bytes()
            capture = json.loads(raw)
            artifact = dict(path=after['source_capture'], sha256=batch.transport.digest(raw),
                            bytes_base64=base64.b64encode(raw).decode())
            current = batch.eligibility.decide(capture['record'], capture['sourceType'], artifact)
            for key, value in current.items(): self.assertEqual(after[key], value)
            if before['decision'] != after['decision']: changed.append(after['source_job_id'])
            self.assertFalse(after['salary_evaluated'])
        self.assertEqual(set(changed), {'CR/030769', 'CR/030774'})
        self.assertEqual(len(preview.development_dataset(ROOT, CORRECTED)['records']), 9)

    def test_user_judgments_are_nonblind_and_separate_from_machine_predictions(self):
        user = json.loads((CORRECTED.parent.parent / 'user-eligibility-judgments.json').read_bytes())
        machine = json.loads(CORRECTED.read_bytes())
        self.assertEqual(user['review_method'], 'user-provided, non-blind')
        self.assertFalse(user['independently_blinded']); self.assertFalse(user['occupational_labels'])
        self.assertIsNone(machine['human_reference'])
        self.assertEqual(len(user['decisions']), 2)
        by_id = {r['case_id']: r for r in machine['capture_decisions']}
        for h in user['decisions']:
            r = by_id[h['case_id']]
            self.assertEqual((h['capture_sha256'], h['country'], h['decision']),
                             (r['capture_sha256'], r['location']['country'], r['decision']))
            self.assertNotIn('human_market_eligibility', r)


if __name__ == '__main__':
    unittest.main()

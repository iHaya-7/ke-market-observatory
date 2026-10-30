"""Integration checks use only the explicitly supplied private Development batch."""
import base64
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest

import transport_vnext as t
sys.path.insert(0, str(t.ROOT / 'scripts'))
import process_experimental_workflow as workflow


class PreviewBindingTests(unittest.TestCase):
    def test_missing_template_fails_closed(self):
        with self.assertRaises(t.TransportError):
            workflow.workflow_app('unexpected template')

    def test_local_binding_uses_generated_decisions(self):
        result = workflow.workflow_app((t.ROOT / 'web/app.js').read_text(encoding='utf-8'))
        self.assertIn('r.occupationalAssessment?.proposed_classification', result)
        self.assertNotIn('Occupational classification: not assessed in this preview.', result)
        self.assertIn('Production approval: not granted', result)


@unittest.skipUnless(os.environ.get('STAGE7_WORKFLOW_SOURCE_ROOT'), 'Explicit private Development fixture root required')
class AuthenticBatchIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(os.environ['STAGE7_WORKFLOW_SOURCE_ROOT'])
        cls.temp = tempfile.TemporaryDirectory(prefix='workflow-test-', dir=t.ROOT / 'learning-local')
        cls.output = Path(cls.temp.name) / 'output'
        cls.report = workflow.run(root / 'learning-local/saudi-s1-fix-20261029/results/market-eligibility.json', cls.output, root)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_separate_decisions_and_original_geographic_outcomes(self):
        rows = self.report['results']
        self.assertEqual(len(rows), 9)
        self.assertEqual(sum(r['market_eligibility']['decision'] == 'Accept' for r in rows), 5)
        self.assertEqual(sum(r['market_eligibility']['decision'] == 'Reject' for r in rows), 3)
        self.assertEqual(sum(r['market_eligibility']['decision'] == 'Unresolved' for r in rows), 1)
        for row in rows:
            self.assertIsNone(row['production_approval'])
            self.assertFalse(any(row['occupational_assessment']['human_ground_truth'].values()))
        self.assertIsNone(self.report['evaluation_metrics'])

    def test_rdf_roundtrip_and_evidence_resolution(self):
        passed = [r for r in self.report['results'] if r['execution'] == 'PASS']
        self.assertEqual(len(passed), 9)
        for row in passed:
            self.assertTrue(row['validation']['experimental_shacl_conforms'])
            self.assertTrue(row['validation']['source_fidelity_passed'])
            self.assertGreater(row['validation']['resolved_evidence_passages'], 0)

    def test_s1_evidence_reaches_rdf_and_occupational_input_without_promotion(self):
        found = 0
        for result in self.report['results']:
            if result['market_eligibility']['rule'] != 'S1':
                continue
            considered = result['occupational_assessment']['evidence_considered']
            for support in result['market_eligibility']['responsibility_support']:
                loc = support['locator']
                matching = [r for r in considered if
                            (e := t.loads(r['evidence_locator_json']))['source'] == loc['source']
                            and e['start'] <= loc['start'] < loc['end'] <= e['end']]
                self.assertTrue(matching, 'Existing S1 passage was dropped before occupational assessment')
                found += 1
        self.assertGreater(found, 0)

    def test_one_corrupt_capture_does_not_block_a_valid_record(self):
        root = Path(os.environ['STAGE7_WORKFLOW_SOURCE_ROOT'])
        report = t.loads((root / 'learning-local/saudi-s1-fix-20261029/results/market-eligibility.json').read_bytes())
        report['capture_decisions'] = report['capture_decisions'][:2]
        report['capture_decisions'][0]['capture_sha256'] = '0' * 64
        with tempfile.TemporaryDirectory(prefix='workflow-invalid-', dir=root / 'learning-local') as tmp:
            path = Path(tmp) / 'input.json'
            path.write_text(t.canonical(report), encoding='utf-8')
            result = workflow.run(path, Path(self.temp.name) / 'isolated-failure', root)
        self.assertEqual([r['execution'] for r in result['results']], ['BLOCKED', 'PASS'])
        self.assertIsNone(result['results'][0]['market_eligibility'])
        self.assertIsNone(result['results'][0]['occupational_assessment'])
        dataset = t.loads((Path(self.temp.name) / 'isolated-failure/preview/data/market.json').read_bytes())
        self.assertEqual(len(dataset['records']), 1)
        self.assertEqual(len(dataset['processingFailures']), 1)

    def test_provider_body_resolves_to_original_structured_field(self):
        rows = [r for r in self.report['results'] if '/originalRecord/jobAd/sections/jobDescription/text' in r['graph_field_references'].values()]
        self.assertEqual(len(rows), 1)
        packet = t.loads((self.output / rows[0]['case_id'] / 'packet.json').read_bytes())
        ref = t.reference(packet, '/description')
        self.assertEqual(t.resolve_reference(packet, ref), packet['record']['description'])
        self.assertIn('qualifications', packet['unconsumed_source_sections'])
        self.assertEqual(rows[0]['market_eligibility']['decision'], 'Accept')

    def test_source_and_response_tampering_rejected(self):
        packet = t.loads(next(self.output.glob('NEW-*/packet.json')).read_bytes())
        for target in ('record', 'response', 'identity', 'timestamp'):
            changed = copy.deepcopy(packet)
            if target == 'record': changed['record']['title'] += ' changed'
            elif target == 'response': changed['response_bytes_base64'] = base64.b64encode(b'{}').decode()
            elif target == 'identity': changed['identity']['source_url'] += '/changed'
            else: changed['batch_spec']['retrieved_at_utc'] = '2000-01-01T00:00:00Z'
            with self.subTest(target=target), self.assertRaises(t.TransportError):
                t.verify_packet(changed)

    def test_preview_contains_actual_separate_results(self):
        dataset = t.loads((self.output / 'preview/data/market.json').read_bytes())
        self.assertFalse(dataset['meta']['automationActivated'])
        self.assertEqual(len(dataset['records']), 9)
        for row, result in zip(dataset['records'], self.report['results']):
            self.assertEqual(row['collection'], 'development-preview')
            self.assertEqual(row['occupationalAssessment'], result['occupational_assessment'])
            self.assertEqual(row['salaryAssessment'], result['salary_assessment'])
            self.assertEqual(row['marketEligibility']['decision'], result['market_eligibility']['decision'])

    def test_rerun_cannot_overwrite_outputs(self):
        root = Path(os.environ['STAGE7_WORKFLOW_SOURCE_ROOT'])
        with self.assertRaisesRegex(t.TransportError, 'Fresh output required'):
            workflow.run(root / 'learning-local/saudi-s1-fix-20261029/results/market-eligibility.json', self.output, root)


if __name__ == '__main__':
    unittest.main()

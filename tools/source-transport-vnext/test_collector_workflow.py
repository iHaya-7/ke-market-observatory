"""Collector boundary checks using an explicitly installed authentic saved response."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import transport_vnext as t
import sys
sys.path.insert(0, str(t.ROOT / 'scripts'))
import collect_observatory as collector


@unittest.skipUnless(os.environ.get('STAGE7_COLLECTOR_RESPONSES'), 'Explicit saved collector response manifest required')
class CollectorWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(dir=t.ROOT / 'learning-local')
        cls.state = Path(cls.directory.name) / 'state'
        cls.manifest = Path(os.environ['STAGE7_COLLECTOR_RESPONSES']).resolve()
        with patch.object(collector.refresh, 'fetch_json', side_effect=AssertionError('Network forbidden')):
            cls.first = collector.collect(cls.state, saved=cls.manifest)
        cls.initial = t.loads((cls.state / 'state.json').read_bytes())

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def test_authentic_collector_record_reaches_rdf_review_and_frontend(self):
        candidate, = self.initial['candidates'].values()
        self.assertEqual(candidate['result']['execution'], 'PASS')
        self.assertTrue(candidate['result']['validation']['experimental_shacl_conforms'])
        self.assertTrue(candidate['result']['validation']['source_fidelity_passed'])
        dataset = t.loads((self.first / 'preview/data/market.json').read_bytes())
        row, = dataset['records']
        self.assertEqual(row['title'], 'Graph Engineer')
        self.assertEqual(row['marketEligibility']['decision'], 'Reject')
        self.assertEqual(row['operationalReview']['status'], 'Pending human review')
        self.assertIsNone(row['operationalReview']['productionApproval'])
        self.assertEqual(len(dataset['reviewQueue']), 1)
        self.assertIn('operationalReview', (self.first / 'preview/index.html').read_text(encoding='utf-8'))

    def test_repeat_reuses_evidence_without_duplicate_rows(self):
        with patch.object(collector.workflow, 'run', side_effect=AssertionError('Unchanged evidence must not rerun')):
            output = collector.collect(self.state, saved=self.manifest)
        after = t.loads((self.state / 'state.json').read_bytes())
        self.assertEqual(after, self.initial)
        self.assertEqual(t.loads((output / 'run.json').read_bytes())['outcomes'][0]['status'], 'Unchanged')

    def test_failed_source_preserves_previous_candidate(self):
        with patch.object(collector.refresh, 'get_board', side_effect=OSError('Unit-test source failure')):
            output = collector.collect(self.state, saved=self.manifest)
        self.assertEqual(t.loads((self.state / 'state.json').read_bytes()), self.initial)
        self.assertIn('Failed', t.loads((output / 'run.json').read_bytes())['sourceHealth'][0]['status'])

    def test_revision_bound_reviews_survive_but_do_not_approve_publication(self):
        key, = self.initial['candidates']
        revision = self.initial['candidates'][key]['revision']
        # Synthetic review-state control, never a human decision or evaluation output.
        reviews = {key: {revision: {'testOnly': True, 'note': 'Review pending'}}}
        path = self.state / 'review-decisions.json'
        path.write_text(t.canonical(reviews), encoding='utf-8')
        before = path.read_bytes()
        output = collector.collect(self.state, saved=self.manifest)
        self.assertEqual(path.read_bytes(), before)
        row, = t.loads((output / 'preview/data/market.json').read_bytes())['records']
        self.assertEqual(row['operationalReview']['decision'], reviews[key][revision])
        self.assertIsNone(row['operationalReview']['productionApproval'])

    def test_changed_revision_keeps_history_and_old_review_separate(self):
        state = self.state.parent / 'changed-state'
        state.mkdir()
        prior = copy.deepcopy(self.initial)
        key, = prior['candidates']
        prior['candidates'][key]['revision'] = 'unit-test-prior-revision'
        (state / 'state.json').write_text(t.canonical(prior), encoding='utf-8')
        reviews = {key: {'unit-test-prior-revision': {'testOnly': True}}}
        (state / 'review-decisions.json').write_text(t.canonical(reviews), encoding='utf-8')
        output = collector.collect(state, saved=self.manifest)
        row, = t.loads((output / 'preview/data/market.json').read_bytes())['records']
        self.assertEqual(row['operationalReview']['status'], 'Pending human review')
        after = t.loads((state / 'state.json').read_bytes())['candidates'][key]
        self.assertEqual(after['history'][-1]['revision'], 'unit-test-prior-revision')
        self.assertTrue((t.ROOT / after['history'][-1]['artifact']).exists())

    def test_concurrent_run_refuses_before_state_changes(self):
        lock = self.state / 'run.lock'
        lock.write_text('test lock', encoding='utf-8')
        try:
            with self.assertRaises(FileExistsError):
                collector.collect(self.state, saved=self.manifest)
        finally:
            lock.unlink()

    def test_untraceable_merged_fields_fail_without_replacing_prior_evidence(self):
        original = collector.refresh.get_board
        def changed(*args, **kwargs):
            jobs, warnings = original(*args, **kwargs)
            # Deliberately unsupported synthetic merge, confined to this test.
            for job in jobs: job['unit_test_untraceable_field'] = True
            return jobs, warnings
        with patch.object(collector.refresh, 'get_board', side_effect=changed):
            output = collector.collect(self.state, saved=self.manifest)
        report = t.loads((output / 'run.json').read_bytes())
        self.assertIn('single exact source record', report['failures'][0]['blocker'])
        state = t.loads((self.state / 'state.json').read_bytes())
        key, = state['candidates']
        self.assertEqual(state['candidates'][key]['revision'], self.initial['candidates'][key]['revision'])
        self.assertIn('lastProcessingError', state['candidates'][key])

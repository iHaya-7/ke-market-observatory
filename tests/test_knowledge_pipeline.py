"""Behavior and traceability controls; synthetic evidence is not human ground truth."""
import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'knowledge-engineering/05-knowledge-graph'))
sys.path.insert(0, os.environ.get('KE_LOCAL_DEPS', str(ROOT / 'learning-local/stage6-deps')))
import posting_evidence as evidence


def fixture(duties='', pay='', title='Engineer', heading='Responsibilities'):
    raw = (f'<html><head><meta property="og:title" content="{title}"></head>'
           f'<body><h1>{title}</h1><h2>{heading}</h2>{duties}<h2>Requirements</h2>'
           '<p>Experience with OWL and knowledge graphs preferred.</p>'
           f'<h2>Compensation</h2>{pay}</body></html>').encode()
    entry = {'candidate_id': 'SYNTHETIC', 'requested_url': 'https://example.org/jobs/123',
             'upstream_job_id': '123', 'employer': 'Example', 'job_title': title,
             'captured_utc': '2026-10-26T12:00:00+00:00', 'snapshot_file': 'originals/example.html'}
    item = evidence.extract(raw, entry)
    item['archive'] = str(ROOT / 'learning-local/synthetic.zip')
    return raw, item


class ExtractionTests(unittest.TestCase):
    def test_explicit_knowledge_representation_action(self):
        _, item = fixture('<p>Design ontologies for computational reasoning.</p>')
        self.assertIsNotNone(item['responsibilities'][0]['mapping'])

    def test_non_duties_never_support_mapping(self):
        _, item = fixture('<p>Develop machine learning training systems.</p>')
        self.assertFalse(any(d['mapping'] for d in item['responsibilities']))

    def test_negated_and_incidental_representation_mentions(self):
        for text in ['Build presentations about knowledge graphs.', 'Build backend features in the Knowledge Graph service.',
                     'Do not design ontologies.', 'Design pipelines; our company builds knowledge graphs.',
                     'Design training materials about ontologies.', 'Build products that use knowledge graphs.']:
            with self.subTest(text=text):
                self.assertIsNone(evidence.interpret_duty(text))

    def test_exact_trace_resolution_with_unicode_and_entities(self):
        raw, item = fixture('<p>Design ontologies &amp; relationships — for reasoning.</p>')
        for p in item['passages']:
            self.assertEqual(evidence.resolve_html(raw, p['locator']), p['text'])
        bad = dict(item['passages'][0]['locator'], end=100000)
        with self.assertRaises(ValueError):
            evidence.resolve_html(raw, bad)

    def test_unknown_section_does_not_prove_negative_scope(self):
        _, item = fixture('<p>Design ontologies.</p>', heading='Overview')
        self.assertEqual(item['responsibility_coverage'], 'responsibilities unresolved')
        self.assertEqual(item['responsibilities'], [])

    def test_original_pay_units_retained(self):
        _, item = fixture(pay='<p>The US base salary range for this role is USD 120,000 - 144,000 per year.</p>')
        salary = item['salaries'][0]
        self.assertEqual((salary['lowerAmount'], salary['upperAmount'], salary['currency'], salary['payPeriod'], salary['compensationBasis']),
                         (120000, 144000, 'USD', 'Annual', 'base'))

    def test_period_not_inferred_from_large_amount_or_annual_benefits(self):
        _, item = fixture(pay='<p>Annual leave and training.</p><p>Benefits details.</p><p>Base Salary: $204,000 - $216,000 plus equity.</p>')
        self.assertIsNone(item['salaries'][0]['payPeriod'])
        self.assertIsNone(item['salaries'][0]['currency'])
        _, item = fixture(pay='<p>Base salary USD 100,000 - 120,000 plus annual bonus.</p>')
        self.assertIsNone(item['salaries'][0]['payPeriod'])

    def test_funding_and_no_salary_not_pay_observations(self):
        _, item = fixture(pay='<p>Raised $100,000 - $200,000 funding.</p><p>Discretionary bonus and benefits.</p>')
        self.assertEqual(item['salaries'], [])

    def test_multiple_bands_kept_independent(self):
        _, item = fixture(pay='<p>Annual base salary USD 100,000 - 120,000.</p><p>Monthly base pay SAR 20,000 - 25,000.</p>')
        self.assertEqual(len(item['salaries']), 2)
        self.assertEqual(item['salaries'][0]['payPeriod'], 'Annual')
        self.assertEqual(item['salaries'][1]['payPeriod'], 'Monthly')

    def test_market_not_transferred_to_another_band(self):
        _, item = fixture(pay='<p>The US base salary range is USD 100,000 - 120,000 annually.</p><p>Base salary CAD 90,000 - 110,000 annually.</p>')
        self.assertIsNone(item['salaries'][1]['payMarket'])

    def test_source_alias_preserves_job_identity(self):
        self.assertEqual(evidence.source_identity('https://boards.greenhouse.io/x/jobs/123?gh_jid=123'),
                         evidence.source_identity('https://job-boards.greenhouse.io/x/jobs/123'))
        with self.assertRaises(ValueError):
            evidence.source_identity('https://boards.greenhouse.io/x/jobs/123?gh_jid=456')


try:
    from rdflib import Graph, Literal
    from rdflib.namespace import RDF, XSD, DCTERMS
    import pyshacl
    spec = importlib.util.spec_from_file_location('ke_pilot_test', ROOT / 'knowledge-engineering/07-evaluation/ke_decision_pilot.py')
    pilot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pilot)
    builder, KE = pilot.validation.builder, pilot.KE
    HAS_RDF = True
except ImportError:
    HAS_RDF = False


@unittest.skipUnless(HAS_RDF, 'Install the existing requirements-local.txt into learning-local/stage6-deps for KG controls')
class DecisionTests(unittest.TestCase):
    def decide(self, duties='', pay='', title='Engineer', heading='Responsibilities'):
        _, item = fixture(duties, pay, title, heading)
        graph, *_ = builder.build_postings([item])
        return pilot.assess_captured(graph)[0], graph

    def test_generic_title_with_core_duties_and_trace(self):
        case, graph = self.decide('<p>Design and maintain ontologies for machine reasoning.</p>', title='Data Engineer')
        self.assertEqual(case['occupational_classification'], 'Core KE')
        self.assertTrue(case['responsibility_evidence'][0]['mapped_to_representation'])
        self.assertTrue(list(graph.triples((None, KE.actsOnRepresentation, None))))
        for decision in case['machine_decisions']:
            self.assertTrue(decision['evidence'])

    def test_title_invariance_and_misleading_core_title(self):
        for title in ('Knowledge Engineer', 'Research Engineer, Knowledge Graph Intelligence', 'Analyst'):
            case, _ = self.decide('<p>Develop machine learning models for text classification.</p>', title=title)
            self.assertEqual(case['occupational_classification'], 'Outside Scope')

    def test_adjacent_graph_platform_with_boundary_question(self):
        case, _ = self.decide('<p>Implement backend features and API endpoints in the Knowledge Graph service.</p>')
        self.assertEqual(case['occupational_classification'], 'Adjacent technical')
        self.assertTrue(case['missing_information'])

    def test_missing_and_ambiguous_duties_abstain(self):
        for duties in ('', '<p>Work on exciting ideas.</p>', '<p>Design knowledge graphs, maybe in future.</p>'):
            case, _ = self.decide(duties, title='Knowledge Engineer')
            self.assertEqual(case['occupational_classification'], 'Insufficient Evidence')
            self.assertTrue(case['human_review_needed'])

    def test_salary_positive_despite_outside_occupation(self):
        case, _ = self.decide('<p>Develop machine learning infrastructure.</p>', '<p>The US base salary range is USD 120,000 - 144,000 annually.</p>')
        self.assertEqual(case['salary_evidence_status'], 'Eligible')
        self.assertEqual(case['machine_recommendation'], 'Not admitted: occupational scope')
        self.assertFalse(case['approved'])

    def test_core_occupation_does_not_supply_salary(self):
        case, _ = self.decide('<p>Design ontologies for reasoning.</p>')
        self.assertEqual(case['occupational_classification'], 'Core KE')
        self.assertEqual(case['salary_evidence_status'], 'No disclosed numeric salary')

    def test_monthly_sar_base_salary(self):
        case, _ = self.decide('<p>Design ontologies for reasoning.</p>', pay='<p>The Saudi Arabia base salary range is SAR 20,000 - 25,000 per month.</p>')
        self.assertEqual(case['salary_evidence_status'], 'Eligible')
        self.assertEqual(case['salary_observations'][0]['original']['payPeriod'], 'Monthly')
        self.assertIn('domestic', case['machine_recommendation'])

    def test_unparsed_representation_duty_prevents_negative_scope(self):
        case, _ = self.decide('<p>Develop machine learning models.</p><p>Curate ontologies for reasoning.</p>')
        self.assertEqual(case['occupational_classification'], 'Insufficient Evidence')

    def test_missing_salary_dimensions_abstain(self):
        for pay, gap in [('<p>Base salary USD 120,000 - 144,000.</p>', 'payPeriod'),
                         ('<p>Annual salary USD 120,000 - 144,000.</p>', 'compensationBasis'),
                         ('<p>Annual base salary $120,000 - $144,000.</p>', 'currency'),
                         ('<p>Annual base salary USD 120,000 - 144,000.</p>', 'payMarket')]:
            with self.subTest(gap=gap):
                case, _ = self.decide(pay=pay)
                self.assertEqual(case['salary_evidence_status'], 'Insufficient Evidence')
                self.assertIn(gap, case['missing_information'])

    def test_original_total_compensation_not_base(self):
        case, _ = self.decide(pay='<p>Annual total compensation USD 120,000 - 144,000.</p>')
        self.assertEqual(case['salary_evidence_status'], 'Ineligible')

    def test_negative_trace_controls_on_actual_captures(self):
        archive = ROOT / 'knowledge-engineering/00-baseline/local-corpus/development-v2/Development_v2_Source_Captures.zip'
        if not archive.exists():
            self.skipTest('Private Development v2 captures not present')
        graph, *_ = builder.build_postings(evidence.load_captures(archive))
        checks = pilot.validation.validate_captures(graph, archive)
        self.assertEqual(checks['artifacts'], 8)
        self.assertTrue(checks['shacl_conforms'])
        cases = pilot.assess_captured(graph)
        self.assertEqual(len(cases), 8)
        self.assertTrue(all(c['human_review_needed'] and not c['approved'] and not c['published'] for c in cases))
        # Source-backed regression, not an accuracy claim: title and compensation
        # decisions must be independent, including an occupational negative.
        by_id = {c['case_id']: c for c in cases}
        self.assertEqual(by_id['DEV2-007']['occupational_classification'], 'Outside Scope')
        self.assertEqual(by_id['DEV2-007']['salary_evidence_status'], 'Eligible')
        self.assertIn('currency', by_id['DEV2-002']['missing_information'])
        for predicate, replacement in [(KE.passageText, Literal('altered', datatype=XSD.string)),
                                       (KE.passageLocator, Literal('{}', datatype=XSD.string))]:
            mutated = Graph() + graph
            passage = next(mutated.subjects(RDF.type, KE.EvidencePassage))
            mutated.set((passage, predicate, replacement))
            with self.assertRaises(ValueError):
                pilot.validation.validate_captures(mutated, archive)


if __name__ == '__main__':
    unittest.main()

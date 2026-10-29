"""Authoritative geographic scope tests; human reference is non-blind eligibility."""
import base64
import copy
import json
import os
from pathlib import Path
import unittest

import market_eligibility_vnext as market
import transport_vnext as transport


def posting(title='Senior Data Engineer', country='Saudi Arabia', body='<h2>Responsibilities</h2><p>Build ordinary data pipelines.</p>', **extra):
    record = {'title': title, 'id': '123', 'shortcode': '123', 'url': 'https://example.test/jobs/123',
              'country': country, 'city': 'Jeddah' if country == 'Saudi Arabia' else 'Cairo', 'description': body}
    record.update(extra)
    raw = json.dumps({'sourceId': 'synthetic', 'sourceJobId': '123', 'record': record}).encode()
    artifact = {'path': 'synthetic-original.json', 'sha256': transport.digest(raw),
                'bytes_base64': base64.b64encode(raw).decode()}
    return record, artifact


def decide(**kwargs):
    record, artifact = posting(**kwargs)
    return market.decide(record, 'workable', artifact)


class GeographicScopeTests(unittest.TestCase):
    def test_global_explicit_ke_professions_and_seniority_variants(self):
        for title in market.TITLE_FAMILIES:
            for variant in (title, 'Senior ' + title, title + ' - Remote', title + ' II'):
                with self.subTest(title=variant):
                    self.assertTrue(decide(title=variant, country='United States')['job_market_eligible'])

    def test_global_generic_titles_rejected_even_with_direct_ontology_work(self):
        body = '<h2>Responsibilities</h2><p>Own ontologies and knowledge graphs.</p>'
        for title in ('AI Engineer', 'Senior Data Engineer', 'Software Engineer', 'Principal AI Systems Architect',
                      'Data Architect - Knowledge Graphs', 'Knowledge Graph Platform Software Engineer'):
            with self.subTest(title=title):
                result = decide(title=title, country='United States', body=body)
                self.assertFalse(result['job_market_eligible']); self.assertEqual(result['rule'], 'G1')

    def test_saudi_broader_titles_require_actual_substantive_work(self):
        for action in ('Design ontologies.', 'Build knowledge graphs.', 'Implement semantic layers.',
                       'Curate controlled vocabularies.', 'Govern taxonomies.', 'Model semantic models.'):
            with self.subTest(action=action):
                result = decide(body='<h2>Responsibilities</h2><p>' + action + '</p>')
                self.assertTrue(result['job_market_eligible']); self.assertEqual(result['rule'], 'S1')
                self.assertTrue(result['responsibility_support'])

    def test_saudi_title_alone_or_generic_ai_data_work_does_not_qualify(self):
        for title in ('Ontology Engineer', 'Senior Data Engineer', 'AI Architect'):
            self.assertFalse(decide(title=title)['job_market_eligible'])

    def test_qualification_company_mentions_and_sales_are_not_substantive_duties(self):
        for body in ('<p>Our company uses knowledge graphs.</p><h2>Responsibilities</h2><p>Build ordinary pipelines.</p>',
                     '<h2>Requirements</h2><p>Design ontologies in previous roles.</p>',
                     '<h2>Responsibilities</h2><p>Support sales presentations about knowledge graphs.</p>',
                     '<h2>Responsibilities</h2><p>Do not build ontologies.</p>'):
            with self.subTest(body=body): self.assertFalse(decide(body=body)['job_market_eligible'])

    def test_semantic_pipeline_requires_explicit_role_context_and_duty_connection(self):
        context = '<p>This role builds a data layer that will support knowledge graph and ontology systems.</p>'
        duty = '<h2>Responsibilities</h2><p>Build ingestion frameworks to feed semantic reasoning engines.</p>'
        supported = decide(body=context + duty)
        self.assertTrue(supported['job_market_eligible']); self.assertEqual(supported['rule'], 'S2')
        self.assertTrue(supported['responsibility_support'][0]['role_context'])
        self.assertFalse(decide(body=duty)['job_market_eligible'])
        self.assertFalse(decide(body=context + duty.replace('semantic reasoning engines', 'AI models'))['job_market_eligible'])

    def test_location_is_capture_specific_even_when_title_mentions_ksa(self):
        context = '<p>This role will support knowledge graph systems.</p>'
        body = context + '<h2>Responsibilities</h2><p>Build ingestion frameworks to feed semantic reasoning engines.</p>'
        saudi = decide(title='Senior Data Engineer - KSA', country='Saudi Arabia', body=body)
        egypt = decide(title='Senior Data Engineer - KSA', country='Egypt', body=body)
        self.assertTrue(saudi['job_market_eligible']); self.assertFalse(egypt['job_market_eligible'])
        self.assertEqual(egypt['location']['country'], 'Egypt'); self.assertEqual(egypt['rule'], 'G1')

    def test_missing_or_conflicting_country_cannot_default_to_global(self):
        for country in ('', None, 'unknown', 'Remote'):
            result = decide(title='Knowledge Graph Engineer', country=country)
            self.assertIsNone(result['job_market_eligible']); self.assertEqual(result['rule'], 'L0')
        result = decide(title='Knowledge Graph Engineer', locations=[{'country': 'Egypt', 'countryCode': 'EG'}])
        self.assertIsNone(result['job_market_eligible']); self.assertTrue(result['location']['conflict'])

    def test_posting_location_only_not_description_travel_or_title(self):
        result = decide(title='Senior Data Engineer - Riyadh KSA', country='Egypt',
                        body='<p>Travel to Saudi Arabia.</p><h2>Responsibilities</h2><p>Build ontologies.</p>')
        self.assertFalse(result['job_market_eligible']); self.assertEqual(result['location']['country'], 'Egypt')

    def test_geographic_branches_do_not_depend_on_salary_availability_or_validity(self):
        base = '<h2>Responsibilities</h2><p>Build ontologies.</p>'
        for extras in ({}, {'salaryRange': None}, {'salaryRange': {'min': -200, 'max': 'invalid', 'currency': None}},
                       {'salaryEligible': False, 'salaryBasis': 'total'}):
            self.assertTrue(decide(body=base, **extras)['job_market_eligible'])
            self.assertTrue(decide(title='Taxonomy Specialist', country='United States', **extras)['job_market_eligible'])

    def test_salary_description_cannot_manufacture_job_responsibilities(self):
        record = {'id': '123', 'text': 'Data Engineer', 'hostedUrl': 'https://example.test/jobs/123', 'country': 'SA',
                  'description': '<p>Ordinary work.</p>', 'salaryDescription': '<h2>Responsibilities</h2><p>Build ontologies.</p>'}
        raw = json.dumps({'record': record}).encode(); artifact = {'path': 'synthetic.json', 'sha256': transport.digest(raw), 'bytes_base64': base64.b64encode(raw).decode()}
        self.assertFalse(market.decide(record, 'lever', artifact)['job_market_eligible'])

    def test_case_ids_and_old_human_or_machine_flags_do_not_override_scope(self):
        result = decide(country='Egypt', case_id='EVAL-f5abd1d8389ba873', approved=True,
                        human_market_eligibility='Accept', occupational_classification='Core KE')
        self.assertFalse(result['job_market_eligible'])
        self.assertFalse(result['occupational_classification_used'])

    def test_missing_saudi_description_remains_ineligible(self):
        record, artifact = posting(); record['description'] = ''
        self.assertFalse(market.decide(record, 'workable', artifact)['job_market_eligible'])


class AuthenticMarketTests(unittest.TestCase):
    def test_all_ten_against_nonblind_user_reference_and_egypt_variant(self):
        path = os.environ.get('STAGE7_MARKET_HUMAN_REFERENCE')
        self.assertTrue(path, 'Set STAGE7_MARKET_HUMAN_REFERENCE')
        reference = transport.loads(Path(path).read_bytes())
        self.assertFalse(reference['independently_blinded']); self.assertFalse(reference['occupational_labels'])
        captures = market.all_development(); comparison = market.compare_reference(captures, reference)
        self.assertEqual(len(comparison), 10)
        self.assertEqual(sum(r['human_market_eligibility'] == 'Accept' for r in comparison), 1)
        self.assertTrue(all(r['agrees'] for r in comparison))
        self.assertEqual(sum(r['decision'] == 'Accept' for r in comparison), 1)
        accepted = next(r for r in comparison if r['decision'] == 'Accept')
        variants = [r for r in captures if r['case_id'] == accepted['case_id']]
        self.assertTrue(any(r['location']['country'] == 'Egypt' and r['decision'] == 'Reject' for r in variants))
        self.assertEqual(accepted['location']['country'], 'Saudi Arabia')
        self.assertTrue(accepted['responsibility_support'])
        for r in comparison:
            self.assertFalse(r['salary_evaluated']); self.assertFalse(r['occupational_classification_used'])
        wrong = copy.deepcopy(reference)
        egypt = next(r for r in variants if r['location']['country'] == 'Egypt')
        target = next(r for r in wrong['decisions'] if r['case_id'] == accepted['case_id'])
        target['capture_sha256'] = egypt['capture_sha256']; target['country'] = 'Egypt'
        with self.assertRaisesRegex(transport.TransportError, 'different capture/location'):
            market.compare_reference(captures, wrong)


if __name__ == '__main__': unittest.main()

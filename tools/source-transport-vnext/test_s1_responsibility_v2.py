"""Saudi S1 structure coverage and conservative exclusions; original source spans stay exact."""
import unittest

import market_eligibility_vnext as market
from test_market_eligibility_vnext import posting, decide


class SaudiS1CoverageTests(unittest.TestCase):
    def test_confirmed_semantic_engineering_statements_in_list_and_paragraph_layouts(self):
        statements = [
            'Design, develop, and maintain Semantic Layer and Data Mart solutions within Teradata environments.',
            'Design Semantic and Data Mart layers from scratch using ERWin Data Modeler.',
            'Lead and mentor a team of Semantic Layer developers.',
            'Enforce data governance, data quality standards, and naming conventions across the Semantic Layer.',
        ]
        for text in statements:
            for layout in ('<ul><li>{}</li></ul>', '<p>• {}</p>', '<p>{}</p>'):
                with self.subTest(text=text, layout=layout):
                    record, artifact = posting(body='<h2>Key Responsibilities</h2>' + layout.format(text))
                    row = market.decide(record, 'workable', artifact)
                    self.assertEqual((row['decision'], row['rule']), ('Accept', 'S1'))
                    packet = market.source_projection(record, 'workable', artifact)
                    for e in row['responsibility_support']:
                        self.assertEqual(market.consumer.resolve_evidence(packet, e['locator']), e['matched_clause'])
                        self.assertIn(e['matched_clause'], text)

    def test_coordinated_verbs_and_heading_variants_have_no_title_dependency(self):
        for heading in ('Responsibilities', 'Key Responsibilities:', 'Your Responsibilities',
                        'Tasks and Responsibilities', "What You'll Do"):
            for verbs in ('Design and maintain', 'Design, develop and maintain', 'Develop and implement'):
                row = decide(title='Platform Specialist', body=f'<p><strong>{heading}</strong></p><p>• {verbs} semantic layers.</p>')
                self.assertEqual((row['decision'], row['rule']), ('Accept', 'S1'))

    def test_incidental_mentions_reporting_usage_and_generic_engineering_are_negative(self):
        negatives = [
            'Use the Semantic Layer to run existing reports.',
            'Build BI dashboards using the Semantic Layer.',
            'Develop reporting pipelines that consume semantic layers.',
            'Design semantic layer reports for executives.',
            'Develop semantic layer reporting dashboards for executives.',
            'Maintain semantic layer documentation and training.',
            'Build generic data pipelines and dashboards.',
            'Our platform uses a Semantic Layer.',
            'Experience designing and maintaining Semantic Layers is preferred.',
            'Lead and mentor a team of BI developers using the Semantic Layer.',
            'Enforce reporting deadlines across the Semantic Layer.',
            'Do not design Semantic Layers.',
            'Design hypothetical Semantic Layers as an example.',
        ]
        for text in negatives:
            with self.subTest(text=text):
                self.assertFalse(decide(body=f'<h2>Responsibilities</h2><p>• {text}</p>')['job_market_eligible'])

    def test_company_descriptions_qualifications_and_unbounded_text_do_not_supply_duties(self):
        duty = '<p>• Design and maintain semantic layers.</p>'
        self.assertFalse(decide(body=duty)['job_market_eligible'])
        self.assertFalse(decide(body='<h2>About Us</h2>' + duty)['job_market_eligible'])
        for stop in ('Requirements', 'Required Skills & Experience', 'Must-Have Skills & Experience',
                     'Preferred Experience', 'Qualifications', 'Benefits', 'Compensation', 'About the Company'):
            with self.subTest(stop=stop):
                body = '<h2>Responsibilities</h2><p>Build ordinary pipelines.</p><h2>' + stop + '</h2>' + duty
                self.assertFalse(decide(body=body)['job_market_eligible'])

    def test_responsibility_context_never_crosses_fields(self):
        self.assertFalse(decide(body='<h2>Responsibilities</h2><p>Build ordinary pipelines.</p>',
                                additional='<p>• Design and maintain semantic layers.</p>')['job_market_eligible'])

    def test_international_gate_does_not_change_for_the_same_semantic_duties(self):
        body = '<h2>Responsibilities</h2><p>• Design, develop, and maintain Semantic Layers.</p>'
        for country in ('Egypt', 'United States', 'United Kingdom'):
            self.assertEqual(decide(country=country, body=body)['decision'], 'Reject')
            self.assertEqual(decide(title='Semantic Engineer', country=country, body=body)['decision'], 'Accept')

    def test_missing_salary_or_old_human_flags_never_supply_or_remove_job_evidence(self):
        body = '<h2>Responsibilities</h2><p>• Lead and mentor a team of Semantic Layer developers.</p>'
        for fields in ({}, {'salaryEligible': False}, {'salaryRange': None}, {'human_market_eligibility': 'Reject'}):
            row = decide(body=body, **fields)
            self.assertTrue(row['job_market_eligible'])
            self.assertFalse(row['salary_evaluated'])
        self.assertFalse(decide(human_market_eligibility='Accept')['job_market_eligible'])


if __name__ == '__main__':
    unittest.main()

"""Salary dimension and population controls. Synthetic examples are not market data."""
import unittest
import os
from pathlib import Path
from html import escape
import consumer_vnext as consumer
import salary_vnext as salary
from test_transport_vnext import fixture
import transport_vnext as transport


def assess(text='', structured=None, country='United States', decision='Accept', fx=None):
    record = fixture()['record']
    record.pop('salaryRange')
    record['description'] = '<p>' + escape(text) + '</p>'
    if structured:
        record.update(structured)
    packet = fixture(record)
    return salary.assess(packet, consumer.consume(packet), dict(decision=decision, location=dict(country=country)),
                         fx or dict(date='2026-10-29', rates=dict(SAR=1, USD=3.75)))


class SalaryTests(unittest.TestCase):
    def test_unsupported_structured_salary_is_preserved_not_reported_absent(self):
        result = assess('Employer description.', structured=dict(salary={'amount': 'negotiable', 'unit': 'custom'}))
        self.assertEqual(result['unhandled_structured_fields'][0]['source']['pointer'], '/record/salary')
        self.assertNotIn('No salary', result['status'])

    def test_country_specific_pay_range_heading_preserves_missing_basis_and_period(self):
        result = assess('United States - Remote Pay Range\n$180,000—$230,000 USD')
        obs, = result['observations']
        self.assertEqual((obs['lower_amount'], obs['upper_amount'], obs['currency'], obs['pay_market']),
                         (180000, 230000, 'USD', 'United States'))
        self.assertIsNone(obs['period'])
        self.assertFalse(obs['comparable'])

    @unittest.skipUnless(os.environ.get('STAGE7_VNEXT_INPUT_DIR'), 'Explicit original Development transport fixture required')
    def test_authentic_original_development_salary_structure(self):
        packet = transport.loads((Path(os.environ['STAGE7_VNEXT_INPUT_DIR']) / 'EVAL-4847917fd586d111.transport.json').read_bytes())
        transport.verify_packet(packet)
        result = salary.assess(packet, consumer.consume(packet), dict(decision='Reject', location=dict(country='United States')),
                               dict(date='2026-10-29', rates=dict(SAR=1, USD=3.75)))
        structured = [o for o in result['observations'] if isinstance(o['original'], dict) and 'interval' in o['original']]
        self.assertEqual((structured[0]['lower_amount'], structured[0]['upper_amount'], structured[0]['currency'], structured[0]['period']),
                         (165000, 185000, 'USD', 'Annual'))
        self.assertFalse(structured[0]['comparable'])

    def test_explicit_base_pay_market_period_and_currency_convert(self):
        result = assess('The US base salary range for this role is USD 120,000 - 144,000 per year.')
        obs, = result['observations']
        self.assertTrue(obs['comparable'])
        self.assertEqual(obs['normalized']['lower_amount'], 37500)
        self.assertEqual(obs['normalized']['upper_amount'], 45000)
        self.assertEqual((result['salaryMin'], result['currency'], result['period']), (120000, 'USD', 'Annual'))
        self.assertIsNone(result['production_approval'])

    def test_dollar_and_period_are_never_inferred_from_us_location_or_size(self):
        obs, = assess('Base salary: $150,000 - $200,000.')['observations']
        self.assertEqual((obs['lower_amount'], obs['upper_amount']), (150000, 200000))
        self.assertIsNone(obs['currency'])
        self.assertIsNone(obs['period'])
        self.assertEqual(obs['compensation_basis'], 'base')
        self.assertIsNone(obs['normalized'])

    def test_market_rejection_cannot_enter_benchmark(self):
        obs, = assess('The US base salary range is USD 120,000 - 144,000 per year.', decision='Reject')['observations']
        self.assertTrue(obs['intrinsic_eligible'])
        self.assertFalse(obs['comparable'])

    def test_structured_provider_units_and_source_label_reuse_existing_rules(self):
        obs, = assess('Original employer description.', structured=dict(
            salaryRange=dict(min=120000, max=144000, currency='USD', interval='per-year-salary'),
            salaryDescriptionPlain='US base salary'))['observations']
        self.assertTrue(obs['comparable'])
        self.assertEqual(obs['evidence'][0]['source']['pointer'], '/record/salaryRange')

    def test_compensation_basis_and_pay_market_must_be_explicit(self):
        for text in ('Salary USD 120,000 - 144,000 per year.',
                     'Total compensation USD 120,000 - 144,000 per year.',
                     'Base salary USD 120,000 - 144,000 per year.'):
            obs, = assess(text)['observations']
            self.assertFalse(obs['comparable'])
            self.assertIsNone(obs['normalized'])

    def test_funding_is_not_salary_and_unparsed_pay_is_not_missing_data(self):
        self.assertEqual(assess('We raised USD 100,000 - 200,000 in funding.')['observations'], [])
        result = assess('Salary USD 120k - 150k per year.')
        self.assertTrue(result['unparsed_signals'])
        self.assertNotIn('No salary', result['status'])

    def test_invalid_fx_or_multiple_currencies_withhold_conversion(self):
        obs, = assess('The US base salary is USD 120,000 - 144,000 per year.', fx=dict(date='invalid', rates=dict(USD=3.75)))['observations']
        self.assertFalse(obs['comparable'])
        obs, = assess('The US base salary is USD 120,000 - EUR 144,000 per year.')['observations']
        self.assertIsNone(obs['currency'])

    def test_monthly_is_not_divided_by_twelve(self):
        obs, = assess('The US base salary is USD 10,000 - 12,000 per month.')['observations']
        self.assertEqual(obs['normalized']['lower_amount'], 37500)


if __name__ == '__main__': unittest.main()

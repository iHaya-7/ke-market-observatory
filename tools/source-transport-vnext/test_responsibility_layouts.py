"""Narrow layout rules: source-grounded positive and negative regressions."""
import os
from pathlib import Path
import unittest

import consumer_vnext as consumer
import transport_vnext as transport
from test_transport_vnext import fixture


def document(body, source_type='lever'):
    if source_type == 'greenhouse':
        record = {'id': '123', 'title': 'Metadata title only',
                  'absolute_url': 'https://example.test/jobs/123', 'content': body}
    else:
        record = fixture()['record']
        record['description'] = body
    packet = fixture(record, source_type=source_type)
    return packet, consumer.consume(packet)


class LayoutTests(unittest.TestCase):
    def test_conditional_prose_introduction_with_gerund_list(self):
        intro = ('As an Engineer your main task will be building services. '
                 'However your responsibilities may also include:')
        statements = ['Supporting service testing.', 'Assisting with releases.', 'Designing data storage.',
                      'Optimising service latency.', 'Getting user feedback.', 'Assisting with planning.',
                      'Working with delivery teams.', 'Collaborating with clients.']
        body = '<p>' + intro + '</p><ul>' + ''.join('<li>' + s + '</li>' for s in statements) + '</ul>'
        packet, result = document(body)
        self.assertEqual([d['text'] for d in result['responsibilities']], statements)
        for duty in result['responsibilities']:
            self.assertEqual(consumer.resolve_evidence(packet, duty['section_context']), intro)
            self.assertEqual(duty['extraction_rule'], 'explicit-conditional-duty-list-v1')
            self.assertEqual(consumer.resolve_evidence(packet, duty['locator']), duty['text'])

    def test_bold_category_prefix_retains_the_entire_original_bullet(self):
        body = ('<h3>Key Responsibilities</h3><ul>'
                '<li><strong>Storage:</strong> Design resilient storage.</li>'
                '<li><strong>Operations:</strong> Monitor systems.</li>'
                '<li><b>Transfer:</b> Lead paired handovers.</li></ul>')
        packet, result = document(body)
        self.assertEqual([d['text'] for d in result['responsibilities']],
                         ['Storage: Design resilient storage.', 'Operations: Monitor systems.', 'Transfer: Lead paired handovers.'])
        for duty in result['responsibilities']:
            self.assertEqual(consumer.resolve_evidence(packet, duty['section_context']), 'Key Responsibilities')
            self.assertEqual(duty['extraction_rule'], 'bold-labeled-duty-list-v1')

    def test_qualifications_benefits_and_interviews_do_not_supply_duties(self):
        for heading in ('Requirements', 'Qualifications', 'Benefits & Perks', 'Our Interview Process'):
            for bullet in ('Designing storage systems.', '<strong>Storage:</strong> Design storage.'):
                with self.subTest(heading=heading, bullet=bullet):
                    _, result = document('<h3>' + heading + '</h3><ul><li>' + bullet + '</li></ul>')
                    self.assertEqual(result['responsibilities'], [])

    def test_responsibility_section_does_not_leak_to_next_list(self):
        _, result = document('<h3>Key Responsibilities</h3><ul><li><strong>Storage:</strong> Design storage.</li></ul>'
                             '<h3>Requirements</h3><ul><li><strong>Storage:</strong> Design storage.</li></ul>')
        self.assertEqual(len(result['responsibilities']), 1)

    def test_no_list_no_direct_intro_or_no_bold_label_does_not_activate_rules(self):
        bodies = [
            '<p>Your responsibilities may also include:</p><p>Designing storage.</p>',
            '<p>Company overview.</p><ul><li>Designing storage.</li></ul>',
            '<p>Our handbook says your responsibilities may also include:</p><ul><li>Designing storage.</li></ul>',
            '<h3>Key Responsibilities</h3><ul><li>Storage: Design storage.</li></ul>',
            '<h3>Key Responsibilities</h3><ul><li><strong>Storage:</strong> Experience with storage.</li></ul>',
            '<h3>Key Responsibilities</h3><ul><li><strong>Experience:</strong> Design storage.</li></ul>',
            '<h3>Responsibilities no longer include</h3><ul><li><strong>Storage:</strong> Design storage.</li></ul>',
        ]
        for body in bodies:
            with self.subTest(body=body):
                _, result = document(body)
                self.assertEqual(result['responsibilities'], [])

    def test_negated_bullets_and_nonadjacent_intro_remain_unmatched(self):
        for bullet in ('Not designing storage.', 'Never supporting releases.', 'No responsibility for delivery.'):
            _, result = document('<p>Your responsibilities may also include:</p><ul><li>' + bullet + '</li></ul>')
            self.assertEqual(result['responsibilities'], [])
        _, result = document('<p>Your responsibilities may also include:</p><p>Required experience:</p>'
                             '<ul><li>Designing storage.</li></ul>')
        self.assertEqual(result['responsibilities'], [])

    def test_nested_and_multi_paragraph_items_remain_outside_new_rules(self):
        for items in ('<li>Supporting systems.<ul><li>Designing storage.</li></ul></li>',
                      '<li><p>Supporting systems.</p><p>Designing storage.</p></li>'):
            _, result = document('<p>Your responsibilities may also include:</p><ul>' + items + '</ul>')
            self.assertEqual(result['responsibilities'], [])

    def test_title_and_hidden_text_cannot_supply_list_context(self):
        packet, _ = document('<p>Overview.</p><ul><li>Designing storage.</li></ul>')
        record = packet['record']; record['text'] = 'Your responsibilities may also include:'
        record['description'] = '<script>Your responsibilities may also include:</script><ul><li>Designing storage.</li></ul>'
        self.assertEqual(consumer.consume(fixture(record))['responsibilities'], [])

    def test_unicode_entities_and_encoded_html_keep_field_offsets(self):
        import html
        original = '<h3>Key Responsibilities</h3><ul><li><strong>Links:</strong> Build روابط &amp; entities.</li></ul>'
        packet, result = document(html.escape(original), source_type='greenhouse')
        duty = result['responsibilities'][0]
        self.assertEqual(duty['text'], 'Links: Build روابط & entities.')
        self.assertEqual(consumer.resolve_evidence(packet, duty['locator']), duty['text'])
        self.assertEqual(packet['record']['content'], html.escape(original))

    def test_conditional_list_ends_before_requirements(self):
        packet, result = document('<p>Your responsibilities may also include:</p><ul><li>Supporting delivery.</li></ul>'
                                  '<p><strong>What we are looking for in this person:</strong></p>'
                                  '<ul><li>Designing experience.</li><li>Working knowledge of storage.</li></ul>')
        self.assertEqual([d['text'] for d in result['responsibilities']], ['Supporting delivery.'])

    def test_legacy_extracted_item_is_not_duplicated(self):
        _, result = document('<h3>Responsibilities</h3><ul><li><strong>Design:</strong> Build storage.</li></ul>')
        self.assertEqual(len(result['responsibilities']), 1)


class AuthenticLayouts:
    def __init__(self, case, directory):
        super().__init__('runTest'); self.case = case; self.directory = directory

    def id(self):
        return 'authentic_layout.' + self.case['case_id']

    def __str__(self):
        return self.id()

    def runTest(self):
        cid = self.case['case_id']
        packet = transport.loads((self.directory / (cid + '.transport.json')).read_bytes())
        previous = transport.loads((self.directory / (cid + '.consumer.json')).read_bytes())
        self.assertEqual(transport.canonical(packet), transport.canonical(transport.load_case(transport.ROOT, self.case)))
        result = consumer.consume(packet)
        self.assertEqual(len(previous['responsibilities']), 0)
        self.assertEqual(len(result['responsibilities']), 8)
        self.assertEqual(result['documents'], previous['documents'])
        self.assertEqual(result['structured_salary'], previous['structured_salary'])
        expected_rule = 'explicit-conditional-duty-list-v1' if packet['source']['type'] == 'greenhouse' else 'bold-labeled-duty-list-v1'
        for duty in result['responsibilities']:
            self.assertEqual(duty['extraction_rule'], expected_rule)
            self.assertEqual(consumer.resolve_evidence(packet, duty['locator']), duty['text'])
            context = consumer.resolve_evidence(packet, duty['section_context'])
            self.assertTrue(consumer.CONDITIONAL_LIST.fullmatch(context) or consumer.LABELED_HEADING.fullmatch(context))
            self.assertLess(duty['section_context']['end'], duty['locator']['start'])
            self.assertFalse(duty['interpretation'])  # No forced representation mapping.


def load_tests(loader, tests, pattern):
    results = os.environ.get('STAGE7_DEVELOPMENT_RESULTS')
    directory = os.environ.get('STAGE7_VNEXT_INPUT_DIR')
    if not results or not directory:
        raise RuntimeError('Set the existing private Development result/input paths')
    directory = Path(directory)
    prior = transport.loads((directory / 'smoke.json').read_bytes())
    selected = {r['case_id'] for r in prior['cases'] if r['responsibility_passages'] == 0}
    if len(selected) != 2:
        raise RuntimeError('Expected two original zero-duty layouts')
    class Authentic(AuthenticLayouts, unittest.TestCase):
        pass
    for case in transport.blocked_cases(transport.ROOT, Path(results)):
        if case['case_id'] in selected:
            tests.addTest(Authentic(case, directory))
    return tests


if __name__ == '__main__':
    unittest.main()

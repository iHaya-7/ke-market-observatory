"""Synthetic invariants plus six private Development integration tests.

Authentic records are read in place, never embedded in tracked test fixtures.
Set STAGE7_DEVELOPMENT_RESULTS to the existing Development compatibility JSON.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

import consumer_vnext as consumer
import transport_vnext as transport


def fixture(record=None, detail=None, extra=None, source_type='lever'):
    record = copy.deepcopy(record) if record is not None else {
        'id': '123', 'text': 'Structured title only', 'hostedUrl': 'https://example.test/jobs/123',
        'description': '<h2>Responsibilities</h2><p>Build ontologies &amp; schemas.</p>',
        'additional': '<p>Requirements</p>',
        'salaryRange': {'min': 100, 'max': 200, 'currency': 'USD', 'interval': 'per-year-salary'}}
    source = {'id': 'synthetic-source', 'type': source_type}
    docs, specs = [], []
    records = [('originals', record)]
    if detail is not None:
        records.append(('details', detail))
    if extra is not None:
        records.append(('originals', extra))
    for i, (role, value) in enumerate(records):
        data = json.dumps({'sourceId': source['id'], 'sourceType': source_type,
                           'sourceJobId': '123', 'capturedAtUtc': '2026-10-21T12:00:00Z',
                           'record': value}, ensure_ascii=False).encode()
        docs.append(data)
        specs.append({'original_path': (transport.CORPUS / role / 'synthetic' / ('SYNTHETIC-' + str(i) + '.json')).as_posix(),
                      'sha256': transport.digest(data)})
    merged = copy.deepcopy(record)
    if detail is not None:
        merged.update(detail)
    return transport.make_packet('SYNTHETIC', specs, docs, json.dumps(merged, ensure_ascii=False).encode(), source)


class SyntheticTests(unittest.TestCase):
    def test_title_metadata_never_inserted_into_body(self):
        packet = fixture(); result = consumer.consume(packet)
        self.assertEqual(result['title_metadata']['value'], packet['record']['text'])
        self.assertEqual(transport.resolve_reference(packet, result['title_metadata']['reference']), packet['record']['text'])
        self.assertTrue(all(packet['record']['text'] not in d['text'] for d in result['documents']))
        self.assertEqual(consumer.resolve_evidence(packet, result['responsibilities'][0]['locator']),
                         'Build ontologies & schemas.')

    def test_salary_types_units_and_basis_are_not_inferred(self):
        packet = fixture(); salary = consumer.consume(packet)['structured_salary'][0]
        self.assertEqual(salary['raw'], packet['record']['salaryRange'])
        self.assertIs(type(salary['dimensions']['min']), int)
        self.assertEqual(salary['dimensions']['explicit_period'], 'Annual')
        self.assertIsNone(salary['dimensions']['compensation_basis'])
        self.assertIsNone(salary['dimensions']['pay_market'])
        self.assertNotIn('salaryEligible', salary)

    def test_missing_and_unknown_interval_remain_unresolved(self):
        for value in (None, 'unknown-unit', ''):
            record = fixture()['record']; record['salaryRange']['interval'] = value
            salary = consumer.consume(fixture(record))['structured_salary'][0]
            self.assertEqual(salary['raw']['interval'], value)
            self.assertIsNone(salary['dimensions']['explicit_period'])
        record = fixture()['record']; del record['salaryRange']['interval']; del record['salaryRange']['currency']
        salary = consumer.consume(fixture(record))['structured_salary'][0]
        self.assertIsNone(salary['dimensions']['explicit_period'])
        self.assertIsNone(salary['dimensions']['currency'])

    def test_field_boundaries_prevent_cross_field_duty_context(self):
        record = fixture()['record']; record['description'] = '<h2>Responsibilities</h2>'
        record['additional'] = '<p>Build ontologies.</p>'
        self.assertEqual(consumer.consume(fixture(record))['responsibilities'], [])

    def test_list_heading_is_metadata_with_its_own_pointer(self):
        record = fixture()['record']; record['description'] = '<p>Overview only.</p>'
        record['lists'] = [{'text': 'Responsibilities:', 'content': '<li>Design ontologies.</li>', 'unknown': None}]
        packet = fixture(record); result = consumer.consume(packet)
        duty = result['responsibilities'][0]
        self.assertEqual(duty['field_pointer'], '/lists/0/content')
        self.assertEqual(transport.resolve_reference(packet, duty['section_metadata']['source']), 'Responsibilities:')
        self.assertEqual(consumer.resolve_evidence(packet, duty['locator']), 'Design ontologies.')
        self.assertNotIn('Responsibilities:', next(d for d in result['documents'] if d['field_pointer'] == '/lists/0/content')['text'])

    def test_alternative_plain_fields_stay_separate(self):
        record = fixture()['record']; record['descriptionPlain'] = 'Different plain description — source value retained.'
        packet = fixture(record); result = consumer.consume(packet)
        self.assertEqual(next(d['text'] for d in result['documents'] if d['field_pointer'] == '/descriptionPlain'), record['descriptionPlain'])
        self.assertEqual(len(result['responsibilities']), 1)
        self.assertEqual(packet['record'], record)

    def test_unicode_entities_and_field_local_offsets(self):
        record = fixture()['record']
        record['description'] = '&lt;h2&gt;Responsibilities&lt;/h2&gt;&lt;p&gt;Design ontologies — ربط &amp;amp; data.&lt;/p&gt;'
        packet = fixture(record); result = consumer.consume(packet)
        self.assertEqual(packet['record']['description'], record['description'])
        self.assertEqual(consumer.resolve_evidence(packet, result['responsibilities'][0]['locator']),
                         'Design ontologies — ربط & data.')
        bad = dict(result['responsibilities'][0]['locator'], end=100000)
        with self.assertRaises(transport.TransportError):
            consumer.resolve_evidence(packet, bad)

    def test_title_and_hidden_script_do_not_create_duties(self):
        record = fixture()['record']; record['text'] = 'Build ontologies'
        record['description'] = '<script>Build ontologies</script><p>Overview.</p>'
        result = consumer.consume(fixture(record))
        self.assertEqual(result['responsibilities'], [])
        self.assertNotIn('Build ontologies', result['documents'][0]['text'])

    def test_unknown_values_and_escaped_pointer_keys_round_trip(self):
        record = fixture()['record']; record['a/b~c'] = {'nested/key': [None, False, 'é', 1.25]}
        packet = fixture(record); result = consumer.consume(transport.loads(transport.canonical(packet)))
        self.assertEqual(transport.resolve_reference(packet, result['raw_field_sources']['a/b~c']), record['a/b~c'])
        ref = transport.reference(packet, '/a~1b~0c/nested~1key/2')
        self.assertEqual(transport.resolve_reference(packet, ref), 'é')

    def test_detail_ownership_is_whole_field_overwrite(self):
        record = fixture()['record']; record['nested'] = {'a': 1, 'b': 2}
        packet = fixture(record, detail={'description': '<p>Detail value.</p>', 'nested': {'a': 3}})
        self.assertEqual(packet['record']['nested'], {'a': 3})
        self.assertEqual(packet['field_owners']['nested'], packet['captures'][1]['sha256'])
        self.assertEqual(packet['field_owners']['text'], packet['captures'][0]['sha256'])
        transport.verify_packet(packet)

    def test_supplementary_original_is_retained_not_selected(self):
        packet = fixture(extra={'text': 'Different version', 'id': '123'})
        self.assertEqual(len(packet['captures']), 2)
        self.assertEqual(packet['record']['text'], 'Structured title only')
        transport.verify_packet(packet)

    def test_bad_hash_identity_and_replay_are_rejected(self):
        packet = fixture()
        import base64
        raw = [base64.b64decode(c['bytes_base64']) for c in packet['captures']]
        replay = base64.b64decode(packet['replay_bytes_base64'])
        for field in ('hash', 'identity', 'replay'):
            specs = copy.deepcopy(packet['capture_specs']); data = list(raw); rp = replay
            if field == 'hash':
                specs[0]['sha256'] = '0' * 64
            elif field == 'identity':
                doc = transport.loads(data[0]); doc['sourceJobId'] = 'other'
                data[0] = json.dumps(doc).encode(); specs[0]['sha256'] = transport.digest(data[0])
            else:
                rp = b'{}'
            with self.subTest(field=field), self.assertRaises(transport.TransportError):
                transport.make_packet('SYNTHETIC', specs, data, rp, packet['source'])

    def test_packet_value_owner_title_and_version_tampering_rejected(self):
        for field in ('record', 'field_owners', 'title_metadata', 'version'):
            packet = fixture()
            if field == 'record': packet[field]['description'] += '<p>Inserted!</p>'
            elif field == 'field_owners': packet[field]['text'] = '0' * 64
            elif field == 'title_metadata': packet[field]['value'] = 'Fake title'
            else: packet[field] = 'unknown'
            with self.subTest(field=field), self.assertRaises(transport.TransportError):
                consumer.consume(packet)

    def test_duplicate_keys_nan_and_invalid_pointer_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(transport.TransportError):
                transport.loads(raw)
        for pointer in ('bad', '/x~2', '/x/01'):
            with self.subTest(pointer=pointer), self.assertRaises(transport.TransportError):
                transport.at({'x': [1]}, pointer)

    def test_path_traversal_links_and_wrong_split_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for rel in ('../x', '/absolute', 'development/../x', 'development/held-out/x', 'other/x'):
                with self.subTest(rel=rel), self.assertRaises(transport.TransportError):
                    transport.safe_path(root, rel, Path('development'))
            try:
                (root / 'development').symlink_to(root, target_is_directory=True)
            except OSError:
                return  # Windows may forbid symlink creation; lexical cases still ran.
            with self.assertRaises(transport.TransportError):
                transport.safe_path(root, 'development/x', Path('development'))

    def test_unmapped_structured_ranges_are_preserved_independently(self):
        record = fixture()['record']; record['pay_input_ranges'] = [
            {'min': '100.00', 'market': None}, {'min': 10, 'unusual_unit': 'per-project'}]
        packet = fixture(record); result = consumer.consume(packet)
        self.assertEqual([s['raw'] for s in result['structured_salary'][1:]], record['pay_input_ranges'])
        self.assertTrue(all('dimensions' not in s for s in result['structured_salary'][1:]))

    def test_unsupported_structured_shape_stops_consumer(self):
        record = fixture()['record']; record['salaryRange'] = ['unexpected shape']
        with self.assertRaisesRegex(transport.TransportError, 'Unsupported salaryRange shape'):
            consumer.consume(fixture(record))


class DevelopmentCaseTest:
    def __init__(self, case):
        super().__init__('runTest')
        self.case = case

    def id(self):
        return 'authentic_development.' + self.case['case_id']

    def __str__(self):
        return self.id()

    def runTest(self):
        packet = transport.load_case(transport.ROOT, self.case)
        original = transport.canonical(packet)
        reloaded = transport.loads(original)
        result = consumer.consume(reloaded)
        self.assertEqual(transport.canonical(packet), original)
        self.assertEqual(result['title_metadata']['value'], packet['record'].get('text', packet['record'].get('title')))
        self.assertEqual(set(result['raw_field_sources']), set(packet['record']))
        for field, ref in result['raw_field_sources'].items():
            self.assertEqual(transport.canonical(transport.resolve_reference(packet, ref)),
                             transport.canonical(packet['record'][field]))
        for doc in result['documents']:
            self.assertEqual(doc['text'], consumer.render(transport.resolve_reference(packet, doc['source']), doc['transform']))
        for duty in result['responsibilities']:
            self.assertEqual(consumer.resolve_evidence(packet, duty['locator']), duty['text'])
        if packet['source']['type'] == 'lever':
            self.assertTrue(packet['record']['salaryRange'])
            self.assertEqual(result['structured_salary'][0]['raw'], packet['record']['salaryRange'])
            self.assertEqual(sum(d['field_pointer'].startswith('/lists/') for d in result['documents']), len(packet['record']['lists']))
            self.assertIsNone(result['structured_salary'][0]['dimensions']['compensation_basis'])
        else:
            # These four historically blocked descriptions omit the metadata title.
            self.assertTrue(all(result['title_metadata']['value'] not in d['text'] for d in result['documents']))
        self.assertFalse(result['classification_executed'])


def load_tests(loader, tests, pattern):
    results = os.environ.get('STAGE7_DEVELOPMENT_RESULTS')
    if not results:
        raise RuntimeError('Set STAGE7_DEVELOPMENT_RESULTS to the verified Development compatibility.json')
    cases = transport.blocked_cases(transport.ROOT, Path(results))
    class AuthenticCase(DevelopmentCaseTest, unittest.TestCase):
        pass
    for case in cases:
        tests.addTest(AuthenticCase(case))
    return tests


if __name__ == '__main__':
    unittest.main()

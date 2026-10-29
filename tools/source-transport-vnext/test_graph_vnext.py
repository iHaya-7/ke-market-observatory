"""RDF mapping, tamper rejection, field fidelity and private Development controls."""
import copy
import os
from pathlib import Path
import unittest

import consumer_vnext as consumer
import transport_vnext as transport
import graph_vnext as builder
import validate_graph_vnext as validation
from rdflib import Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import DCTERMS, RDF, XSD
from test_transport_vnext import fixture

KE, VX, PROV = builder.KE, builder.VX, builder.PROV


def build(packet):
    consumed = consumer.consume(packet)
    return builder.build_graph(packet, consumed), consumed


class GraphTests(unittest.TestCase):
    def test_source_title_is_metadata_with_original_pointer(self):
        packet = fixture(); graph, consumed = build(packet)
        report = validation.validate_graph(graph, packet, consumed)
        posting = next(graph.subjects(RDF.type, KE.JobPosting))
        self.assertEqual(str(graph.value(posting, DCTERMS.title)), packet['record']['text'])
        title_evidence = graph.value(posting, VX.titleEvidence)
        locator = transport.loads(str(graph.value(title_evidence, KE.passageLocator)))
        self.assertEqual(locator['source']['pointer'], '/record/text')
        self.assertEqual(report['responsibilities'], 1)
        self.assertTrue(report['experimental_shacl_conforms'])

    def test_all_evidence_assertions_resolve_and_round_trip(self):
        packet = fixture(); graph, consumed = build(packet)
        graph = Graph().parse(data=graph.serialize(format='turtle'), format='turtle')
        report = validation.validate_graph(graph, packet, consumed)
        self.assertTrue(report['source_fidelity_passed'])
        for statement in graph.subjects(RDF.type, VX.SourceAssertion):
            triple = tuple(graph.value(statement, p) for p in (RDF.subject, RDF.predicate, RDF.object))
            self.assertIn(triple, graph)
            self.assertTrue(list(graph.objects(statement, PROV.wasDerivedFrom)))

    def test_original_salary_values_and_explicit_units(self):
        packet = fixture(); graph, consumed = build(packet)
        salary = next(graph.subjects(RDF.type, KE.SalaryObservation))
        self.assertEqual(graph.value(salary, KE.lowerAmount).toPython(), 100)
        self.assertEqual(str(graph.value(salary, KE.currency)), 'USD')
        self.assertEqual(str(graph.value(salary, KE.payPeriod)), 'Annual')
        self.assertEqual(transport.loads(str(graph.value(salary, VX.sourceValueJSON))), packet['record']['salaryRange'])
        self.assertEqual(transport.loads(str(graph.value(salary, VX.intervalTokenJSON))), 'per-year-salary')
        for p in (KE.compensationBasis, KE.payMarket, KE.salaryForRole, KE.roleConcept):
            self.assertFalse(list(graph.triples((None, p, None))))

    def test_unit_not_borrowed_from_other_description_fields(self):
        record = fixture()['record']; record['salaryRange'].pop('interval'); record['salaryRange'].pop('currency')
        record['salaryDescription'] = '<p>Annual salary USD 100 - 200.</p>'
        packet = fixture(record); graph, consumed = build(packet)
        validation.validate_graph(graph, packet, consumed)
        salary = next(graph.subjects(RDF.type, KE.SalaryObservation))
        self.assertIsNone(graph.value(salary, KE.payPeriod))
        self.assertIsNone(graph.value(salary, KE.currency))

    def test_unknown_intervals_and_unmapped_structures_stay_separate(self):
        record = fixture()['record']; record['salaryRange']['interval'] = 'unmapped-project-unit'
        record['pay_input_ranges'] = [{'min': '20.00', 'unit': 'per-project'}, {'amount': None}]
        packet = fixture(record); graph, consumed = build(packet)
        report = validation.validate_graph(graph, packet, consumed)
        self.assertEqual(report['structured_salary_observations'], 3)
        self.assertFalse(list(graph.triples((None, KE.payPeriod, None))))
        actual = {str(v) for n in graph.subjects(RDF.type, KE.SalaryObservation) for v in graph.objects(n, VX.sourceValueJSON)}
        self.assertEqual(actual, {transport.canonical(r) for r in [record['salaryRange']] + record['pay_input_ranges']})

    def test_invalid_amounts_preserved_without_valid_numeric_facts(self):
        for lower, upper in ((True, '200'), (-1, -2), (200, 100)):
            record = fixture()['record']; record['salaryRange'].update(min=lower, max=upper)
            packet = fixture(record); graph, consumed = build(packet)
            validation.validate_graph(graph, packet, consumed)
            salary = next(graph.subjects(RDF.type, KE.SalaryObservation))
            self.assertIsNone(graph.value(salary, KE.lowerAmount))
            self.assertIsNone(graph.value(salary, KE.upperAmount))
            self.assertEqual(transport.loads(str(graph.value(salary, VX.sourceValueJSON))), record['salaryRange'])

    def test_zero_duties_never_create_role_or_negative_classification(self):
        record = fixture()['record']; record['description'] = '<p>Unrecognized layout without a duty section.</p>'
        packet = fixture(record); graph, consumed = build(packet)
        report = validation.validate_graph(graph, packet, consumed)
        self.assertEqual(report['responsibilities'], 0)
        self.assertFalse(list(graph.subjects(RDF.type, KE.JobRole)))
        self.assertFalse(list(graph.triples((None, KE.advertisesRole, None))))
        self.assertFalse(list(graph.triples((None, KE.outcome, None))))
        self.assertFalse(report['frozen_profile_conforms'])

    def test_detail_owner_unicode_and_list_context_are_preserved(self):
        record = fixture()['record']; record['description'] = '<p>Overview.</p>'
        record['lists'] = [{'text': 'Responsibilities:', 'content': '<p>Design ontologies &amp; علاقات.</p>'}]
        packet = fixture(record, detail={'additional': '<p>Detail only.</p>'})
        graph, consumed = build(packet)
        validation.validate_graph(graph, packet, consumed)
        duty = next(graph.subjects(RDF.type, KE.Responsibility))
        self.assertEqual(str(graph.value(duty, KE.actionText)), 'Design ontologies & علاقات.')
        p = next(p for p in graph.objects(duty, KE.evidencePassage)
                 if transport.loads(str(graph.value(p, KE.passageLocator)))['transform'] != 'json')
        contexts = list(graph.objects(p, KE.contextPassage))
        self.assertTrue(any(transport.loads(str(graph.value(c, KE.passageLocator)))['source']['pointer'] == '/record/lists/0/text' for c in contexts))

    def test_forged_consumer_output_is_rejected(self):
        packet = fixture(); consumed = consumer.consume(packet)
        consumed['responsibilities'][0]['text'] = 'Fabricated duty'
        with self.assertRaisesRegex(transport.TransportError, 'Consumer output'):
            builder.build_graph(packet, consumed)

    def test_changed_title_assertion_is_rejected(self):
        packet = fixture(); graph, consumed = build(packet)
        posting = next(graph.subjects(RDF.type, KE.JobPosting))
        graph.set((posting, DCTERMS.title, builder.string('Fabricated title')))
        with self.assertRaises(transport.TransportError):
            validation.validate_graph(graph, packet, consumed)

    def test_wrong_source_pointer_or_span_is_rejected(self):
        for mutation in ('pointer', 'span'):
            packet = fixture(); graph, consumed = build(packet)
            p = next(p for p in graph.subjects(RDF.type, KE.EvidencePassage)
                     if transport.loads(str(graph.value(p, KE.passageLocator)))['transform'] != 'json')
            locator = transport.loads(str(graph.value(p, KE.passageLocator)))
            if mutation == 'pointer': locator['source']['pointer'] = '/record/text'
            else: locator['end'] = 100000
            graph.set((p, KE.passageLocator, builder.string(transport.canonical(locator))))
            with self.subTest(mutation=mutation), self.assertRaises(transport.TransportError):
                validation.validate_graph(graph, packet, consumed)

    def test_altered_capture_hash_missing_provenance_and_phantom_facts_rejected(self):
        for mutation in ('hash', 'provenance', 'human', 'role', 'basis'):
            packet = fixture(); graph, consumed = build(packet)
            if mutation == 'hash':
                artifact = next(graph.subjects(RDF.type, KE.EvidenceArtifact))
                graph.set((artifact, KE.sha256, builder.string('0' * 64)))
            elif mutation == 'provenance':
                statement = next(graph.subjects(RDF.type, VX.SourceAssertion))
                graph.remove((statement, PROV.wasDerivedFrom, None))
            elif mutation == 'human': graph.add((URIRef('urn:fake'), RDF.type, KE.HumanAssessment))
            elif mutation == 'role': graph.add((URIRef('urn:fake'), KE.roleConcept, URIRef('urn:fake:concept')))
            else: graph.add((next(graph.subjects(RDF.type, KE.SalaryObservation)), KE.compensationBasis, builder.string('base')))
            with self.subTest(mutation=mutation), self.assertRaises(transport.TransportError):
                validation.validate_graph(graph, packet, consumed)


class AuthenticGraphTest:
    def __init__(self, case, directory, zero):
        super().__init__('runTest'); self.case = case; self.directory = directory; self.zero = zero

    def id(self):
        return 'authentic_development_graph.' + self.case['case_id']

    def __str__(self):
        return self.id()

    def runTest(self):
        cid = self.case['case_id']
        packet = transport.loads((self.directory / (cid + '.transport.json')).read_bytes())
        previous = transport.loads((self.directory / (cid + '.consumer.json')).read_bytes())
        consumed = consumer.consume(packet)
        self.assertEqual(transport.canonical(packet), transport.canonical(transport.load_case(transport.ROOT, self.case)))
        graph = builder.build_graph(packet, consumed)
        serialized = graph.serialize(format='turtle')
        parsed = Graph().parse(data=serialized, format='turtle')
        self.assertTrue(isomorphic(graph, parsed))
        report = validation.validate_graph(parsed, packet, consumed)
        self.assertTrue(report['experimental_shacl_conforms'])
        self.assertEqual(report['experimental_violations'], 0)
        self.assertTrue(report['source_fidelity_passed'])
        self.assertEqual(report['responsibilities'], len(consumed['responsibilities']))
        if self.zero:
            self.assertEqual(len(previous['responsibilities']), 0)
            self.assertEqual(report['responsibilities'], 8)
            for duty in consumed['responsibilities']:
                self.assertIn('section_context', duty)
                nodes = list(graph.subjects(KE.actionText, builder.string(duty['text'])))
                self.assertTrue(nodes)
                section = transport.canonical(duty['section_context'])
                self.assertTrue(any(str(graph.value(c, KE.passageLocator)) == section
                                    for node in nodes for p in graph.objects(node, KE.evidencePassage)
                                    for c in graph.objects(p, KE.contextPassage)))
        else:
            self.assertEqual(consumed['responsibilities'], previous['responsibilities'])
        for field in ('documents', 'identity', 'structured_salary', 'title_metadata', 'raw_field_sources'):
            self.assertEqual(consumed[field], previous[field])
        self.assertFalse(list(graph.triples((None, KE.roleConcept, None))))
        for n in graph.subjects(RDF.type, KE.SalaryObservation):
            self.assertIsNone(graph.value(n, KE.compensationBasis))
            self.assertIsNone(graph.value(n, KE.payMarket))


def load_tests(loader, tests, pattern):
    results = os.environ.get('STAGE7_DEVELOPMENT_RESULTS')
    directory = os.environ.get('STAGE7_VNEXT_INPUT_DIR')
    if not results or not directory:
        raise RuntimeError('Set STAGE7_DEVELOPMENT_RESULTS and STAGE7_VNEXT_INPUT_DIR for private Development tests')
    directory = Path(directory)
    smoke = transport.loads((directory / 'smoke.json').read_bytes())
    zero = {r['case_id'] for r in smoke['cases'] if r['responsibility_passages'] == 0}
    if len(zero) != 2:
        raise RuntimeError('Expected the two verified zero-responsibility Development cases')
    class Authentic(AuthenticGraphTest, unittest.TestCase):
        pass
    for case in transport.blocked_cases(transport.ROOT, Path(results)):
        tests.addTest(Authentic(case, directory, case['case_id'] in zero))
    return tests


if __name__ == '__main__':
    unittest.main()

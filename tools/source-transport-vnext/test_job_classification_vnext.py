"""Rule behavior and provenance tests; synthetic examples are not ground truth."""
import base64
import copy
import csv
from html import escape
from html.parser import HTMLParser
import io
import os
from pathlib import Path
import unittest

import classify_jobs_vnext as classifier
import consumer_vnext as consumer
import graph_vnext as builder
import review_export_vnext as evidence
import transport_vnext as transport
import semantic_graph_vnext as semantic
from rdflib import URIRef
from rdflib.namespace import DCTERMS
from test_transport_vnext import fixture


def source_rows(*texts, title='Metadata title', body=None):
    record = fixture()['record']; record['text'] = title
    record['description'] = body if body is not None else '<h2>Responsibilities</h2>' + ''.join('<p>' + escape(t) + '</p>' for t in texts)
    packet = fixture(record); consumed = consumer.consume(packet)
    graph = builder.build_graph(packet, consumed)
    rows = evidence.query_rows(graph, packet, reader=lambda a: base64.b64decode(a['bytes_base64'], validate=True))
    return rows


class RuleTests(unittest.TestCase):
    def test_semantic_assertions_are_separate_resolvable_and_tamper_checked(self):
        record = fixture()['record']; record['description'] = '<h2>Responsibilities</h2><p>Own ontologies.</p>'
        packet = fixture(record); consumed = consumer.consume(packet)
        graph = builder.build_graph(packet, consumed)
        before = set(graph)
        rows = evidence.query_rows(graph, packet, reader=lambda a: base64.b64decode(a['bytes_base64']))
        decision = classifier.classify_job(rows, self.concepts)
        inferred = semantic.build(graph, decision)
        self.assertEqual(semantic.validate(inferred, graph, decision)['assertions'], 1)
        self.assertEqual(set(graph), before)
        inferred.add((URIRef('urn:test:fake'), DCTERMS.subject, URIRef('urn:test:unsupported')))
        with self.assertRaises(transport.TransportError): semantic.validate(inferred, graph, decision)

    def test_graph_construction_and_canonical_entity_linking_use_existing_taxonomy(self):
        rows, decision = self.decide(
            'Design, implement, and maintain ingestion pipelines that transform source data into RDF triple stores.',
            'Build entity linking workflows to resolve supplier identities into canonical graph nodes.')
        self.assertEqual(decision['proposed_classification'], 'Core KE')
        self.assertEqual(set(decision['triggered_rules']), {'C2', 'C3'})
        self.assertTrue(all(e['concept_uri'] == str(classifier.ROLE['knowledge-graph-engineer']) for e in decision['supporting_evidence']))
        classifier.validate_decisions([decision], rows, self.concepts)

    def test_graph_mentions_consumption_and_collateral_work_do_not_become_core(self):
        for text in ('Build GraphRAG applications using existing knowledge graphs.',
                     'Build ingestion pipelines for generic graph algorithms.',
                     'Build entity matching workflows for contact deduplication.',
                     'Create presentations about ingestion pipelines that transform data into RDF triple stores.',
                     'Create training to implement knowledge graph components.',
                     'Query knowledge graphs to produce reports.'):
            _, decision = self.decide(text)
            self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence', text)

    def test_graph_component_delivery_is_adjacent_not_representation_ownership(self):
        _, decision = self.decide('Collaborate with engineers to implement the knowledge graph components required by the product.')
        self.assertEqual(decision['proposed_classification'], 'Adjacent Technical')
        self.assertEqual(decision['triggered_rules'], ['A2'])

    def test_coordinated_verbs_do_not_lose_explicit_ontology_object(self):
        _, decision = self.decide('Design, build, and maintain ontologies.', 'Validate ontologies against domain constraints.')
        self.assertEqual(decision['proposed_classification'], 'Core KE')

    def test_bi_layers_do_not_automatically_map_to_ontology_engineering(self):
        _, decision = self.decide('Design Semantic Layer and Data Mart solutions.', 'Maintain Semantic layers for reporting.')
        self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')
        self.assertTrue(any('BI-oriented' in s for s in decision['unresolved_uncertainties']))

    @classmethod
    def setUpClass(cls):
        cls.concepts = classifier.vocabulary()

    def decide(self, *texts, **kwargs):
        rows = source_rows(*texts, **kwargs)
        return rows, classifier.classify_job(rows, self.concepts, case_id='SYNTHETIC')

    def test_explicit_representation_ownership_supports_core_and_exact_concept(self):
        rows, decision = self.decide('Own ontologies for computational reasoning.')
        self.assertEqual(decision['proposed_classification'], 'Core KE')
        support = decision['supporting_evidence'][0]
        self.assertEqual(support['concept_uri'], str(classifier.ROLE['ontology-engineer']))
        self.assertEqual(support['representation_text'], 'ontologies')
        self.assertIn(str(builder.KE.actsOnRepresentation), support['ontology_basis'])
        self.assertTrue(classifier.validate_decisions([decision], rows, self.concepts))

    def test_two_distinct_direct_duties_support_core(self):
        rows, decision = self.decide('Design ontologies for reasoning.', 'Validate ontologies against source constraints.')
        self.assertEqual(decision['proposed_classification'], 'Core KE')
        self.assertEqual(len(decision['supporting_evidence']), 2)
        classifier.validate_decisions([decision], rows, self.concepts)

    def test_one_direct_duty_and_duplicate_views_do_not_establish_core(self):
        for texts in (('Design ontologies.',), ('Design ontologies.', 'Design ontologies.')):
            _, decision = self.decide(*texts)
            self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')

    def test_title_changes_never_change_classification(self):
        rows = source_rows('Build RESTful APIs.', title='Knowledge Engineer Ontology Architect')
        first = classifier.classify_job(rows, self.concepts)
        changed = copy.deepcopy(rows); changed[0]['source_title'] = 'Unrelated title'
        second = classifier.classify_job(changed, self.concepts)
        self.assertEqual(first['proposed_classification'], second['proposed_classification'])
        self.assertEqual(first['supporting_evidence'], second['supporting_evidence'])

    def test_generic_technical_work_abstains_instead_of_adjacent_or_neither(self):
        _, decision = self.decide('Build RESTful APIs.', 'Maintain CI/CD pipelines.')
        self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')
        self.assertEqual(decision['triggered_rules'], ['U1'])

    def test_empty_evidence_abstains_even_with_a_core_title(self):
        decision = classifier.classify_job([], self.concepts, case_id='SYNTHETIC', source_title='Ontology Engineer')
        self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')
        self.assertFalse(decision['supporting_evidence'])

    def test_explicit_supporting_semantic_system_link_is_adjacent(self):
        rows, decision = self.decide('Build ingestion frameworks to feed semantic reasoning engines.')
        self.assertEqual(decision['proposed_classification'], 'Adjacent Technical')
        support = decision['supporting_evidence'][0]
        self.assertEqual(support['concept_uri'], classifier.EXP + 'SemanticSystemSupport')
        self.assertNotIn('occupational concept', support['concept_relation'])
        classifier.validate_decisions([decision], rows, self.concepts)

    def test_ai_mentions_and_cross_duty_connections_do_not_establish_adjacent(self):
        for texts in (('Build ingestion frameworks to feed AI models.',),
                      ('Build ingestion frameworks.', 'Maintain semantic reasoning engines.')):
            _, decision = self.decide(*texts)
            self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')

    def test_api_product_names_and_collateral_are_not_representation_work(self):
        for text in ('Build reports about ontologies.', 'Own ontology documentation.',
                     'Build APIs for a product called Knowledge Graph.', 'Build graph databases.',
                     'Maintain familiarity with ontologies.'):
            with self.subTest(text=text):
                _, decision = self.decide(text)
                self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')

    def test_negation_and_conditional_context_cannot_establish_core(self):
        for text in ('Own ontologies without designing knowledge representations.',
                     'Build ontologies as a hypothetical example.'):
            _, decision = self.decide(text)
            self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')
        rows = source_rows('Own ontologies.')
        rows[0]['section_context_text'] = 'Your responsibilities may also include:'
        decision = classifier.classify_job(rows, self.concepts)
        self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')

    def test_neither_requires_corroborated_positive_alternative_function(self):
        rows, decision = self.decide('Collaborate to negotiate and close client agreements.',
                                    'Build and grow relationships at target accounts to drive upsell.')
        self.assertEqual(decision['proposed_classification'], 'Neither')
        self.assertEqual(len(decision['supporting_evidence']), 2)
        classifier.validate_decisions([decision], rows, self.concepts)
        _, one = self.decide('Collaborate to negotiate and close client agreements.')
        self.assertEqual(one['proposed_classification'], 'Insufficient Evidence')

    def test_mixed_or_unmapped_representation_evidence_prevents_neither(self):
        business = ('Collaborate to negotiate and close client agreements.',
                    'Build relationships at accounts to drive upsell.')
        for extra in ('Own ontologies.', 'Build reports about ontologies.', 'Build RESTful APIs.'):
            _, decision = self.decide(*business, extra)
            self.assertEqual(decision['proposed_classification'], 'Insufficient Evidence')

    def test_bold_category_clause_provenance_keeps_original_offsets(self):
        rows = source_rows(body='<h3>Key Responsibilities</h3><ul><li><strong>Pipeline Engineering:</strong> Build ingestion frameworks to feed semantic reasoning engines.</li></ul>')
        decision = classifier.classify_job(rows, self.concepts)
        self.assertEqual(decision['proposed_classification'], 'Adjacent Technical')
        support = decision['supporting_evidence'][0]
        self.assertGreater(support['clause_span_start'], rows[0]['span_start_codepoint'])
        self.assertTrue(support['quote'].startswith('Pipeline Engineering:'))
        classifier.validate_decisions([decision], rows, self.concepts)

    def test_fabricated_decision_quote_concept_or_rule_is_rejected(self):
        rows, decision = self.decide('Own ontologies.')
        for field in ('classification', 'quote', 'concept', 'rule'):
            wrong = copy.deepcopy(decision)
            if field == 'classification': wrong['proposed_classification'] = 'Neither'
            elif field == 'quote': wrong['supporting_evidence'][0]['quote'] = 'Invented evidence'
            elif field == 'concept': wrong['supporting_evidence'][0]['concept_uri'] = 'urn:invented'
            else: wrong['supporting_evidence'][0]['rule_id'] = 'INVENTED'
            with self.subTest(field=field), self.assertRaises(transport.TransportError):
                classifier.validate_decisions([wrong], rows, self.concepts)

    def test_human_ground_truth_stays_blank_independent_of_machine_proposal(self):
        rows, decision = self.decide('Own ontologies.')
        human = list(csv.DictReader(io.StringIO(classifier.human_csv([decision]))))[0]
        self.assertEqual(human, {'case_id': 'SYNTHETIC', 'human_classification': '', 'reviewer_id': '', 'reviewer_notes': ''})
        self.assertNotIn('Core KE', classifier.human_csv([decision]))
        wrong = copy.deepcopy(decision); wrong['human_ground_truth']['classification'] = 'Core KE'
        with self.assertRaises(transport.TransportError): classifier.validate_decisions([wrong], rows, self.concepts)

    def test_taxonomy_and_new_concepts_remain_explicitly_experimental(self):
        self.assertIn('approval pending', self.concepts[str(classifier.ROLE['knowledge-engineer'])]['status'])
        self.assertIn('not a frozen taxonomy occupation', self.concepts[classifier.EXP + 'SemanticSystemSupport']['status'])
        self.assertFalse(any(k.endswith('Approved') for k in self.concepts))


class DecisionPage(HTMLParser):
    def __init__(self): super().__init__(); self.cards = []; self.resources = []; self.links = []
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'data-decision' in attrs: self.cards.append(attrs['data-decision'])
        if 'src' in attrs: self.resources.append(attrs['src'])
        if tag == 'link': self.resources.append(attrs.get('href'))
        if tag == 'a': self.links.append(attrs.get('href', ''))


class AuthenticDecisionTests(unittest.TestCase):
    def test_all_six_saved_graphs_produce_explainable_proposals(self):
        paths = [os.environ.get(k) for k in ('STAGE7_VNEXT_GRAPH_DIR', 'STAGE7_VNEXT_REVIEW_PACKET_DIR', 'STAGE7_DEVELOPMENT_RESULTS')]
        self.assertTrue(all(paths), 'Set the saved Development graph, packet and result paths')
        rows, _ = evidence.collect(*(Path(p) for p in paths))
        concepts = classifier.vocabulary(); decisions = classifier.classify_all(rows, concepts)
        self.assertEqual(len(decisions), 6)
        self.assertEqual(sum(d['responsibilities_considered'] for d in decisions), 49)
        self.assertTrue(classifier.validate_decisions(decisions, rows, concepts))
        self.assertTrue(all(d['proposed_classification'] in classifier.CATEGORIES for d in decisions))
        self.assertTrue(all(all(v == '' for v in d['human_ground_truth'].values()) for d in decisions))
        for decision in decisions:
            if decision['proposed_classification'] != 'Insufficient Evidence':
                self.assertTrue(decision['supporting_evidence'])
                self.assertTrue(all(s['ontology_basis'] and s['concept_uri'] in concepts for s in decision['supporting_evidence']))
        page = DecisionPage(); page.feed(classifier.decision_html(decisions))
        self.assertEqual(len(page.cards), 6)
        self.assertEqual(page.resources, [])
        self.assertTrue(all(h.startswith('#') or h == 'human-ground-truth.csv' for h in page.links))
        self.assertEqual(len(list(csv.DictReader(io.StringIO(classifier.human_csv(decisions))))), 6)


if __name__ == '__main__':
    unittest.main()

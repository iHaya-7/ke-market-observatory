"""Saved-graph query completeness, source resolution, CSV and offline review UI."""
import base64
import copy
import csv
from html.parser import HTMLParser
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

import consumer_vnext as consumer
import graph_vnext as builder
import review_export_vnext as review
import transport_vnext as transport
from rdflib import Literal, URIRef
from rdflib.namespace import RDF
from test_transport_vnext import fixture


def memory_source(artifact):
    return base64.b64decode(artifact['bytes_base64'], validate=True)


def sample(record=None):
    packet = fixture(record)
    graph = builder.build_graph(packet, consumer.consume(packet))
    return packet, graph


def rows_for(packet, graph):
    return review.query_rows(graph, packet, reader=memory_source)


class ReviewHTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.cards = 0; self.selects = []; self.current_select = None
        self.textareas = []; self.current_textarea = None; self.resources = []; self.links = []; self.csp = ''

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'article' and 'data-responsibility' in attrs: self.cards += 1
        if tag == 'select': self.current_select = []; self.selects.append(self.current_select)
        if tag == 'option' and self.current_select is not None: self.current_select.append(attrs)
        if tag == 'textarea': self.current_textarea = []; self.textareas.append(self.current_textarea)
        if 'src' in attrs: self.resources.append(attrs['src'])
        if tag == 'link' and 'href' in attrs: self.resources.append(attrs['href'])
        if tag == 'a': self.links.append(attrs.get('href', ''))
        if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy': self.csp = attrs['content']

    def handle_endtag(self, tag):
        if tag == 'select': self.current_select = None
        if tag == 'textarea': self.current_textarea = None

    def handle_data(self, data):
        if self.current_textarea is not None: self.current_textarea.append(data)


class QueryTests(unittest.TestCase):
    def test_context_joins_do_not_multiply_responsibilities(self):
        record = fixture()['record']; record['description'] = '<p>Overview.</p>'
        record['lists'] = [{'text': 'Responsibilities:', 'content': '<li>Build ontologies.</li>'}]
        packet, graph = sample(record); rows = rows_for(packet, graph)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['section_context_text'], 'Responsibilities:')
        self.assertEqual(rows[0]['field_pointer'], '/record/lists/0/content')
        self.assertEqual(len(json.loads(rows[0]['section_contexts_json'])), 1)

    def test_unicode_span_is_codepoints_and_exact_source_text(self):
        record = fixture()['record']; record['description'] = '<p>😀 Intro.</p><h2>Responsibilities</h2><p>Build روابط &amp; ontologies.</p>'
        packet, graph = sample(record); row = rows_for(packet, graph)[0]
        self.assertEqual(row['responsibility_text'], 'Build روابط & ontologies.')
        self.assertEqual(row['field_context_text'][row['span_start_codepoint']:row['span_end_codepoint']], row['responsibility_text'])
        self.assertEqual(row['capture_sha256'], packet['captures'][0]['sha256'])

    def test_identical_text_at_two_distinct_spans_is_two_rows(self):
        record = fixture()['record']; record['description'] = '<h2>Responsibilities</h2><p>Build ontologies.</p><p>Build ontologies.</p>'
        packet, graph = sample(record); rows = rows_for(packet, graph)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['responsibility_text'], rows[1]['responsibility_text'])
        self.assertNotEqual(rows[0]['responsibility_id'], rows[1]['responsibility_id'])
        self.assertNotEqual(rows[0]['span_start_codepoint'], rows[1]['span_start_codepoint'])

    def test_missing_graph_link_or_action_provenance_is_incomplete(self):
        for predicate in (builder.KE.hasResponsibility, builder.PROV.wasDerivedFrom):
            packet, graph = sample()
            if predicate == builder.KE.hasResponsibility:
                graph.remove((None, predicate, None))
            else:
                statement = next(s for s in graph.subjects(RDF.predicate, builder.KE.actionText))
                graph.remove((statement, predicate, None))
            with self.subTest(predicate=predicate), self.assertRaisesRegex(transport.TransportError, 'incomplete'):
                rows_for(packet, graph)

    def test_duplicate_action_evidence_is_rejected(self):
        packet, graph = sample()
        statement = next(graph.subjects(RDF.predicate, builder.KE.actionText))
        original = graph.value(statement, builder.PROV.wasDerivedFrom)
        duplicate = URIRef('urn:synthetic:duplicate-evidence')
        for p, obj in list(graph.predicate_objects(original)): graph.add((duplicate, p, obj))
        graph.add((statement, builder.PROV.wasDerivedFrom, duplicate))
        with self.assertRaisesRegex(transport.TransportError, 'duplicate'):
            rows_for(packet, graph)

    def test_original_capture_bytes_are_verified_not_only_embedded_packet(self):
        packet, graph = sample()
        with self.assertRaisesRegex(transport.TransportError, 'capture hash'):
            review.query_rows(graph, packet, reader=lambda a: memory_source(a) + b' ')

    def test_invalid_rendered_locator_is_rejected(self):
        packet, graph = sample()
        statement = next(graph.subjects(RDF.predicate, builder.KE.actionText))
        evidence = graph.value(statement, builder.PROV.wasDerivedFrom)
        locator = json.loads(str(graph.value(evidence, builder.KE.passageLocator)))
        locator['end'] = 999999
        graph.set((evidence, builder.KE.passageLocator, builder.string(transport.canonical(locator))))
        with self.assertRaisesRegex(transport.TransportError, 'bounds'):
            rows_for(packet, graph)

    def test_conditional_section_context_is_exact_and_resolvable(self):
        record = fixture()['record']; record['description'] = '<p>Your responsibilities may also include:</p><ul><li>Supporting delivery.</li></ul>'
        packet, graph = sample(record); row = rows_for(packet, graph)[0]
        self.assertEqual(row['section_context_text'], 'Your responsibilities may also include:')
        context = json.loads(row['section_contexts_json'])[0]
        self.assertEqual(consumer.resolve_evidence(packet, context['locator']), context['text'])

    def test_csv_round_trip_preserves_quotes_newlines_unicode_and_blank_judgments(self):
        packet, graph = sample(); rows = rows_for(packet, graph)
        rows[0]['responsibility_text'] = 'Build "روابط", schemas\nand entities — 😀.'
        output = review.csv_text(rows)
        self.assertEqual(output.encode('utf-8').decode('utf-8'), output)
        parsed = list(csv.DictReader(io.StringIO(output)))
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]['responsibility_text'], rows[0]['responsibility_text'])
        self.assertEqual(tuple(parsed[0]), review.COLUMNS)
        self.assertTrue(all(parsed[0][field] == '' for field in review.REVIEW_FIELDS))

    def test_html_is_offline_escaped_and_starts_with_blank_review_fields(self):
        packet, graph = sample(); rows = rows_for(packet, graph)
        rows[0]['responsibility_text'] = '</script><img src="https://invalid.test/leak">'
        page = review.html_text(rows); parsed = ReviewHTML(); parsed.feed(page)
        self.assertEqual(parsed.cards, 1)
        self.assertEqual(parsed.resources, [])
        self.assertTrue(all(link.startswith('#') or link == 'responsibilities.csv' for link in parsed.links))
        self.assertIn("connect-src 'none'", parsed.csp)
        self.assertEqual(len(parsed.selects), 2)
        self.assertTrue(all(options[0]['value'] == '' for options in parsed.selects))
        self.assertFalse(any('selected' in option and option.get('value') for options in parsed.selects for option in options))
        self.assertTrue(all(not text for text in parsed.textareas))
        self.assertNotIn('<img src="https://invalid.test/leak">', page)
        self.assertIn('\\u003c/script\\u003e', page)
        for forbidden in ('fetch(', 'XMLHttpRequest', 'WebSocket', 'localStorage'):
            self.assertNotIn(forbidden, review.SCRIPT)

    def test_bundle_is_utf8_complete_and_never_overwrites(self):
        packet, graph = sample(); rows = rows_for(packet, graph)
        with tempfile.TemporaryDirectory(prefix='review-export-test-', dir=transport.ROOT / 'learning-local') as temp:
            self.assertTrue(Path(temp).resolve().is_relative_to(transport.ROOT / 'learning-local'))
            output = Path(temp) / 'new-review'
            review.write_bundle(rows, output)
            parsed = list(csv.DictReader(io.StringIO((output / 'responsibilities.csv').read_text(encoding='utf-8'))))
            self.assertEqual(len(parsed), 1)
            self.assertTrue((output / 'review.html').read_text(encoding='utf-8').startswith('<!doctype html>'))
            before = (output / 'responsibilities.csv').read_bytes()
            with self.assertRaisesRegex(transport.TransportError, 'already exists'):
                review.write_bundle(rows, output)
            self.assertEqual((output / 'responsibilities.csv').read_bytes(), before)

    def test_bundle_rejects_prefilled_human_judgments(self):
        packet, graph = sample(); rows = rows_for(packet, graph)
        rows[0][review.REVIEW_FIELDS[0]] = 'Yes'
        with tempfile.TemporaryDirectory(prefix='review-export-test-', dir=transport.ROOT / 'learning-local') as temp:
            self.assertTrue(Path(temp).resolve().is_relative_to(transport.ROOT / 'learning-local'))
            with self.assertRaisesRegex(transport.TransportError, 'blank'):
                review.write_bundle(rows, Path(temp) / 'new-review')


class DevelopmentQueries(unittest.TestCase):
    def test_all_49_saved_development_responsibilities_and_contexts(self):
        graph_dir = os.environ.get('STAGE7_VNEXT_GRAPH_DIR')
        packet_dir = os.environ.get('STAGE7_VNEXT_REVIEW_PACKET_DIR')
        results = os.environ.get('STAGE7_DEVELOPMENT_RESULTS')
        self.assertTrue(graph_dir and packet_dir and results, 'Set the saved Development graph/packet/result paths')
        rows, hashes = review.collect(Path(graph_dir), Path(packet_dir), Path(results))
        self.assertEqual(len(rows), 49)
        self.assertEqual(len({r['responsibility_id'] for r in rows}), 49)
        self.assertEqual(sorted(Counter(r['case_id'] for r in rows).values()), [3, 5, 8, 8, 8, 17])
        self.assertEqual(len(hashes), 18)
        parsed = list(csv.DictReader(io.StringIO(review.csv_text(rows))))
        self.assertEqual(len(parsed), 49)
        self.assertTrue(all(r[f] == '' for r in parsed for f in review.REVIEW_FIELDS))
        page = ReviewHTML(); page.feed(review.html_text(rows))
        self.assertEqual(page.cards, 49)
        self.assertEqual(len(page.selects), 98)
        self.assertEqual(len(page.textareas), 49)
        self.assertEqual(len({link for link in page.links if link.startswith('#case-')}), 6)


from collections import Counter


if __name__ == '__main__':
    unittest.main()

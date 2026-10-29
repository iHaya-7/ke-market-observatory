"""Experimental source-fact RDF builder; no classifier, approval or evaluation."""
import argparse
import base64
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote
from uuid import uuid4

import consumer_vnext as consumer
import transport_vnext as transport

HERE = Path(__file__).resolve().parent
sys.path.insert(0, os.environ.get('KE_LOCAL_DEPS', str(
    transport.ROOT / 'learning-local/development-v2-deps/Lib/site-packages')))
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, XSD

KE = Namespace('urn:ke-market-observatory:ontology:')
VX = Namespace('urn:ke-market-observatory:experimental:source-transport-vnext:')
PROV = Namespace('http://www.w3.org/ns/prov#')
BASE = 'urn:ke-market-observatory:experimental:source-transport-vnext:instance:'
VERSION = 'development-source-graph-vnext-2'


def string(value):
    return Literal(value, datatype=XSD.string, normalize=False)


def raw_json(value):
    return Literal(transport.canonical(value), datatype=RDF.JSON, normalize=False)


def numeric(value):
    """Only original JSON numbers, never bool/string/coerced or invented values."""
    if type(value) not in (int, float):
        return None
    try:
        number = Decimal(str(value))
        return number if number.is_finite() and number >= 0 else None
    except InvalidOperation:
        return None


def check_consumer(packet, consumed):
    transport.verify_packet(packet)
    transport.require(transport.canonical(consumer.consume(packet)) == transport.canonical(consumed),
                      'Consumer output does not match verified source packet')


def implementation_hashes():
    paths = [HERE / p for p in ('graph_vnext.py', 'consumer_vnext.py', 'transport_vnext.py',
                               'validate_graph_vnext.py', 'vocabulary_vnext.ttl', 'shapes_vnext.ttl')]
    paths.append(Path(consumer.primitives.__file__))
    paths.append(transport.ROOT / 'knowledge-engineering/04-ontology/ontology.ttl')
    return {p.relative_to(transport.ROOT).as_posix(): transport.digest(p.read_bytes()) for p in paths}


def build_graph(packet, consumed, *, activity=None, generated_at=None):
    """Return an independent graph, retaining every field and exact evidence owner.

    Reified SourceAssertion records distinguish source evidence from build metadata.
    Unknown salary facts are absent. Roles exist only when duties were extracted;
    title strings never supply duties or occupational concept assignments.
    """
    check_consumer(packet, consumed)
    g = Graph()
    for prefix, ns in (('ke', KE), ('vx', VX), ('prov', PROV), ('dct', DCTERMS)):
        g.bind(prefix, ns)
    run = activity or URIRef(BASE + 'build:' + str(uuid4()))
    now = generated_at or Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime)
    agent = URIRef(BASE + 'software:' + VERSION)
    g.add((run, RDF.type, PROV.Activity))
    g.add((run, RDF.type, VX.GraphBuild))
    g.add((agent, RDF.type, PROV.SoftwareAgent))
    g.add((run, PROV.wasAssociatedWith, agent))
    g.add((run, PROV.startedAtTime, now))
    g.add((run, VX.implementationHashesJSON, raw_json(implementation_hashes())))
    g.add((run, VX.transportSHA256, string(transport.digest(transport.canonical(packet).encode()))))
    g.add((run, VX.consumerSHA256, string(transport.digest(transport.canonical(consumed).encode()))))
    identity = packet['identity']
    stem = BASE + 'posting:' + quote(identity['source_id'], safe='') + ':' + quote(identity['source_job_id'], safe='')
    posting = URIRef(stem)
    g.add((posting, RDF.type, KE.JobPosting))
    g.add((posting, PROV.wasGeneratedBy, run))
    g.add((run, VX.posting, posting))
    g.add((run, VX.caseId, string(packet['case_id'])))
    g.add((run, VX.extractedResponsibilityCount, Literal(len(consumed['responsibilities']), datatype=XSD.integer)))

    artifacts = {}
    for artifact in packet['captures']:
        data = base64.b64decode(artifact['bytes_base64'], validate=True)
        doc = transport.loads(data)
        node = URIRef(BASE + 'capture:sha256:' + artifact['sha256'])
        artifacts[artifact['sha256']] = node
        g.add((node, RDF.type, KE.EvidenceArtifact))
        g.add((node, KE.sha256, string(artifact['sha256'])))
        g.add((node, KE.artifactLocation, Literal(artifact['path'], datatype=XSD.anyURI)))
        g.add((node, KE.capturedAt, Literal(doc['capturedAtUtc'], datatype=XSD.dateTime)))
        g.add((node, DCTERMS.source, URIRef(identity['source_url'])))
        g.add((run, PROV.used, node))

    def passage(ref, *, span=None):
        source_value = transport.resolve_reference(packet, ref)
        locator = dict(span) if span is not None else {'source': ref, 'pointer': ref['pointer'], 'transform': 'json'}
        resolved = consumer.resolve_evidence(packet, span) if span is not None else transport.canonical(source_value)
        key = transport.digest(transport.canonical(locator).encode())
        node = URIRef(BASE + 'evidence:' + key)
        g.add((node, RDF.type, KE.EvidencePassage))
        g.add((node, KE.inArtifact, artifacts[ref['capture_sha256']]))
        g.add((node, KE.passageLocator, string(transport.canonical(locator))))
        g.add((node, KE.passageText, string(resolved)))
        g.add((node, VX.sourceValueJSON, raw_json(source_value)))
        g.add((node, PROV.wasGeneratedBy, run))
        return node

    def assertion(subject, predicate, value, evidence, policy='Exact original source value'):
        """Bind every source-derived triple to its own concrete source evidence."""
        g.add((subject, predicate, value))
        key = transport.digest(transport.canonical([subject.n3(), predicate.n3(), value.n3()]).encode())
        statement = URIRef(BASE + 'assertion:' + key)
        g.add((statement, RDF.type, RDF.Statement))
        g.add((statement, RDF.type, VX.SourceAssertion))
        for prop, obj in ((RDF.subject, subject), (RDF.predicate, predicate), (RDF.object, value)):
            g.add((statement, prop, obj))
        for p in evidence:
            g.add((statement, PROV.wasDerivedFrom, p))
        g.add((statement, VX.derivation, string(policy)))
        g.add((statement, PROV.wasGeneratedBy, run))

    primary = packet['primary_capture_sha256']
    primary_doc = transport.loads(base64.b64decode(next(
        a['bytes_base64'] for a in packet['captures'] if a['sha256'] == primary), validate=True))
    for prop, key in ((VX.sourceId, 'sourceId'), (VX.sourceJobId, 'sourceJobId')):
        ref = {'capture_sha256': primary, 'pointer': '/' + key}
        assertion(posting, prop, string(str(primary_doc[key])), [passage(ref)],
                  'Source identifier rendered as a string; exact original JSON value also retained')
    if 'sourceType' in primary_doc:
        ref = {'capture_sha256': primary, 'pointer': '/sourceType'}
        assertion(posting, VX.sourceType, string(primary_doc['sourceType']), [passage(ref)])
    title = consumed['title_metadata']
    title_evidence = passage(title['reference'])
    assertion(posting, DCTERMS.title, string(title['value']), [title_evidence])
    g.add((posting, VX.titleEvidence, title_evidence))
    raw_fields = {}
    for key, ref in consumed['raw_field_sources'].items():
        raw_fields[key] = passage(ref)
        g.add((posting, VX.rawFieldEvidence, raw_fields[key]))
    url_field = next(k for k in (
        ('hostedUrl',) if identity['source_type'] == 'lever' else
        ('absolute_url',) if identity['source_type'] == 'greenhouse' else ('url', 'application_url', 'shortlink'))
        if packet['record'].get(k))
    assertion(posting, DCTERMS.source, URIRef(identity['source_url']), [raw_fields[url_field]])
    for artifact in packet['captures']:
        node = artifacts[artifact['sha256']]
        ref = {'capture_sha256': artifact['sha256'], 'pointer': '/capturedAtUtc'}
        assertion(node, KE.capturedAt, g.value(node, KE.capturedAt), [passage(ref)],
                  'Original capture time; value-preserving xsd:dateTime lexical normalization')
        assertion(node, DCTERMS.source, URIRef(identity['source_url']), [raw_fields[url_field]])

    views = {}
    for doc in consumed['documents']:
        node = URIRef(stem + ':field-view:' + transport.digest(doc['field_pointer'].encode()))
        views[doc['field_pointer']] = node
        g.add((node, RDF.type, VX.FieldView))
        g.add((posting, VX.fieldView, node))
        p = passage(doc['source'])
        assertion(node, VX.renderedText, string(doc['text']), [p], 'Versioned field rendering: ' + doc['transform'])
        g.add((node, VX.fieldPointer, string(doc['field_pointer'])))
        g.add((node, VX.transform, string(doc['transform'])))
        g.add((node, KE.evidencePassage, p))
        g.add((node, PROV.wasGeneratedBy, run))
        if doc['section_label']:
            label = doc['section_label']
            assertion(node, VX.sectionLabel, string(label['value']), [passage(label['source'])])
    for doc in consumed['documents']:
        if doc['alternative_to']:
            g.add((views[doc['field_pointer']], VX.alternativeViewOf, views[doc['alternative_to']]))

    role = URIRef(stem + ':role')
    for i, duty in enumerate(consumed['responsibilities']):
        node = URIRef(stem + ':responsibility:' + str(i))
        p = passage(duty['locator']['source'], span=duty['locator'])
        context = passage(duty['locator']['source'])
        g.add((p, KE.contextPassage, context))
        refs = [p]
        if duty.get('section_context'):
            section = duty['section_context']
            section_evidence = passage(section['source'], span=section)
            g.add((p, KE.contextPassage, section_evidence))
            refs.append(section_evidence)
        if duty['section_metadata']:
            label = passage(duty['section_metadata']['source'])
            g.add((p, KE.contextPassage, label))
            refs.append(label)
        g.add((role, RDF.type, KE.JobRole))
        g.add((role, PROV.wasGeneratedBy, run))
        g.add((node, RDF.type, KE.Responsibility))
        g.add((node, PROV.wasGeneratedBy, run))
        assertion(posting, KE.advertisesRole, role, refs, 'Advertised function represented only by extracted duty passages')
        assertion(role, KE.hasResponsibility, node, refs, 'Field-scoped machine extraction; no occupational classification')
        assertion(node, KE.actionText, string(duty['text']), [p], 'Exact rendered span, not title-derived')
        for ref in refs:
            g.add((node, KE.evidencePassage, ref))

    for i, salary in enumerate(consumed['structured_salary']):
        node = URIRef(stem + ':salary:' + str(i))
        p = passage(salary['source'])
        g.add((node, RDF.type, KE.SalaryObservation))
        g.add((node, RDF.type, VX.StructuredSalary))
        g.add((node, PROV.wasGeneratedBy, run))
        g.add((node, KE.evidencePassage, p))
        assertion(posting, KE.hasSalaryObservation, node, [p])
        assertion(node, VX.sourceValueJSON, raw_json(salary['raw']), [p])
        # No assumption about base/total, applicability, employer, tax or eligibility.
        for missing in ('compensation_basis', 'pay_market', 'eligibility', 'band_applicability'):
            g.add((node, VX.unresolvedDimension, string(missing)))
        if salary['kind'] != 'source-structured-salary':
            g.add((node, VX.unresolvedDimension, string('structured_dimensions_unmapped')))
            continue
        raw = salary['raw']; sources = salary['field_sources']
        lo, hi = numeric(raw.get('min')), numeric(raw.get('max'))
        if lo is not None and hi is not None and lo > hi:
            lo = hi = None  # Original invalid range remains in the JSON evidence.
            g.add((node, VX.unresolvedDimension, string('reversed_numeric_range')))
        for key, prop, number in (('min', KE.lowerAmount, lo), ('max', KE.upperAmount, hi)):
            if number is not None:
                lexical = format(number, 'f')
                if '.' not in lexical:
                    lexical += '.0'
                assertion(node, prop, Literal(lexical, datatype=XSD.decimal, normalize=False),
                          [passage(sources[key])], 'Original JSON number to RDF decimal; no unit conversion')
            elif key in raw:
                g.add((node, VX.unresolvedDimension, string('unmapped_' + key)))
        if isinstance(raw.get('currency'), str) and raw['currency'].strip():
            assertion(node, KE.currency, string(raw['currency']), [passage(sources['currency'])])
        else:
            g.add((node, VX.unresolvedDimension, string('currency')))
        if 'interval' in raw:
            assertion(node, VX.intervalTokenJSON, raw_json(raw['interval']), [passage(sources['interval'])])
        period = salary['dimensions']['explicit_period']
        if period is not None:
            assertion(node, KE.payPeriod, string(period), [passage(sources['interval'])],
                      'Explicit Lever interval token mapped by consumer PERIODS; no inferred unit')
        else:
            g.add((node, VX.unresolvedDimension, string('pay_period')))
    return g


def main():
    parser = argparse.ArgumentParser(description='Build six experimental Development RDF graphs; no classifier.')
    parser.add_argument('--input-dir', type=Path, required=True, help='Existing vNext packet/consumer directory')
    parser.add_argument('--blocked-results', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True, help='New directory below ignored learning-local')
    args = parser.parse_args()
    root = transport.ROOT
    input_dir = transport.safe_path(root, args.input_dir.resolve().relative_to(root), Path('learning-local'))
    output = transport.safe_path(root, args.output_dir.resolve().relative_to(root), Path('learning-local'))
    transport.require(not output.exists(), 'Output already exists; no overwrites')
    transport.require(subprocess.run(['git', 'check-ignore', '--quiet', '--', str(output / 'probe.json')],
                                     cwd=root).returncode == 0, 'Output must be Git-ignored')
    from validate_graph_vnext import validate_graph
    prepared = []
    for case in transport.blocked_cases(root, args.blocked_results):
        cid = case['case_id']
        packet_path = transport.safe_path(root, (input_dir / (cid + '.transport.json')).relative_to(root), Path('learning-local'))
        consumed_path = transport.safe_path(root, (input_dir / (cid + '.consumer.json')).relative_to(root), Path('learning-local'))
        packet = transport.loads(packet_path.read_bytes())
        consumed = transport.loads(consumed_path.read_bytes())
        # Anchor the saved packet to the original Development indexes/capture bytes.
        transport.require(transport.canonical(packet) == transport.canonical(transport.load_case(root, case)),
                          'Saved packet differs from authenticated local Development inputs')
        graph = build_graph(packet, consumed)
        validation = validate_graph(graph, packet, consumed)
        serialized = graph.serialize(format='turtle')
        from rdflib.compare import isomorphic
        transport.require(isomorphic(graph, Graph().parse(data=serialized, format='turtle')), 'RDF round-trip failure')
        prepared.append((cid, serialized, validation))
    output.mkdir(parents=True, exist_ok=False)
    summary = []
    for cid, serialized, validation in prepared:
        with (output / (cid + '.ttl')).open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(serialized)
        with (output / (cid + '.validation.json')).open('x', encoding='utf-8') as handle:
            handle.write(transport.canonical(validation) + '\n')
        summary.append({'case_id': cid, **validation, 'rdf_round_trip': True})
    with (output / 'summary.json').open('x', encoding='utf-8') as handle:
        handle.write(transport.canonical({'version': VERSION, 'scope': 'Development only', 'cases': summary}) + '\n')
    print(transport.canonical({'graphs_built': len(summary), 'experimental_conforms': sum(r['experimental_shacl_conforms'] for r in summary),
                               'zero_responsibility_cases': [r['case_id'] for r in summary if r['responsibilities'] == 0],
                               'output_dir': output.relative_to(root).as_posix()}))


if __name__ == '__main__':
    main()

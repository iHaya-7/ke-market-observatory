"""Offline ABox builder: legacy private mappings or manifest-bound HTML captures."""
from pathlib import Path
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import quote, urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
if not os.environ.get('KE_LOCAL_DEPS'):
    sys.path.insert(0, str(ROOT / 'learning-local/stage5-deps'))
sys.path.insert(0, os.environ.get('KE_LOCAL_DEPS', str(ROOT / 'learning-local/stage6-deps')))
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS, DCTERMS

HERE = Path(__file__).resolve().parent
LOCAL = ROOT / 'knowledge-engineering/00-baseline/local-corpus/development/stage5'
CORPUS = ROOT / 'knowledge-engineering/00-baseline/local-corpus/20261021T125408Z-ebb0b062'
CASES = ('EVAL-0d7b2c3f9f39cbcc', 'EVAL-4847917fd586d111', 'EVAL-5808d42f328be89c')
KE = Namespace('urn:ke-market-observatory:ontology:')
PROV = Namespace('http://www.w3.org/ns/prov#')
BASE = 'urn:ke-market-observatory:instance:'
sys.path.insert(0, str(HERE))
from posting_evidence import VERSION, load_captures


def assessment(g, target, kind, outcome, rationale, evidence, run, agent, now, unresolved=()):
    """Shared machine-only assessment writer, including interpretations/abstentions."""
    node = URIRef(str(run) + ':assessment:' + str(uuid4()))
    for cls in (KE.Assessment, KE.MachineAssessment):
        g.add((node, RDF.type, cls))
    g.add((node, KE.assessmentTarget, target))
    for prop, value in [('assessmentKind', kind), ('outcome', outcome), ('rationale', rationale),
                        ('criteriaReference', VERSION + ' builder-sha256:' + sha(Path(__file__)))]:
        g.add((node, KE[prop], Literal(value, datatype=XSD.string)))
    for value in unresolved:
        g.add((node, KE.unresolvedFact, Literal(value, datatype=XSD.string)))
    for p in evidence:
        g.add((node, KE.evidencePassage, p))
    g.add((node, OWL.versionInfo, Literal(VERSION)))
    g.add((node, PROV.wasGeneratedBy, run))
    g.add((node, PROV.wasAttributedTo, agent))
    g.add((node, PROV.generatedAtTime, now))
    return node


def build_postings(postings):
    """Materialize extracted duties, supported mappings and separate pay bands.

    No private legacy mapping is loaded and no source or approval is written.
    """
    g = Graph()
    g.bind('ke', KE)
    g.bind('prov', PROV)
    run = URIRef(BASE + 'capture-run:' + str(uuid4()))
    agent = URIRef(BASE + 'software:' + VERSION)
    now = Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime)
    g.add((run, RDF.type, PROV.Activity))
    g.add((agent, RDF.type, PROV.SoftwareAgent))
    g.add((run, PROV.wasAssociatedWith, agent))
    import posting_evidence
    for code in (Path(__file__), Path(posting_evidence.__file__)):
        g.add((run, DCTERMS.identifier, Literal(code.name + '-sha256:' + sha(code))))
    for item in postings:
        stem = BASE + 'capture-posting:' + quote(item['source_id'], safe='') + ':' + quote(item['source_job_id'], safe='')
        posting, role = URIRef(stem), URIRef(stem + ':role')
        artifact = URIRef(BASE + 'artifact:sha256:' + item['sha256'])
        publisher = URIRef(BASE + 'publisher:' + quote(item['publisher'], safe=''))
        g.add((posting, RDF.type, KE.JobPosting))
        g.add((role, RDF.type, KE.JobRole))
        g.add((posting, KE.advertisesRole, role))
        for identifier in (item['case_id'], 'sourceId:' + item['source_id'], 'sourceJobId:' + item['source_job_id']):
            g.add((posting, DCTERMS.identifier, Literal(identifier)))
        g.add((posting, DCTERMS.title, Literal(item['title'])))
        g.add((posting, DCTERMS.description, Literal(item['responsibility_coverage'])))
        g.add((posting, DCTERMS.source, URIRef(item['source_url'])))
        g.add((artifact, RDF.type, KE.EvidenceArtifact))
        g.add((artifact, DCTERMS.source, URIRef(item['source_url'])))
        g.add((publisher, RDF.type, PROV.Agent))
        g.add((publisher, RDFS.label, Literal(item['publisher'])))
        g.add((artifact, DCTERMS.publisher, publisher))
        g.add((artifact, DCTERMS.identifier, Literal(item['source_job_id'])))
        g.add((artifact, KE.sha256, Literal(item['sha256'], datatype=XSD.string)))
        location = Path(item['archive']).resolve().relative_to(ROOT).as_posix() + '#' + item['member']
        g.add((artifact, KE.artifactLocation, Literal(location, datatype=XSD.anyURI)))
        g.add((artifact, KE.capturedAt, Literal(item['captured_at'], datatype=XSD.dateTime)))
        g.add((artifact, DCTERMS.description, Literal(item['identity_status'])))
        refs = {}
        for p in item['passages']:
            node = URIRef(stem + ':' + p['id'])
            refs[p['id']] = node
            g.add((node, RDF.type, KE.EvidencePassage))
            g.add((node, KE.inArtifact, artifact))
            g.add((node, KE.passageLocator, Literal(json.dumps(p['locator'], sort_keys=True), datatype=XSD.string)))
            g.add((node, KE.passageText, Literal(p['text'], datatype=XSD.string)))
        context = refs[item['context_passage']]
        g.add((posting, KE.evidencePassage, context))
        for section in item['responsibility_sections']:
            g.add((role, KE.evidencePassage, refs[section]))
        for i, duty in enumerate(item['responsibilities']):
            node = URIRef(stem + ':duty:' + str(i))
            g.add((node, RDF.type, KE.Responsibility))
            g.add((role, KE.hasResponsibility, node))
            g.add((node, KE.actionText, Literal(duty['text'], datatype=XSD.string)))
            p = refs[duty['passage']]
            g.add((node, KE.evidencePassage, p))
            g.add((p, KE.contextPassage, context))
            mapping = duty['mapping']
            if mapping:
                rep = URIRef(str(node) + ':representation')
                g.add((rep, RDF.type, KE.KnowledgeRepresentation))
                g.add((rep, RDFS.label, Literal(mapping['representation'])))
                g.add((node, KE.actsOnRepresentation, rep))
                g.add((rep, KE.evidencePassage, p))
                g.add((role, KE.roleConcept, URIRef('urn:ke-market-observatory:role:' + mapping['concept'])))
                assessment(g, node, 'responsibility interpretation', 'Supported representation action',
                           mapping['rationale'], [p], run, agent, now)
        for i, salary in enumerate(item['salaries']):
            node = URIRef(stem + ':salary:' + str(i))
            g.add((node, RDF.type, KE.SalaryObservation))
            g.add((posting, KE.hasSalaryObservation, node))
            g.add((node, KE.evidencePassage, refs[salary['passage']]))
            # Each observation comes from this posting's own offered band.
            g.add((node, KE.salaryForRole, role))
            if salary['market_passage']:
                g.add((node, KE.evidencePassage, refs[salary['market_passage']]))
            for prop in ('lowerAmount', 'upperAmount', 'currency', 'payPeriod', 'compensationBasis', 'payMarket', 'bandApplicability'):
                if salary[prop] is not None:
                    datatype = XSD.decimal if prop in ('lowerAmount', 'upperAmount') else XSD.string
                    g.add((node, KE[prop], Literal(str(salary[prop]), datatype=datatype)))
    return g, run, agent, now


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pointer(value, path):
    for part in path.split('/')[1:]:
        part = part.replace('~1', '/').replace('~0', '~')
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def rendered(value):
    # Versioned locator transform: unescape once, strip tags, unescape once,
    # collapse Unicode whitespace to one ASCII space, strip edges.
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', html.unescape(value))).split())


def resolve(document, locator):
    value = pointer(document, locator['pointer'])
    if locator['transform'] == 'json':
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    text = rendered(value)
    return text[locator.get('start', 0):locator.get('end', len(text))]


def main():
    mapping_path = LOCAL / 'mapping.json'
    require(mapping_path.exists(), 'Private development/stage5/mapping.json is required; no corpus discovery is performed.')
    subprocess.run(['git', 'check-ignore', '--quiet', str(mapping_path)], cwd=ROOT, check=True)
    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    require(tuple(c['case'] for c in mapping['cases']) == CASES, 'Only the fixed three Development cases are allowed.')
    schema = Graph().parse(ROOT / 'knowledge-engineering/04-ontology/ontology.ttl')
    taxonomy = Graph().parse(ROOT / 'knowledge-engineering/03-taxonomy/role-taxonomy.ttl')
    g = Graph()
    for prefix, ns in [('ke', KE), ('prov', PROV), ('dcterms', DCTERMS)]:
        g.bind(prefix, ns)
    now = Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime)
    agent = URIRef(BASE + 'software:stage5-builder')
    run = URIRef(BASE + 'run:' + str(uuid4()))
    g.add((agent, RDF.type, PROV.SoftwareAgent))
    g.add((run, RDF.type, PROV.Activity))
    g.add((run, PROV.wasAssociatedWith, agent))
    g.add((run, DCTERMS.description, Literal('Offline mapping materialization and exact source-value fidelity verification; no semantic classifier.')))
    g.add((run, DCTERMS.identifier, Literal('builder-sha256:' + sha(Path(__file__)))))
    g.add((run, DCTERMS.identifier, Literal('mapping-sha256:' + sha(mapping_path))))
    checked = []
    def string(s, p, v):
        g.add((s, p, Literal(v, datatype=XSD.string)))
    for case in mapping['cases']:
        require(case['split'] == 'development', 'Non-Development input rejected')
        path = (CORPUS / case['artifact']).resolve()
        require(path.is_relative_to(CORPUS.resolve()) and case['case'] in path.name
                and path.parts[-3] in ('details', 'originals'), 'Only case-specific original artifacts allowed')
        require(sha(path) == case['sha256'], 'Source artifact changed')
        doc = json.loads(path.read_text(encoding='utf-8'))
        require(doc['sourceId'] == case['sourceId'] and str(doc['sourceJobId']) == case['sourceJobId'], 'Source identity mismatch')
        stem = BASE + 'posting:' + quote(case['sourceId'], safe='') + ':' + quote(case['sourceJobId'], safe='')
        posting, role = URIRef(stem), URIRef(stem + ':role')
        artifact = URIRef(BASE + 'artifact:sha256:' + case['sha256'])
        publisher = URIRef(BASE + 'publisher:' + quote(case['publisher'], safe=''))
        g.add((publisher, RDF.type, PROV.Agent))
        g.add((publisher, RDFS.label, Literal(case['publisher'])))
        g.add((posting, RDF.type, KE.JobPosting))
        for identifier in [case['case'], 'sourceId:' + case['sourceId'], 'sourceJobId:' + case['sourceJobId']]:
            g.add((posting, DCTERMS.identifier, Literal(identifier)))
        source = pointer(doc, case['urlPointer'])
        g.add((posting, DCTERMS.source, URIRef(source)))
        g.add((posting, DCTERMS.title, Literal(pointer(doc, case['titlePointer']))))
        g.add((posting, KE.advertisesRole, role))
        g.add((role, RDF.type, KE.JobRole))
        g.add((artifact, RDF.type, KE.EvidenceArtifact))
        g.add((artifact, DCTERMS.source, URIRef(source)))
        g.add((artifact, DCTERMS.publisher, publisher))
        for identifier in [case['sourceId'], case['sourceJobId']]:
            g.add((artifact, DCTERMS.identifier, Literal(identifier)))
        string(artifact, KE.sha256, case['sha256'])
        g.add((artifact, KE.artifactLocation, Literal(path.relative_to(ROOT).as_posix(), datatype=XSD.anyURI)))
        g.add((artifact, KE.capturedAt, Literal(doc['capturedAtUtc'], datatype=XSD.dateTime)))
        g.add((artifact, DCTERMS.description, Literal('Preserved case-specific source record, extracted during Stage 0; not the raw HTTP bytes.')))
        passages = {}
        for item in case['passages']:
            text = resolve(doc, item['locator'])
            require(text == item['text'], 'Passage does not match preserved source')
            p = URIRef(stem + ':passage:' + item['id'])
            passages[item['id']] = p
            g.add((p, RDF.type, KE.EvidencePassage))
            g.add((p, KE.inArtifact, artifact))
            string(p, KE.passageLocator, json.dumps(item['locator'], sort_keys=True))
            string(p, KE.passageText, text)
            checked.append((p, path, item['locator'], text))
        for item in case['passages']:
            for context in item.get('context', []):
                g.add((passages[item['id']], KE.contextPassage, passages[context]))
        for item in case['facts']:
            node = URIRef(stem + ':' + item['id'])
            cls = KE[item['type']]
            require(cls in (KE.Responsibility, KE.SalaryObservation), 'Unsupported fact class')
            g.add((node, RDF.type, cls))
            g.add((role if cls == KE.Responsibility else posting,
                   KE.hasResponsibility if cls == KE.Responsibility else KE.hasSalaryObservation, node))
            for ref in item['evidence']:
                g.add((node, KE.evidencePassage, passages[ref]))
            for prop, specification in item['values'].items():
                passage = next(p for p in case['passages'] if p['id'] == specification['passage'])
                value = specification['value']
                if 'pointer' in specification:
                    require(str(pointer(doc, specification['pointer'])) == str(value), 'Structured scalar mismatch')
                else:
                    require(specification.get('lexical', str(value)) in passage['text'], 'Scalar not present in source passage')
                require(specification['passage'] in item['evidence'], 'Scalar evidence not linked')
                datatype = XSD.decimal if prop in ('lowerAmount', 'upperAmount') else XSD.string
                if datatype == XSD.decimal:
                    require(Decimal(str(value)).is_finite() and Decimal(str(value)) >= 0, 'Invalid amount')
                    if 'lexical' in specification:
                        require(Decimal(specification['lexical'].replace(',', '')) == Decimal(str(value)), 'Amount differs from source wording')
                    value = format(Decimal(str(value)), 'f')
                    if '.' not in value:
                        value += '.0'
                g.add((node, KE[prop], Literal(str(value), datatype=datatype)))
            assessment = URIRef(str(node) + ':fidelity-v1')
            g.add((assessment, RDF.type, KE.MachineAssessment))
            g.add((assessment, RDF.type, KE.Assessment))
            g.add((assessment, KE.assessmentTarget, node))
            for ref in item['evidence']:
                g.add((assessment, KE.evidencePassage, passages[ref]))
            string(assessment, KE.assessmentKind, 'source extraction fidelity')
            string(assessment, KE.outcome, 'Exact source-value match')
            string(assessment, KE.rationale, 'Recorded values match the specified preserved passage or JSON scalar. This checks extraction fidelity only, not relevance, role scope, salary eligibility or semantic claim support.')
            string(assessment, KE.criteriaReference, 'Stage 5 build_graph.py sha256:' + sha(Path(__file__)))
            g.add((assessment, OWL.versionInfo, Literal('1')))
            g.add((assessment, PROV.wasAttributedTo, agent))
            g.add((assessment, PROV.wasGeneratedBy, run))
            g.add((assessment, PROV.generatedAtTime, now))
    # Lightweight procedural checks, not SHACL or OWL reasoning.
    for s, p, o in g:
        for term in (s, p, o):
            if isinstance(term, URIRef):
                require(bool(urlsplit(str(term)).scheme) and not re.search(r'[\s<>"{}|\\^`]', str(term)), 'Malformed IRI')
                if str(term).startswith(str(KE)):
                    require((term, None, None) in schema, 'Undeclared ontology term')
        if p == RDF.type and str(o).startswith(str(KE)):
            require((o, RDF.type, OWL.Class) in schema, 'Not an ontology class')
        if str(p).startswith(str(KE)):
            require((p, RDF.type, OWL.ObjectProperty) in schema or (p, RDF.type, OWL.DatatypeProperty) in schema, 'Not a property')
            if (p, RDF.type, OWL.ObjectProperty) in schema:
                require(isinstance(o, URIRef), 'Object property requires an IRI')
            else:
                require(isinstance(o, Literal) and o.datatype == schema.value(p, RDFS.range), 'Wrong literal datatype')
            domain = schema.value(p, RDFS.domain)
            if domain:
                require((s, RDF.type, domain) in g, 'Wrong subject type')
            range_ = schema.value(p, RDFS.range)
            if (p, RDF.type, OWL.ObjectProperty) in schema and range_:
                require((o, RDF.type, range_) in g or (o, RDF.type, range_) in taxonomy, 'Wrong object type')
        if p == KE.roleConcept:
            require((o, RDF.type, SKOS.Concept) in taxonomy, 'Unknown SKOS concept')
    for cls in (KE.Responsibility, KE.SalaryObservation):
        for s in g.subjects(RDF.type, cls):
            require(any(g.objects(s, KE.evidencePassage)), 'Fact without evidence')
    for salary in g.subjects(RDF.type, KE.SalaryObservation):
        lo, hi = g.value(salary, KE.lowerAmount), g.value(salary, KE.upperAmount)
        require(lo is None or hi is None or Decimal(str(lo)) <= Decimal(str(hi)), 'Reversed salary bounds')
    require(not list(g.subjects(RDF.type, KE.HumanAssessment)), 'Human assessments prohibited')
    require(not list(g.triples((None, OWL.sameAs, None))), 'Identity merging prohibited')
    output = LOCAL / 'graph.ttl'
    subprocess.run(['git', 'check-ignore', '--quiet', str(output)], cwd=ROOT, check=True)
    g.serialize(output, format='turtle')
    parsed = Graph().parse(output, format='turtle')
    require(set(parsed) == set(g), 'RDF round-trip mismatch')
    for p, path, locator, text in checked:
        require(resolve(json.loads(path.read_text(encoding='utf-8')), locator) == text, 'Locator no longer resolves')
    union = parsed + schema + taxonomy
    results = {}
    for query in sorted((HERE / 'queries').glob('*.rq')):
        result = union.query(query.read_text(encoding='utf-8'))
        results[query.name] = {'variables': [str(v) for v in result.vars],
                               'rows': [[None if v is None else str(v) for v in row] for row in result]}
    (LOCAL / 'query-results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding='utf-8')
    counts = {str(c).removeprefix(str(KE)): len(set(g.subjects(RDF.type, c)))
              for c in sorted(set(g.objects(None, RDF.type))) if str(c).startswith(str(KE))}
    report = {'cases': len(CASES), 'entities': len(set(g.subjects())), 'triples': len(g),
              'schema_triples': len(schema), 'taxonomy_triples': len(taxonomy), 'types': counts,
              'evidence_links': len(list(g.triples((None, KE.evidencePassage, None)))),
              'resolved_passages': len(checked), 'query_rows': {q: len(r['rows']) for q, r in results.items()}}
    (LOCAL / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    if '--captures' in sys.argv:
        import argparse
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--captures', type=Path, required=True)
        parser.add_argument('--output', type=Path, required=True)
        args = parser.parse_args()
        require(args.output.resolve().is_relative_to((ROOT / 'learning-local').resolve()), 'Capture graph output must stay in learning-local')
        graph, *_ = build_postings(load_captures(args.captures))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        graph.serialize(args.output, format='turtle')
        print(json.dumps({'postings': len(list(graph.subjects(RDF.type, KE.JobPosting))), 'triples': len(graph)}))
    else:
        main()

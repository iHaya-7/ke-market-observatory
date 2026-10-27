"""Offline SHACL plus separate source-integrity checks; controls use memory copies."""
from pathlib import Path
from collections import Counter
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, os.environ.get('KE_LOCAL_DEPS', str(ROOT / 'learning-local/stage6-deps')))
from pyshacl import validate
from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, XSD, DCTERMS
from rdflib.namespace import RDFS, OWL, SKOS

HERE = Path(__file__).resolve().parent
LOCAL = ROOT / 'knowledge-engineering/00-baseline/local-corpus/development'
GRAPH = LOCAL / 'stage5/graph.ttl'
OUTPUT = LOCAL / 'stage6'
KE = Namespace('urn:ke-market-observatory:ontology:')
PROV = Namespace('http://www.w3.org/ns/prov#')
SH = Namespace('http://www.w3.org/ns/shacl#')
spec = importlib.util.spec_from_file_location('stage5', HERE.parent / '05-knowledge-graph/build_graph.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)  # Main is guarded; never builds/overwrites the graph.


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one(g, subject, predicate):
    values = list(g.objects(subject, predicate))
    require(len(values) == 1, 'cardinality')
    return values[0]


def allowed_sources():
    mapping = json.loads((LOCAL / 'stage5/mapping.json').read_text(encoding='utf-8'))
    require(tuple(c['case'] for c in mapping['cases']) == builder.CASES, 'Development scope changed')
    allowed = {}
    for case in mapping['cases']:
        p = (builder.CORPUS / case['artifact']).resolve()
        require(case['split'] == 'development' and p.is_relative_to(builder.CORPUS.resolve())
                and case['case'] in p.name and p.parts[-3] in ('details', 'originals'), 'Unsafe source path')
        allowed[p] = case
    return allowed


def locate(doc, locator):
    require(isinstance(locator, dict) and set(locator) <= {'pointer', 'transform', 'start', 'end'}, 'locator_structure')
    pointer = locator.get('pointer')
    require(isinstance(pointer, str) and pointer.startswith('/record/')
            and not re.search(r'~(?![01])', pointer), 'locator_pointer')
    value = doc
    for token in pointer.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            require(bool(re.fullmatch(r'0|[1-9][0-9]*', token)), 'locator_index')
            value = value[int(token)]
        else:
            require(isinstance(value, dict), 'locator_container')
            value = value[token]
    transform = locator.get('transform')
    require(transform in ('json', 'text-v1'), 'locator_transform')
    if transform == 'json':
        require('start' not in locator and 'end' not in locator, 'json_offsets')
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    require(isinstance(value, str), 'locator_text_type')
    text = builder.rendered(value)
    require(('start' in locator) == ('end' in locator), 'incomplete_span')
    start, end = locator.get('start', 0), locator.get('end', len(text))
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), 'locator_bounds')
    return text[start:end]


def integrity(g, allowed):
    """No URL fetching; only the fixed three allowed case-specific files are opened."""
    errors, documents = [], {}
    exists = hashes = resolved = matches = 0
    for artifact in sorted(g.subjects(RDF.type, KE.EvidenceArtifact)):
        try:
            path = (ROOT / str(one(g, artifact, KE.artifactLocation))).resolve()
            require(path in allowed, 'artifact_not_allowlisted')
            require(path.is_file(), 'artifact_missing')
            exists += 1
            checksum = digest(path)
            require(checksum == str(one(g, artifact, KE.sha256)).lower()
                    and checksum == allowed[path]['sha256'], 'checksum_mismatch')
            hashes += 1
            doc = json.loads(path.read_text(encoding='utf-8'))
            case = allowed[path]
            require(doc['sourceId'] == case['sourceId'] and str(doc['sourceJobId']) == case['sourceJobId'], 'source_identity_mismatch')
            require(str(one(g, artifact, DCTERMS.source)) == builder.pointer(doc, case['urlPointer']), 'source_url_mismatch')
            require(one(g, artifact, KE.capturedAt) == Literal(doc['capturedAtUtc'], datatype=XSD.dateTime), 'capture_time_mismatch')
            documents[artifact] = doc
        except (ValueError, KeyError, IndexError, TypeError, OSError) as error:
            errors.append({'category': str(error), 'node': str(artifact)})
    for passage in sorted(g.subjects(RDF.type, KE.EvidencePassage)):
        try:
            artifact = one(g, passage, KE.inArtifact)
            require(artifact in documents, 'artifact_unverified')
            locator = json.loads(str(one(g, passage, KE.passageLocator)))
            try:
                text = locate(documents[artifact], locator)
            except (ValueError, KeyError, IndexError, TypeError):
                raise ValueError('locator_unresolvable') from None
            resolved += 1
            stored = list(g.objects(passage, KE.passageText))
            if stored:
                require(len(stored) == 1 and str(stored[0]) == text, 'passage_text_mismatch')
                matches += 1
        except (ValueError, KeyError, TypeError) as error:
            errors.append({'category': str(error), 'node': str(passage)})
    return {'passed': not errors, 'artifacts_existing': exists, 'checksums_matching': hashes,
            'passages_resolved': resolved, 'passage_text_matches': matches,
            'categories': dict(Counter(e['category'] for e in errors)), 'errors': errors}


def shacl(g, shapes, schema):
    conforms, report, _ = validate(g, shacl_graph=shapes, ont_graph=schema,
                                  inference='none', advanced=False, inplace=False,
                                  do_owl_imports=False, meta_shacl=True)
    rows = []
    for result in report.subjects(RDF.type, SH.ValidationResult):
        rows.append({name: str(report.value(result, prop)) for name, prop in
                     [('path', SH.resultPath), ('component', SH.sourceConstraintComponent),
                      ('focus', SH.focusNode), ('severity', SH.resultSeverity)]})
    return {'conforms': bool(conforms), 'violations': len(rows),
            'categories': dict(Counter(r['component'].split('#')[-1] for r in rows)), 'results': rows}, report


def validate_captures(g, archive):
    """Validate only the supplied ZIP and reconstructed source/mapping facts.

    The legacy allowlist and historical private mapping are deliberately unused.
    Reconstruction is in memory from current captures, never historical artifacts.
    """
    from posting_evidence import load_captures, resolve_html
    import zipfile
    postings = load_captures(archive)
    expected, *_ = builder.build_postings(postings)
    def source_facts(graph):
        return {(s, p, o) for s, p, o in graph
                if str(s).startswith((builder.BASE + 'capture-posting:', builder.BASE + 'artifact:', builder.BASE + 'publisher:'))}
    require(source_facts(g) == source_facts(expected), 'Capture source facts or responsibility mappings changed')
    matched = 0
    with zipfile.ZipFile(archive) as z:
        by_hash = {p['sha256']: p for p in postings}
        for passage in g.subjects(RDF.type, KE.EvidencePassage):
            artifact = one(g, passage, KE.inArtifact)
            item = by_hash[str(one(g, artifact, KE.sha256))]
            resolved = resolve_html(z.read(item['member']), json.loads(str(one(g, passage, KE.passageLocator))))
            require(resolved == str(one(g, passage, KE.passageText)), 'Capture passage mismatch')
            matched += 1
    schema = Graph().parse(HERE.parent / '04-ontology/ontology.ttl').parse(HERE.parent / '03-taxonomy/role-taxonomy.ttl')
    shapes = Graph().parse(HERE / 'shapes.ttl')
    structure, _ = shacl(g, shapes, schema)
    require(structure['conforms'], 'Capture graph fails SHACL: ' + json.dumps(structure))
    require(not list(g.subjects(RDF.type, KE.HumanAssessment)), 'Machine path cannot create human assessments')
    require(not list(g.triples((None, OWL.sameAs, None))), 'Identity merging prohibited')
    for s, p, o in g:
        if str(p).startswith(str(KE)):
            require((p, None, None) in schema, 'Undeclared ontology term')
            domain, range_ = schema.value(p, RDFS.domain), schema.value(p, RDFS.range)
            if domain:
                require((s, RDF.type, domain) in g, 'Wrong property domain')
            if (p, RDF.type, OWL.DatatypeProperty) in schema:
                require(isinstance(o, Literal) and o.datatype == range_, 'Wrong property datatype')
            elif range_:
                require((o, RDF.type, range_) in g or (o, RDF.type, range_) in schema, 'Wrong property range')
        if p == RDF.type and str(o).startswith(str(KE)):
            require((o, RDF.type, OWL.Class) in schema, 'Undeclared ontology class')
    return {'shacl_conforms': True, 'source_integrity_passed': True,
            'artifacts': len(postings), 'resolved_passages': matched, 'source_facts_match': True}


def main():
    before = digest(GRAPH)
    g = Graph().parse(GRAPH)
    shapes = Graph().parse(HERE / 'shapes.ttl')
    schema = Graph().parse(HERE.parent / '04-ontology/ontology.ttl')
    schema.parse(HERE.parent / '03-taxonomy/role-taxonomy.ttl')
    allowed = allowed_sources()
    source_hashes = {p: digest(p) if p.is_file() else None for p in allowed}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'check-ignore', '--quiet', str(OUTPUT / 'results.json')], cwd=ROOT, check=True)
    real, report = shacl(g, shapes, schema)
    report.serialize(OUTPUT / 'shacl-report.ttl', format='turtle')
    sources = integrity(g, allowed)
    coverage = {str(s).split(':')[-1]: len(set(g.subjects(RDF.type, cls)))
                for s, cls in shapes.subject_objects(SH.targetClass)}
    controls = {}
    def first(cls):
        return sorted(g.subjects(RDF.type, cls))[0]
    def control(name, subject, predicate, replacement, expected):
        copy = Graph() + g
        copy.remove((subject, predicate, None))
        if replacement is not None:
            copy.add((subject, predicate, replacement))
        result, _ = shacl(copy, shapes, schema)
        require(not result['conforms'] and any(r['path'] == str(predicate)
                and r['component'] == str(expected) for r in result['results']), 'Control failed: ' + name)
        controls[name] = result
    passage, artifact = first(KE.EvidencePassage), first(KE.EvidenceArtifact)
    assessment = first(KE.MachineAssessment)
    control('passage_without_artifact', passage, KE.inArtifact, None, SH.MinCountConstraintComponent)
    control('artifact_bad_sha256', artifact, KE.sha256, Literal('bad', datatype=XSD.string), SH.PatternConstraintComponent)
    control('artifact_without_source', artifact, DCTERMS.source, None, SH.MinCountConstraintComponent)
    control('assessment_without_evidence', assessment, KE.evidencePassage, None, SH.MinCountConstraintComponent)
    control('assessment_without_activity', assessment, PROV.wasGeneratedBy, None, SH.MinCountConstraintComponent)
    control('salary_string_bound', first(KE.SalaryObservation), KE.lowerAmount,
            Literal('invalid', datatype=XSD.string), SH.DatatypeConstraintComponent)
    optional = Graph() + g
    for salary in optional.subjects(RDF.type, KE.SalaryObservation):
        for prop in (KE.currency, KE.payPeriod, KE.payMarket, KE.compensationBasis):
            optional.remove((salary, prop, None))
    positive, _ = shacl(optional, shapes, schema)
    require(positive['conforms'], 'Permissible missing salary context rejected')
    # Well-formed RDF can still point to wrong bytes/text. No source files are edited.
    integrity_controls = {}
    for name, subject, predicate, replacement, category in [
        ('wrong_checksum', artifact, KE.sha256, Literal('0' * 64, datatype=XSD.string), 'checksum_mismatch'),
        ('wrong_locator', passage, KE.passageLocator, Literal(json.dumps({'pointer': '/record/nonexistent-test-field', 'transform': 'text-v1'}), datatype=XSD.string), 'locator_unresolvable'),
        ('wrong_text', passage, KE.passageText, Literal('SYNTHETIC NEGATIVE CONTROL', datatype=XSD.string), 'passage_text_mismatch')]:
        copy = Graph() + g
        copy.set((subject, predicate, replacement))
        structure, _ = shacl(copy, shapes, schema)
        checked = integrity(copy, allowed)
        require(structure['conforms'] and not checked['passed'] and category in checked['categories'], 'Integrity control failed: ' + name)
        integrity_controls[name] = {'shacl_conforms': structure['conforms'], 'integrity': checked}
    require(digest(GRAPH) == before and all((digest(p) if p.is_file() else None) == h
            for p, h in source_hashes.items()), 'Inputs changed during validation')
    result = {'graph_sha256': before, 'shapes_sha256': digest(HERE / 'shapes.ttl'),
              'node_shapes': len(list(shapes.subjects(RDF.type, SH.NodeShape))),
              'property_shapes': len(set(shapes.objects(None, SH.property))),
              'focus_counts': coverage, 'unexercised_shapes': [s for s, n in coverage.items() if n == 0],
              'shacl': real, 'source_integrity': sources, 'negative_controls': controls,
              'missing_salary_context': positive, 'integrity_controls': integrity_controls,
              'inputs_unchanged': True}
    (OUTPUT / 'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    # Console is aggregate only; detailed failures and graph node identities stay private.
    print(json.dumps({'node_shapes': result['node_shapes'], 'property_shapes': result['property_shapes'],
                      'focus_counts': coverage, 'shacl_conforms': real['conforms'],
                      'shacl_violations': real['violations'],
                      'source_integrity': {k: v for k, v in sources.items() if k != 'errors'},
                      'negative_control_violations': {k: v['violations'] for k, v in controls.items()},
                      'missing_salary_context_conforms': positive['conforms'],
                      'integrity_controls_rejected': len(integrity_controls), 'inputs_unchanged': True}, indent=2))
    require(real['conforms'] and sources['passed'], 'Real graph failed; see private validation results')


if __name__ == '__main__':
    if '--captures' in sys.argv:
        import argparse
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--captures', type=Path, required=True)
        parser.add_argument('--graph', type=Path, required=True)
        args = parser.parse_args()
        print(json.dumps(validate_captures(Graph().parse(args.graph), args.captures), indent=2))
    else:
        main()

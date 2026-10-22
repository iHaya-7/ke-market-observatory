"""Stage 7A: Development-only evidence triage, not a semantic classifier."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from uuid import uuid4
import importlib.util
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'learning-local/stage6-deps'))
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD, OWL, DCTERMS

spec = importlib.util.spec_from_file_location('validation', HERE.parent / '06-validation/validate_graph.py')
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)  # No main, rebuild, controls, or output writes.
KE, PROV = validation.KE, validation.PROV
OUT = validation.LOCAL / 'stage7a'
FIELDS = ('lowerAmount', 'upperAmount', 'currency', 'payPeriod', 'compensationBasis',
          'payMarket', 'employerName', 'recruitingAgentName', 'bandApplicability')
REQUIRED = ('lowerAmount', 'currency', 'payPeriod', 'compensationBasis', 'payMarket')
RULES = {
    'R0': 'Relevance unsupported: selected duties and structural validation do not establish substantive representation work or complete negative coverage. Abstain; do not inspect titles or keyword counts.',
    'S1': 'Inventory represented salary fields per statement. Missing policy dimensions or employer/agent attribution block automated eligibility. Missing graph data does not prove absence from the source.',
    'S2': 'Compare explicit values only between reciprocally contextualized statements on the same posting and artifact. Flag potential disagreement; do not merge bands or transfer values. Limited explicit period/basis aliases do not infer missing units.',
    'S3': 'Even complete represented fields do not prove semantic applicability or support. Eligibility remains unsupported without an implemented, evidence-backed semantic rule.',
    'V1': 'Route unresolved relevance or salary decisions to the private pilot review queue, with scoped questions and citations. This is machine review need, not human Ground Truth or production queue membership.',
}


def values(g, node, field):
    return sorted({str(v) for v in g.objects(node, KE[field]) if str(v).strip()})


def citations(g, nodes):
    direct = {p for n in nodes for p in g.objects(n, KE.evidencePassage)}
    return sorted(direct | {c for p in direct for c in g.objects(p, KE.contextPassage)})


def normalize(field, value):
    # Compare stated equivalent spellings only; never supply absent values.
    if field == 'payPeriod':
        return {'per year': 'Annual', 'per-year-salary': 'Annual', 'Annual': 'Annual',
                'per month': 'Monthly', 'per-month-salary': 'Monthly', 'Monthly': 'Monthly'}.get(value, value)
    if field == 'compensationBasis' and value.lower() in ('base salary', 'base pay', 'base'):
        return 'base'
    return value


def salary_diagnostic(g, node):
    facts = {f: values(g, node, f) for f in FIELDS}
    missing = [f for f in REQUIRED if not facts[f]]
    if not facts['employerName'] and not facts['recruitingAgentName']:
        missing.append('employer_or_recruiting_agent_attribution')
    disagreements = [f for f, vals in facts.items() if len({normalize(f, v) for v in vals}) > 1]
    return {'observation': str(node), 'source_facts': facts, 'missing_graph_fields': missing,
            'potential_disagreements': disagreements,
            'status': 'Incomplete represented evidence' if missing else 'Represented fields present; semantic sufficiency unverified'}


def context_candidates(g, observations):
    result = []
    for left, right in combinations(sorted(observations), 2):
        lp, rp = set(g.objects(left, KE.evidencePassage)), set(g.objects(right, KE.evidencePassage))
        linked = any((a, KE.contextPassage, b) in g and (b, KE.contextPassage, a) in g
                     and g.value(a, KE.inArtifact) == g.value(b, KE.inArtifact)
                     and g.value(a, KE.inArtifact) is not None for a in lp for b in rp)
        if not linked:
            continue
        a, b = salary_diagnostic(g, left)['source_facts'], salary_diagnostic(g, right)['source_facts']
        conflicts = [f for f in FIELDS if a[f] and b[f]
                     and {normalize(f, v) for v in a[f]} != {normalize(f, v) for v in b[f]}]
        result.append({'rule': 'S2', 'observations': [str(left), str(right)],
                       'interpretation_status': 'Candidate only; same-band identity unconfirmed',
                       'potential_disagreements': conflicts,
                       'fields_supplied_across_statements': [f for f in REQUIRED if a[f] or b[f]],
                       'equal_explicit_endpoints': all(a[f] and a[f] == b[f] for f in ('lowerAmount', 'upperAmount')),
                       'evidence': [str(p) for p in citations(g, [left, right])]})
    return result


def decide(g):
    cases = []
    for posting in sorted(g.subjects(RDF.type, KE.JobPosting)):
        ids = [str(i) for i in g.objects(posting, DCTERMS.identifier) if str(i).startswith('EVAL-')]
        validation.require(len(ids) == 1, 'Ambiguous case identity')
        duties = sorted({d for r in g.objects(posting, KE.advertisesRole) for d in g.objects(r, KE.hasResponsibility)})
        salaries = sorted(g.objects(posting, KE.hasSalaryObservation))
        evidence = citations(g, duties + salaries)
        diagnostics = [salary_diagnostic(g, s) for s in salaries]
        candidates = context_candidates(g, salaries)
        decisions = [{'target': str(posting), 'kind': 'relevance', 'outcome': 'Abstain', 'rule': 'R0',
                      'rationale': RULES['R0'], 'unresolved': ['Substantive action/object meaning and complete duty coverage are not established by this graph.'],
                      'evidence': [str(p) for p in citations(g, duties)]}]
        for diagnostic, salary in zip(diagnostics, salaries):
            unresolved = ['Not represented on this statement: ' + f for f in diagnostic['missing_graph_fields']]
            unresolved += ['Potential disagreement: ' + f for f in diagnostic['potential_disagreements']]
            unresolved += ['Semantic attribution, compensation applicability and context reconciliation remain unverified.']
            decisions.append({'target': str(salary), 'kind': 'salary eligibility', 'outcome': 'Abstain',
                              'rule': 'S1+S2+S3', 'rationale': ' '.join(RULES[r] for r in ('S1', 'S2', 'S3')),
                              'unresolved': unresolved, 'evidence': [str(p) for p in citations(g, [salary])]})
        questions = ['Does the full advertised work substantively create, curate, validate, govern, integrate or use explicit knowledge representations? Selected duties alone do not settle inclusion or exclusion.']
        missing = sorted({f for d in diagnostics for f in d['missing_graph_fields']})
        if salaries:
            questions.append('For each retained statement, verify source-supported ' + ', '.join(missing)
                             + '; distinguish graph extraction omissions from source omissions, and establish band applicability before eligibility.')
        else:
            questions.append('No salary observation is represented. Inspect complete source compensation context; do not infer that no pay is disclosed.')
        if candidates:
            questions.append('Do the reciprocally linked salary statements describe the same band? Reconcile explicit values before using their complementary fields; no merge is authorized by this candidate link.')
        potential = sorted({f for c in candidates for f in c['potential_disagreements']})
        if potential:
            questions.append('Resolve potentially conflicting contextual fields: ' + ', '.join(potential))
        decisions.append({'target': str(posting), 'kind': 'review need', 'outcome': 'Yes', 'rule': 'V1',
                          'rationale': RULES['V1'], 'unresolved': questions, 'evidence': [str(p) for p in evidence]})
        cases.append({'case_id': ids[0], 'posting': str(posting),
                      'source_facts': {'responsibilities': [{'iri': str(d), 'action_text': values(g, d, 'actionText'),
                                                            'evidence': [str(p) for p in citations(g, [d])]} for d in duties],
                                       'salary_statements': [{'observation': d['observation'], 'values': d['source_facts'],
                                                              'evidence': [str(p) for p in citations(g, [URIRef(d['observation'])])]}
                                                             for d in diagnostics]},
                      'machine_salary_diagnostics': [{k: v for k, v in d.items() if k != 'source_facts'} for d in diagnostics],
                      'candidate_semantic_interpretation': {'relevance': 'Unsupported in this pilot; no inferred occupational assignment.', 'salary_context': candidates},
                      'machine_decisions': decisions, 'review_questions': questions})
    return sorted(cases, key=lambda c: c['case_id'])


def controls(g):
    """Small synthetic mutations; never labels, accuracy tests or saved source facts."""
    original = decide(g)
    copy = Graph() + g
    copy.remove((None, DCTERMS.title, None))
    for p in copy.subjects(RDF.type, KE.JobPosting):
        copy.add((p, DCTERMS.title, Literal('SYNTHETIC Knowledge Engineer')))
    validation.require(decide(copy) == original, 'Title affected decision')
    copy = Graph() + g
    for p in (KE.currency, KE.payPeriod):
        copy.remove((None, p, None))
    validation.require(all({'currency', 'payPeriod'} <= set(d['missing_graph_fields'])
                           for c in decide(copy) for d in c['machine_salary_diagnostics']), 'Missing units inferred')
    pair = next(c['candidate_semantic_interpretation']['salary_context'][0] for c in original
                if c['candidate_semantic_interpretation']['salary_context'])
    copy = Graph() + g
    left, right = map(URIRef, pair['observations'])
    copy.set((left, KE.payPeriod, Literal('Monthly', datatype=XSD.string)))
    validation.require('payPeriod' in context_candidates(copy, [left, right])[0]['potential_disagreements'], 'Conflict not detected')
    copy.remove((None, KE.contextPassage, None))
    validation.require(not context_candidates(copy, [left, right]), 'Unlinked statements compared')
    validation.require(all(d['outcome'] == 'Abstain' for c in original for d in c['machine_decisions']
                           if d['kind'] in ('relevance', 'salary eligibility')), 'Unsupported verdict')
    return ['title invariance', 'missing units stay missing', 'contextual period conflict detected',
            'no unlinked statement comparison', 'no unsupported relevance or eligibility verdict']


def main():
    g = Graph().parse(validation.GRAPH)
    schema_path = HERE.parent / '04-ontology/ontology.ttl'
    taxonomy_path = HERE.parent / '03-taxonomy/role-taxonomy.ttl'
    shapes_path = HERE.parent / '06-validation/shapes.ttl'
    schema = Graph().parse(schema_path).parse(taxonomy_path)
    shapes = Graph().parse(shapes_path)
    allowed = validation.allowed_sources()
    files = [validation.GRAPH, validation.LOCAL / 'stage5/mapping.json', schema_path, taxonomy_path,
             shapes_path, Path(validation.__file__), HERE.parent / '00-baseline/EVALUATION_PROTOCOL.md', *allowed]
    hashes = {p: validation.digest(p) for p in files}
    structure, _ = validation.shacl(g, shapes, schema)
    integrity = validation.integrity(g, allowed)
    validation.require(structure['conforms'] and integrity['passed'], 'Input validation failed; no pilot decisions issued')
    cases = decide(g)
    validation.require(tuple(c['case_id'] for c in cases) == validation.builder.CASES, 'Only the existing three Development cases are allowed')
    tests = controls(g)
    run_id = str(uuid4())
    run = URIRef('urn:ke-market-observatory:pilot:run:' + run_id)
    agent = URIRef('urn:ke-market-observatory:pilot:software:stage7a')
    now = Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime)
    results = Graph()
    results.bind('ke', KE)
    results.bind('prov', PROV)
    results.add((run, RDF.type, PROV.Activity))
    results.add((run, PROV.wasAssociatedWith, agent))
    results.add((agent, RDF.type, PROV.SoftwareAgent))
    code_hash = validation.digest(Path(__file__))
    results.add((run, DCTERMS.identifier, Literal('pilot-sha256:' + code_hash)))
    queue = []
    for case in cases:
        for index, decision in enumerate(case['machine_decisions']):
            assessment = URIRef(str(run) + ':' + case['case_id'] + ':' + str(index))
            decision['assessment'] = str(assessment)
            for cls in (KE.MachineAssessment, KE.Assessment):
                results.add((assessment, RDF.type, cls))
            results.add((assessment, KE.assessmentTarget, URIRef(decision['target'])))
            for prop, value in [(KE.assessmentKind, decision['kind']), (KE.outcome, decision['outcome']),
                                (KE.rationale, decision['rationale']),
                                (KE.criteriaReference, 'Stage7A-v1 ' + decision['rule'] + ' sha256:' + code_hash)]:
                results.add((assessment, prop, Literal(value, datatype=XSD.string)))
            for issue in decision['unresolved']:
                results.add((assessment, KE.unresolvedFact, Literal(issue, datatype=XSD.string)))
                if decision['kind'] == 'review need':
                    results.add((assessment, KE.reviewQuestion, Literal(issue, datatype=XSD.string)))
            validation.require(bool(decision['evidence']), 'Decision without relevant evidence context')
            for passage in decision['evidence']:
                results.add((assessment, KE.evidencePassage, URIRef(passage)))
            results.add((assessment, OWL.versionInfo, Literal('Stage7A-v1')))
            results.add((assessment, PROV.wasAttributedTo, agent))
            results.add((assessment, PROV.wasGeneratedBy, run))
            results.add((assessment, PROV.generatedAtTime, now))
        for index, category in enumerate(('Role relevance', 'Pay evidence')):
            entry = URIRef(str(run) + ':' + case['case_id'] + ':queue:' + str(index))
            results.add((entry, RDF.type, KE.ReviewQueueEntry))
            results.add((entry, KE.queueTarget, URIRef(case['posting'])))
            results.add((entry, KE.queueCategory, Literal(category, datatype=XSD.string)))
            results.add((entry, PROV.generatedAtTime, now))
            results.add((entry, PROV.wasGeneratedBy, run))
            queue.append({'case_id': case['case_id'], 'category': category, 'entry': str(entry),
                          'review_assessment': case['machine_decisions'][-1]['assessment']})
    checked, _ = validation.shacl(g + results, shapes, schema)
    validation.require(checked['conforms'], 'Pilot assessments fail existing SHACL')
    validation.require(not list(results.subjects(RDF.type, KE.HumanAssessment)), 'Human labels prohibited')
    for _, predicate, obj in results:
        if str(predicate).startswith(str(KE)):
            validation.require((predicate, None, None) in schema, 'Undeclared ontology property')
        if predicate == RDF.type and str(obj).startswith(str(KE)):
            validation.require((obj, RDF.type, OWL.Class) in schema, 'Undeclared ontology class')
    summary = {'development_cases': len(cases), 'machine_assessments': sum(len(c['machine_decisions']) for c in cases),
               'decision_counts': dict(Counter(d['kind'] + ': ' + d['outcome'] for c in cases for d in c['machine_decisions'])),
               'salary_statements': sum(len(c['source_facts']['salary_statements']) for c in cases),
               'contextual_statement_candidates': sum(len(c['candidate_semantic_interpretation']['salary_context']) for c in cases),
               'contextual_potential_conflicts': sum(bool(p['potential_disagreements']) for c in cases for p in c['candidate_semantic_interpretation']['salary_context']),
               'pilot_queue_entries': len(queue), 'pilot_queued_cases': len(cases),
               'input_shacl_conforms': structure['conforms'], 'input_source_integrity_passed': integrity['passed'],
               'output_shacl_conforms': checked['conforms'], 'synthetic_controls_passed': len(tests)}
    # Supply actual trace chains as pilot output, not retroactive baseline citations.
    cited = {p for c in cases for d in c['machine_decisions'] for p in d['evidence']}
    trace = {}
    for passage in sorted(cited):
        p = URIRef(passage)
        a = validation.one(g, p, KE.inArtifact)
        trace[passage] = {'artifact': str(a), 'locator': str(validation.one(g, p, KE.passageLocator)),
                          'source': str(validation.one(g, a, DCTERMS.source)),
                          'identifiers': sorted(str(v) for v in g.objects(a, DCTERMS.identifier)),
                          'location': str(validation.one(g, a, KE.artifactLocation)),
                          'sha256': str(validation.one(g, a, KE.sha256)),
                          'captured_at': str(validation.one(g, a, KE.capturedAt))}
    summary['distinct_cited_passages'] = len(trace)
    validation.require(all(validation.digest(p) == h for p, h in hashes.items()), 'An input changed')
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', 'check-ignore', '--quiet', str(OUT / 'pilot-results.json')], cwd=ROOT, check=True)
    results.serialize(OUT / 'pilot-assessments.ttl', format='turtle')
    validation.require(set(Graph().parse(OUT / 'pilot-assessments.ttl')) == set(results), 'Output RDF round-trip failed')
    payload = {'version': 'Stage7A-v1', 'run_id': run_id, 'generated_at': str(now), 'code_sha256': code_hash,
               'input_hashes': {p.relative_to(ROOT).as_posix(): h for p, h in hashes.items()},
               'rules': RULES, 'summary': summary, 'cases': cases, 'pilot_review_queue': queue,
               'evidence_trace': trace, 'synthetic_controls': tests,
               'human_ground_truth': 'Not accessed or created; machine outputs must not be used as reference labels.'}
    (OUT / 'pilot-results.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()

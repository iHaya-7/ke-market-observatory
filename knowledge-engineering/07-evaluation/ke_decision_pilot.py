"""Stage 7A: Development-only evidence triage, not a semantic classifier."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
from itertools import combinations
from uuid import uuid4
import importlib.util
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, os.environ.get('KE_LOCAL_DEPS', str(ROOT / 'learning-local/stage6-deps')))
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


def assess_captured(g):
    """Evidence decisions over the existing ontology, independent of titles/labels.

    This path is opt-in and offline. Its outputs are recommendations, never
    production approval records or independent human judgments.
    """
    sys.path.insert(0, str(ROOT / 'scripts'))
    from refresh import salary_info
    cases = []
    for posting in sorted(g.subjects(RDF.type, KE.JobPosting)):
        role = validation.one(g, posting, KE.advertisesRole)
        duties = sorted(g.objects(role, KE.hasResponsibility))
        mapped = [d for d in duties if list(g.objects(d, KE.actsOnRepresentation))]
        texts = [str(validation.one(g, d, KE.actionText)) for d in duties]
        refs = sorted({p for d in duties for p in g.objects(d, KE.evidencePassage)})
        context = list(g.objects(posting, KE.evidencePassage))
        coverage = str(g.value(posting, DCTERMS.description))
        section_text = ' '.join(str(g.value(p, KE.passageText)) for p in g.objects(role, KE.evidencePassage))
        missing = []
        if mapped:
            occupational = 'Core KE'
            reason = 'Explicit duties engineer knowledge representations: ' + ' | '.join(str(g.value(d, KE.actionText)) for d in mapped)
        elif re.search(r'\b(?:knowledge graph|ontology|semantic model)\b', ' '.join(texts), re.I) and re.search(r'\b(?:backend|API|indexing|query engine|integration)\b', ' '.join(texts), re.I):
            occupational = 'Adjacent technical'
            reason = 'Duties implement a graph service/platform; explicit ownership of domain entities, relationships or semantic models is not established.'
            missing = ['Confirm whether graph platform duties include substantive domain representation modeling/integration.']
        elif coverage == 'delimited responsibility section' and not re.search(r'\b(?:ontolog(?:y|ies)|knowledge graphs?|semantic model|RDF|SHACL)\b', section_text, re.I) and re.search(r'\b(?:ML|machine learning|NLP|model training|recruit|marketing|sales|administrative)\b', ' '.join(texts), re.I):
            occupational = 'Outside Scope'
            reason = 'The captured, delimited duty section describes other work, with no supported action on knowledge representations: ' + ' | '.join(texts[:2])
        else:
            occupational = 'Insufficient Evidence'
            reason = 'No supported representation duty and no sufficiently specific, bounded alternative work evidence; abstain.'
            missing = ['Obtain explicit responsibilities and representation ownership; title/skill mentions cannot settle scope.']
        decisions = [{'target': str(posting), 'kind': 'occupational relevance', 'outcome': occupational,
                      'rationale': reason, 'unresolved': missing, 'evidence': [str(p) for p in (refs or context)]}]
        salaries = []
        for salary in sorted(g.objects(posting, KE.hasSalaryObservation)):
            facts = {f: str(g.value(salary, KE[f])) if g.value(salary, KE[f]) is not None else None for f in FIELDS}
            gaps = [f for f in REQUIRED if not facts[f]]
            if facts['payMarket'] and not re.search(r'\b(?:United States|US|New York|NY|California|Seattle|WA|Saudi Arabia|Riyadh|KSA|United Kingdom|UK|London|Germany|Netherlands)\b', facts['payMarket'], re.I):
                gaps.append('payMarket specificity/applicability')
            if not list(g.objects(salary, KE.salaryForRole)):
                gaps.append('bandApplicability')
            # Reuse production amount/unit/base validation on this extracted band.
            raw = {'salaryRange': {'min': float(facts['lowerAmount']) if facts['lowerAmount'] else None,
                                   'max': float(facts['upperAmount']) if facts['upperAmount'] else None,
                                   'currency': facts['currency'], 'interval': facts['payPeriod']},
                   'salaryDescriptionPlain': {'base': 'base salary', 'total': 'total compensation'}.get(facts['compensationBasis'], '')}
            parsed = salary_info(raw, 'lever', '')
            if facts['compensationBasis'] == 'total':
                status, salary_reason = 'Ineligible', 'Explicit total compensation is outside the base-salary evidence measure.'
            elif gaps or not parsed['salaryEligible']:
                status = 'Insufficient Evidence'
                salary_reason = 'Abstain on intrinsic base-pay eligibility: ' + (', '.join(gaps) if gaps else 'unsupported units, invalid amount or ambiguous compensation basis')
            else:
                status, salary_reason = 'Eligible', 'Captured original posting supplies attributable, role-applicable base pay, currency, period and market; independent human authentication is pending.'
            evidence = [str(p) for p in g.objects(salary, KE.evidencePassage)]
            decisions.append({'target': str(salary), 'kind': 'intrinsic salary eligibility', 'outcome': status,
                              'rationale': salary_reason, 'unresolved': gaps, 'evidence': evidence})
            salaries.append({'observation': str(salary), 'original': facts, 'status': status,
                             'missing_information': gaps, 'explanation': salary_reason, 'evidence': evidence,
                             'sar_per_month': None})
        if not salaries:
            salary_status = 'No disclosed numeric salary'
            decisions.append({'target': str(posting), 'kind': 'intrinsic salary eligibility', 'outcome': salary_status,
                              'rationale': 'No supported numeric offered salary band extracted from the captured posting; no amount is inferred from benefits.',
                              'unresolved': ['A numerical salary statement and its units/context are required.'], 'evidence': [str(p) for p in context]})
        else:
            statuses = {s['status'] for s in salaries}
            salary_status = next(iter(statuses)) if len(statuses) == 1 else 'Mixed; assess each band separately'
        # Intrinsic eligibility is never conditioned on the occupational result.
        if occupational == 'Outside Scope':
            benchmark = 'Not admitted: occupational scope'
        elif occupational != 'Core KE' or salary_status != 'Eligible':
            benchmark = 'Not admitted: unresolved scope or salary evidence'
        elif any(re.search(r'\b(?:Saudi Arabia|Riyadh|KSA)\b', s['original']['payMarket'] or '', re.I) for s in salaries):
            benchmark = 'Not admitted: domestic evidence is separate from international benchmark'
        else:
            benchmark = 'Candidate only: independent occupational and salary reviews required'
        decisions.append({'target': str(posting), 'kind': 'international KE benchmark admission', 'outcome': benchmark,
                          'rationale': 'Admission requires Core KE, intrinsically eligible international base pay and independent source-backed human reviews. No job or salary is approved.',
                          'unresolved': ['Independent occupational and salary verification; benchmark comparability and applicable band review.'],
                          'evidence': [str(p) for p in (refs or context)] + [p for s in salaries for p in s['evidence']]})
        cases.append({'case_id': next(str(v) for v in g.objects(posting, DCTERMS.identifier) if not str(v).startswith(('sourceId:', 'sourceJobId:'))),
                      'posting': str(posting), 'title': str(g.value(posting, DCTERMS.title)),
                      'source_url': str(g.value(posting, DCTERMS.source)), 'occupational_classification': occupational,
                      'responsibility_evidence': [{'text': text, 'evidence': [str(p) for p in g.objects(d, KE.evidencePassage)],
                                                   'mapped_to_representation': d in mapped} for d, text in zip(duties, texts)],
                      'salary_evidence_status': salary_status, 'salary_observations': salaries,
                      'missing_information': missing + [gap for s in salaries for gap in s['missing_information']]
                                             + ([] if salaries else ['Numeric salary and context not disclosed/extracted.']),
                      'machine_recommendation': benchmark, 'explanation': reason,
                      'human_review_needed': True,
                      'review_reason': 'Verify captured source identity/applicability and machine interpretation before any approval; resolve listed gaps.',
                      'approved': False, 'published': False, 'machine_decisions': decisions})
    return sorted(cases, key=lambda c: c['case_id'])


def run_captures(archive, output, expected=None):
    from posting_evidence import load_captures, VERSION
    import csv
    from decimal import Decimal, ROUND_HALF_UP
    output = output.resolve()
    validation.require(output.is_relative_to((ROOT / 'learning-local').resolve()), 'Outputs must stay in ignored learning-local')
    # Hash inputs before reading them; expectations are used only after decisions.
    protected = [archive, HERE.parent / '04-ontology/ontology.ttl', HERE.parent / '03-taxonomy/role-taxonomy.ttl',
                 HERE.parent / '06-validation/shapes.ttl', ROOT / 'data/curated.json']
    if expected:
        protected.append(expected)
    before = {str(p): validation.digest(p) for p in protected}
    g, run, agent, now = validation.builder.build_postings(load_captures(archive))
    checks = validation.validate_captures(g, archive)
    cases = assess_captured(g)
    # Reuse existing retained FX metadata; no network or live rate substitution.
    fx = json.loads((ROOT / 'data/curated.json').read_text(encoding='utf-8'))['fx']
    for case in cases:
        for salary in case['salary_observations']:
            facts = salary['original']
            currency, period = facts['currency'], facts['payPeriod']
            if salary['status'] == 'Eligible' and currency in fx['rates'] and period in ('Annual', 'Monthly'):
                rate = Decimal(str(fx['rates'][currency]))
                divisor = Decimal(12 if period == 'Annual' else 1)
                salary['sar_per_month'] = {key: str((Decimal(facts[field]) * rate / divisor).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)) if facts[field] else None
                                           for key, field in [('min', 'lowerAmount'), ('max', 'upperAmount')]}
                salary['conversion'] = {'display': 'SAR/month', 'rate_to_sar': str(rate), 'fx_date': fx['date'],
                                        'fx_source': fx['source'], 'rounding': 'half up to 0.01', 'nominal_only': True}
        for decision in case['machine_decisions']:
            node = validation.builder.assessment(g, URIRef(decision['target']), decision['kind'], decision['outcome'],
                                                decision['rationale'], list(map(URIRef, decision['evidence'])), run, agent, now, decision['unresolved'])
            g.add((node, KE.criteriaReference, Literal('captured-posting-v1 pilot-sha256:' + validation.digest(Path(__file__)), datatype=XSD.string)))
            decision['assessment'] = str(node)
    checks['with_assessments'] = validation.validate_captures(g, archive)
    trace = {}
    for p in g.subjects(RDF.type, KE.EvidencePassage):
        artifact = validation.one(g, p, KE.inArtifact)
        trace[str(p)] = {'text': str(g.value(p, KE.passageText)), 'locator': json.loads(str(g.value(p, KE.passageLocator))),
                         'source_url': str(g.value(artifact, DCTERMS.source)),
                         'source_job_id': str(g.value(artifact, DCTERMS.identifier)),
                         'artifact_location': str(g.value(artifact, KE.artifactLocation)),
                         'sha256': str(g.value(artifact, KE.sha256)), 'captured_at': str(g.value(artifact, KE.capturedAt))}
    comparisons = []
    if expected:
        with expected.open(encoding='utf-8-sig', newline='') as handle:
            expected_rows = {r['candidate_id']: r for r in csv.DictReader(handle)}
        validation.require(set(expected_rows) == {c['case_id'] for c in cases}, 'Expectation case IDs mismatch')
        for case in cases:
            row = expected_rows[case['case_id']]
            role_hypothesis = row['assistant_role_hypothesis_NOT_GROUND_TRUTH']
            salary_hypothesis = row['intrinsic_salary_evidence_status_NOT_HUMAN_APPROVED']
            role_expected = ('Core KE' if role_hypothesis.startswith('Core KE') else
                             'Outside Scope' if role_hypothesis.startswith('Outside') else None)
            role_comparison = ('Boundary unresolved; provisional adjacent recommendation' if role_expected is None else
                               'Agrees with preliminary hypothesis' if role_expected == case['occupational_classification'] else 'Disagrees')
            salary_expected = {'COMPLETE_SOURCE_CONTEXT': 'Eligible', 'NO_NUMERIC_SALARY': 'No disclosed numeric salary',
                               'MISSING_PAY_PERIOD': 'Insufficient Evidence', 'MISSING_BASE_PAY_BASIS': 'Insufficient Evidence'}.get(salary_hypothesis)
            salary_gaps = {gap for salary in case['salary_observations'] for gap in salary['missing_information']}
            extra_gaps = sorted(salary_gaps - {'payPeriod' if salary_hypothesis == 'MISSING_PAY_PERIOD' else 'compensationBasis'}) if salary_hypothesis in ('MISSING_PAY_PERIOD', 'MISSING_BASE_PAY_BASIS') else []
            comparisons.append({'case_id': case['case_id'], 'preliminary_role_expectation': role_hypothesis,
                                'preliminary_salary_expectation': salary_hypothesis,
                                'machine_role': case['occupational_classification'], 'machine_salary': case['salary_evidence_status'],
                                'role_comparison': role_comparison,
                                'salary_comparison': 'Agrees on status' if salary_expected == case['salary_evidence_status'] else 'Disagrees on status',
                                'additional_salary_gaps': extra_gaps,
                                'disagreement': (role_expected is not None and role_expected != case['occupational_classification']) or salary_expected != case['salary_evidence_status'],
                                'interpretation': 'AI-assisted expectations only; agreement is not independent accuracy. Boundary choices require human adjudication.'})
    validation.require(all(validation.digest(Path(p)) == h for p, h in before.items()), 'Input changed')
    output.mkdir(parents=True, exist_ok=True)
    g.serialize(output / 'graph.ttl', format='turtle')
    validation.require(set(Graph().parse(output / 'graph.ttl')) == set(g), 'RDF round-trip failed')
    schema = Graph().parse(HERE.parent / '04-ontology/ontology.ttl').parse(HERE.parent / '03-taxonomy/role-taxonomy.ttl')
    queries = {}
    for path in sorted((HERE.parent / '05-knowledge-graph/queries').glob('*.rq')):
        result = (g + schema).query(path.read_text(encoding='utf-8'))
        queries[path.name] = [[None if v is None else str(v) for v in row] for row in result]
    payload = {'version': VERSION, 'generated_at': str(now), 'input_hashes': before,
               'implementation_hashes': {str(p.relative_to(ROOT)): validation.digest(p) for p in [Path(__file__), Path(validation.__file__), Path(validation.builder.__file__), HERE.parent / '05-knowledge-graph/posting_evidence.py', ROOT / 'scripts/refresh.py']},
               'human_ground_truth': 'None. Preliminary expectations are AI-assisted, not independent human judgments.',
               'checks': checks, 'cases': cases, 'expectation_comparison': comparisons, 'evidence_trace': trace,
               'summary': {'cases': len(cases), 'occupations': dict(Counter(c['occupational_classification'] for c in cases)),
                           'salary_status': dict(Counter(c['salary_evidence_status'] for c in cases)),
                           'approved': 0, 'published': 0}, 'query_row_counts': {k: len(v) for k, v in queries.items()}}
    (output / 'results.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    (output / 'query-results.json').write_text(json.dumps(queries, indent=2, ensure_ascii=False), encoding='utf-8')
    (output / 'review-queue.json').write_text(json.dumps([{'case_id': c['case_id'], 'questions': c['missing_information'] + [c['review_reason']],
                                                         'source_url': c['source_url'], 'evidence': c['machine_decisions'][0]['evidence']} for c in cases], indent=2), encoding='utf-8')
    lines = ['# Development v2 machine recommendations', '',
             'All eight cases require human source and interpretation review before approval. Nothing is approved or published. '
             'AI-assisted expectations are development hypotheses, not independent human ground truth. No accuracy is calculated.', '',
             'Detailed locators, hashed ZIP-member identity, capture times, full responsibility evidence, original salary values and machine assessments are in [results.json](results.json). '
             'SAR/month is a nominal display only; original amounts and units are retained. No conversion is offered for unresolved salary evidence.', '']
    for c in cases:
        lines += ['## ' + c['case_id'] + ' — ' + c['title'], '', '[Captured original source](' + c['source_url'] + ')', '',
                  '**Occupation:** ' + c['occupational_classification'] + '. ' + c['explanation'], '']
        selected = [d for d in c['responsibility_evidence'] if d['mapped_to_representation']] or c['responsibility_evidence'][:2]
        for d in selected:
            p = trace[d['evidence'][0]]
            lines += ['> ' + d['text'], '', 'Locator: `' + json.dumps(p['locator'], sort_keys=True) + '` in `' + p['artifact_location'] + '`.', '']
        lines += ['**Salary:** ' + c['salary_evidence_status'] + '.', '']
        for s in c['salary_observations']:
            f = s['original']
            if s['sar_per_month']:
                lines += ['Primary display: **SAR ' + s['sar_per_month']['min'] + '–' + str(s['sar_per_month']['max']) + '/month**, using retained FX dated ' + s['conversion']['fx_date'] + '.', '']
            lines += ['Original: ' + str(f['lowerAmount']) + '–' + str(f['upperAmount']) + ' ' + str(f['currency'] or '(currency unresolved; see original symbol)') + ' / ' + str(f['payPeriod'] or '(period unresolved)') + '; basis: ' + str(f['compensationBasis']) + '; market: ' + str(f['payMarket']) + '.', '', s['explanation'], '']
        lines += ['**Missing information:** ' + ('; '.join(c['missing_information']) or 'No machine-required field gap; independent verification remains pending.') + '', '',
                  '**Final recommendation:** ' + c['machine_recommendation'] + '. **Human review: Yes.**', '']
    lines += ['## Comparison with preliminary AI expectations', '']
    for c in comparisons:
        lines += ['- ' + c['case_id'] + ': ' + c['role_comparison'] + '; ' + c['salary_comparison'] +
                  ('. Additional source gaps: ' + ', '.join(c['additional_salary_gaps']) if c['additional_salary_gaps'] else '') + '.']
    lines += ['', 'Agreement is not verified accuracy. Independent source-only labels, adjudication and a frozen paired baseline replay are still required to measure improvement.', '']
    (output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'summary': payload['summary'], 'checks': checks, 'output': str(output)}, indent=2))
    return payload


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
    if '--captures' in sys.argv:
        import argparse
        parser = argparse.ArgumentParser(description='Offline captured-posting extension of the existing KE pilot')
        parser.add_argument('--captures', type=Path, required=True)
        parser.add_argument('--output', type=Path, required=True)
        parser.add_argument('--expected', type=Path)
        args = parser.parse_args()
        run_captures(args.captures, args.output, args.expected)
    else:
        main()

"""Experimental job decisions from verified RDF responsibilities, never titles.

Rule/catalog provenance is separate from frozen source facts. Outputs are machine
proposals, not ontology additions, human judgments or classification evaluation.
"""
import argparse
from collections import defaultdict
import csv
from html import escape
import io
from pathlib import Path
import re
import subprocess

import graph_vnext as builder
import review_export_vnext as evidence
import transport_vnext as transport
from rdflib import Graph, Namespace
from rdflib.namespace import OWL, RDF, RDFS, SKOS

VERSION = 'development-job-classifier-vnext-1'
EXP = 'urn:ke-market-observatory:experimental:job-classifier-vnext:'
ROLE = Namespace('urn:ke-market-observatory:role:')
CATEGORIES = ('Core KE', 'Adjacent Technical', 'Neither', 'Insufficient Evidence')
HUMAN_COLUMNS = ('case_id', 'human_classification', 'reviewer_id', 'reviewer_notes')
RULES = {
    'C1': {'name': 'Direct representation engineering',
           'condition': 'An imperative engineering action directly targets an explicit ontology, knowledge graph, semantic model, RDF schema or SHACL constraint. Collateral/product objects do not qualify.',
           'ontology_basis': [str(builder.KE.Responsibility), str(builder.KE.KnowledgeRepresentation), str(builder.KE.actsOnRepresentation)]},
    'C2': {'name': 'Core job proposal threshold',
           'condition': 'C1 includes explicit ownership (Own), or at least two nonduplicate responsibility statements directly engineer knowledge representations. Conditional/negated/qualification evidence cannot satisfy this threshold.'},
    'A1': {'name': 'Semantic-system infrastructure support',
           'condition': 'In one duty clause, an engineering action on ingestion frameworks/pipelines explicitly feeds semantic reasoning engines, or a technical API/query/pipeline component explicitly serves a knowledge graph. Generic AI/backend work and product names alone do not qualify.',
           'concept_uri': EXP + 'SemanticSystemSupport',
           'ontology_basis': [str(builder.KE.Responsibility)],
           'boundary_definition': [str(ROLE['knowledge-engineer']), str(ROLE['knowledge-graph-engineer'])]},
    'N1': {'name': 'Commercial account delivery',
           'condition': 'The responsibility explicitly negotiates and closes deals/agreements, or grows account relationships to drive upsell.',
           'concept_uri': EXP + 'CommercialWork', 'ontology_basis': [str(builder.KE.Responsibility)]},
    'N2': {'name': 'Commercial reporting and sales support',
           'condition': 'The responsibility creates reports about campaign results/advertising metrics or explicitly supports sales positioning/presentation materials.',
           'concept_uri': EXP + 'CommercialWork', 'ontology_basis': [str(builder.KE.Responsibility)]},
    'N3': {'name': 'Neither proposal threshold',
           'condition': 'At least two nonduplicate responsibilities support N1/N2, with no representation candidate, unmapped representation mention, adjacent support, conditional context or competing technical-engineering evidence. This is a scoped machine proposal, not proof that all possible duties are non-KE.',
           'boundary_definition': [str(ROLE['knowledge-engineer'])]},
    'U1': {'name': 'Abstain',
           'condition': 'Use Insufficient Evidence for missing/unmapped/conditional evidence, insufficient core-role support or mixed functional evidence. Generic technical work is not automatically Adjacent or Neither.'},
}
EXPERIMENTAL_CONCEPTS = {
    EXP + 'SemanticSystemSupport': {
        'label': 'Technical support for an explicit semantic reasoning/knowledge-graph system',
        'definition': 'Technical component delivery explicitly supports a semantic system; does not establish ownership of its knowledge representation.',
        'status': 'Experimental rule concept; not a frozen taxonomy occupation'},
    EXP + 'CommercialWork': {
        'label': 'Commercial account, reporting or sales work',
        'definition': 'Explicitly advertised commercial deliverables; not a KE occupational concept and not an exhaustive occupation classification.',
        'status': 'Experimental rule concept; not a frozen taxonomy occupation'},
}

REPRESENTATION = re.compile(r'\b(?:ontolog(?:y|ies)|knowledge graphs?|semantic models?|semantic reasoning engines?|RDF|SHACL|linked data)\b', re.I)
UNSAFE = re.compile(r'\b(?:not|never|without|may|might|could|occasionally|optional|familiarity|experience|preferred|skills? required|example|hypothetical)\b', re.I)
CONDITIONAL_CONTEXT = re.compile(r'\b(?:may|might|could|optional|example|qualifications?|requirements)\b', re.I)
DIRECT = re.compile(
    r'^(?P<action>design|build|implement|maintain|create|define|model|develop|integrate|extend|validate|own)'
    r'\s+(?:(?:and\s+)?(?:design|build|implement|maintain|create|define|develop|validate)\s*,?\s*)*'
    r'(?:(?:a|an|the|our|explicit|domain|formal|enterprise)\s+)*'
    r'(?P<object>ontolog(?:y|ies)|knowledge graphs?|semantic models?|RDF schemas?|SHACL constraints?)\b', re.I)
COLLATERAL = re.compile(r'^\s*(?:API(?:s)?|services?|products?|backend|documentation|presentations?|reports?|marketing|training|dashboards?)\b', re.I)
TECHNICAL = re.compile(r'\b(?:RESTful APIs?|CI/CD pipelines?|cloud infrastructure|ingestion frameworks?|data pipelines?|data storage solutions|GitOps|authentication mechanisms|data lakehouse)\b', re.I)
ACTION = re.compile(r'^(?:design|build|develop|implement|integrate|maintain|create|define|model|extend|validate|own)\b', re.I)
COMPONENT = re.compile(r'\b(?:ingestion frameworks?|data pipelines?|query APIs?|APIs?|query engines?|backend components?)\b', re.I)
SEMANTIC_FEED = re.compile(r'\bto feed\b[^.;\n]*\bsemantic reasoning engines?\b', re.I)
KG_SUPPORT = re.compile(r'\bfor (?:a|an|the|our) knowledge graph\b(?!\s+(?:product|service|named|called)\b)', re.I)
DEAL = re.compile(r'\bnegotiate\s*,?\s*(?:and\s+)?close\b[^.;\n]*\b(?:agreements|contracts|deals)\b', re.I)
UPSELL = re.compile(r'\b(?:build|grow)\b[^.;\n]*\brelationships\b[^.;\n]*\bupsell\b', re.I)
REPORT = re.compile(r'\breports?\b[^.;\n]*\b(?:campaign results|advertising metrics)\b', re.I)
SALES = re.compile(r'^support the sales organization\b[^.;\n]*\b(?:positioning stories|presentation materials)\b', re.I)


def vocabulary():
    ontology = Graph().parse(transport.ROOT / 'knowledge-engineering/04-ontology/ontology.ttl')
    taxonomy = Graph().parse(transport.ROOT / 'knowledge-engineering/03-taxonomy/role-taxonomy.ttl')
    concepts = dict(EXPERIMENTAL_CONCEPTS)
    for node in taxonomy.subjects(RDF.type, SKOS.Concept):
        concepts[str(node)] = {'label': str(taxonomy.value(node, SKOS.prefLabel)),
                               'definition': str(taxonomy.value(node, SKOS.definition)),
                               'status': 'Existing taxonomy proposal; team approval pending'}
    for node in (builder.KE.Responsibility, builder.KE.KnowledgeRepresentation, builder.KE.actsOnRepresentation):
        transport.require((node, None, None) in ontology, 'Missing ontology basis')
        concepts[str(node)] = {'label': str(ontology.value(node, RDFS.label)),
                               'definition': str(ontology.value(node, RDFS.comment)),
                               'status': 'Existing ontology proposal; no new approval inferred'}
    return concepts


def clauses(text):
    """Preserve source offsets while isolating a small, explicit clause grammar."""
    for match in re.finditer(r'[^.;\n]+', text):
        raw = match.group(); offset = match.start() + len(raw) - len(raw.lstrip())
        value = raw.strip()
        # A source category prefix is retained in the quotation but not an action.
        prefix = re.match(r'^[^:]{1,100}:\s+(?=(?:design|build|implement|optimize|monitor|ensure|lead)\b)', value, re.I)
        if prefix:
            offset += prefix.end(); value = value[prefix.end():]
        if value:
            yield value, offset


def support(row, rule_id, clause, offset, concept, relation):
    local_start, local_end = offset, offset + len(clause)
    transport.require(row['responsibility_text'][local_start:local_end] == clause, 'Rule quote offset mismatch')
    return {'rule_id': rule_id, 'rule_uri': EXP + 'rule:' + rule_id,
            'concept_uri': concept, 'concept_relation': relation,
            'ontology_basis': RULES[rule_id].get('ontology_basis', []),
            'responsibility_id': row['responsibility_id'], 'quote': row['responsibility_text'],
            'matched_clause': clause, 'source_capture': row['source_capture'],
            'capture_sha256': row['capture_sha256'], 'field_pointer': row['field_pointer'],
            'evidence_locator_json': row['evidence_locator_json'],
            'clause_span_start': row['span_start_codepoint'] + local_start,
            'clause_span_end': row['span_start_codepoint'] + local_end,
            'section_context_text': row['section_context_text'],
            'section_contexts_json': row['section_contexts_json']}


def independent(items):
    """Repeated document representations do not become independent job duties."""
    result, seen_clauses, seen_duties = [], set(), set()
    for item in items:
        key = re.sub(r'\W+', ' ', item['matched_clause'].casefold()).strip()
        if key not in seen_clauses and item['responsibility_id'] not in seen_duties:
            result.append(item); seen_clauses.add(key); seen_duties.add(item['responsibility_id'])
    return result


def classify_job(rows, concepts, *, case_id=None, source_title=''):
    transport.require((bool(rows) and len({r['case_id'] for r in rows}) == 1)
                      or (not rows and case_id is not None), 'One case identity required')
    core, adjacent, commercial = [], [], []
    unsafe_mentions, unmatched_mentions = [], []
    technical, conditional = False, False
    for row in rows:
        context_unsafe = bool(CONDITIONAL_CONTEXT.search(row['section_context_text']))
        conditional |= context_unsafe
        for clause, offset in clauses(row['responsibility_text']):
            technical |= bool(TECHNICAL.search(clause))
            if context_unsafe or UNSAFE.search(clause):
                if REPRESENTATION.search(clause): unsafe_mentions.append(row['responsibility_id'])
                continue
            direct = DIRECT.match(clause)
            mapped = False
            if direct and not COLLATERAL.match(clause[direct.end():]):
                target = direct['object'].casefold()
                concept = str(ROLE['knowledge-graph-engineer'] if target.startswith('knowledge graph') else
                              ROLE['knowledge-engineer'] if target.startswith('semantic model') else ROLE['ontology-engineer'])
                item = support(row, 'C1', clause, offset, concept, 'candidate occupational concept; experimental interpretation')
                item['action'] = direct['action'].casefold(); item['representation_text'] = direct['object']
                core.append(item); mapped = True
            if ACTION.match(clause) and COMPONENT.search(clause) and (SEMANTIC_FEED.search(clause) or KG_SUPPORT.search(clause)):
                adjacent.append(support(row, 'A1', clause, offset, EXP + 'SemanticSystemSupport',
                                        'experimental supporting-work concept, not a taxonomy occupation'))
                mapped = True
            if DEAL.search(clause) or UPSELL.search(clause):
                commercial.append(support(row, 'N1', clause, offset, EXP + 'CommercialWork', 'experimental alternative-function evidence'))
            if (ACTION.match(clause) and REPORT.search(clause)) or SALES.search(clause):
                commercial.append(support(row, 'N2', clause, offset, EXP + 'CommercialWork', 'experimental alternative-function evidence'))
            if REPRESENTATION.search(clause) and not mapped:
                unmatched_mentions.append(row['responsibility_id'])
    core, adjacent, commercial = independent(core), independent(adjacent), independent(commercial)
    has_core = any(i['action'] == 'own' for i in core) or len(core) >= 2
    commercial_threshold = len(commercial) >= 2
    uncertainty = ['Only extracted, source-verified responsibilities are assessed; complete role coverage and primary work are not independently established.',
                   'Existing taxonomy/ontology definitions are proposals; all decision rules and concept assignments here are experimental.']
    if not rows:
        uncertainty.append('No extracted responsibilities are available; titles are not decision evidence.')
    if (has_core or adjacent) and commercial_threshold:
        classification, supporting, triggered = 'Insufficient Evidence', [], ['U1']
        uncertainty.append('Competing representation-related and commercial responsibilities leave primary function unresolved.')
    elif has_core and not unsafe_mentions:
        classification, supporting, triggered = 'Core KE', core, ['C1', 'C2']
        uncertainty.append('Direct representation engineering supports a proposed Core function; job-level scope still requires human review.')
    elif adjacent and not unsafe_mentions:
        classification, supporting, triggered = 'Adjacent Technical', adjacent, ['A1']
        uncertainty.append('Technical delivery explicitly supports a semantic system; ownership of the representation and a Core role are not established.')
    elif commercial_threshold and not (core or adjacent or unsafe_mentions or unmatched_mentions or technical or conditional):
        classification, supporting, triggered = 'Neither', commercial, sorted({s['rule_id'] for s in commercial} | {'N3'})
        uncertainty.append('Neither is supported by explicit commercial functions in the observed duties, not by missing KE keywords; unextracted duties may change the job-level proposal.')
    else:
        classification, supporting, triggered = 'Insufficient Evidence', [], ['U1']
        if core: uncertainty.append('A representation-engineering candidate lacks explicit ownership or a second independent direct duty.')
        if technical: uncertainty.append('Generic technical duties do not establish direct representation work or explicit semantic-system support.')
        if conditional: uncertainty.append('The source qualifies some duties as conditional; those statements cannot establish the primary function.')
        if unsafe_mentions: uncertainty.append('Representation mentions occur in negated, conditional or qualification-like language.')
        if unmatched_mentions: uncertainty.append('Representation terminology is present but no supported action/object or technical-support rule resolves it.')
        if not any((core, technical, conditional, unsafe_mentions, unmatched_mentions)):
            uncertainty.append('No rule has enough positive, function-specific evidence to support a job-level decision.')
    for item in supporting:
        transport.require(item['concept_uri'] in concepts, 'Undefined decision concept')
        item['concept'] = concepts[item['concept_uri']]
    return {'version': VERSION, 'case_id': rows[0]['case_id'] if rows else case_id,
            'source_title': rows[0]['source_title'] if rows else source_title,
            'proposed_classification': classification, 'triggered_rules': triggered,
            'supporting_evidence': supporting, 'core_candidates': core if classification != 'Core KE' else [],
            'unresolved_uncertainties': uncertainty, 'responsibilities_considered': len(rows),
            'evidence_considered': [{k: r[k] for k in ('responsibility_id', 'responsibility_text', 'source_capture', 'capture_sha256',
                                                       'field_pointer', 'evidence_locator_json', 'section_context_text')} for r in rows],
            'human_ground_truth': {'classification': '', 'reviewer_id': '', 'reviewer_notes': ''}}


def classify_all(rows, concepts=None):
    concepts = vocabulary() if concepts is None else concepts
    groups = defaultdict(list)
    for row in rows: groups[row['case_id']].append(row)
    return [classify_job(group, concepts) for group in groups.values()]


def validate_decisions(decisions, rows, concepts):
    expected = classify_all(rows, concepts)
    transport.require(transport.canonical(decisions) == transport.canonical(expected), 'Decision claims do not follow the evidence/rules')
    by_id = {r['responsibility_id']: r for r in rows}
    for decision in decisions:
        transport.require(all(v == '' for v in decision['human_ground_truth'].values()), 'Human judgments must remain blank')
        if decision['proposed_classification'] != 'Insufficient Evidence':
            transport.require(bool(decision['supporting_evidence']), 'Positive decision has no source evidence')
        for item in decision['supporting_evidence']:
            source = by_id[item['responsibility_id']]
            transport.require(item['quote'] == source['responsibility_text'], 'Quotation differs from source duty')
            start, end = item['clause_span_start'], item['clause_span_end']
            transport.require(source['field_context_text'][start:end] == item['matched_clause'], 'Rule clause fails provenance resolution')
            transport.require(item['concept_uri'] in concepts and item['rule_id'] in RULES, 'Unsupported concept/rule')
    return True


def human_csv(decisions):
    out = io.StringIO(newline=''); writer = csv.DictWriter(out, fieldnames=HUMAN_COLUMNS, lineterminator='\n')
    writer.writeheader()
    for d in decisions:
        writer.writerow({'case_id': d['case_id'], 'human_classification': '', 'reviewer_id': '', 'reviewer_notes': ''})
    return out.getvalue()


def decision_html(decisions):
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'none\'; connect-src \'none\'; base-uri \'none\'">',
             '<title>Experimental Development job decisions</title><style>' + evidence.STYLE + '\n.proposal{font-size:22px;font-weight:700;color:#176579}.rule{font:13px ui-monospace,monospace}.support{border-left:3px solid #8cafbb;padding-left:14px;margin:18px 0}blockquote{margin:8px 0;white-space:pre-wrap;line-height:1.55}.concept{font-size:14px;color:#3f606c}</style></head><body>',
             '<header><h1>Experimental job decisions</h1><p>Six Development jobs · machine proposals with original responsibility evidence</p>',
             '<p>Human ground truth is blank and independent. Existing vocabulary remains a proposal; no classification accuracy is established.</p></header>',
             '<div class="bar"><a class="csv-link" href="human-ground-truth.csv" download>Blank human judgment CSV</a><span class="muted">Human classification, reviewer identity and notes are empty.</span></div>',
             '<main><nav class="case-nav" aria-label="Development jobs">']
    for d in decisions: parts.append('<a href="#' + escape(d['case_id'], quote=True) + '">' + escape(d['case_id']) + '</a>')
    parts.append('</nav>')
    for d in decisions:
        parts.append('<section class="case card" id="' + escape(d['case_id'], quote=True) + '" data-decision="' + escape(d['case_id'], quote=True) + '"><h2>' + escape(d['source_title']) + '</h2><p class="muted">' + escape(d['case_id']) + '</p><p class="proposal">' + escape(d['proposed_classification']) + '</p>')
        parts.append('<h3>Rules triggered</h3>')
        for rule_id in d['triggered_rules']:
            rule = RULES[rule_id]
            parts.append('<p><strong>' + rule_id + ' · ' + escape(rule['name']) + '</strong><br>' + escape(rule['condition']) + '</p>')
        parts.append('<h3>Supporting responsibility evidence</h3>')
        if not d['supporting_evidence']:
            parts.append('<p>No classification-positive evidence satisfies the decision rules. The source duties below remain available for independent review.</p>')
        for item in d['supporting_evidence']:
            parts.append('<div class="support"><p class="rule">' + escape(item['rule_id']) + ' · ' + escape(item['concept']['label']) + '</p><blockquote>' + escape(item['quote']) + '</blockquote>')
            if item['section_context_text']: parts.append('<p class="qualifier">' + escape(item['section_context_text']) + '</p>')
            parts.append('<p class="concept">' + escape(item['concept_relation']) + '<br>' + escape(item['concept']['definition']) + '<br>' + escape(item['concept_uri']) + '</p>')
            parts.append('<details><summary>Exact source and ontology/rule provenance</summary><pre>' + escape(transport.canonical({k: item[k] for k in ('source_capture', 'capture_sha256', 'field_pointer', 'evidence_locator_json', 'matched_clause', 'clause_span_start', 'clause_span_end', 'ontology_basis', 'rule_uri')})) + '</pre></details></div>')
        parts.append('<h3>Unresolved uncertainties</h3><ul>' + ''.join('<li>' + escape(s) + '</li>' for s in d['unresolved_uncertainties']) + '</ul>')
        parts.append('<details><summary>All ' + str(d['responsibilities_considered']) + ' considered responsibilities</summary>')
        for r in d['evidence_considered']:
            parts.append('<blockquote>' + escape(r['responsibility_text']) + '</blockquote><details><summary>Source location</summary><pre>' + escape(transport.canonical(r)) + '</pre></details>')
        parts.append('</details><p class="muted">Human ground-truth classification: ______ · Reviewer: ______ · Notes: ______</p></section>')
    parts.append('</main></body></html>')
    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(description='Experimental explainable job classification from saved Development RDF.')
    parser.add_argument('--graph-dir', type=Path, required=True)
    parser.add_argument('--packet-dir', type=Path, required=True)
    parser.add_argument('--blocked-results', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    root = transport.ROOT
    output = transport.safe_path(root, args.output_dir.resolve().relative_to(root), Path('learning-local'))
    transport.require(not output.exists(), 'Output exists; never overwrite saved results')
    transport.require(subprocess.run(['git', 'check-ignore', '--quiet', '--', str(output / 'probe.json')], cwd=root).returncode == 0, 'Output must be ignored')
    rows, hashes = evidence.collect(args.graph_dir, args.packet_dir, args.blocked_results)
    concepts = vocabulary(); decisions = classify_all(rows, concepts)
    transport.require(len(decisions) == 6, 'Expected all six Development jobs')
    validate_decisions(decisions, rows, concepts)
    # Market inclusion follows the user's geographic scope, independently of
    # occupational proposals. Keep every capture variant separate, including
    # equal upstream IDs advertised in different countries.
    import market_eligibility_vnext as market
    market_cases = transport.development_cases(root)
    market_decisions = [capture for d in decisions
                        for capture in market.case_captures(root, market_cases[d['case_id']])]
    output.mkdir(parents=True, exist_ok=False)
    files = {'decisions.json': transport.canonical({'version': VERSION, 'decisions': decisions}),
             'market-eligibility.json': transport.canonical({'policy': market.POLICY,
                 'capture_decisions': market_decisions, 'occupational_decisions_file': 'decisions.json',
                 'salary_evaluated': False}),
             'rules.json': transport.canonical({'version': VERSION, 'rules': RULES, 'concepts': concepts}),
             'human-ground-truth.csv': human_csv(decisions), 'decisions.html': decision_html(decisions),
             'verification.json': transport.canonical({'cases': 6, 'source_evidence_rows': len(rows),
                 'all_positive_decisions_have_verified_evidence_and_rules': True, 'human_ground_truth_blank': True,
                 'input_sha256': hashes, 'rule_code_sha256': transport.digest(Path(__file__).read_bytes()),
                 'ontology_sha256': transport.digest((root / 'knowledge-engineering/04-ontology/ontology.ttl').read_bytes()),
                 'taxonomy_sha256': transport.digest((root / 'knowledge-engineering/03-taxonomy/role-taxonomy.ttl').read_bytes())})}
    for name, value in files.items():
        with (output / name).open('x', encoding='utf-8', newline='') as handle: handle.write(value)
    print(transport.canonical({'proposals': [{'case_id': d['case_id'], 'classification': d['proposed_classification'],
                 'rules': d['triggered_rules']} for d in decisions], 'review_page': str(output / 'decisions.html')}))


if __name__ == '__main__':
    main()

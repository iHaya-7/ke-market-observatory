"""User-authorized geographic job scope, separate from occupation and salary.

Decide each authenticated capture independently. Case IDs and human decisions
are absent from the rule function; no cross-location acceptance propagation.
"""
import argparse
import base64
from collections import Counter
import csv
import io
from pathlib import Path
import re
import subprocess

import consumer_vnext as consumer
import transport_vnext as transport

VERSION = 'user-market-scope-2026-10-29'
S1_IMPLEMENTATION_VERSION = 'saudi-s1-responsibility-2'
SA = 'Saudi Arabia'
ALIASES = {'sa': SA, 'saudi arabia': SA, 'ksa': SA,
           'us': 'United States', 'usa': 'United States', 'united states': 'United States',
           'united states of america': 'United States', 'eg': 'Egypt', 'egypt': 'Egypt',
           'gb': 'United Kingdom', 'uk': 'United Kingdom', 'united kingdom': 'United Kingdom',
           'ae': 'United Arab Emirates', 'uae': 'United Arab Emirates',
           'de': 'Germany', 'germany': 'Germany', 'ca': 'Canada', 'canada': 'Canada'}
UNKNOWN = {'', 'unknown', 'not specified', 'unspecified', 'remote', 'worldwide', 'global',
           'multiple', 'international', 'anywhere', 'n/a', 'null'}
TITLE_FAMILIES = (
    'Knowledge Engineer', 'Knowledge Graph Engineer', 'Ontology Engineer', 'Ontologist',
    'Semantic Engineer', 'Semantic Web Engineer', 'Taxonomy Specialist', 'Taxonomy Engineer',
    'Knowledge Representation Engineer', 'Semantic Modeling Engineer', 'Semantic Modelling Engineer',
    'Ontology Architect', 'Knowledge Graph Architect', 'Knowledge Engineering Manager')
SENIORITY = r'(?:(?:senior|sr\.?|junior|jr\.?|lead|principal|staff|associate|graduate|mid[- ]level|chief)\s+)*'
TITLE_RULE = re.compile(r'^' + SENIORITY + r'(?P<profession>' + '|'.join(
    re.escape(p) for p in sorted(TITLE_FAMILIES, key=len, reverse=True)) +
    r')(?:\s+(?:I{1,3}|IV|V|[1-9]))?(?:\s*\(IC\))?(?:\s*[-–—|,]\s*[^\n]+)?$', re.I)
S1_ACTION = (r'(?:design(?:ing)?|develop(?:ing)?|build(?:ing)?|creat(?:e|ing)|implement(?:ing)?|maintain(?:ing)?|'
    r'validat(?:e|ing)|govern(?:ing)?|curat(?:e|ing)|integrat(?:e|ing)|defin(?:e|ing)|model(?:ing|ling)?|own(?:ing)?)')
S1_OBJECT = (r'knowledge graphs?|ontolog(?:y|ies)|semantic(?:\s+and\s+data mart)? layers?|taxonom(?:y|ies)|semantic models?|'
             r'controlled vocabularies|knowledge representations?|RDF schemas?|SHACL constraints?')
DIRECT = re.compile(
    r'^' + S1_ACTION + r'(?:(?:\s*,\s*(?:and\s+)?|\s+and\s+)' + S1_ACTION + r')*\s+'
    r'(?:(?:a|an|the|our|domain|explicit|formal|enterprise)\s+)*'
    r'(?P<object>' + S1_OBJECT + r')\b', re.I)
SEMANTIC_LEAD = re.compile(
    r'^lead(?:ing)?(?:\s+and\s+mentor(?:ing)?)?\s+(?:a\s+|the\s+|our\s+)?team\s+of\s+'
    r'(?P<object>semantic layer)\s+developers\b', re.I)
SEMANTIC_GOVERNANCE = re.compile(
    r'^enforc(?:e|ing)\s+(?:data\s+)?governance'
    r'(?:(?:,\s*(?:and\s+)?|\s+and\s+)(?:data quality standards|naming conventions))*'
    r'\s+across\s+(?:the\s+|our\s+)?(?P<object>semantic layers?)\b', re.I)
S1_HEADING = re.compile(r'^(?:(?:(?:key|main|core|your|job|role)\s+)?responsibilities|'
                        r'(?:duties|tasks) and responsibilities|responsibilities and duties|'
                        r'what you(?: will|[\x27’]ll) (?:do|own))\s*:?$', re.I)
S1_STOP = re.compile(r'^(?:required skills|skills(?: and experience)?|required experience|preferred experience|'
                     r'must[- ]have|nice to have|about (?:us|the company)|your (?:skills|qualifications))\b', re.I)
BULLET = re.compile(r'^\s*(?:[•●▪◦‣*-]\s+|\d+[.)]\s+)')
COLLATERAL = re.compile(r'^\s*(?:products?|presentations?|documentation|training|marketing|sales|report(?:s|ing)?|dashboards?|visualizations?|usage)\b', re.I)
NEGATED = re.compile(r'\b(?:not|never|no responsibility|familiarity|experience with|hypothetical|example)\b', re.I)
ROLE_CONTEXT = re.compile(
    r'^(?:This|The) (?:role|position|platform|data layer)\b[^.\n]*\b(?:support|supports|enable|enables|integrate|integrates)\b'
    r'[^.\n]*\b(?:knowledge graphs?|ontolog(?:y|ies)|semantic layers?|taxonom(?:y|ies)|semantic knowledge model(?:s|ing))\b', re.I)
PIPELINE = re.compile(r'^(?:build|develop|implement|integrate|maintain)\b[^.\n]*\b(?:ingestion frameworks?|data pipelines?)\b'
                      r'[^.\n]*\bto feed\b[^.\n]*\bsemantic reasoning engines?\b', re.I)
POLICY = {'version': VERSION, 'authority': 'User scope instruction, 2026-10-29',
          'G1': 'Outside Saudi Arabia: a clearly named KE profession in the original title is required. Description mentions cannot bypass this gate.',
          'S1': 'Saudi Arabia: an actual responsibility directly creates, models, curates, governs, validates or integrates an explicit knowledge representation.',
          'S2': 'Saudi Arabia: a responsibility explicitly builds ingestion/pipelines feeding semantic reasoning engines, corroborated by same-field source text assigning the role/platform to knowledge-graph/ontology/semantic-model support.',
          'L0': 'Unresolved or conflicting posting geography cannot establish market eligibility. Title, body mentions and remote status do not supply a country.',
          'salary': 'Salary availability, values and eligibility never enter the job eligibility rules.',
          'occupation': 'Core/Adjacent/Neither/Insufficient Evidence occupation proposals are a separate dimension.'}


def normalize_country(value):
    if not isinstance(value, str): return None
    text = value.strip(); low = text.casefold()
    if low in UNKNOWN or re.search(r'[,;/|]|\bor\b', low): return None
    return ALIASES.get(low, text)


def location(record):
    """Only posting location fields; never description/title/headquarters strings."""
    evidence, countries, displays = [], [], []
    def explicit(pointer, value):
        country = normalize_country(value)
        if country:
            evidence.append({'pointer': pointer, 'value': value, 'country': country}); countries.append(country)
    if record.get('country'):
        explicit('/country', record['country'])
    for i, item in enumerate(record.get('locations') or []):
        if isinstance(item, dict):
            if item.get('countryCode'): explicit('/locations/' + str(i) + '/countryCode', item['countryCode'])
            if item.get('country'): explicit('/locations/' + str(i) + '/country', item['country'])
    loc = record.get('location'); label = loc.get('name') if isinstance(loc, dict) else loc
    categories = record.get('categories')
    if not label and isinstance(categories, dict): label = categories.get('location')
    if isinstance(label, str) and label.strip(): displays.append(label.strip())
    # Greenhouse's assigned posting location/office countries supply explicit
    # country evidence. Never inspect employer prose or interpret the title's KSA.
    if not countries:
        candidates = [('/location/name' if isinstance(loc, dict) else '/location', label)]
        candidates += [('/offices/' + str(i) + '/location', x.get('location'))
                       for i, x in enumerate(record.get('offices') or []) if isinstance(x, dict)]
        for pointer, value in candidates:
            if not isinstance(value, str): continue
            for alias, country in sorted(ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
                if re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', value, re.I):
                    evidence.append({'pointer': pointer, 'value': value, 'country': country}); countries.append(country)
    unique = set(countries)
    country = next(iter(unique)) if len(unique) == 1 else None
    city = record.get('city')
    if isinstance(city, str) and city.strip(): displays.insert(0, city.strip())
    if country and not any(country.casefold() in s.casefold() for s in displays): displays.append(country)
    return {'country': country, 'display': ', '.join(dict.fromkeys(displays)) or 'Location unresolved',
            'evidence': evidence, 'conflict': len(unique) > 1}


def source_projection(record, source_type, artifact):
    """A field view of THIS capture, not a new replay input or merged posting."""
    return {'record': record, 'source': {'type': source_type},
            'field_owners': {k: artifact['sha256'] for k in record}, 'captures': [artifact]}


def clauses(text):
    for match in re.finditer(r'[^.\n]+', text):
        value = match.group().strip(); offset = match.start() + len(match.group()) - len(match.group().lstrip())
        prefix = re.match(r'^[^:]{1,100}:\s+(?=(?:design|build|implement|optimize|monitor|ensure|lead)\b)', value, re.I)
        if prefix: value = value[prefix.end():]; offset += prefix.end()
        yield value, offset


def s1_clauses(text):
    for clause, offset in clauses(text):
        bullet = BULLET.match(clause)
        if bullet:
            offset += bullet.end(); clause = clause[bullet.end():]
        yield clause, offset


def s1_match(clause):
    return DIRECT.match(clause) or SEMANTIC_LEAD.match(clause) or SEMANTIC_GOVERNANCE.match(clause)


def s1_duties(documents):
    """Saudi-only bounded responsibility views; never rewrite the rendered text or source."""
    duties = []
    for doc in documents:
        if doc['alternative_to']: continue
        label = doc['section_label']
        active = bool(label and S1_HEADING.fullmatch(label['value'].strip()))
        for row in re.finditer(r'[^\n]+', doc['text']):
            text = row.group(); heading = text.strip()
            if S1_HEADING.fullmatch(heading): active = True; continue
            if consumer.primitives.STOP.fullmatch(heading.rstrip(':')) or S1_STOP.match(heading):
                active = False; continue
            if active and any(s1_match(c) for c, _ in s1_clauses(text)):
                duties.append({'text': text, 'locator': {'source': doc['source'], 'transform': doc['transform'],
                                                       'start': row.start(), 'end': row.end()}})
    return duties


def saudi_support(record, source_type, artifact):
    packet = source_projection(record, source_type, artifact)
    if not any(isinstance(record.get(k), str) and record[k].strip() for k in
               ('content', 'description', 'full_description', 'opening', 'descriptionBody', 'additional')) and not record.get('lists'):
        return []
    docs = [d for d in consumer.document_views(packet) if not d['field_pointer'].startswith('/salaryDescription')]
    duties = consumer.extract_responsibilities(packet, docs)
    # Saudi responsibility detection is isolated from graph extraction and S2.
    scoped = s1_duties(docs)
    scoped_locators = {transport.canonical(d['locator']) for d in scoped}
    existing = {transport.canonical(d['locator']) for d in duties}
    duties.extend(d for d in scoped if transport.canonical(d['locator']) not in existing)
    context_by_ref = {}
    for doc in docs:
        matches = []
        for row in re.finditer(r'[^\n]+', doc['text']):
            for clause, offset in clauses(row.group()):
                if ROLE_CONTEXT.search(clause) and not NEGATED.search(clause):
                    matches.append({'source': doc['source'], 'transform': doc['transform'],
                                    'start': row.start() + offset, 'end': row.start() + offset + len(clause)})
        context_by_ref[transport.canonical(doc['source'])] = matches
    supported = []
    for duty in duties:
        for clause, offset in s1_clauses(duty['text']):
            if NEGATED.search(clause): continue
            direct = s1_match(clause) if transport.canonical(duty['locator']) in scoped_locators else None
            rule = 'S1' if direct and not COLLATERAL.match(clause[direct.end():]) else None
            contexts = context_by_ref.get(transport.canonical(duty['locator']['source']), [])
            if rule is None and PIPELINE.search(clause) and contexts: rule = 'S2'
            if rule:
                loc = {**duty['locator'], 'start': duty['locator']['start'] + offset,
                       'end': duty['locator']['start'] + offset + len(clause)}
                transport.require(consumer.resolve_evidence(packet, loc) == clause, 'Eligibility duty span mismatch')
                context_evidence = [{'text': consumer.resolve_evidence(packet, c), 'locator': c} for c in contexts] if rule == 'S2' else []
                supported.append({'rule': rule, 'quote': duty['text'], 'matched_clause': clause,
                                  'locator': loc, 'role_context': context_evidence})
    return supported


def decide(record, source_type, artifact):
    """No case ID, human reference, salary or occupational proposal is an input."""
    title = record.get('text') if source_type == 'lever' else record.get('title')
    transport.require(isinstance(title, str) and title.strip(), 'Missing original job title')
    loc = location(record); support = []; title_match = TITLE_RULE.fullmatch(title.strip())
    if loc['country'] is None:
        eligible, rule, reason = None, 'L0', 'Posting country is conflicting or unresolved; market scope cannot be established.'
    elif loc['country'] != SA:
        eligible, rule = bool(title_match), 'G1'
        reason = ('Original title explicitly names the KE profession ' + title_match['profession'] + '; salary is assessed separately.'
                  if title_match else 'Non-Saudi posting has a generic/non-KE occupational title; description mentions cannot satisfy the global title gate.')
    else:
        support = saudi_support(record, source_type, artifact)
        eligible = bool(support); rule = support[0]['rule'] if support else 'S0'
        reason = ('Saudi posting has source-cited substantive semantic responsibility evidence under ' + rule + '.'
                  if support else 'Saudi posting lacks supported substantive knowledge-representation responsibilities; title and generic Data/AI/software duties do not establish eligibility.')
    return {'policy_version': VERSION, 'title': title, 'location': loc,
            'job_market_eligible': eligible, 'decision': 'Accept' if eligible is True else 'Reject' if eligible is False else 'Unresolved',
            'rule': rule, 'reason': reason, 'responsibility_support': support,
            'source_capture': artifact['path'], 'capture_sha256': artifact['sha256'],
            'salary_evaluated': False, 'occupational_classification_used': False}


def case_captures(root, case):
    rows = []
    source_types = {s['id']: s['type'] for s in transport.loads((root / 'config/sources.json').read_bytes())['sources']}
    for i, spec in enumerate(case['captures']):
        path = transport.safe_path(root, spec['original_path'], transport.CORPUS)
        raw = path.read_bytes(); transport.require(transport.digest(raw) == spec['sha256'], 'Original capture hash mismatch')
        doc = transport.loads(raw)
        transport.require(doc['sourceId'] in source_types, 'Unknown source ID')
        transport.require(str(doc['sourceJobId']) == str(case['source_job_id']), 'Index/source job mismatch')
        transport.require(doc['sourceId'] == case['source_id'], 'Index/source ID mismatch')
        artifact = {'path': spec['original_path'].replace('\\', '/'), 'sha256': spec['sha256'],
                    'bytes_base64': base64.b64encode(raw).decode('ascii')}
        row = decide(doc['record'], source_types[doc['sourceId']], artifact)
        row.update({'case_id': case['case_id'], 'source_id': doc['sourceId'],
                    'source_job_id': str(doc['sourceJobId']), 'primary_indexed_capture': i == 0})
        rows.append(row)
    return rows


def all_development(root=transport.ROOT):
    cases = transport.development_cases(root)
    return [row for case in cases.values() for row in case_captures(root, case)]


def compare_reference(captures, reference):
    transport.require(reference.get('review_method') == 'user-provided, non-blind'
                      and reference.get('judgment_dimension') == 'job_market_eligibility'
                      and reference.get('independently_blinded') is False, 'Human reference must disclose non-blind market scope')
    primary = {r['case_id']: r for r in captures if r['primary_indexed_capture']}
    human = reference['decisions']
    transport.require(len(human) == len({r['case_id'] for r in human}) == 10
                      and {r['case_id'] for r in human} == set(primary), 'Reference must contain all ten authentic cases')
    result = []
    for h in human:
        row = primary[h['case_id']]
        transport.require(h['decision'] in ('Accept', 'Reject'), 'Invalid human eligibility decision')
        transport.require(h['capture_sha256'] == row['capture_sha256']
                          and h['country'] == row['location']['country'], 'Human decision bound to a different capture/location')
        result.append({**row, 'human_market_eligibility': h['decision'], 'agrees': row['decision'] == h['decision'],
                       'human_review_method': reference['review_method']})
    return result


def main():
    parser = argparse.ArgumentParser(description='Capture-specific Development market scope; occupation and salary stay separate.')
    parser.add_argument('--human-reference', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(); root = transport.ROOT
    output = transport.safe_path(root, args.output_dir.resolve().relative_to(root), Path('learning-local'))
    transport.require(not output.exists(), 'Output exists; no overwrites')
    transport.require(subprocess.run(['git', 'check-ignore', '--quiet', '--', str(output / 'probe.json')], cwd=root).returncode == 0, 'Output must be ignored')
    reference_path = transport.safe_path(root, args.human_reference.resolve().relative_to(root), Path('learning-local'))
    reference = transport.loads(reference_path.read_bytes())
    captures = all_development(root); comparison = compare_reference(captures, reference)
    report = {'policy': POLICY, 'title_families': TITLE_FAMILIES, 'capture_decisions': captures,
              'comparison': comparison, 'disagreements': [r['case_id'] for r in comparison if not r['agrees']],
              'reference_dimension': 'User-provided non-blind market eligibility; not blinded occupational ground truth'}
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'market-eligibility.json').open('x', encoding='utf-8') as f: f.write(transport.canonical(report))
    stream = io.StringIO(newline=''); fields = ('case_id', 'title', 'location', 'experimental_eligibility', 'human_eligibility', 'human_review_method', 'agrees', 'rule', 'reason', 'capture_sha256')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n'); writer.writeheader()
    for r in comparison:
        writer.writerow({'case_id': r['case_id'], 'title': r['title'], 'location': r['location']['display'],
                         'experimental_eligibility': r['decision'], 'human_eligibility': r['human_market_eligibility'],
                         'human_review_method': r['human_review_method'],
                         'agrees': r['agrees'], 'rule': r['rule'], 'reason': r['reason'], 'capture_sha256': r['capture_sha256']})
    with (output / 'comparison.csv').open('x', encoding='utf-8', newline='') as f: f.write(stream.getvalue())
    print(transport.canonical({'comparison': [{'case_id': r['case_id'], 'title': r['title'], 'location': r['location']['display'], 'decision': r['decision'], 'human': r['human_market_eligibility'], 'rule': r['rule']} for r in comparison],
                               'capture_count': len(captures), 'disagreements': report['disagreements']}))


if __name__ == '__main__':
    main()

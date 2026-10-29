"""Isolated field-aware consumer. No frozen extract(), graph build or classifier.

Title is metadata, not body text. Each HTML/plain field has its own document and
offset space. Lever list labels are section metadata, not synthesized prose.
Salary objects are retained independently of prose and eligibility decisions.
"""
import copy
import html
import importlib.util
import re

from transport_vnext import ROOT, at, canonical, reference, require, resolve_reference, verify_packet

spec = importlib.util.spec_from_file_location(
    'vnext_frozen_html_primitives', ROOT / 'knowledge-engineering/05-knowledge-graph/posting_evidence.py')
primitives = importlib.util.module_from_spec(spec)
spec.loader.exec_module(primitives)  # Only pure rendering/regex helpers; never extract().

HTML = 'html-blocks-v1-field-vnext-1'
PLAIN = 'plain-field-vnext-1'
PERIODS = {'per-year-salary': 'Annual', 'per-month-salary': 'Monthly',
           'per-hour-wage': 'Hourly'}

# These rules apply only to actual top-level HTML list items immediately after
# explicit duty context. They are not additional global keyword/title rules.
CONDITIONAL_LIST = re.compile(
    r'^(?:Your responsibilities may also include:|As (?:a|an) .+?\byour (?:main )?task will be '
    r'.+?\byour responsibilities may also include:)\s*$', re.I)
LABELED_HEADING = re.compile(r'^(?:Key )?Responsibilities:?$', re.I)
GERUND_DUTY = re.compile(r'^(?:supporting|assisting|designing|optimising|getting|working|collaborating)\b', re.I)
LABELED_ACTION = re.compile(r'^(?:design|build|implement|optimize|monitor|ensure|lead)\b', re.I)
NON_DUTY_LABEL = re.compile(r'^(?:experience|education|qualifications?|skills|requirements|benefits|nice to have)\b', re.I)


class _ListLayout(primitives.VisibleBlocks):
    """Observe list/bold boundaries without changing the frozen rendering.

    Only single-row items in top-level lists are supported by these additions.
    Nested or multi-paragraph bullets remain outside the new layout rules.
    """
    def __init__(self):
        super().__init__()
        self.lists, self.items, self.complete = [], [], []

    def handle_starttag(self, tag, attrs):
        if self.skip:
            super().handle_starttag(tag, attrs)
            return
        if tag in ('ul', 'ol'):
            if self.items:
                self.items[-1]['nested'] = True
            self.lists.append({'first_row': None, 'depth': len(self.lists) + 1})
        if tag == 'li':
            super().handle_starttag(tag, attrs)  # Same flush as the frozen renderer.
            group = self.lists[-1] if self.lists else None
            if group is not None and group['first_row'] is None:
                group['first_row'] = len(self.rows)
            self.items.append({'start': len(self.rows), 'group': group, 'nested': False,
                               'leading': True, 'bold_depth': 0, 'label_parts': []})
            return
        if tag in ('strong', 'b') and self.items:
            item = self.items[-1]
            if item['bold_depth'] or item['leading']:
                item['bold_depth'] += 1
        super().handle_starttag(tag, attrs)

    def handle_data(self, value):
        if not self.skip and self.items:
            item = self.items[-1]
            if item['bold_depth']:
                item['label_parts'].append(value)
            elif value.strip():
                item['leading'] = False
        super().handle_data(value)

    def handle_endtag(self, tag):
        if self.skip:
            super().handle_endtag(tag)
            return
        if tag == 'li' and self.items:
            super().handle_endtag(tag)
            item = self.items.pop()
            item['end'] = len(self.rows)
            self.complete.append(item)
            return
        if tag in ('strong', 'b') and self.items and self.items[-1]['bold_depth']:
            self.items[-1]['bold_depth'] -= 1
            if not self.items[-1]['bold_depth']:
                self.items[-1]['leading'] = False
        super().handle_endtag(tag)
        if tag in ('ul', 'ol') and self.lists:
            self.lists.pop()


def layout_duties(packet, doc):
    if doc['transform'] != HTML:
        return []
    raw = resolve_reference(packet, doc['source'])
    derived = html.unescape(raw) if raw.lstrip().startswith('&lt;') else raw
    parser = _ListLayout()
    parser.feed(derived)
    parser.flush()
    require('\n'.join(parser.rows) == doc['text'], 'Layout/rendered field alignment failed')
    rows = list(re.finditer(r'[^\n]+', doc['text']))
    result = []
    for item in sorted(parser.complete, key=lambda i: i['start']):
        group = item['group']
        if (group is None or group['depth'] != 1 or item['nested']
                or item['end'] != item['start'] + 1 or not group['first_row']):
            continue
        context = rows[group['first_row'] - 1]
        text = rows[item['start']].group()
        conditional = bool(CONDITIONAL_LIST.fullmatch(context.group()))
        heading = bool(LABELED_HEADING.fullmatch(context.group().strip()))
        label = ' '.join(''.join(item['label_parts']).split())
        rule = None
        if conditional and not label and GERUND_DUTY.match(text):
            rule = 'explicit-conditional-duty-list-v1'
        elif (heading and label.endswith(':') and len(label) <= 100
              and text.startswith(label) and not NON_DUTY_LABEL.match(label)
              and LABELED_ACTION.match(text[len(label):].lstrip())):
            rule = 'bold-labeled-duty-list-v1'
        if rule:
            row = rows[item['start']]
            result.append({'text': text, 'field_pointer': doc['field_pointer'],
                           'section_metadata': copy.deepcopy(doc['section_label']),
                           'locator': {'source': copy.deepcopy(doc['source']), 'transform': doc['transform'],
                                       'start': row.start(), 'end': row.end()},
                           'section_context': {'source': copy.deepcopy(doc['source']), 'transform': doc['transform'],
                                               'start': context.start(), 'end': context.end()},
                           'extraction_rule': rule,
                           'interpretation': primitives.interpret_duty(text)})
    return result


def render(raw, transform):
    require(isinstance(raw, str), 'Document field must be a string')
    if transform == PLAIN:
        return raw
    require(transform == HTML, 'Unsupported field transform')
    # Keep raw exactly in transport; explicitly version the derived view.
    derived = html.unescape(raw) if raw.lstrip().startswith('&lt;') else raw
    return primitives.visible(derived.encode('utf-8'))[0]


def resolve_evidence(packet, locator):
    raw = resolve_reference(packet, locator['source'])
    text = render(raw, locator['transform'])
    start, end = locator['start'], locator['end']
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text),
            'Invalid field evidence span')
    return text[start:end]


def document_views(packet):
    record = packet['record']; kind = packet['source']['type']; views = []
    def add(pointer, transform, label=None, alias=None):
        raw = at(record, pointer)
        require(isinstance(raw, str), 'Non-text document field: ' + pointer)
        views.append({'field_pointer': pointer, 'source': reference(packet, pointer),
                      'transform': transform, 'text': render(raw, transform),
                      'section_label': label, 'alternative_to': alias})
    pairs = [('content', None)] if kind == 'greenhouse' else (
        [(n, n + 'Plain') for n in ('opening', 'descriptionBody', 'description', 'additional', 'salaryDescription')]
        if kind == 'lever' else [('description', None), ('full_description', None)])
    for field, plain in pairs:
        if field in record:
            add('/' + field, HTML)
        if plain and plain in record:
            add('/' + plain, PLAIN, alias=('/' + field if field in record else None))
    if 'lists' in record:
        require(isinstance(record['lists'], list), 'Lists field must be an array')
        for index, item in enumerate(record['lists']):
            require(isinstance(item, dict) and isinstance(item.get('text'), str), 'Invalid list section metadata')
            require('content' in item, 'List section missing original content')
            add('/lists/' + str(index) + '/content', HTML,
                label={'value': item['text'], 'source': reference(packet, '/lists/' + str(index) + '/text')})
    require(any(v['text'].strip() for v in views), 'No nonempty body fields')
    return views


def structured_salary(packet):
    record = packet['record']; observations = []
    if 'salaryRange' in record and record['salaryRange'] is not None:
        raw = record['salaryRange']
        require(isinstance(raw, dict), 'Unsupported salaryRange shape; original retained but consumer stops')
        interval = raw.get('interval')
        period = PERIODS.get(interval) if packet['source']['type'] == 'lever' else None
        observations.append({'kind': 'source-structured-salary', 'raw': copy.deepcopy(raw),
                             'source': reference(packet, '/salaryRange'),
                             'field_sources': {k: reference(packet, '/salaryRange/' + k.replace('~', '~0').replace('/', '~1')) for k in raw},
                             'dimensions': {'min': raw.get('min'), 'max': raw.get('max'),
                                            'currency': raw.get('currency'), 'interval_token': interval,
                                            'explicit_period': period,
                                            'compensation_basis': None, 'pay_market': None},
                             'unresolved': ['compensation_basis', 'pay_market'] + ([] if period else ['pay_period']),
                             'interpretation': 'Source salary range; no base/total, eligibility, currency or market inference'})
    if 'pay_input_ranges' in record:
        require(isinstance(record['pay_input_ranges'], list), 'Unsupported pay_input_ranges shape')
        for i, raw in enumerate(record['pay_input_ranges']):
            observations.append({'kind': 'source-structured-range-uninterpreted', 'raw': copy.deepcopy(raw),
                                 'source': reference(packet, '/pay_input_ranges/' + str(i)),
                                 'interpretation': 'Original structure retained; dimensions not mapped by this consumer'})
    return observations


def extract_responsibilities(packet, documents):
    """Field extraction shared with capture-specific market scope checks.

    Callers authenticate their source bytes first. No replay selection, location,
    title classification or salary decision occurs in this pure extraction step.
    """
    duties = []
    for doc in documents:
        # HTML and plain alternatives are both retained. Prefer HTML for duty
        # interpretation; never combine fields or count alternatives as new jobs.
        if doc['alternative_to']:
            continue
        label = doc['section_label']
        active = bool(label and primitives.DUTIES.fullmatch(label['value'].strip().rstrip(':')))
        for row in re.finditer(r'[^\n]+', doc['text']):
            text = row.group()
            if primitives.DUTIES.fullmatch(text.strip().rstrip(':')):
                active = True
                continue
            if primitives.STOP.fullmatch(text.strip().rstrip(':')):
                active = False
                continue
            if active and primitives.DUTY_ACTION.search(text):
                duties.append({'text': text, 'field_pointer': doc['field_pointer'],
                               'section_metadata': copy.deepcopy(label),
                               'locator': {'source': copy.deepcopy(doc['source']),
                                           'transform': doc['transform'], 'start': row.start(), 'end': row.end()},
                               'interpretation': primitives.interpret_duty(text)})
        existing = {canonical(d['locator']) for d in duties}
        for duty in layout_duties(packet, doc):
            if canonical(duty['locator']) not in existing:
                duties.append(duty)
                existing.add(canonical(duty['locator']))
    return duties


def consume(packet):
    verify_packet(packet)
    documents = document_views(packet)
    duties = extract_responsibilities(packet, documents)
    result = {'version': 'development-field-consumer-vnext-2', 'case_id': packet['case_id'],
              'identity': copy.deepcopy(packet['identity']), 'title_metadata': copy.deepcopy(packet['title_metadata']),
              'documents': documents, 'responsibilities': duties, 'structured_salary': structured_salary(packet),
              'raw_field_sources': {k: reference(packet, '/' + k.replace('~', '~0').replace('/', '~1'))
                                    for k in packet['record']},
              'classification_executed': False,
              'scope': 'Field-scoped extraction only; no cross-field coverage, salary eligibility or approvals'}
    for name, ref in result['raw_field_sources'].items():
        require(canonical(resolve_reference(packet, ref)) == canonical(packet['record'][name]), 'Raw field fidelity failure')
    for evidence in duties:
        require(resolve_evidence(packet, evidence['locator']) == evidence['text'], 'Evidence fidelity failure')
        if 'section_context' in evidence:
            resolve_evidence(packet, evidence['section_context'])
    return result

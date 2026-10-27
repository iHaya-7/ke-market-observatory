"""Original Development split only. No discovery of shared/full corpus files."""
import contextlib
import csv
import datetime
import difflib
import html
from html.parser import HTMLParser
import importlib.metadata
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
import replay_support as p

sys.dont_write_bytecode = True
root = p.ROOT
out = p.OUT / 'development-split'
out.mkdir(exist_ok=True)
dev = root / 'knowledge-engineering/00-baseline/local-corpus/development/stage7b/v1'
first = json.loads(p.read(dev / 'development-case-index.json'))
seven_root = p.REMAINING
seven = json.loads(p.read(seven_root / 'source-inventory-v1.json'))['cases']
# Read only the case/split columns of this Development-only reviewer template;
# no judgments are used, copied, or interpreted.
splits = {r['case_id']: r['dataset_split'] for r in csv.DictReader(io.StringIO(p.read(seven_root / 'review-v1.csv').decode('utf-8-sig')))}
assert len(first) == 3 and len(seven) == 7
assert all(c['dataset_split'] == 'development' for c in first)
assert set(splits) == {c['case_id'] for c in seven} and set(splits.values()) == {'development'}
cases = first + seven
assert len({c['case_id'] for c in cases}) == 10
scope = {r['case_id']: r for r in csv.DictReader(io.StringIO(p.read(dev / 'salary-band-scope.csv').decode('utf-8-sig')))}
frozen = json.loads(p.read(p.FREEZE))
runtime = p.OUT / 'isolated-runtime'
for name, expected in frozen['frozen_files'].items():
    assert p.sha(p.read(runtime / name)) == expected['sha256'], name
deps = p.DEPS
os.environ['KE_LOCAL_DEPS'] = str(deps)
sys.path.insert(0, str(deps))
versions = {name: importlib.metadata.version(name) for name in frozen['dependencies']}
assert all(versions[name] == spec['version'] for name, spec in frozen['dependencies'].items())
before_path = p.BEFORE_PATH
assert p.read(before_path) == subprocess.check_output(['git', 'show', p.BASELINE + ':scripts/refresh.py'], cwd=root)
before = p.module('development_before', before_path)
pilot = p.module('development_after', runtime / 'knowledge-engineering/07-evaluation/ke_decision_pilot.py')
after = sys.modules['posting_evidence']
config = json.loads(subprocess.check_output(['git', 'show', p.BASELINE + ':config/sources.json'], cwd=root))
fx = json.loads(p.read(runtime / 'data/curated.json'))['fx']
assert fx['rates'] == {'SAR': 1, 'USD': 3.75, 'GBP': 5.005005, 'EUR': 4.205639}
assert fx['date'] == '2026-10-20'

class TextInventory(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self.tags = [], []
    def handle_data(self, value): self.text.append(value)
    def handle_starttag(self, tag, attrs): self.tags.append(tag)

rows = []
for case in cases:
    cid = case['case_id']
    row = {'case_id': cid, 'status': 'NOT EXECUTED', 'before': None, 'after': None,
           'before_execution': 'NOT EXECUTED', 'after_execution': 'NOT EXECUTED',
           'salary_designation': scope.get(cid, {'scope_status': 'No verified designation supplied by the consulted Development-only allowlist'}),
           'salary_output_binding': 'Unapproved; all extracted observations retained without selecting one',
           'captures': [], 'errors': []}
    try:
        docs = []
        for cap in case['captures']:
            path = (root / cap['original_path']).resolve()
            assert path.is_relative_to(p.CORPUS.resolve()) and cid in path.name
            assert path.parts[-3] in ('originals', 'details')
            data = p.read(path)
            assert p.sha(data) == cap['sha256'], 'Original capture checksum mismatch'
            doc = json.loads(data)
            docs.append((cap, doc))
            row['captures'].append({'path': str(path), 'sha256': p.sha(data), 'record': doc,
                'pointer_policy': 'Every preserved field remains at /record/<escaped field name>; no shared raw response opened'})
        primary = docs[0][1]
        detail = next((d for c,d in docs if '/details/' in c['original_path']), None)
        source_id = primary['sourceId']
        source = next(s for s in config['sources'] if s['id'] == source_id)
        kind = source['type']
        row['source_format'] = kind
        replay_path = p.CORPUS / 'selected' / cid / 'replay-input.json'
        raw = json.loads(p.read(replay_path))
        merged = dict(primary['record'])
        if detail: merged.update(detail['record'])
        assert raw == merged, 'Designated replay record differs from captured primary/detail merge'
        doc = detail or primary
        upstream = str(raw.get('id') if kind != 'workable' else raw.get('shortcode') or raw.get('code') or raw.get('id'))
        assert all(str(d['sourceJobId']) == upstream and d['sourceId'] == source_id for _,d in docs)
        if 'source_job_id' in case: assert str(case['source_job_id']) == upstream
        title = raw.get('text') or raw.get('title')
        url = raw.get('absolute_url') if kind == 'greenhouse' else raw.get('hostedUrl') if kind == 'lever' else raw.get('url') or raw.get('application_url') or raw.get('shortlink')
        clock = doc['capturedAtUtc']
        row['identity'] = {'source_id': source_id, 'source_job_id': upstream, 'url': url, 'title': title,
                           'replay_sha256': p.seen[replay_path], 'replay_matches_captures': True}
        row['settings'] = {'clock': clock, 'fx': fx, 'initial_curated': [], 'initial_automatic': [],
                           'overrides': {'approved': [], 'rejected': []}, 'network': 'No requests', 'expected_labels': None}
        row['structured_fields'] = [{'pointer': '/record/' + k.replace('~','~0').replace('/','~1'),
            'value': v, 'after_json_consumption': False} for k,v in raw.items() if k not in ('content','description','full_description')]
        if kind == 'lever':
            row['status'] = 'BLOCKED'
            row['reason'] = 'Nonempty salaryRange plus split description/additional/list fields. Proven single-field HTML transport cannot preserve consumption of the structured salary observation; no synthesized page or salary prose created.'
            row['structured_salary_nonempty'] = bool(raw.get('salaryRange'))
            continue
        if raw.get('pay_input_ranges'):
            raise ValueError('Nonempty structured pay_input_ranges has no verified HTML transport')
        field = 'content' if kind == 'greenhouse' else 'description'
        if kind == 'workable' and raw.get('full_description'):
            raise ValueError('Additional full_description needs a verified multi-field transport')
        content = raw[field]
        if detail: assert content == detail['record'][field]
        transport = html.unescape(content) if content.lstrip().startswith('&lt;') else content
        mode = 'one outer HTML unescape' if transport != content else 'UTF-8 only; already HTML'
        if transport != content:
            escaped = transport.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')
            assert content in (escaped, escaped.replace("'", '&#39;')), 'Outer entity layer is not exactly reversible'
            row['outer_roundtrip'] = 'Exact, including numeric apostrophe escaping where present'
        parser = TextInventory(); parser.feed(transport); parser.close()
        encoded = transport.encode('utf-8')
        visible, _ = after.visible(encoded)
        row['transport'] = {'mode': mode, 'pointer': '/record/' + field, 'sha256': p.sha(encoded),
                            'derived_not_original_html_capture': True, 'title_present': title in visible,
                            'before_after_cleaned_text_equal': ' '.join(visible.split()) == before.clean(content)}
        if title not in visible:
            raise ValueError('Frozen After requires manifest job title inside content; original HTML fragment lacks it. Title insertion not attempted. Frozen whitespace-rendering differences, if present, were not corrected.')
        assert not set(parser.tags).intersection(after.VisibleBlocks.hidden), 'Hidden source content requires separate fidelity analysis'
        left, right = before.clean(content), ' '.join(visible.split())
        changes = [{'before': left[i:j], 'after': right[k:l], 'before_offset': i, 'after_offset': k}
                   for tag,i,j,k,l in difflib.SequenceMatcher(None,left,right,autojunk=False).get_opcodes() if tag != 'equal']
        row['transport']['frozen_renderer_differences'] = changes
        assert all(not x['before'].strip() and not x['after'].strip() for x in changes), 'Non-whitespace visible text differs from Before cleaned source'
        # Different frozen renderers may put whitespace around inline elements.
        # Record, never repair, this native behavior. Independently verify that
        # every source text character survives apart from frozen whitespace.
        assert ''.join(''.join(parser.text).split()) == ''.join(visible.split()), 'Visible source characters omitted or altered'
        row['transport']['text_fidelity'] = True
        member = 'originals/' + cid + '.html'
        entry = {'candidate_id': cid, 'status': 'CAPTURED', 'snapshot_file': member, 'job_title': title,
                 'requested_url': url, 'upstream_job_id': upstream, 'employer': source['company'],
                 'captured_utc': clock, 'sha256': p.sha(encoded), 'bytes': len(encoded)}
        archive = runtime / 'learning-local/development-split' / (cid + '.zip')
        archive.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('capture_report.json', json.dumps({'entries': [entry], 'notice': 'Derived transport from original JSON; no new capture'}))
            z.writestr(member, encoded)
        items = after.load_captures(archive)
        assert len(items) == 1 and items[0]['case_id'] == cid
        for passage in items[0]['passages']:
            assert after.resolve_html(encoded, passage['locator']) == passage['text']
        row['transport']['native_locators'] = [x['locator'] for x in items[0]['passages']]
        row['transport']['source_id_crosswalk'] = {'original': source_id, 'after': items[0]['source_id']}
        row['transport']['provenance_owner'] = 'Wrapper chain from captured JSON hash/pointer to derived HTML hash; native locators remain HTML-only'
        fixed = datetime.datetime.fromisoformat(clock.replace('Z','+00:00'))
        class FixedClock(datetime.datetime):
            @classmethod
            def now(cls, tz=None): return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)
        pilot.validation.builder.datetime = FixedClock
        body = before.clean(raw[field]) if kind == 'greenhouse' else before.clean(str(raw.get('description',''))+' '+str(raw.get('full_description','')))
        normalized = before.normalize(raw, source, clock)
        row['before'] = {'assess_role': before.assess_role(before.clean(title), body),
                         'salary_info': before.salary_info(raw, kind, body), 'normalize': normalized,
                         'actual_operational_queue': before.build_review_queue([], [normalized] if normalized else [], {'approved': [], 'rejected': []})}
        row['before_execution'] = 'PASS'
        output = runtime / 'learning-local/development-split' / cid
        with contextlib.redirect_stdout(io.StringIO()):
            row['after'] = pilot.run_captures(archive, output)
        row['after_pilot_queue'] = json.loads((output / 'review-queue.json').read_text())
        assert len(row['after']['cases']) == 1 and row['after']['cases'][0]['case_id'] == cid
        row['after_execution'] = 'PASS'
        row['status'], row['reason'] = 'PASS', 'Faithful single-field transport; frozen execution and source/SHACL validation passed. Salary designation and output bindings remain unapproved.'
    except Exception as error:
        row['status'] = 'BLOCKED'
        row['reason'] = str(error)
        row['errors'].append({'type': type(error).__name__, 'message': str(error)})
    finally:
        rows.append(row)
        (out / (cid + '.json')).write_text(json.dumps(row, indent=2, ensure_ascii=False), encoding='utf-8')
        print('Case completed:', row['status'])

assert all(p.sha(path.read_bytes()) == digest for path,digest in p.seen.items()), 'Read input changed'
summary = {'scope': '10 original Development identities from Development-only indexes/templates; no full corpus manifest or shared raw response accessed',
           'identity_basis': 'Existing local Development-only indexes and their capture hashes; not a fresh verification against the forbidden mixed-split manifest',
           'dependency_versions': versions, 'inputs_unchanged': True, 'approvals': 'Not collected or inferred by this tool',
           'cases': [{k:r.get(k) for k in ('case_id','source_format','status','reason','before_execution','after_execution')} for r in rows]}
(out / 'compatibility.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')

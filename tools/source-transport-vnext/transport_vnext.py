"""Development-only, lossless structured transport. Never discovers corpus cases."""
import argparse
import base64
import copy
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

VERSION = 'development-source-transport-vnext-1'
ROOT = Path(__file__).resolve().parents[2]
DEV = Path('knowledge-engineering/00-baseline/local-corpus/development/stage7b/v1')
CORPUS = Path('knowledge-engineering/00-baseline/local-corpus/20261021T125408Z-ebb0b062')


class TransportError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise TransportError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def loads(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise TransportError('Non-finite JSON number: ' + value)
    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise TransportError('Invalid UTF-8 JSON') from error


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':'))


def escape(token):
    return str(token).replace('~', '~0').replace('/', '~1')


def tokens(pointer):
    require(isinstance(pointer, str) and pointer.startswith('/'), 'Invalid JSON pointer')
    result = pointer[1:].split('/')
    require(all(not re.search(r'~(?![01])', t) for t in result), 'Invalid pointer escape')
    return [t.replace('~1', '/').replace('~0', '~') for t in result]


def at(value, pointer):
    for token in tokens(pointer):
        if isinstance(value, list):
            require(bool(re.fullmatch(r'0|[1-9][0-9]*', token)), 'Invalid array pointer')
            require(int(token) < len(value), 'Array pointer out of bounds')
            value = value[int(token)]
        else:
            require(isinstance(value, dict) and token in value, 'Pointer does not resolve')
            value = value[token]
    return value


def safe_path(root, relative, within):
    """Reject links and traversal before reading an explicitly designated file."""
    text = str(relative).replace('\\', '/')
    rel = PurePosixPath(text)
    require(not rel.is_absolute() and '..' not in rel.parts and ':' not in text,
            'Unsafe relative path')
    require(not any(re.search(r'(?i)held|holdout|mixed', p) for p in rel.parts),
            'Forbidden split path')
    cursor = root.resolve()
    for part in rel.parts:
        cursor /= part
        require(not cursor.is_symlink() and not cursor.is_junction(), 'Linked path rejected')
    require(cursor.resolve().is_relative_to((root / within).resolve()), 'Path outside allowlist')
    return cursor


def make_packet(case_id, specs, capture_bytes, replay_bytes, source):
    """Input bytes remain embedded verbatim; merged fields retain their owners.

    The primary is the first indexed capture. The first detail overwrites whole
    top-level fields exactly as in the transferred wrapper, never recursively.
    Supplementary original versions are retained, never silently merged.
    """
    require(bool(re.fullmatch(r'[A-Za-z0-9_-]+', case_id)), 'Unsafe case ID')
    require(source.get('type') in ('greenhouse', 'lever', 'workable'), 'Unsupported source type')
    require(len(specs) == len(capture_bytes) and bool(specs), 'Capture list mismatch')
    docs, artifacts, clean_specs = [], [], []
    for spec, data in zip(specs, capture_bytes):
        path = spec['original_path'].replace('\\', '/')
        short = PurePosixPath(path)
        require(not short.is_absolute() and '..' not in short.parts and ':' not in path,
                'Unsafe capture path')
        require(short.parts[:len(CORPUS.parts)] == CORPUS.parts, 'Wrong corpus')
        tail = short.parts[len(CORPUS.parts):]
        require(len(tail) == 3 and tail[0] in ('originals', 'details')
                and case_id in tail[-1] and tail[-1].endswith('.json'), 'Not a case-specific capture')
        require(digest(data) == spec['sha256'], 'Original capture hash mismatch')
        doc = loads(data)
        require(isinstance(doc.get('record'), dict), 'Capture record must be an object')
        require(doc.get('sourceId') == source['id'], 'Source ID mismatch')
        require(doc.get('sourceType', source['type']) == source['type'], 'Source type mismatch')
        docs.append((tail[0], doc))
        artifacts.append({'sha256': digest(data), 'path': path,
                          'bytes_base64': base64.b64encode(data).decode('ascii')})
        clean_specs.append({'original_path': path, 'sha256': spec['sha256']})
    require(docs[0][0] == 'originals', 'First capture must be the indexed primary')
    details = [i for i, (role, _) in enumerate(docs) if role == 'details']
    require(len(details) <= 1, 'Multiple detail versions need an explicit selection policy')
    record = copy.deepcopy(docs[0][1]['record'])
    owners = {key: artifacts[0]['sha256'] for key in record}
    if details:
        index = details[0]
        record.update(copy.deepcopy(docs[index][1]['record']))
        owners.update({key: artifacts[index]['sha256'] for key in docs[index][1]['record']})
    require(canonical(record) == canonical(loads(replay_bytes)), 'Replay differs from primary/detail merge')
    kind = source['type']
    job_id = record.get('id') if kind != 'workable' else (
        record.get('shortcode') or record.get('code') or record.get('id'))
    require(job_id is not None and str(job_id) != '', 'Missing source job ID')
    require(all(str(d['sourceJobId']) == str(job_id) for _, d in docs), 'Source job ID mismatch')
    title_key = 'text' if kind == 'lever' else 'title'
    title = record.get(title_key)
    require(isinstance(title, str) and bool(title.strip()), 'Missing structured title')
    url_keys = {'lever': ('hostedUrl',), 'greenhouse': ('absolute_url',),
                'workable': ('url', 'application_url', 'shortlink')}[kind]
    url_key = next((k for k in url_keys if record.get(k)), None)
    require(url_key is not None and isinstance(record[url_key], str), 'Missing original source URL')
    packet = {'version': VERSION, 'case_id': case_id, 'source': copy.deepcopy(source),
              'capture_specs': clean_specs, 'captures': artifacts,
              'replay_bytes_base64': base64.b64encode(replay_bytes).decode('ascii'),
              'replay_sha256': digest(replay_bytes), 'record': record, 'field_owners': owners,
              'identity': {'source_id': source['id'], 'source_type': kind,
                           'source_job_id': str(job_id), 'source_url': record[url_key]},
              'primary_capture_sha256': artifacts[0]['sha256']}
    packet['title_metadata'] = {'value': title, 'reference': reference(packet, '/' + title_key)}
    return packet


def reference(packet, pointer):
    key = tokens(pointer)[0]
    require(key in packet['field_owners'], 'Field has no source owner')
    at(packet['record'], pointer)
    return {'capture_sha256': packet['field_owners'][key], 'pointer': '/record' + pointer}


def resolve_reference(packet, ref):
    matches = [a for a in packet['captures'] if a['sha256'] == ref['capture_sha256']]
    require(bool(matches), 'Unknown source artifact')
    data = base64.b64decode(matches[0]['bytes_base64'], validate=True)
    require(digest(data) == ref['capture_sha256'], 'Source artifact hash mismatch')
    return at(loads(data), ref['pointer'])


def verify_packet(packet):
    require(packet.get('version') == VERSION, 'Unsupported transport version')
    try:
        raw = [base64.b64decode(a['bytes_base64'], validate=True) for a in packet['captures']]
        replay = base64.b64decode(packet['replay_bytes_base64'], validate=True)
        rebuilt = make_packet(packet['case_id'], packet['capture_specs'], raw, replay, packet['source'])
        require(canonical(rebuilt) == canonical(packet), 'Packet value/provenance tampering')
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, TransportError):
            raise
        raise TransportError('Invalid transport packet') from error
    return packet


def development_cases(root):
    first = loads(safe_path(root, DEV / 'development-case-index.json', DEV).read_bytes())
    remaining = DEV / 'Lubna/remaining-seven-v1'
    seven = loads(safe_path(root, remaining / 'source-inventory-v1.json', remaining).read_bytes())['cases']
    # Deliberately project only identity columns, never labels or judgments.
    rows = [{k: row[k] for k in ('case_id', 'dataset_split', 'source_id', 'source_job_id')}
            for row in csv.DictReader(io.StringIO(safe_path(
                root, remaining / 'review-v1.csv', remaining).read_text(encoding='utf-8-sig')))]
    require(len(first) == 3 and len(seven) == len(rows) == 7, 'Expected Development 3+7 package')
    require(all(c['dataset_split'] == 'development' for c in first)
            and all(r['dataset_split'] == 'development' for r in rows), 'Non-Development input')
    require(len({r['case_id'] for r in rows}) == 7
            and {r['case_id'] for r in rows} == {c['case_id'] for c in seven}, 'Seven-case identity mismatch')
    result = {c['case_id']: copy.deepcopy(c) for c in first + seven}
    require(len(result) == 10, 'Duplicate Development case IDs')
    for row in rows:
        result[row['case_id']].update(row)
    return result


def blocked_cases(root, results_path):
    rel = results_path.resolve().relative_to(root.resolve())
    path = safe_path(root, rel, Path('learning-local'))
    require(path.name == 'compatibility.json' and path.parent.name == 'development-split',
            'Use the explicit Development compatibility summary')
    cases = development_cases(root)
    rows = loads(path.read_bytes())['cases']
    require(len(rows) == len({r['case_id'] for r in rows}) == 10
            and {r['case_id'] for r in rows} == set(cases), 'Summary is not the authentic Development set')
    ids = [r['case_id'] for r in rows if r['status'] == 'BLOCKED']
    require(len(ids) == 6, 'Expected exactly six historical blockers')
    return [cases[cid] for cid in ids]


def load_case(root, case):
    raw = [safe_path(root, c['original_path'], CORPUS).read_bytes() for c in case['captures']]
    replay = safe_path(root, CORPUS / 'selected' / case['case_id'] / 'replay-input.json', CORPUS).read_bytes()
    source_id = loads(raw[0])['sourceId']
    sources = loads((root / 'config/sources.json').read_bytes())['sources']
    match = next((s for s in sources if s['id'] == source_id), None)
    require(match is not None, 'Unknown configured source')
    packet = make_packet(case['case_id'], case['captures'], raw, replay,
                         {'id': match['id'], 'type': match['type']})
    for key in ('source_id', 'source_job_id'):
        if key in case:
            require(str(case[key]) == packet['identity'][key], 'Index identity mismatch: ' + key)
    return packet


def main():
    parser = argparse.ArgumentParser(description='Development-only vNext transport smoke; no classifier or evaluation.')
    parser.add_argument('--blocked-results', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True, help='New directory under ignored learning-local')
    args = parser.parse_args()
    output = args.output_dir.resolve()
    rel = output.relative_to(ROOT)
    safe_path(ROOT, rel, Path('learning-local'))
    require(not output.exists(), 'Output already exists; never overwrite')
    require(subprocess.run(['git', 'check-ignore', '--quiet', '--', str(rel / 'probe.json')],
                           cwd=ROOT).returncode == 0, 'Output is not Git-ignored')
    cases = blocked_cases(ROOT, args.blocked_results)
    from consumer_vnext import consume, resolve_evidence
    prepared = []
    # Validate every case before creating output, so a transport failure stops here.
    for case in cases:
        packet = load_case(ROOT, case)
        consumed = consume(loads(canonical(packet)))
        for evidence in consumed['responsibilities']:
            require(resolve_evidence(packet, evidence['locator']) == evidence['text'], 'Evidence round-trip failed')
        prepared.append((packet, consumed))
    output.mkdir(parents=True, exist_ok=False)
    statuses = []
    for packet, consumed in prepared:
        for suffix, value in (('transport', packet), ('consumer', consumed)):
            with (output / (packet['case_id'] + '.' + suffix + '.json')).open('x', encoding='utf-8') as handle:
                json.dump(value, handle, ensure_ascii=False, allow_nan=False, indent=2)
        statuses.append({'case_id': packet['case_id'], 'transport_status': 'PASS',
                         'documents': len(consumed['documents']),
                         'structured_salary_observations': len(consumed['structured_salary']),
                         'responsibility_passages': len(consumed['responsibilities'])})
    with (output / 'smoke.json').open('x', encoding='utf-8') as handle:
        json.dump({'version': VERSION, 'scope': 'six authentic Development transport cases only',
                   'classification_executed': False, 'cases': statuses}, handle, indent=2)
    print(json.dumps({'processed': len(statuses), 'blocked': 0, 'output_dir': str(rel)}))


if __name__ == '__main__':
    main()

"""Query saved Development RDF into a verified, private offline review bundle."""
import argparse
import base64
from collections import Counter, defaultdict
import csv
from html import escape
import io
import json
from pathlib import Path
import subprocess

import consumer_vnext as consumer
import transport_vnext as transport
import graph_vnext as builder
from rdflib import Graph
from rdflib.namespace import RDF

HERE = Path(__file__).resolve().parent
KE, VX, PROV = builder.KE, builder.VX, builder.PROV
REVIEW_FIELDS = ('Is this a genuine job responsibility?',
                 'Does it provide evidence of Knowledge Engineering work?', 'Reviewer notes')
COLUMNS = ('case_id', 'source_title', 'responsibility_id', 'responsibility_text',
           'source_capture', 'capture_sha256', 'field_pointer', 'render_transform',
           'span_start_codepoint', 'span_end_codepoint', 'evidence_locator_json',
           'section_context_text', 'section_contexts_json', 'field_context_text') + REVIEW_FIELDS


def one(graph, subject, predicate):
    values = list(graph.objects(subject, predicate))
    transport.require(len(values) == 1, 'Expected exactly one ' + str(predicate))
    return values[0]


def query(name):
    return (HERE / 'queries' / name).read_text(encoding='utf-8')


def original_bytes(artifact):
    return transport.safe_path(transport.ROOT, artifact['path'], transport.CORPUS).read_bytes()


def evidence_reader(packet, reader):
    """Resolve against ORIGINAL bytes, also comparing the packet's embedded copy."""
    artifacts = {a['sha256']: a for a in packet['captures']}
    cache = {}
    def resolve(row):
        sha = str(row['sha256']); capture = str(row['capture'])
        transport.require(sha in artifacts and capture == artifacts[sha]['path'], 'Capture/reference mismatch')
        if sha not in cache:
            data = reader(artifacts[sha])
            transport.require(transport.digest(data) == sha, 'Original Development capture hash mismatch')
            transport.require(data == base64.b64decode(artifacts[sha]['bytes_base64'], validate=True),
                              'Original and transported bytes differ')
            cache[sha] = transport.loads(data)
        locator = transport.loads(str(row['locator']))
        ref = locator['source']
        transport.require(ref['capture_sha256'] == sha, 'Locator belongs to another capture')
        value = transport.at(cache[sha], ref['pointer'])
        transport.require(transport.canonical(value) == str(row['source_value']), 'Exact source field value differs')
        if locator['transform'] == 'json':
            transport.require(locator['pointer'] == ref['pointer'], 'JSON pointer mismatch')
            resolved = transport.canonical(value)
        else:
            text = consumer.render(value, locator['transform'])
            start, end = locator['start'], locator['end']
            transport.require(type(start) is int and type(end) is int and 0 <= start < end <= len(text),
                              'Evidence span out of bounds')
            resolved = text[start:end]
        transport.require(resolved == str(row['text']), 'Evidence text does not resolve to original source')
        return locator, value, resolved
    return resolve


def query_rows(graph, packet, *, reader=original_bytes):
    """Exactly one row per RDF responsibility; contexts are aggregated separately."""
    transport.verify_packet(packet)
    runs = list(graph.subjects(RDF.type, VX.GraphBuild))
    transport.require(len(runs) == 1, 'Exactly one graph build required')
    run = runs[0]
    transport.require(str(one(graph, run, VX.caseId)) == packet['case_id'], 'Graph/case identity mismatch')
    ids = set(graph.subjects(RDF.type, KE.Responsibility))
    raw = list(graph.query(query('responsibilities.rq')))
    returned = [r['responsibility'] for r in raw]
    transport.require(len(returned) == len(set(returned)) and set(returned) == ids,
                      'Query is incomplete or returns duplicate responsibility evidence')
    transport.require(int(one(graph, run, VX.extractedResponsibilityCount)) == len(raw),
                      'Graph responsibility count does not match query')
    resolve = evidence_reader(packet, reader)
    contexts = defaultdict(list)
    seen_contexts = set()
    for r in graph.query(query('responsibility_contexts.rq')):
        key = (r['responsibility'], r['evidence'], r['context'])
        transport.require(key not in seen_contexts and r['responsibility'] in ids, 'Duplicate/orphan context')
        seen_contexts.add(key)
        locator, value, text = resolve(r)
        contexts[r['responsibility']].append({'evidence': r['evidence'], 'locator': locator,
                                            'source_capture': str(r['capture']), 'text': text, 'value': value})
    rows = []
    for r in raw:
        transport.require(str(r['case_id']) == packet['case_id'], 'Query case mismatch')
        locator, field, text = resolve(r)
        transport.require(locator['transform'] in (consumer.HTML, consumer.PLAIN), 'Duty is not a rendered field span')
        body = consumer.render(field, locator['transform'])
        section = []
        for ctx in contexts[r['responsibility']]:
            transport.require(ctx['evidence'] == r['evidence'], 'Context belongs to another evidence passage')
            ref = ctx['locator']['source']
            full_field = ctx['locator']['transform'] == 'json' and ref == locator['source']
            if not full_field:
                value = ctx['value'] if ctx['locator']['transform'] == 'json' else ctx['text']
                transport.require(isinstance(value, str), 'Section qualifier must be source text')
                section.append({'text': value, 'source_capture': ctx['source_capture'],
                                'locator': ctx['locator']})
        section.sort(key=lambda c: transport.canonical(c['locator']))
        row = {'case_id': str(r['case_id']), 'source_title': str(r['title']),
               'responsibility_id': str(r['responsibility']), 'responsibility_text': text,
               'source_capture': str(r['capture']), 'capture_sha256': str(r['sha256']),
               'field_pointer': locator['source']['pointer'], 'render_transform': locator['transform'],
               'span_start_codepoint': locator['start'], 'span_end_codepoint': locator['end'],
               'evidence_locator_json': transport.canonical(locator),
               'section_context_text': '\n\n'.join(c['text'] for c in section),
               'section_contexts_json': transport.canonical(section), 'field_context_text': body}
        row.update({name: '' for name in REVIEW_FIELDS})
        rows.append(row)
    rows.sort(key=lambda r: (r['case_id'], r['field_pointer'], r['span_start_codepoint'], r['responsibility_id']))
    return rows


def collect(graph_dir, packet_dir, results, *, root=transport.ROOT, expected_total=49):
    graph_dir = transport.safe_path(root, graph_dir.resolve().relative_to(root), Path('learning-local'))
    packet_dir = transport.safe_path(root, packet_dir.resolve().relative_to(root), Path('learning-local'))
    rows, hashes = [], {}
    cases = transport.blocked_cases(root, results)
    for case in cases:
        cid = case['case_id']
        def read(folder, suffix):
            path = transport.safe_path(root, (folder / (cid + suffix)).relative_to(root), Path('learning-local'))
            data = path.read_bytes(); hashes[path.relative_to(root).as_posix()] = transport.digest(data)
            return data
        packet = transport.loads(read(packet_dir, '.transport.json'))
        consumed = transport.loads(read(packet_dir, '.consumer.json'))
        transport.require(transport.canonical(packet) == transport.canonical(transport.load_case(root, case)),
                          'Packet does not match authentic Development case')
        builder.check_consumer(packet, consumed)
        graph = Graph().parse(data=read(graph_dir, '.ttl').decode('utf-8'), format='turtle')
        run = next(iter(graph.subjects(RDF.type, VX.GraphBuild)), None)
        transport.require(run is not None, 'Missing graph build')
        for predicate, value in ((VX.transportSHA256, packet), (VX.consumerSHA256, consumed)):
            transport.require(str(one(graph, run, predicate)) == transport.digest(transport.canonical(value).encode()),
                              'Saved graph input digest mismatch')
        result = query_rows(graph, packet)
        actual = Counter((r['responsibility_text'], r['evidence_locator_json']) for r in result)
        expected = Counter((d['text'], transport.canonical(d['locator'])) for d in consumed['responsibilities'])
        transport.require(actual == expected, 'RDF query does not cover verified consumer responsibilities exactly')
        rows.extend(result)
    transport.require(len(rows) == expected_total, 'Unexpected total responsibility row count')
    transport.require(len({r['responsibility_id'] for r in rows}) == len(rows), 'Cross-case duplicate responsibility ID')
    transport.require(all(transport.digest((root / p).read_bytes()) == h for p, h in hashes.items()), 'Input changed during query')
    return rows, hashes


def csv_text(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator='\n', extrasaction='raise')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


STYLE = '''
:root{font-family:system-ui,sans-serif;color:#172c35;background:#f3f6f7;font-size:16px}
*{box-sizing:border-box}body{margin:0}header{background:#153d48;color:white;padding:24px max(24px,calc((100vw - 1180px)/2))}
header h1{font-size:25px;margin:0 0 8px}header p{margin:6px 0;max-width:850px;line-height:1.5}
.bar{position:sticky;top:0;background:#fff;border-bottom:1px solid #ccd8dc;padding:12px 24px;z-index:2;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
button,.csv-link{background:#176579;color:white;border:0;border-radius:6px;padding:11px 16px;font-weight:650;cursor:pointer;text-decoration:none}
main{max-width:1180px;margin:auto;padding:24px}.case-nav{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:28px}
.case-nav a{background:#e0edf1;padding:9px 12px;border-radius:5px;color:#143d49;font-size:13px;text-decoration:none}
.case{scroll-margin-top:90px;margin-bottom:40px}.case h2{font-size:20px;margin:4px 0}.case .title{color:#47626c;margin:8px 0 16px}
.card{background:#fff;border:1px solid #cfdbdf;border-radius:9px;margin:14px 0;padding:20px;box-shadow:0 2px 5px #203b4510}
.card h3{font-size:13px;color:#57727c;margin:0 0 12px}.duty{font-size:17px;line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere;margin:0 0 16px}
.qualifier{border-left:3px solid #a5c5cf;padding:8px 14px;white-space:pre-wrap;color:#37535e;line-height:1.5;background:#f4f8fa}
.empty-context{font-size:13px;color:#607882}details{margin:14px 0}summary{cursor:pointer;font-size:14px;color:#255b6b}
pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.55 ui-monospace,monospace;background:#f4f6f7;padding:12px;max-height:350px;overflow:auto}
dl{display:grid;grid-template-columns:140px 1fr;gap:8px;font-size:13px}dt{font-weight:650}dd{margin:0;overflow-wrap:anywhere}
.review{border-top:1px solid #e0e7ea;margin-top:18px;padding-top:16px;display:grid;grid-template-columns:1fr 1fr;gap:16px}
label{display:block;font-size:14px;line-height:1.4}select,textarea{display:block;width:100%;margin-top:8px;border:1px solid #aabcc4;border-radius:5px;background:white;padding:10px;font:inherit;color:#183b49}
.notes{grid-column:1/-1}textarea{min-height:65px;resize:vertical}.muted{font-size:13px;color:#516d78}
@media(max-width:650px){main{padding:14px}.card{padding:15px}.review{grid-template-columns:1fr}dl{grid-template-columns:1fr}.bar{position:static}.case h2{font-size:16px}}
@media print{.bar,.case-nav,.review{display:none}.card{break-inside:avoid;box-shadow:none}body{background:white}.case{break-before:page}}
'''

SCRIPT = r'''
const rows = JSON.parse(document.getElementById('evidence-data').textContent);
const columns = JSON.parse(document.getElementById('column-data').textContent);
document.querySelectorAll('[data-row][data-field]').forEach(control => {
  control.addEventListener('input', () => { rows[Number(control.dataset.row)][control.dataset.field] = control.value; });
});
document.querySelectorAll('.case-nav a').forEach(link => link.addEventListener('click', () => {
  const target = document.getElementById(link.hash.slice(1));
  if (target) target.scrollIntoView({behavior: 'smooth', block: 'start'});
}));
const cell = value => {
  const s = String(value ?? '');
  return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
};
document.getElementById('download-review').addEventListener('click', () => {
  const text = [columns.map(cell).join(','), ...rows.map(row => columns.map(c => cell(row[c])).join(','))].join('\n') + '\n';
  const url = URL.createObjectURL(new Blob([text], {type: 'text/csv;charset=utf-8'}));
  const link = document.createElement('a'); link.href = url; link.download = 'responsibility-review.csv';
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
'''


def json_script(value):
    return json.dumps(value, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


def html_text(rows):
    groups = defaultdict(list)
    for index, row in enumerate(rows):
        groups[row['case_id']].append((index, row))
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; script-src \'unsafe-inline\'; connect-src \'none\'; form-action \'none\'; base-uri \'none\'">',
             '<title>Development responsibility evidence review</title><style>' + STYLE + '</style></head><body>',
             '<header><h1>Responsibility evidence review</h1><p>' + str(len(rows)) + ' verified source spans · ' + str(len(groups)) + ' Development cases</p>',
             '<p>Read each statement with its original context, then record your own judgment. All reviewer fields start blank.</p></header>',
             '<div class="bar"><button id="download-review" type="button">Download review CSV</button>',
             '<a class="csv-link" href="responsibilities.csv" download>Original blank CSV</a>',
             '<span class="muted">Changes stay in this tab. Download CSV to save your review.</span></div><main>',
             '<nav class="case-nav" aria-label="Development cases">']
    for cid, entries in groups.items():
        parts.append('<a href="#case-' + escape(cid, quote=True) + '">' + escape(cid) + ' · ' + str(len(entries)) + '</a>')
    parts.append('</nav>')
    for cid, entries in groups.items():
        parts.append('<section class="case" id="case-' + escape(cid, quote=True) + '"><h2>' + escape(cid) + '</h2>')
        parts.append('<p class="title">Source title: ' + escape(entries[0][1]['source_title']) + '</p>')
        fields = {}
        for _, r in entries:
            fields[(r['source_capture'], r['field_pointer'])] = r['field_context_text']
        parts.append('<details><summary>Full source field context</summary>')
        for (capture, pointer), text in fields.items():
            parts.append('<p class="muted">' + escape(capture) + ' · ' + escape(pointer) + '</p><pre>' + escape(text) + '</pre>')
        parts.append('</details>')
        for number, (index, r) in enumerate(entries, 1):
            parts.append('<article class="card" data-responsibility="' + escape(r['responsibility_id'], quote=True) + '"><h3>Responsibility ' + str(number) + ' of ' + str(len(entries)) + '</h3>')
            parts.append('<p class="duty">' + escape(r['responsibility_text']) + '</p>')
            if r['section_context_text']:
                parts.append('<div class="qualifier">' + escape(r['section_context_text']) + '</div>')
            else:
                parts.append('<p class="empty-context">A separate section qualifier was not recorded. Read the field context below.</p>')
            start = max(0, r['span_start_codepoint'] - 240); end = min(len(r['field_context_text']), r['span_end_codepoint'] + 240)
            parts.append('<details><summary>Source context and exact location</summary><pre>' + escape(r['field_context_text'][start:end]) + '</pre><dl>')
            for label, value in (('Capture', r['source_capture']), ('SHA-256', r['capture_sha256']),
                                 ('Field pointer', r['field_pointer']), ('Rendered span', str(r['span_start_codepoint']) + '–' + str(r['span_end_codepoint'])),
                                 ('Transform', r['render_transform'])):
                parts.append('<dt>' + label + '</dt><dd>' + escape(str(value)) + '</dd>')
            parts.append('</dl><p class="muted">Spans use zero-based Unicode code-point offsets with an exclusive end.</p>')
            if r['section_context_text']:
                parts.append('<pre>' + escape(r['section_contexts_json']) + '</pre>')
            parts.append('</details><div class="review">')
            for field in REVIEW_FIELDS[:2]:
                ident = 'review-' + str(index) + '-' + str(REVIEW_FIELDS.index(field))
                parts.append('<label for="' + ident + '">' + escape(field) + '<select id="' + ident + '" data-row="' + str(index) + '" data-field="' + escape(field, quote=True) + '"><option value=""></option><option value="Yes">Yes</option><option value="No">No</option><option value="Uncertain">Uncertain</option></select></label>')
            parts.append('<label class="notes" for="notes-' + str(index) + '">Reviewer notes<textarea id="notes-' + str(index) + '" data-row="' + str(index) + '" data-field="Reviewer notes"></textarea></label></div></article>')
        parts.append('</section>')
    parts += ['</main><script id="evidence-data" type="application/json">' + json_script(rows) + '</script>',
              '<script id="column-data" type="application/json">' + json_script(COLUMNS) + '</script>',
              '<script>' + SCRIPT + '</script></body></html>']
    return '\n'.join(parts)


def write_bundle(rows, output):
    root = transport.ROOT
    output = transport.safe_path(root, output.resolve().relative_to(root), Path('learning-local'))
    transport.require(not output.exists(), 'Output already exists; no overwrites')
    transport.require(subprocess.run(['git', 'check-ignore', '--quiet', '--', str(output / 'probe.json')], cwd=root).returncode == 0,
                      'Review output must be Git-ignored')
    transport.require(all(r[f] == '' for r in rows for f in REVIEW_FIELDS), 'Initial review judgments must be blank')
    csv_data, html_data = csv_text(rows), html_text(rows)
    transport.require(list(csv.DictReader(io.StringIO(csv_data))) == [{k: str(v) for k, v in r.items()} for r in rows],
                      'CSV round-trip changed evidence values')
    output.mkdir(parents=True, exist_ok=False)
    for name, text in (('responsibilities.csv', csv_data), ('review.html', html_data)):
        with (output / name).open('x', encoding='utf-8', newline='') as handle:
            handle.write(text)


def main():
    parser = argparse.ArgumentParser(description='Query saved Development RDF into a private offline evidence review.')
    parser.add_argument('--graph-dir', type=Path, required=True)
    parser.add_argument('--packet-dir', type=Path, required=True)
    parser.add_argument('--blocked-results', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    rows, hashes = collect(args.graph_dir, args.packet_dir, args.blocked_results)
    write_bundle(rows, args.output_dir)
    report = {'verified_evidence_rows': len(rows), 'case_counts': dict(Counter(r['case_id'] for r in rows)),
              'reviewer_fields_blank': True, 'original_capture_and_context_locators_verified': True,
              'source_input_sha256': hashes, 'query_sha256': {p.name: transport.digest(p.read_bytes()) for p in (HERE / 'queries').glob('*.rq')},
              'classification_executed': False}
    with (args.output_dir / 'verification.json').open('x', encoding='utf-8') as handle:
        json.dump(report, handle, indent=2)
    print(transport.canonical({'verified_evidence_rows': len(rows), 'case_counts': report['case_counts'],
                               'review_page': str(args.output_dir / 'review.html')}))


if __name__ == '__main__':
    main()

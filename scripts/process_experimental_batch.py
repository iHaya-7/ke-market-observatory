"""Process explicitly selected, separately saved employer captures with unchanged market rules."""
import argparse
import base64
import copy
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import sys

from preview_filters import ROOT
sys.path.insert(0, str(ROOT / 'tools/source-transport-vnext'))
import transport_vnext as transport
import market_eligibility_vnext as eligibility


class SourceFields(HTMLParser):
    """Select original HTML fields by explicit attributes; retain exact character spans."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.lines = [0]
        self.lines.extend(i + 1 for i, c in enumerate(text) if c == '\n')
        self.stack, self.fields, self.scripts = [], {}, []
        self.feed(text)

    def char_offset(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('meta', 'link', 'img', 'input', 'br', 'hr', 'source', 'area', 'wbr', 'embed'): return
        self.stack.append((tag, attrs, self.char_offset() + len(self.get_starttag_text())))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        index = next((i for i in range(len(self.stack) - 1, -1, -1) if self.stack[i][0] == tag), None)
        if index is None: return
        _, attrs, start = self.stack[index]
        end = self.char_offset()
        if attrs.get('data-sourceflow-prop') in ('content', 'location'):
            key = attrs['data-sourceflow-prop']
            transport.require(key not in self.fields, 'Ambiguous source field: ' + key)
            self.fields[key] = dict(start=start, end=end, value=self.text[start:end])
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.scripts.append(dict(start=start, end=end, value=transport.loads(self.text[start:end])))
        del self.stack[index:]


def project(spec, body):
    """Alias explicit provider fields only; keep original values and mapping, never rewrite prose."""
    kind = spec['format']
    if kind in ('workable', 'greenhouse'):
        original = transport.at(transport.loads(body), spec['pointer'])
        return copy.deepcopy(original), {'record': {'response_pointer': spec['pointer']}}, original
    if kind == 'smartrecruiters':
        original = transport.loads(body)
        mapping = {'title': '/name', 'country': '/location/country', 'city': '/location/city'}
        record = {key: transport.at(original, pointer) for key, pointer in mapping.items()}
        # Original country code is retained. No guessed national eligibility or pay market.
        record['location'] = {'name': original['location']['fullLocation']}
        mapping['location.name'] = '/location/fullLocation'
        return record, {'json_fields': mapping}, original
    fields = SourceFields(body.decode('utf-8'))
    jobs = [s for s in fields.scripts if isinstance(s['value'], dict) and s['value'].get('@type') == 'JobPosting']
    transport.require(len(jobs) == 1, 'Expected one original JobPosting')
    source = jobs[0]; original = source['value']
    mapping = {'title': '/title', 'description': '/description',
               'country': '/jobLocation/address/addressCountry', 'city': '/jobLocation/address/addressLocality'}
    record = {key: transport.at(original, pointer) for key, pointer in mapping.items()}
    provenance = {'jsonld_span': {'start': source['start'], 'end': source['end']}, 'jsonld_fields': mapping}
    if kind == 'sourceflow':
        # JSON-LD has flattened paragraphs; use the untouched original description HTML instead.
        record['description'] = fields.fields['content']['value']
        provenance['html_fields'] = {'description': fields.fields['content']}
        del provenance['jsonld_fields']['description']
        if fields.fields.get('location'):
            record['location'] = {'name': fields.fields['location']['value']}
            provenance['html_fields']['location.name'] = fields.fields['location']
    return record, provenance, original


def known_postings(root):
    """Only explicit Development indexes and existing public records; no corpus manifest discovery."""
    import refresh
    cases = transport.development_cases(root)
    identities = {(c['source_id'], str(c['source_job_id'])) for c in cases.values()}
    public = transport.loads((root / 'public/data/market.json').read_bytes())
    urls = {refresh.canonical(r['sourceUrl']) for r in public['records']}
    return identities, urls


def process(selection, root=ROOT):
    import refresh
    root = Path(root).resolve()
    selection = transport.safe_path(root, Path(selection).resolve().relative_to(root), Path('learning-local'))
    selected = transport.loads(selection.read_bytes())
    transport.require(0 < len(selected['candidates']) <= 10, 'At most ten deliberately selected candidates')
    output = selection.parent / 'processed'
    transport.require(not output.exists(), 'Use a fresh processed batch; no overwrites')
    identities, urls = known_postings(root)
    prepared = []
    for spec in selected['candidates']:
        identity = (spec['source_id'], str(spec['source_job_id']))
        url = refresh.canonical(spec['source_url'])
        transport.require(identity not in identities and url not in urls, 'Previously processed posting excluded')
        identities.add(identity); urls.add(url)
        path = transport.safe_path(root, spec['response_path'], selection.parent)
        body = path.read_bytes()
        transport.require(transport.digest(body) == spec['response_sha256'], 'Response hash mismatch')
        record, projection, original = project(spec, body)
        capture = dict(sourceId=spec['source_id'], sourceJobId=str(spec['source_job_id']), sourceType=spec['format'],
                       sourceUrl=spec['source_url'], retrievedAtUtc=spec['retrieved_at_utc'],
                       record=record, originalRecord=original, fieldMapping=projection,
                       response=dict(path=spec['response_path'], sha256=spec['response_sha256'], pointer=spec.get('pointer')),
                       listingStatus=spec['listing_status'], listingEvidence=spec['listing_evidence'],
                       employer=spec['employer'], uncertainties=spec.get('uncertainties', []),
                       salaryAvailability=spec['salary_availability'])
        encoded = transport.canonical(capture).encode('utf-8')
        case_id = 'NEW-' + hashlib.sha256((spec['source_id'] + '\0' + str(spec['source_job_id']) + '\0'
                                         + str(record.get('country'))).encode()).hexdigest()[:16]
        destination = output / 'captures' / (case_id + '.json')
        artifact = dict(path=destination.relative_to(root).as_posix(), sha256=transport.digest(encoded),
                        bytes_base64=base64.b64encode(encoded).decode())
        decision = eligibility.decide(record, spec['format'], artifact)
        decision.update(case_id=case_id, source_id=spec['source_id'], source_job_id=str(spec['source_job_id']),
                        primary_indexed_capture=True, source_url=spec['source_url'],
                        listing_status=spec['listing_status'], listing_evidence=spec['listing_evidence'],
                        salary_availability=spec['salary_availability'], uncertainties=spec.get('uncertainties', []))
        prepared.append((destination, encoded, decision))
    output.mkdir()
    (output / 'captures').mkdir()
    for path, raw, _ in prepared:
        with path.open('xb') as f: f.write(raw)
    decisions = [d for _, _, d in prepared]
    report = dict(batch_kind='new-employer-candidates', policy=eligibility.POLICY,
                  title_families=eligibility.TITLE_FAMILIES, capture_decisions=decisions,
                  human_reference=None, selection_path=selection.relative_to(root).as_posix(),
                  eligibility_implementation_sha256=transport.digest((root / 'tools/source-transport-vnext/market_eligibility_vnext.py').read_bytes()),
                  shortfalls=selected['shortfalls'])
    with (output / 'market-eligibility.json').open('x', encoding='utf-8') as f: f.write(transport.canonical(report))
    print(json.dumps([dict(title=d['title'], location=d['location'], decision=d['decision'], rule=d['rule'],
                           responsibility_support=d['responsibility_support']) for d in decisions], ensure_ascii=True))
    return output


def rerun_saved(results_path, output, root=ROOT):
    """Reuse authenticated capture bytes; write a fresh report without copying captures."""
    from preview_market_eligibility import development_dataset
    root = Path(root).resolve()
    results_path = transport.safe_path(root, Path(results_path).resolve().relative_to(root), Path('learning-local'))
    output = transport.safe_path(root, Path(output).resolve().relative_to(root), Path('learning-local'))
    transport.require(not output.exists(), 'Use a fresh result directory; no overwrites')
    prior_bytes = results_path.read_bytes(); prior = transport.loads(prior_bytes)
    transport.require(prior.get('batch_kind') == 'new-employer-candidates', 'Expected saved employer batch')
    development_dataset(root, results_path)  # Authenticate source bytes and field mappings first.
    selection_path = transport.safe_path(root, prior['selection_path'], Path('learning-local'))
    decisions = []
    for row in prior['capture_decisions']:
        path = transport.safe_path(root, row['source_capture'], selection_path.parent / 'processed/captures')
        raw = path.read_bytes(); capture = transport.loads(raw)
        artifact = dict(path=row['source_capture'], sha256=transport.digest(raw), bytes_base64=base64.b64encode(raw).decode())
        transport.require(artifact['sha256'] == row['capture_sha256'], 'Capture hash mismatch')
        current = eligibility.decide(capture['record'], capture['sourceType'], artifact)
        result = {**copy.deepcopy(row), **current}
        resolved = [n for n in result.get('uncertainties', [])
                    if current['rule'] == 'S1' and n.startswith('Explicit semantic-layer duty is present. Unchanged S1 may miss')]
        if resolved:
            result['prior_coverage_notes'] = resolved
            result['uncertainties'] = [n for n in result['uncertainties'] if n not in resolved]
        decisions.append(result)
    report = {**copy.deepcopy(prior), 'capture_decisions': decisions,
              'previous_results': results_path.relative_to(root).as_posix(),
              'previous_results_sha256': transport.digest(prior_bytes),
              'responsibility_detection_version': eligibility.S1_IMPLEMENTATION_VERSION,
              'eligibility_implementation_sha256': transport.digest((root / 'tools/source-transport-vnext/market_eligibility_vnext.py').read_bytes())}
    output.mkdir()
    with (output / 'market-eligibility.json').open('x', encoding='utf-8') as f: f.write(transport.canonical(report))
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--selection', type=Path)
    mode.add_argument('--rerun-results', type=Path)
    parser.add_argument('--output', type=Path, help='Fresh directory for a saved-capture rerun')
    args = parser.parse_args()
    if args.rerun_results:
        if not args.output: parser.error('--output is required with --rerun-results')
        print(rerun_saved(args.rerun_results, args.output))
    else:
        if args.output: parser.error('--output applies only to --rerun-results')
        process(args.selection)

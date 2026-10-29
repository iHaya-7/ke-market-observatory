"""Project saved Development decisions into the existing site; never refresh or publish."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse
import copy
import json
import subprocess
import sys

from preview_filters import ROOT, build_preview

sys.path.insert(0, str(ROOT / 'tools/source-transport-vnext'))
import transport_vnext as transport


def development_dataset(root, results_path):
    root = Path(root).resolve()
    results_path = transport.safe_path(root, Path(results_path).resolve().relative_to(root), Path('learning-local'))
    raw = results_path.read_bytes()
    results = transport.loads(raw)
    new_batch = results.get('batch_kind') == 'new-employer-candidates'
    cases = {} if new_batch else transport.development_cases(root)
    primary = [r for r in results['capture_decisions'] if r['primary_indexed_capture']]
    if new_batch:
        transport.require(0 < len(primary) <= 10 and len(primary) == len({r['case_id'] for r in primary}), 'Expected up to ten separate new postings')
        transport.require(results.get('human_reference') is None, 'New system decisions are not human reference labels')
        selection_path = transport.safe_path(root, results['selection_path'], Path('learning-local'))
        selection = transport.loads(selection_path.read_bytes())
    else:
        transport.require(len(primary) == len(cases) == len({r['case_id'] for r in primary}) == 10
                          and {r['case_id'] for r in primary} == set(cases), 'Expected ten indexed Development postings')
    config = transport.loads((root / 'config/sources.json').read_bytes())
    sources = {s['id']: s for s in config['sources']}
    public = transport.loads((root / 'public/data/market.json').read_bytes())
    records = []
    for decision in primary:
        if new_batch:
            case = dict(case_id=decision['case_id'], source_id=decision['source_id'], source_job_id=decision['source_job_id'])
            path = transport.safe_path(root, decision['source_capture'], selection_path.parent / 'processed/captures')
        else:
            case = cases[decision['case_id']]
            spec = case['captures'][0]
            transport.require(decision['source_capture'] == spec['original_path'].replace('\\', '/')
                              and decision['capture_sha256'] == spec['sha256'], 'Decision is not bound to the primary indexed capture')
            path = transport.safe_path(root, decision['source_capture'], transport.CORPUS / 'originals')
        capture_bytes = path.read_bytes()
        transport.require(transport.digest(capture_bytes) == decision['capture_sha256'], 'Source capture hash mismatch')
        capture = transport.loads(capture_bytes)
        record = capture['record']
        if new_batch:
            from process_experimental_batch import project
            selected = [s for s in selection['candidates'] if s['source_id'] == capture['sourceId'] and str(s['source_job_id']) == capture['sourceJobId']]
            transport.require(len(selected) == 1, 'Ambiguous batch source identity')
            selected = selected[0]
            response_path = transport.safe_path(root, selected['response_path'], selection_path.parent)
            body = response_path.read_bytes()
            transport.require(transport.digest(body) == selected['response_sha256'] == capture['response']['sha256'], 'Raw response changed')
            projected, mapping, original = project(selected, body)
            transport.require(projected == record and mapping == capture['fieldMapping'] and original == capture['originalRecord'], 'Projection no longer resolves exactly to source')
        transport.require(capture['sourceId'] == case['source_id'] == decision['source_id']
                          and str(capture['sourceJobId']) == str(case['source_job_id']) == decision['source_job_id'], 'Posting identity mismatch')
        transport.require(decision['title'] == (record.get('title') or record.get('text')),
                          'Decision title differs from source')
        transport.require(decision['decision'] in ('Accept', 'Reject', 'Unresolved')
                          and decision['job_market_eligible'] is {'Accept': True, 'Reject': False, 'Unresolved': None}[decision['decision']],
                          'Inconsistent generated decision')
        location = decision['location']
        source = dict(company=capture['employer']) if new_batch else sources[case['source_id']]
        salary = record.get('salaryRange') or {}
        period = {'per-year-salary': 'Annual', 'per-month-salary': 'Monthly'}.get(salary.get('interval'))
        # Explicit provider units only. Unknown or unsupported units stay raw, without conversion.
        mapped = (period is not None and salary.get('currency') in ('SAR', 'USD', 'EUR', 'GBP')
                  and type(salary.get('min')) in (int, float))
        row = dict(id=case['case_id'], title=decision['title'], company=record.get('company_name') or source['company'],
                   country=location['country'], city=record.get('city') or location['display'],
                   region='saudi' if location['country'] == 'Saudi Arabia' else 'global',
                   skills=[], level='Not assessed', experience='Not assessed', relevance='Not assessed',
                   sourceUrl=record.get('absolute_url') or record.get('hostedUrl') or record.get('url') or capture.get('sourceUrl'),
                   sourceId=case['source_id'], sourceLabel=case['source_id'], evidenceDate=capture.get('capturedAtUtc') or capture.get('retrievedAtUtc'),
                   collection='development-preview', listingStatus=capture.get('listingStatus', 'Historical reference'),
                   summary=decision['reason'], notes='Market eligibility is separate from occupational classification and salary eligibility.',
                   salaryMin=salary.get('min') if mapped else None, salaryMax=salary.get('max') if mapped else None,
                   currency=salary.get('currency') if mapped else None, period=period if mapped else None,
                   salaryBasis='unknown', salaryBasisVerified=False, salaryEligible=False,
                   compensation='Salary eligibility not evaluated', marketEligibility=copy.deepcopy(decision),
                   originalStructuredSalary={k: record[k] for k in ('salaryRange', 'salary', 'salary_ranges') if k in record},
                   locationVariants=[copy.deepcopy(v) for v in results['capture_decisions']
                                     if v['case_id'] == case['case_id'] and not v['primary_indexed_capture']
                                     and v['location']['country'] != location['country']])
        records.append(row)
    # Replace the local sample completely; never append Development jobs to production records/statistics.
    return dict(schemaVersion=2, records=records, sources=[], changes=[],
                reviewQueue=[dict(id=r['id'], title=r['title'], company=r['company'], sourceUrl=r['sourceUrl'],
                                  category='Market eligibility', reason=r['marketEligibility']['reason'])
                             for r in records if r['marketEligibility']['decision'] == 'Reject'],
                fx=copy.deepcopy(public['fx']),
                meta=dict(automationActivated=False, staleAfterHours=48, coverage=f'{len(records)} private experimental postings only; not published market statistics.'),
                developmentPreview=dict(kind='market-eligibility', label='Development / Experimental Preview',
                                        policy=results['policy'], resultsPath=results_path.relative_to(root).as_posix(),
                                        resultsSha256=transport.digest(raw), batchKind=results.get('batch_kind', 'original-development'),
                                        shortfalls=results.get('shortfalls', [])))


def build_development_preview(results_path, output, root=ROOT):
    root = Path(root).resolve()
    output = transport.safe_path(root, Path(output).resolve().relative_to(root), Path('learning-local'))
    transport.require(not output.exists(), 'Use a fresh preview directory; no overwrites')
    transport.require(subprocess.run(['git', 'check-ignore', '--quiet', '--', str(output / 'index.html')], cwd=root).returncode == 0,
                      'Preview must be Git-ignored')
    dataset = development_dataset(root, results_path)
    return build_preview(root, output, dataset=dataset)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, required=True, help='Saved Development market-eligibility.json')
    parser.add_argument('--output', type=Path, required=True, help='Fresh Git-ignored learning-local directory')
    parser.add_argument('--serve', action='store_true')
    parser.add_argument('--port', type=int, default=8766)
    args = parser.parse_args()
    output = build_development_preview(args.results, args.output)
    print(f'Development / Experimental Preview: {output / "index.html"}', flush=True)
    if args.serve:
        server = ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(output)))
        print(f'http://127.0.0.1:{server.server_port}/#saudi', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


if __name__ == '__main__':
    main()

"""Explicit local collector -> existing vNext -> pending review -> existing site.

Saved mode consumes an explicit Development response manifest (never the network).
Live mode requires --live and configured source IDs. No production files are written.
State and immutable run evidence must be beneath ignored learning-local/.
"""
import argparse
import base64
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import uuid

import process_experimental_workflow as workflow
from process_experimental_batch import project
from preview_filters import ROOT, build_preview
from observatory_bundle import build_bundle
import refresh

t = workflow.t


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(t.canonical(value))


def collect(state_dir, *, saved=None, source_ids=(), live=False):
    state_dir = t.safe_path(ROOT, Path(state_dir).resolve().relative_to(ROOT), Path('learning-local'))
    t.require(subprocess.run(['git', 'check-ignore', '--quiet', str(state_dir / 'state.json')], cwd=ROOT).returncode == 0,
              'Operational state must be ignored')
    t.require(bool(saved) != bool(live), 'Choose saved responses OR explicitly authorized live collection')
    config = t.loads((ROOT / 'config/sources.json').read_bytes())
    if saved:
        saved = t.safe_path(ROOT, Path(saved).resolve().relative_to(ROOT), Path('learning-local'))
    manifest = t.loads(Path(saved).read_bytes()) if saved else None
    if manifest:
        t.require(manifest.get('scope') == 'Development-only', 'Explicit Development-only manifest required')
        sources = manifest['sources']
    else:
        t.require(source_ids, 'Explicit configured source IDs required for live collection')
        sources = [s for s in config['sources'] if s['id'] in source_ids and s.get('enabled')]
        t.require({s['id'] for s in sources} == set(source_ids), 'Unknown or disabled source')
    t.require(len({s['id'] for s in sources}) == len(sources), 'Duplicate source identity')
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = state_dir / 'run.lock'
    with lock.open('x'):
        pass
    try:
        return _run(state_dir, sources, config, manifest, saved)
    finally:
        lock.unlink()


def _run(state_dir, sources, config, manifest, saved):
    state_path = state_dir / 'state.json'
    state = t.loads(state_path.read_bytes()) if state_path.exists() else dict(candidates={})
    reviews_path = state_dir / 'review-decisions.json'
    reviews_bytes = reviews_path.read_bytes() if reviews_path.exists() else None
    reviews = t.loads(reviews_bytes) if reviews_bytes else {}
    implementation = t.digest(b''.join(Path(module.__file__).read_bytes() for module in
        (workflow, workflow.batch, workflow.batch_transport, workflow.consumer, workflow.graph,
         workflow.classifier, workflow.market, workflow.salary_vnext, workflow.semantic_graph_vnext,
         workflow.validator, workflow.evidence, workflow.operational_market, workflow.representation_actions, t, refresh)))
    run = state_dir / 'runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-' + uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    health, failures, outcomes = [], [], []
    for source in sources:
        responses = []
        def capture(url, body, retrieved):
            sha = t.digest(body)
            path = run / 'responses' / sha
            path.parent.mkdir(exist_ok=True)
            if not path.exists():
                with path.open('xb') as stream: stream.write(body)
            responses.append(dict(url=url, body=body, retrieved=retrieved, path=path))
        def fetch(url, timeout):
            if manifest is None:
                return refresh.fetch_json(url, timeout, capture=capture)
            matches = [r for r in manifest['responses'] if r['url'] == url]
            t.require(len(matches) == 1, 'No unique saved response for ' + url)
            item = matches[0]
            path = t.safe_path(Path(saved).resolve().parent, item['path'], Path('.'))
            body = path.read_bytes()
            t.require(t.digest(body) == item['sha256'], 'Saved response hash mismatch')
            capture(url, body, item['retrieved_at_utc'])
            return t.loads(body)
        try:
            jobs, warnings = refresh.get_board(source, config, fetch=fetch)
            health.append(dict(source, status='Saved response replay' if manifest else 'OK',
                               jobCount=len(jobs), warnings=warnings,
                               retrievedAt=[r['retrieved'] for r in responses]))
        except Exception as error:
            health.append(dict(source, status='Failed; previous candidates retained', error=str(error)))
            continue
        seen, observed_ids = set(), set()
        for raw in jobs:
            job_id = str(raw.get('id') or raw.get('shortcode') or raw.get('code'))
            if source.get('record_ids') is not None and job_id not in source['record_ids']:
                continue
            key = source['id'] + '/' + job_id
            # Workable can publish the same shortcode for distinct countries.
            # Preserve each source geography independently, including missingness.
            if source['type'] == 'workable':
                key += '@' + t.digest(t.canonical(raw.get('country')).encode())[:12]
            observed_ids.add(job_id)
            try:
                record = copy.deepcopy(raw)
                record.pop('_detailsUnavailable', None)  # Collector error marker, not source evidence.
                revision = t.digest(t.canonical(record).encode())
                if key in seen and state['candidates'].get(key, {}).get('revision') == revision:
                    outcomes.append(dict(identity=key, status='Duplicate unchanged', revision=revision))
                    continue
                t.require(key not in seen, 'Conflicting duplicate source identity/geography')
                seen.add(key)
                prior = state['candidates'].get(key)
                if prior and prior['revision'] == revision and prior.get('implementation') == implementation and prior['result']['execution'] == 'PASS':
                    prior.pop('lastProcessingError', None)
                    outcomes.append(dict(identity=key, status='Unchanged', revision=revision))
                    continue
                matches = []
                for response in responses:
                    payload = t.loads(response['body'])
                    values = payload if isinstance(payload, list) else payload.get('jobs', [payload])
                    for index, value in enumerate(values):
                        if value == record:
                            pointer = '/' + str(index) if isinstance(payload, list) else '/jobs/' + str(index) if 'jobs' in payload else ''
                            matches.append((response, pointer))
                merged_transport = False
                if matches:
                    response, pointer = matches[-1]
                else:
                    # Retain exact board and detail bytes; reproduce only the
                    # existing collector's field overwrite semantics, explicitly.
                    t.require(source['type'] == 'greenhouse', 'Merged provider fields lack a single exact source record; multi-response transport required')
                    components = []
                    for response_item in responses:
                        payload = t.loads(response_item['body'])
                        values = payload.get('jobs', [payload]) if isinstance(payload, dict) else []
                        for index, value in enumerate(values):
                            if str(value.get('id')) == job_id:
                                components.append(dict(path=response_item['path'].relative_to(ROOT).as_posix(),
                                    sha256=t.digest(response_item['body']), bytes_base64=base64.b64encode(response_item['body']).decode(),
                                    pointer='/jobs/'+str(index) if 'jobs' in payload else '', url=response_item['url'],
                                    retrieved_at_utc=response_item['retrieved']))
                    t.require(len(components) == 2 and components[0]['pointer'].startswith('/jobs/') and components[1]['pointer'] == '',
                              'Merged provider fields lack a single exact source record or unambiguous board/detail pair')
                    envelope = dict(kind='exact-api-response-envelope-v1', components=components)
                    body = t.canonical(envelope).encode()
                    response = dict(body=body, retrieved=components[-1]['retrieved_at_utc'])
                    pointer, merged_transport = '', True
                folder = run / ('posting-' + t.digest(key.encode())[:16])
                folder.mkdir()
                # Keep each source response beneath its selection for existing strict transport guards.
                body = response['body']
                response_path = folder / 'response.json'
                response_path.write_bytes(body)
                url = record.get('absolute_url') or record.get('hostedUrl') or record.get('url')
                t.require(isinstance(url, str) and url.startswith('https://'), 'Original posting URL missing')
                spec = dict(format=source['type'], source_id=source['id'], source_job_id=job_id,
                            source_url=url, employer=source['company'], pointer=pointer,
                            response_path=response_path.relative_to(ROOT).as_posix(), response_sha256=t.digest(body),
                            retrieved_at_utc=response['retrieved'], listing_status='Not yet verified open',
                            listing_evidence='API response retained; application availability not independently checked.',
                            salary_availability=dict(status='Not assessed by collector', evaluated_for_benchmark=False))
                if merged_transport: spec['transport_components'] = True
                projected, mapping, original = project(spec, body)
                t.require(projected == record, 'Transport projection differs from collected record')
                capture_data = dict(sourceId=source['id'], sourceJobId=job_id, sourceType=source['type'],
                    sourceUrl=url, retrievedAtUtc=response['retrieved'], record=projected, originalRecord=original,
                    fieldMapping=mapping, response=dict(path=spec['response_path'], sha256=spec['response_sha256'], pointer=pointer),
                    employer=source['company'], listingStatus=spec['listing_status'], listingEvidence=spec['listing_evidence'],
                    salaryAvailability=spec['salary_availability'], uncertainties=[])
                case = 'NEW-' + t.digest((source['id']+'\0'+job_id+'\0'+str(projected.get('country'))).encode())[:16]
                capture_path = folder / 'processed/captures' / (case + '.json')
                write(capture_path, capture_data)
                encoded = capture_path.read_bytes()
                artifact = dict(path=capture_path.relative_to(ROOT).as_posix(), sha256=t.digest(encoded), bytes_base64=base64.b64encode(encoded).decode())
                decision = workflow.operational_market.decide(projected, source['type'], artifact)
                decision.update(case_id=case, source_id=source['id'], source_job_id=job_id, primary_indexed_capture=True,
                                listing_status=spec['listing_status'], listing_evidence=spec['listing_evidence'],
                                salary_availability=spec['salary_availability'])
                selection = folder / 'selection.json'
                write(selection, dict(candidates=[spec]))
                report = folder / 'market-eligibility.json'
                write(report, dict(batch_kind='new-employer-candidates', policy=workflow.operational_market.POLICY,
                    capture_decisions=[decision], human_reference=None, selection_path=selection.relative_to(ROOT).as_posix()))
                completed = workflow.run(report, folder / 'workflow', ROOT, build_views=False)
                result, = completed['results']
                dataset = t.loads((folder / 'workflow/preview/data/market.json').read_bytes())
                row, = dataset['records']
                history = copy.deepcopy(prior.get('history', [])) if prior else []
                if prior: history.append(dict(revision=prior['revision'], artifact=prior['artifact']))
                state['candidates'][key] = dict(revision=revision, implementation=implementation, row=row, result=result, history=history,
                                                artifact=str((folder / 'workflow').relative_to(ROOT)))
                outcomes.append(dict(identity=key, revision=revision, status=result['execution']))
            except Exception as error:
                failures.append(dict(identity=key, title=raw.get('title') or raw.get('text'), error_type=type(error).__name__, blocker=str(error)))
                if key in state['candidates']:
                    state['candidates'][key]['lastProcessingError'] = 'Previous evidence retained; latest processing failed: ' + str(error)
        for missing in set(source.get('record_ids', [])) - observed_ids:
            failures.append(dict(identity=source['id']+'/'+missing, title=missing, error_type='MissingSelectedRecord',
                                 blocker='Selected job was absent from this response; no closure or rejection inferred'))
    published = t.loads((ROOT / 'public/data/market.json').read_bytes())
    rows = []
    for key, entry in state['candidates'].items():
        row = copy.deepcopy(entry['row'])
        review = reviews.get(key, {}).get(entry['revision'])
        row['operationalReview'] = dict(identity=key, revision=entry['revision'],
            status='Recorded review; publication not authorized' if review is not None else 'Pending human review',
            decision=review, productionApproval=None, lastProcessingError=entry.get('lastProcessingError'))
        row['operationalReview']['possibleDuplicateIdentities'] = [other for other, candidate in state['candidates'].items()
            if other != key and refresh.canonical(candidate['row']['sourceUrl']) == refresh.canonical(row['sourceUrl'])]
        rows.append(row)
    dataset = dict(schemaVersion=2, records=rows, sources=health, changes=[dict(type=o['status'],
                   title=state['candidates'][o['identity']]['row']['title'],
                   company=state['candidates'][o['identity']]['row']['company'],
                   at=datetime.now(timezone.utc).isoformat()) for o in outcomes],
                   reviewQueue=[dict(id=r['id'], title=r['title'], company=r['company'], sourceUrl=r['sourceUrl'],
                                    category='Human review', reason=r['operationalReview']['status']) for r in rows],
                   processingFailures=failures, fx=published['fx'],
                   collectionRun=dict(performed=manifest is None, mode='Live API collection' if manifest is None else 'Saved API response replay'),
                   meta=dict(automationActivated=False, generatedAtUtc=datetime.now(timezone.utc).isoformat(),
                             coverage='Local review candidates; excluded from published statistics'),
                   developmentPreview=dict(kind='market-eligibility', workflow=True, operational=True, policy=workflow.operational_market.POLICY,
                                           label='Development / Experimental collector preview'))
    build_preview(ROOT, run / 'preview', dataset=dataset, app_source=workflow.workflow_app((ROOT / 'web/app.js').read_text(encoding='utf-8')))
    build_bundle(ROOT, run, dataset)
    write(run / 'run.json', dict(sourceHealth=health, outcomes=outcomes, failures=failures, live=manifest is None,
                               implementationSha256=t.digest(Path(__file__).read_bytes())))
    write(run / 'state.json', state)
    t.require((reviews_path.read_bytes() if reviews_path.exists() else None) == reviews_bytes,
              'Review decisions changed during run; retry')
    # The only replacement is a local index. Every capture, revision and run remains immutable.
    temporary = state_dir / ('state-' + uuid.uuid4().hex + '.tmp')
    write(temporary, state)
    temporary.replace(state_path)
    return run


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--saved-responses', type=Path)
    mode.add_argument('--live', action='store_true')
    parser.add_argument('--source', action='append', default=[])
    args = parser.parse_args()
    output = collect(args.state, saved=args.saved_responses, source_ids=args.source, live=args.live)
    summary = t.loads((output / 'run.json').read_bytes())
    if summary['failures'] or any(s.get('error') for s in summary['sourceHealth']):
        import sys
        print('Collection/processing limitations retained in run.json and preview; previous evidence preserved.', file=sys.stderr)
    print(output / 'preview/index.html')

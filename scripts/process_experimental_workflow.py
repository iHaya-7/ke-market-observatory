"""Offline Development batch -> verified RDF -> separate decisions -> existing preview.

Only saved new-employer-candidates reports are accepted. Source-root may point to
the private fixture checkout; code always comes from this checkout. Outputs must
be fresh and ignored. Neither production nor historical results are written.
"""
import argparse
from pathlib import Path
import subprocess
from datetime import datetime, timezone

from preview_market_eligibility import development_dataset, transport as t
from preview_filters import ROOT, build_preview
from batch_transport_vnext import make_batch_packet
import consumer_vnext as consumer
import graph_vnext as graph
import validate_graph_vnext as validator
import review_export_vnext as evidence
import classify_jobs_vnext as classifier
import market_eligibility_vnext as market
import batch_transport_vnext as batch_transport
import process_experimental_batch as batch
import refresh
import salary_vnext
import semantic_graph_vnext


def workflow_app(source):
    """Bind generated assessments in the existing LOCAL preview detail panel.

    Production assets and the historical preview remain byte-for-byte untouched.
    Fail closed when the existing template changes instead of silently mislabeling.
    """
    replacements = {
        "'Not assessed. The saved market eligibility decision is a separate dimension.'":
        "esc(workflowLabel(r.occupationalAssessment?.proposed_classification||'Not assessed'))+' — '+esc(wf('Experimental machine proposal; separate from market eligibility.','مقترح آلي تجريبي؛ مستقل عن أهلية السوق.'))",
        'Occupational classification: not assessed in this preview. Salary eligibility: not evaluated. Job eligibility does not establish either.':
        "${workflowEvidence(r)}",
        'Accepted international job postings · missing salary does not remove an eligible job. Salary eligibility has not been evaluated; none enter published benchmarks.':
        'Accepted international postings; salary evidence is assessed separately. This is a local Development sample, not published market statistics.',
        'Salary eligibility not evaluated': 'Salary evidence: see assessment',
        "'Salary eligibility','—','Not evaluated'": "'Comparable salary observations',num(market.records.flatMap(r=>r.salaryAssessment?.observations||[]).filter(o=>o.comparable).length),'Development only'",
    }
    for old, new in replacements.items():
        t.require(source.count(old) == 1, 'Preview template binding changed')
        source = source.replace(old, new)
    source = source.replace('r.marketEligibility.listing_status||r.listingStatus', 'r.listingStatus')
    source = source.replace("esc(r.marketEligibility.salary_availability?.status||'Salary availability not assessed')", "esc(r.salaryAssessment?.status||'Salary not assessed')")
    source = source.replace('<p>${esc(originalPay(r))} · ${esc(t(r.compensation))}</p>',
                            '<p dir="auto">${esc(originalPay(r))} · ${esc(t(r.compensation))}</p>')
    # Install local bindings before the first render, including direct #global
    # navigation. Appending them after bootstrap leaves a stale initial view.
    bootstrap = "validate(market);mount(location.hash.slice(1)||'overview');refresh();"
    t.require(source.count(bootstrap) == 1, 'Preview bootstrap binding changed')
    bindings = (ROOT / 'web/workflow-preview.js').read_text(encoding='utf-8')
    return source.replace(bootstrap, bindings + '\n' + bootstrap)


def run(results_path, output, source_root=ROOT):
    source_root = Path(source_root).resolve()
    results_path = t.safe_path(source_root, Path(results_path).resolve().relative_to(source_root), Path('learning-local'))
    results = t.loads(results_path.read_bytes())
    t.require(results.get('batch_kind') == 'new-employer-candidates', 'Only explicitly selected Development batch inputs supported')
    output = t.safe_path(ROOT, Path(output).resolve().relative_to(ROOT), Path('learning-local'))
    t.require(not output.exists(), 'Fresh output required; historical results are never overwritten')
    t.require(subprocess.run(['git', 'check-ignore', '--quiet', '--', str(output / 'results.json')], cwd=ROOT).returncode == 0, 'Output must be ignored')
    selection_path = t.safe_path(source_root, results['selection_path'], Path('learning-local'))
    selection = t.loads(selection_path.read_bytes())
    concepts = classifier.vocabulary()
    output.mkdir(parents=True)
    outcomes = []
    dataset = None
    records, failures = [], []
    seen = set()
    for saved in results['capture_decisions']:
        if not saved.get('primary_indexed_capture'):
            continue
        case_id = saved.get('case_id')
        t.require(isinstance(case_id, str) and case_id.startswith('NEW-') and case_id.replace('-', '').isalnum(), 'Invalid batch identity')
        t.require(case_id not in seen, 'Duplicate primary identity')
        seen.add(case_id)
        folder = output / case_id
        folder.mkdir()
        try:
            one = development_dataset(source_root, results_path, only_case=case_id)
            row, = one['records']
            if dataset is None:
                dataset = one
            result = process_case(saved, row, source_root, selection_path, selection, concepts, folder, one['fx'])
            records.append(row)
        except Exception as error:
            result = dict(case_id=case_id, title=saved.get('title', 'Unknown posting'), execution='BLOCKED',
                          blocker=str(error), error_type=type(error).__name__, occupational_assessment=None,
                          market_eligibility=None, salary_assessment=None, production_approval=None)
            failures.append(result)
        (folder / 'result.json').write_text(t.canonical(result), encoding='utf-8')
        outcomes.append(result)
    if dataset is None:
        dataset = dict(schemaVersion=2, records=[], sources=[], changes=[], reviewQueue=[],
                       fx=t.loads((source_root / 'public/data/market.json').read_bytes())['fx'],
                       meta=dict(automationActivated=False), developmentPreview=dict(kind='market-eligibility',
                       label='Development / Experimental Preview', policy=results['policy']))
    dataset['records'] = records
    dataset['reviewQueue'] = [dict(id=r['id'], title=r['title'], company=r['company'], sourceUrl=r['sourceUrl'],
                                   category='Market eligibility', reason=r['marketEligibility']['reason'])
                              for r in records if r['marketEligibility']['decision'] != 'Accept']
    dataset['processingFailures'] = failures
    dataset['developmentPreview']['workflow'] = True
    dataset['meta']['generatedAtUtc'] = datetime.now(timezone.utc).isoformat()
    dataset['meta']['coverage'] = f'{len(records)} processed Development postings; {len(failures)} isolated failures; no published statistics.'
    report = dict(scope='Development / Experimental only', results=outcomes,
                  input_results_sha256=t.digest(results_path.read_bytes()),
                  implementation_sha256={str(p.relative_to(ROOT)):t.digest(p.read_bytes()) for p in
                      [Path(__file__), Path(market.__file__), Path(classifier.__file__), Path(consumer.__file__),
                       Path(graph.__file__), Path(t.__file__), Path(batch_transport.__file__), Path(batch.__file__),
                       Path(validator.__file__), Path(evidence.__file__), Path(refresh.__file__),
                       Path(salary_vnext.__file__), Path(semantic_graph_vnext.__file__), ROOT / 'web/app.js', ROOT / 'web/workflow-preview.js']},
                  human_judgments=None, evaluation_metrics=None)
    (output / 'results.json').write_text(t.canonical(report), encoding='utf-8')
    build_preview(ROOT, output / 'preview', dataset=dataset,
                  app_source=workflow_app((ROOT / 'web/app.js').read_text(encoding='utf-8')))
    return report


def process_case(saved, row, source_root, selection_path, selection, concepts, folder, fx):
        path = t.safe_path(source_root, saved['source_capture'], selection_path.parent / 'processed/captures')
        raw = path.read_bytes()
        capture = t.loads(raw)
        spec, = [s for s in selection['candidates'] if s['source_id'] == capture['sourceId'] and str(s['source_job_id']) == capture['sourceJobId']]
        response = t.safe_path(source_root, spec['response_path'], selection_path.parent).read_bytes()
        packet = make_batch_packet(row['id'], saved['source_capture'], raw, spec, response)
        artifact = packet['captures'][0]
        decision = market.decide(capture['record'], capture['sourceType'], artifact)
        # Existing market outputs must reproduce, not merely be carried forward.
        t.require(all(saved[k] == v for k, v in decision.items()), 'Market decision regression')
        result = dict(case_id=row['id'], title=row['title'], market_eligibility=decision,
                      production_approval=None, source_capture=artifact['path'], capture_sha256=artifact['sha256'],
                      source_response=dict(path=spec['response_path'], sha256=spec['response_sha256']),
                      field_mapping=capture['fieldMapping'], graph_field_references=packet['field_references'],
                      unconsumed_source_sections=packet['unconsumed_source_sections'])
        (folder / 'packet.json').write_text(t.canonical(packet), encoding='utf-8')
        try:
            consumed = consumer.consume(packet)
            rdf = graph.build_graph(packet, consumed)
            validation = validator.validate_graph(rdf, packet, consumed)
            rows = evidence.query_rows(rdf, packet, reader=lambda a: t.safe_path(
                source_root, a['path'], selection_path.parent / 'processed/captures').read_bytes())
            occupation = classifier.classify_job(rows, concepts, case_id=row['id'], source_title=row['title'])
            if rows:
                classifier.validate_decisions([occupation], rows, concepts)
            semantic = semantic_graph_vnext.build(rdf, occupation)
            semantic.serialize(destination=folder / 'semantic-assertions.ttl', format='turtle')
            semantic_validation = semantic_graph_vnext.validate(
                graph.Graph().parse(folder / 'semantic-assertions.ttl'), rdf, occupation)
            rdf.serialize(destination=folder / 'graph.ttl', format='turtle')
            reloaded = graph.Graph().parse(folder / 'graph.ttl')
            validator.validate_graph(reloaded, packet, consumed)
            (folder / 'consumer.json').write_text(t.canonical(consumed), encoding='utf-8')
            result.update(execution='PASS', validation=validation, semantic_validation=semantic_validation,
                          occupational_assessment=occupation)
        except t.TransportError as error:
            # A missing body is not evidence for a negative occupational decision.
            if str(error) != 'No nonempty body fields':
                raise
            consumed = dict(documents=[])
            occupation = classifier.classify_job([], concepts, case_id=row['id'], source_title=row['title'])
            result.update(execution='BLOCKED', blocker=str(error), occupational_assessment=occupation)
        salary = salary_vnext.assess(packet, consumed, decision, fx)
        result['salary_assessment'] = dict(salary, source_capture=artifact['path'], capture_sha256=artifact['sha256'],
                                          input_field_pointers=['/record/' + t.escape(k) for k in capture['record']],
                                          observation_applicability=None)
        row.update({key: salary[key] for key in ('salaryMin', 'salaryMax', 'currency', 'period', 'salaryEligible',
                    'salaryBasis', 'salaryBasisVerified', 'compensation', 'salaryReview')})
        row['occupationalAssessment'] = occupation
        row['salaryAssessment'] = result['salary_assessment']
        row['workflowValidation'] = result.get('validation', dict(blocker=result.get('blocker')))
        row['sourceListingStatus'] = row['listingStatus']
        row['listingStatus'] = 'Not yet verified open'
        # Existing preview already displays SAR/month only for supported units and FX.
        row['notes'] += ' Experimental machine proposals only; no production approval. Unsupported salary dimensions remain unresolved.'
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.results, args.output, args.source_root)
    for result in report['results']:
        print(result['execution'], result['title'], '|', (result['market_eligibility'] or {}).get('decision'), '|',
              (result['occupational_assessment'] or {}).get('proposed_classification'), '|',
              (result['salary_assessment'] or {}).get('compensation', result.get('blocker')))

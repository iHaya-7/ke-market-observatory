"""Bridge saved, authenticated Development batch captures to the existing graph.

The original response and projection specification travel with the packet. Graph
locators address the unchanged capture; its fieldMapping resolves the second hop
to the original response. No synthetic corpus path or source field is introduced.
"""
import base64
import copy
from pathlib import Path, PurePosixPath
import sys

import transport_vnext as t

sys.path.insert(0, str(t.ROOT / 'scripts'))
from process_experimental_batch import project

VERSION = 'development-batch-transport-vnext-1'


def make_batch_packet(case_id, capture_path, capture_bytes, spec, response_bytes):
    t.require(case_id.startswith('NEW-') and case_id.replace('-', '').isalnum(), 'Expected batch case identity')
    for path in (capture_path, spec['response_path']):
        parts = PurePosixPath(path).parts
        t.require(parts and parts[0] == 'learning-local' and '..' not in parts
                  and ':' not in path and '\\' not in path, 'Expected local Development path')
    t.require(t.digest(response_bytes) == spec['response_sha256'], 'Response hash mismatch')
    capture = t.loads(capture_bytes)
    record, mapping, original = project(spec, response_bytes)
    t.require(capture['record'] == record and capture['fieldMapping'] == mapping
              and capture['originalRecord'] == original, 'Projection differs from original response')
    t.require(capture['sourceId'] == spec['source_id']
              and capture['sourceJobId'] == str(spec['source_job_id'])
              and capture['sourceType'] == spec['format']
              and capture['sourceUrl'] == spec['source_url']
              and capture['retrievedAtUtc'] == spec['retrieved_at_utc']
              and capture['response'] == dict(path=spec['response_path'], sha256=spec['response_sha256'], pointer=spec.get('pointer')),
              'Capture identity/provenance mismatch')
    expected = 'NEW-' + t.digest((spec['source_id'] + '\0' + str(spec['source_job_id']) + '\0' + str(record.get('country'))).encode())[:16]
    t.require(case_id == expected, 'Batch case identity mismatch')
    references = {k: '/record/' + t.escape(k) for k in record}
    unused_sections = []
    if spec['format'] == 'smartrecruiters':
        # Value-preserving aliases only. Captures and the historical projection
        # stay unchanged; the graph resolves directly into originalRecord.
        sections = original.get('jobAd', {}).get('sections', {})
        for field, section in (('description', 'jobDescription'), ('full_description', 'additionalInformation')):
            value = sections.get(section, {}).get('text')
            if isinstance(value, str) and value.strip():
                t.require(field not in record, 'Ambiguous body alias')
                record[field] = value
                references[field] = '/originalRecord/jobAd/sections/' + section + '/text'
        unused_sections = [k for k in sections if k not in ('jobDescription', 'additionalInformation')]
    sha = t.digest(capture_bytes)
    packet = dict(version=VERSION, case_id=case_id,
                  source=dict(id=spec['source_id'], type=spec['format']),
                  record=copy.deepcopy(record), field_owners={k: sha for k in record},
                  field_references=references, unconsumed_source_sections=unused_sections,
                  captures=[dict(path=capture_path, sha256=sha, bytes_base64=base64.b64encode(capture_bytes).decode())],
                  primary_capture_sha256=sha,
                  identity=dict(source_id=spec['source_id'], source_type=spec['format'],
                                source_job_id=str(spec['source_job_id']), source_url=spec['source_url']),
                  batch_spec=copy.deepcopy(spec), response_bytes_base64=base64.b64encode(response_bytes).decode())
    title_key = 'text' if spec['format'] == 'lever' else 'title'
    t.require(isinstance(record.get(title_key), str) and record[title_key].strip(), 'Missing title')
    packet['title_metadata'] = dict(value=record[title_key], reference=t.reference(packet, '/' + title_key))
    return packet


def verify_batch_packet(packet):
    t.require(len(packet['captures']) == 1, 'One saved batch capture required')
    artifact = packet['captures'][0]
    rebuilt = make_batch_packet(packet['case_id'], artifact['path'],
                                base64.b64decode(artifact['bytes_base64'], validate=True),
                                packet['batch_spec'], base64.b64decode(packet['response_bytes_base64'], validate=True))
    t.require(t.canonical(rebuilt) == t.canonical(packet), 'Batch packet/provenance tampering')
    return packet

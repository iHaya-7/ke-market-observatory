"""Local shared-data export; publication and experimental decisions stay separate."""
import hashlib
import json
from pathlib import Path

from preview_filters import build_preview


def build_bundle(root, output, experimental):
    root, output = Path(root), Path(output)
    published_path = root / 'public/data/market.json'
    published_bytes = published_path.read_bytes()
    published = json.loads(published_bytes)
    decisions_path = root / 'data/review_decisions.json'
    decisions_bytes = decisions_path.read_bytes() if decisions_path.exists() else None
    decisions = json.loads(decisions_bytes) if decisions_bytes is not None else None
    ids = [r['id'] for r in experimental['records']]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate experimental identities')
    # Existing production decisions are retained verbatim, never interpreted as
    # authorization to publish a new experimental assessment of a similar job.
    bundle = dict(schemaVersion=1, published=published, experimental=experimental,
                  reviewDecisions=decisions,
                  publicationGate='Experimental records are not approved for publication',
                  collection=dict(performed=False, mode='Saved Development evidence'),
                  provenance=dict(publishedPath='public/data/market.json',
                                  publishedSha256=hashlib.sha256(published_bytes).hexdigest(),
                                  reviewDecisionsSha256=hashlib.sha256(decisions_bytes).hexdigest()
                                  if decisions_bytes is not None else None))
    data = output / 'preview/data'
    data.mkdir(parents=True, exist_ok=True)
    (data / 'observatory.json').write_text(json.dumps(bundle, ensure_ascii=True), encoding='utf-8')
    (data / 'published.json').write_bytes(published_bytes)
    if decisions_bytes is not None:
        (data / 'review-decisions.json').write_bytes(decisions_bytes)
    build_preview(root, output / 'preview/published', dataset=published)
    for page, href, label in (
        (output / 'preview/index.html', 'published/index.html', 'Published records / السجلات المنشورة'),
        (output / 'preview/published/index.html', '../index.html', 'Experimental candidates / المرشحون التجريبيون'),
    ):
        html = page.read_text(encoding='utf-8')
        marker = '<body>'
        if html.count(marker) != 1:
            raise ValueError('Existing site body binding changed')
        notice = (f'<nav class="notice" aria-label="Dataset"><a href="{href}">{label}</a>'
                  f' · Published: {len(published["records"])} · Experimental: {len(ids)}'
                  ' · Local snapshot; no live collection / نسخة محلية دون جمع مباشر'
                  ' · Separate statistics; experimental publication approval pending.</nav>')
        page.write_text(html.replace(marker, marker + notice, 1), encoding='utf-8')
    # Fail closed if another process changes the source while the bundle builds.
    if published_path.read_bytes() != published_bytes:
        raise ValueError('Published dataset changed during local export; rerun into a fresh directory')
    if decisions_bytes is not None and decisions_path.read_bytes() != decisions_bytes:
        raise ValueError('Review decisions changed during export; rerun into a fresh directory')
    return bundle

"""Portable setup for private Development replay; never discovers corpus cases."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
if not __debug__:
    raise RuntimeError('Do not use -O: replay relies on assertions as fidelity gates.')
ROOT = Path(__file__).resolve().parents[2]
BASELINE = 'ee5bd15ff52b6a88e15a2dafab6886422980f557'
CORPUS = ROOT / 'knowledge-engineering/00-baseline/local-corpus/20261021T125408Z-ebb0b062'
parser = argparse.ArgumentParser(description='Private Development-only replay. No labels, scores, or Held-out discovery.')
parser.add_argument('--freeze', type=Path, required=True, help='Authentic local freeze-manifest.json')
parser.add_argument('--work-dir', type=Path, required=True, help='NEW directory beneath ignored learning-local')
parser.add_argument('--remaining-dir', type=Path, required=True, help='Existing Development-only remaining-seven-v1 directory')
parser.add_argument('--deps', type=Path, default=ROOT / 'learning-local/stage6-deps')
args = parser.parse_args()
FREEZE = args.freeze.resolve()
OUT = args.work_dir.resolve()
REMAINING = args.remaining_dir.resolve()
DEPS = args.deps.resolve()
assert OUT.is_relative_to((ROOT / 'learning-local').resolve()) and OUT != (ROOT / 'learning-local').resolve()
assert not OUT.exists(), 'Use a fresh work directory; never overwrite prior evidence.'
assert REMAINING.is_relative_to((ROOT / 'knowledge-engineering/00-baseline/local-corpus/development').resolve())
subprocess.run(['git', 'check-ignore', '--quiet', str(OUT / 'probe.json')], cwd=ROOT, check=True)
seen = {}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(path):
    data = path.read_bytes()
    seen[path] = sha(data)
    return data

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value

freeze = json.loads(read(FREEZE))
runtime = OUT / 'isolated-runtime'
# Only tracked source/configuration files may be restored. In particular, never
# follow a manifest entry into data, snapshots, local-corpus or review materials.
tracked = set(subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines())
payloads = {}
for name, expected in freeze['frozen_files'].items():
    rel = Path(name)
    assert not rel.is_absolute() and '..' not in rel.parts and name in tracked
    assert not set(rel.parts).intersection({'data', 'local-corpus', 'snapshots', '.git'})
    assert name.startswith(('knowledge-engineering/', 'scripts/', 'tests/', 'web/', '.github/workflows/')) or name == 'config/sources.json'
    data = read(ROOT / rel)
    lf = data.replace(b'\r\n', b'\n')
    exact = next((b for b in (data, lf, lf.replace(b'\n', b'\r\n')) if sha(b) == expected['sha256']), None)
    assert exact is not None, 'Substantive freeze mismatch: ' + name
    payloads[name] = exact
for name, data in payloads.items():
    dest = runtime / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
BEFORE_PATH = OUT / 'before-refresh.py'
BEFORE_PATH.write_bytes(subprocess.check_output(['git', 'show', BASELINE + ':scripts/refresh.py'], cwd=ROOT))
fx = {'rates': {'SAR': 1, 'USD': 3.75, 'GBP': 5.005005, 'EUR': 4.205639},
      'date': '2026-10-20', 'source': 'EVALUATION_PROTOCOL.md section 5 fixed rates; harness configuration'}
config = runtime / 'data/curated.json'
config.parent.mkdir(parents=True, exist_ok=True)
config.write_text(json.dumps({'fx': fx}), encoding='utf-8')

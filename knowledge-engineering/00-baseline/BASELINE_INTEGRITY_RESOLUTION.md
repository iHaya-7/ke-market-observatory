# Stage 0 — Baseline integrity resolution

Verified 21 October 2026 (Asia/Riyadh). Approved snapshot: `20261021T110236218Z-ec7c36e4`. This resolves the reproducible-verification issue in [CORPUS_READINESS_REVIEW.md](CORPUS_READINESS_REVIEW.md); it does not approve labeling or resolve the other readiness decisions.

## Finding and verification boundary

**The mismatch is entirely explained by Git line-ending conversion. An isolated reconstruction reproduces every sealed byte hash and passes the original, unmodified verifier.** The approved working-tree directory remains unchanged and still fails direct verification. Passing verification of the reconstructed artifact must not be reported as a direct pass for that directory.

The approved artifact has mixed line endings: four captured JSON datasets were sealed as CRLF bytes; four generated metadata/verifier files and `SHA256SUMS` were LF. The manifest records `core.autocrlf=true` at capture. Current Git configuration also reports `true` from the system Git configuration. `git ls-files --eol` reports `i/lf w/crlf` for all nine snapshot files. Every checked-out file equals its committed LF blob with LF expanded to CRLF; there are no other byte differences.

The verifier splits seal lines on LF and expects a hash/path line without a terminal CR. The CRLF seal triggers `invalid SHA256SUMS line`. Merely fixing that parser would expose four genuine byte-hash mismatches and would also change the sealed verifier. Neither the verifier nor any snapshot file was edited.

| Artifact | Current checkout against seal | Committed snapshot blob against seal | Required reconstructed bytes |
| --- | --- | --- | --- |
| `BASELINE_RESULTS.md`, `MANIFEST.md`, `manifest.json`, `verify.cjs` | Fail: CRLF instead of sealed LF | Exact match, all four | Unmodified LF blobs |
| Four frozen JSON datasets | Exact match, all four | LF blobs differ from sealed CRLF | Controlled LF-to-CRLF expansion, accepted only after hash/size verification |
| `SHA256SUMS` | Differs from separately recorded digest | Exact match to recorded digest | Unmodified LF blob |

The seal's expected SHA-256, recorded outside the snapshot in `corpus-inventory.json`, is:

`6470fbb886bae2b4885e61d265f658209ad68130a2f88baaaa630325872810c1`

Current working-tree seal SHA-256:

`efb3f04022e51959fa4ca49c562ceb9a27b1253ed7258e311ff143458b527a86`

Both the committed seal and an in-memory CRLF-to-LF conversion of the working seal reproduce the expected digest. The sealed metadata contains the original baseline implementation HEAD and its Git object identities. The snapshot itself was committed later; these are distinct provenance references:

- Baseline implementation/capture HEAD: `ee5bd15ff52b6a88e15a2dafab6886422980f557`.
- Pinned commit containing the snapshot used for this reconstruction: `945e49899e112fae45cd1bf925db0c0862f7afd6`.

All 34 recorded capture-time Git blobs were checked against both their recorded Git object IDs and SHA-256 values. For 33, the recorded working-file hash and length can also be reproduced from the blob, using the recorded LF-to-CRLF expansion where necessary. The exception is the root `README.md`, discussed below. This is verification of historical identities, not a claim that today's repository is at the capture HEAD.

## Frozen data verification

All four existing snapshot files match `SHA256SUMS`, both manifest hash fields, and recorded lengths **without transformation**. Their reconstructed bytes also equal these current snapshot bytes. Each reconstructed dataset was additionally matched to its corresponding source blob at the baseline implementation HEAD using the manifest's working-byte identity.

| Frozen path | Bytes | Approved SHA-256 |
| --- | ---: | --- |
| `data/curated.json` | 56944 | `2fd14e04420fe94d62ce2952b0a3e04662709b27bd23d9134f2a2e7424884b46` |
| `data/auto_records.json` | 45113 | `6171360dee49f034efc0e60caa7ad136801d4ba89a35e1ae6243c77de1703795` |
| `data/review_decisions.json` | 43 | `f425ac6675a1a1850c0f066971a97aadb3913670356b11860e85ce7e02cbd47d` |
| `public/data/market.json` | 92238 | `17fa523c0e13341ca499750da7cac4958454ac4e1bf93a403cf6a6dc26ae27e0` |

## Recommended reproducible procedure

Use a new temporary directory reconstructed from binary Git output at the pinned commit. Do not rely on checkout settings, PowerShell text redirection, or universal newline normalization. An all-LF checkout alone does **not** reproduce the four sealed CRLF datasets. The procedure below uses only installed Python 3, Node.js, and Git; no dependencies, network, checkout, repository configuration changes, or production execution are needed.

Run this complete PowerShell block from the repository root. It preserves the originals, prints the isolated directory, verifies provenance before executing the recovered verifier, and stops on any unexpected hash. The isolated directory is retained for inspection. No current working-file content is used to manufacture the reconstructed artifact.

```powershell
@'
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile

root = Path.cwd()
snapshot = 'knowledge-engineering/00-baseline/snapshots/20261021T110236218Z-ec7c36e4'
artifact_commit = '945e49899e112fae45cd1bf925db0c0862f7afd6'
baseline_head = 'ee5bd15ff52b6a88e15a2dafab6886422980f557'
seal_hash = '6470fbb886bae2b4885e61d265f658209ad68130a2f88baaaa630325872810c1'

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=root)

def blob(commit, path):
    return git('cat-file', 'blob', commit + ':' + path)

def sealed_bytes(data, expected, name):
    if sha(data) == expected:
        return data, 'exact Git blob'
    # Only the documented checkout transformation is permitted.
    require(b'\r' not in data, name + ': unexpected CR in source blob')
    expanded = data.replace(b'\n', b'\r\n')
    require(sha(expanded) == expected, name + ': unresolvable sealed hash')
    return expanded, 'LF-to-CRLF reconstruction'

seal = blob(artifact_commit, snapshot + '/SHA256SUMS')
require(sha(seal) == seal_hash, 'Pinned seal differs from approved digest')
entries = {}
for line in seal.decode('ascii').splitlines():
    expected, name = line.split('  ', 1)
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts
            and '\\' not in name and ':' not in name, 'Unsafe seal path')
    require(name not in entries, 'Duplicate seal entry')
    entries[name] = expected
require(len(entries) == 8, 'Unexpected sealed inventory')

payloads = {'SHA256SUMS': seal}
modes = {}
for name, expected in entries.items():
    payloads[name], modes[name] = sealed_bytes(
        blob(artifact_commit, snapshot + '/' + name), expected, name)

manifest = json.loads(payloads['manifest.json'])
require(manifest['git']['head'] == baseline_head, 'Unexpected baseline HEAD')
require(manifest['snapshotId'] == snapshot.rsplit('/', 1)[1], 'Wrong snapshot')
historical = {}
unreconstructed = []
for item in manifest['trackedFilesAtCapture']:
    name = item['path']
    data = blob(baseline_head, name)
    oid = git('rev-parse', baseline_head + ':' + name).decode().strip()
    require(oid == item['headBlobObjectId'], name + ': Git object ID mismatch')
    require(sha(data) == item['headBlobSha256'], name + ': Git blob hash mismatch')
    if item['headToWorkingBytes'] == 'other; see Git status and checksums':
        unreconstructed.append(name)
        continue
    restored, mode = sealed_bytes(data, item['sha256'], name)
    if mode != 'exact Git blob':
        require(item['headToWorkingBytes'] == 'LF-to-CRLF checkout expansion',
                name + ': transformation not recorded')
    require(len(restored) == item['bytes'], name + ': historical length mismatch')
    historical[name] = restored

for item in manifest['dataFiles']:
    name = item['snapshotPath']
    data = payloads[name]
    require(sha(data) == item['originalSha256'] == item['copySha256'],
            name + ': data hash mismatch')
    require(len(data) == item['bytes'], name + ': data length mismatch')
    require(data == historical[item['sourcePath']], name + ': baseline source mismatch')
    current = (root / snapshot / name).read_bytes()
    print(name + ': current snapshot byte-identical = ' + str(current == data))
    # The approved Windows checkout under review must match directly.
    # On an all-LF checkout this check can be false; reconstruction still
    # remains independently hash-verified. Do not claim a direct disk pass.

for name, data in payloads.items():
    current = (root / snapshot / name).read_bytes()
    committed = blob(artifact_commit, snapshot + '/' + name)
    require(current == committed or current == committed.replace(b'\n', b'\r\n'),
            name + ': current checkout has non-line-ending differences')

destination = Path(tempfile.mkdtemp(prefix='ke-approved-baseline-'))
for name, data in payloads.items():
    target = destination / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as output:
        output.write(data)
    require(target.read_bytes() == data, name + ': output write mismatch')

print('Verified historical Git identities:', len(manifest['trackedFilesAtCapture']))
print('Reproduced historical working-file identities:', len(historical))
print('Historical working files not reconstructed:', unreconstructed)
print('Reconstruction modes:', json.dumps(modes, sort_keys=True))
print('Isolated artifact:', destination, flush=True)
subprocess.run(['node', str(destination / 'verify.cjs')], cwd=root, check=True)
'@ | python -B -
if ($LASTEXITCODE -ne 0) { throw 'Baseline verification failed; inspect the error.' }
```

Expected result: all four current dataset comparisons are `True` on the checkout reviewed here; 34 historical Git identities verify and 33 historical working-file identities reproduce, with `README.md` explicitly listed as not reconstructed. Four snapshot files use exact blobs and four datasets use controlled CRLF reconstruction. The original verifier then reports `status: PASS`, `copiedDataFilesVerified: 4`, `sealedFilesVerified: 8`, `descriptiveResultsReproduced: true`, and the approved seal digest.

The procedure intentionally omits `--repository .`: that option requires the current repository HEAD to equal the historical capture HEAD and all capture-time working files to match. The repository has advanced. Historical blob checks above verify those recorded identities without changing HEAD or claiming a present-day production comparison. The reconstructed verifier independently rechecks its complete nine-file inventory, data, embedded evaluation fragments, and descriptive results.

On another checkout, a `False` current-dataset comparison means the on-disk copy is not byte-identical, even if reconstruction passes. Non-line-ending differences abort. Missing historical Git objects also abort; do not substitute newer files or regenerate a baseline. Obtain the original trusted bundle or required history through an explicitly authorized transfer if needed.

## Test outcome, remaining limits, and preservation

The exact documented block was tested locally with Python, Git, and Node.js v24.14.1. All 34 historical Git identities and four direct dataset comparisons passed; 33 historical working-file identities reproduced. The isolated artifact passed the unchanged verifier, including all eight sealed files, all four frozen datasets, descriptive results, and expected seal digest. This establishes a content-identical reconstruction against the approved hashes, not recovery of filesystem timestamps or proof of original capture circumstances.

No discrepancy remains unresolved for the sealed snapshot's nine files. A separate historical working-tree limitation remains: the capture manifest explicitly classifies root `README.md` as `other; see Git status and checksums`. Its recorded working hash is `55b43bffbf2f5f9613100d2961c2cacbea7c12d7bd396e68ea217fbbcc84085e` (15,543 bytes), whereas its verified baseline Git blob SHA-256 is `c0eec8403cf115feab08af87268852af97408e316ddad5ee31f2398861340e11`. Neither exact blob bytes nor LF-to-CRLF expansion reproduces the recorded working hash. Today's README also differs (15,758 bytes; SHA-256 `5ff3da3af9fa48e6d8a185cb0ec088599d1a884240b4a711e05c945abccfc795`). The README is not one of the sealed snapshot files or implementation files, so this does not prevent artifact verification. Do not claim full historical working-tree reconstruction; establishing that README's original bytes would require a matching preserved copy. The manifest's clean Git status does not establish its byte identity.

The snapshot integrity blocker is resolved for the isolated procedure; direct verification of the untouched CRLF checkout remains expected to fail. Trust rests on the previously recorded seal digest and pinned repository history. These are not a signed external attestation, and hashes do not establish source truth.

Before/after fingerprints of all 613 pre-existing tracked/baseline files found no changes or missing files, including the approved snapshot, additional untracked snapshot, corpus evidence, readiness report, and production files. Only this resolution document was added to the repository working tree. Temporary reconstruction artifacts were written outside the repository. No baseline regeneration, refresh, deployment, labels, commit, or push occurred.

Stop after verification and documentation. The other corpus-readiness approvals remain outstanding.

# Development-only replay handoff

This portable wrapper reproduces the local Stage 7 Development compatibility
diagnostic. It does not score accuracy, collect approvals, use human judgments,
or authorize Held-out access. Frozen classifiers, extraction, salary logic,
ontology, taxonomy, SHACL and protocol are not edited.

Only these scripts and this README belong in Git. All job records, manifests,
review files, generated archives, graphs and individual results stay private.
Do not force-add anything from `learning-local` or `local-corpus`.

## Local prerequisites

Haya must supply the authentic artifacts in her own workspace; this commit does
not contain or reconstruct missing source records:

- The matching After `freeze-manifest.json`. Pass its location explicitly.
  Local source bytes must match its hashes exactly or after line-ending-only
  restoration into a new isolated runtime. A mismatch stops execution.
- Git object `ee5bd15ff52b6a88e15a2dafab6886422980f557`, containing the original
  Before `scripts/refresh.py` and `config/sources.json`.
- The existing Development-only package under
  `knowledge-engineering/00-baseline/local-corpus/development/stage7b/v1`:
  `development-case-index.json` and `salary-band-scope.csv`.
- The existing seven-case Development directory, supplied with `--remaining-dir`:
  `source-inventory-v1.json` and `review-v1.csv`. Only case IDs and split values
  are used from the CSV; judgments are never used. It must be inside the private
  `local-corpus/development` tree. Do not supply a mixed-split inventory.
- Original case-specific captures named by those indexes, plus their existing
  `selected/<case_id>/replay-input.json`, under the original local corpus
  `20261021T125408Z-ebb0b062`. Hashes, source IDs and primary/detail equality are
  checked. Shared raw responses and mixed-split corpus manifests are not opened.
- Local dependencies matching the freeze's package versions; pass `--deps` or
  use `learning-local/stage6-deps`. The existing frozen
  `knowledge-engineering/06-validation/requirements-local.txt` lists pins.
  This wrapper does not install dependencies or contact external services.

Use the same Python version as the freeze when reproducing the complete runtime.
Package versions and source identities are checked; dependency wheel hashes and
the interpreter build are not independently authenticated by this wrapper.

## Run

From the repository root, replace each placeholder with a real **local** path:

```text
python -B tools/development-replay/development_replay.py --freeze <local-freeze-manifest.json> --remaining-dir <private-development-remaining-seven-directory> --work-dir learning-local/haya-development-replay
```

`--help` does not read private inputs or create files. Do not use Python `-O`:
the tool explicitly rejects it because fidelity checks use assertions.
`--work-dir` must be new and beneath Git-ignored `learning-local`. Existing
results are never overwritten. Reproduction does not require the earlier local
`replay.py`, `encoding_probe.py`, `paired_replay.py` or their result files.

The helper creates exact frozen runtime copies, recovers Before code from Git,
and writes explicit protocol FX configuration, not a recovered curated dataset.
Each executed case uses its original capture time as the fixed clock, empty
initial Before state and no overrides. After retains its actual pilot queue.

## Outputs and interpretation

Private results appear under `<work-dir>/development-split`; frozen runtime,
derived transport ZIPs and native After outputs are under
`<work-dir>/isolated-runtime`. Outputs may contain complete source records and
absolute local paths: never commit or publish them. Console output is status-only.

Each case retains raw decisions, queues, source hashes/pointers, ignored
structured fields, renderer differences and errors. Salary observations are
not automatically designated or mapped to approved evaluation labels. Operational
Before queues and After pilot queues remain separate. No new metric is defined.

The previous local run reported four successful pairs and six blocked cases;
that is historical diagnostic context, not a promised outcome in another checkout.
The wrapper stops cases with missing required in-content titles, unverified
multi-field/structured-salary transport, or other fidelity failures. It does not
insert titles, synthesize salary prose or relax frozen extraction rules.

Approval decisions remain outside this tool. Haya's reported protocol approval
does not establish Lubna's independent agreement. Nothing here authorizes a final
evaluation or extends compatibility conclusions to Held-out cases.

# Development-only Source Transport vNext prototype

This experimental consumer accepts structured title metadata and independent
source fields without changing the frozen HTML adapter. It does not execute
Before/After classification, graph evaluation, human review or publication.

`transport_vnext.py` reads only the authentic Development indexes and their
designated captures/replay inputs. Original capture and replay bytes are retained
verbatim as base64 with SHA-256 values. Top-level primary/detail overwrite
ownership and RFC 6901 source pointers are explicit. Supplementary originals are
preserved without selecting them over the indexed primary. All source fields,
including unknown fields, remain in the transport. The copied packet is checked
against its source bytes before consumption. Local index hashes are the trust
anchor; a self-contained packet does not independently authenticate an employer.

`consumer_vnext.py` uses the frozen adapter's pure rendering and duty helpers,
never its title-gated `extract()`. Title metadata stays outside description text.
Each HTML/plain field has its own locator space; source text is never stitched
together. Lever list headings have separate metadata pointers. Plain alternatives
remain accessible without being treated as additional postings. Duty extraction
does not carry section state across fields or claim complete negative coverage.

Structured salary objects and all their keys/types remain separate from prose.
Explicit Lever interval tokens can supply Annual/Monthly/Hourly; absent or unknown
tokens remain unresolved. No base-pay basis, pay market, eligibility, human label
or salary-observation designation is inferred. Other structured pay-range shapes
remain explicitly uninterpreted. The consumer does not infer currency/periods
from location, amounts or adjacent fields. Per-field duties may overlap between
source representations; their counts are evidence views, not independent facts.

The frozen adapter, ontology, taxonomy, SHACL and historical results are untouched.
The output is a new JSON transport/consumer contract, not an input compatible
with the existing frozen graph builder. Private integration fixtures are read in
place; none are copied into tracked tests. No third-party dependency is required.

From the repository root, using the verified Python interpreter:

```powershell
$env:STAGE7_DEVELOPMENT_RESULTS = 'learning-local/haya-development-replay-20261028-d0a8eefdb1/development-split/compatibility.json'
$env:STAGE7_VNEXT_INPUT_DIR = 'learning-local/source-transport-vnext-20261028-b00e324d35'
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -B -m unittest discover -s tools/source-transport-vnext -p 'test_*.py' -v
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -B tools/source-transport-vnext/transport_vnext.py --blocked-results $env:STAGE7_DEVELOPMENT_RESULTS --output-dir learning-local/source-transport-vnext-NEW
```

The smoke command requires a fresh Git-ignored output directory. It stops before
writing if any source hash, replay equality, identity or transport check fails.
Outputs contain complete private source records; keep them ignored. A successful
transport smoke is not a frozen replay PASS or evidence of classification accuracy.

## Experimental RDF builder

`graph_vnext.py` consumes verified packets and consumer outputs, anchors them
again to the authentic Development indexes/captures, and creates one RDF graph
per case. Use the existing readable RDFLib/pySHACL installation through
`KE_LOCAL_DEPS`; no installation or network access is performed.

The builder reuses the frozen ontology's posting, responsibility, salary,
artifact and passage terms. New field views, raw JSON values and source-assertion
bindings use only `urn:ke-market-observatory:experimental:source-transport-vnext:`
as declared in `vocabulary_vnext.ttl`. Reified source assertions bind individual
triples to original capture hashes, JSON pointers, exact JSON values or rendered
field spans. List headings and full-field context retain their own pointers.
Original JSON numeric types remain in the raw-value evidence; suitable numeric
amounts additionally receive value-preserving RDF decimals. Malformed amounts
remain raw/unmapped. Original interval tokens are preserved independently of
their explicitly mapped periods. No unit, basis, market, eligibility or role
applicability is supplied from other fields.

Consumer v2 additionally recognizes two narrowly bounded HTML layouts: a direct
second-person responsibility lead-in ending in "your responsibilities may also
include:" followed by a gerund-led list, and a Responsibilities/Key Responsibilities
list with bold category labels preceding explicit action clauses. Only top-level,
single-row HTML list items are supported by these additions. Qualification,
benefit, interview, quoted-guide, negated and nonadjacent contexts do not activate
them. The complete bullet and exact section context retain independent field-span
locators; conditional wording stays in that context. No title or occupational
concept supplies a duty. The two previously zero-duty Development layouts now
yield eight statements each. Other unmatched layouts can still yield zero.
Graph v2 retains the new section spans through `ke:contextPassage`; zero-duty
inputs still receive no fabricated role or negative classification.
`shapes_vnext.ttl` is a separate experimental contract. Validation checks every
pointer/span and assertion, compares graph facts with the verified consumer,
checks vocabulary declarations, runs experimental SHACL and RDF round-tripping.
The unchanged frozen SHACL profile is also run as a diagnostic: its older
locator grammar and mandatory-role rule are incompatible with these incomplete
field-aware records. Experimental conformance does not imply frozen conformance.

```powershell
$env:KE_LOCAL_DEPS = 'learning-local/development-v2-deps/Lib/site-packages'
# Regression tests intentionally retain the original, immutable zero-duty baseline.
$env:STAGE7_VNEXT_INPUT_DIR = 'learning-local/source-transport-vnext-20261028-b00e324d35'
# Keep STAGE7_DEVELOPMENT_RESULTS from the transport command above.
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -B -m unittest discover -s tools/source-transport-vnext -p 'test_*.py' -v
# Regenerate consumer v2 in a NEW directory; never overwrite saved consumer v1.
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -B tools/source-transport-vnext/transport_vnext.py --blocked-results $env:STAGE7_DEVELOPMENT_RESULTS --output-dir learning-local/source-transport-vnext-UPDATED
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -B tools/source-transport-vnext/graph_vnext.py --input-dir learning-local/source-transport-vnext-UPDATED --blocked-results $env:STAGE7_DEVELOPMENT_RESULTS --output-dir learning-local/source-graph-vnext-NEW
```

The output directory must be fresh and ignored. It receives six `.ttl` graphs,
per-case `.validation.json` records and `summary.json`. These contain private
source data and must remain ignored. This command performs source graph building
and integrity validation, not a Before/After replay or a final evaluation.

## Offline evidence review

`queries/responsibilities.rq` joins each duty's reified action-text assertion to
its own evidence. `queries/responsibility_contexts.rq` returns its context links
separately, preventing a context join from multiplying CSV rows.
`review_export_vnext.py` reads the six saved graphs and verifies query completeness
against RDF duty identifiers and verified consumer outputs. Every duty/context
locator is resolved against original capture bytes with SHA-256 checks.

```powershell
$env:STAGE7_VNEXT_GRAPH_DIR = 'learning-local/source-graph-vnext-layouts-20261028-f413eb2022'
$env:STAGE7_VNEXT_REVIEW_PACKET_DIR = 'learning-local/source-transport-vnext-layouts-20261028-f413eb2022'
# Keep the test baseline and result/dependency environment variables above.
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -B -m unittest discover -s tools/source-transport-vnext -p 'test_*.py' -v
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -B tools/source-transport-vnext/review_export_vnext.py --graph-dir $env:STAGE7_VNEXT_GRAPH_DIR --packet-dir $env:STAGE7_VNEXT_REVIEW_PACKET_DIR --blocked-results $env:STAGE7_DEVELOPMENT_RESULTS --output-dir learning-local/responsibility-review-NEW
```

The fresh ignored directory receives UTF-8 `responsibilities.csv`, `review.html`
and a verification record. CSV has one row per responsibility with exact text,
capture/hash, field pointer, zero-based exclusive-end Unicode spans, section
qualifiers and rendered field context. The three reviewer columns are blank.
Open `review.html` directly: all styling, navigation and CSV export work offline.
Edits stay in that browser tab until the reviewer downloads their CSV. No review
judgments are saved to original records, inferred, or transmitted. The page blocks
network connections and includes no external scripts, fonts or source-page embeds.

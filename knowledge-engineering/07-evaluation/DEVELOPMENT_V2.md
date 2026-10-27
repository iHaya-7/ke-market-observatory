# Development v2 integration

26 October 2026. Development work only; no independently verified accuracy or performance improvement is claimed.

The existing builder, validator and decision pilot now accept captured HTML postings with `--captures`. Their default historical three-case commands remain unchanged and still require the missing private Stage 5 mapping/graph. Those historical artifacts were not reconstructed. Development v2 remains separate from the frozen 40-case evaluation, Development v1 and Held-out.

## Existing components and minimal extensions

The Scope already separates responsibility-based occupational scope, intrinsic salary eligibility, international benchmark admission, source evidence and human review. The four-concept SKOS taxonomy and ontology already express the required meanings: `Responsibility`, `actsOnRepresentation`, `KnowledgeRepresentation`, `roleConcept`, `SalaryObservation`, evidence artifacts/passages and machine assessments. Both schemas are reused without changes.

The old builder required an exact three-case allowlist and private `mapping.json`; the old pilot deliberately abstained on all substantive decisions. The old integrity validator understood only those mapped JSON files, and two queries filtered out every case ID except `EVAL-*`. Production `salary_info()` validates structured pay but does not extract HTML salary evidence, and production relevance can accept a title alone. Calling the production normalizer would also discard occupational negatives before their salaries could be assessed.

The extension adds one standard-library HTML evidence adapter alongside the existing builder. It reads only manifest-listed original HTML members, checks checksums, sizes and posting identity, delimits responsibility sections, and preserves independently located pay bands. It recognizes Greenhouse's two board URL aliases while retaining job identity. No expectation or review CSV is an extraction input.

The existing builder materializes these facts and duty-to-representation interpretations with machine provenance. The existing pilot makes occupational and salary recommendations from that graph and reuses production `salary_info()` for amount/unit/base validation. Titles do not affect occupational decisions. Core requires an explicit action on a knowledge representation; backend graph service work can be adjacent; a bounded section describing other work can support Outside Scope; missing/ambiguous or unsupported duties cause abstention. Unparsed representation mentions prevent a negative classification.

Salary assessments retain original amounts, symbols in source excerpts, currency, period, basis and applicability. A bare `$` does not supply USD; missing periods are never inferred from the amount. Annual leave, fundraising and separate pay bands cannot supply salary units. A role-scoped band can use the same posting's explicit single location with both passages cited; a generic remote or unresolved market remains insufficient. Independent human authentication remains pending even for machine-eligible evidence. Original offered base ranges and separate equity are distinguished from total compensation.

The SHACL locator shape now accepts versioned HTML spans alongside legacy JSON pointers. Separate integrity checks re-resolve every passage and compare source/mapping facts to the manifest-bound extraction. The existing five queries are reused; two identifier filters now accept case IDs without a dataset-specific prefix. The graph's source facts, interpretations and machine assessments remain distinguishable. No new ontology terms, database, collector or production publication path was added.

## Run and inspect

Use Python 3.12+ with the existing pinned RDF/SHACL dependencies in an accessible ignored local prefix. Run installation as the same account that will execute validation:

```powershell
python -B -m pip install --prefix learning-local/development-v2-deps --ignore-installed --no-deps -r knowledge-engineering/06-validation/requirements-local.txt
$env:KE_LOCAL_DEPS = (Resolve-Path learning-local/development-v2-deps/Lib/site-packages).Path
python -B knowledge-engineering/07-evaluation/ke_decision_pilot.py --captures knowledge-engineering/00-baseline/local-corpus/development-v2/Development_v2_Source_Captures.zip --output learning-local/development-v2 --expected knowledge-engineering/00-baseline/local-corpus/development-v2/Development_v2_Expected_Behavior.csv
python -B knowledge-engineering/06-validation/validate_graph.py --captures knowledge-engineering/00-baseline/local-corpus/development-v2/Development_v2_Source_Captures.zip --graph learning-local/development-v2/graph.ttl
python -B -m unittest discover -s tests -p 'test_*.py' -v
node --check web/app.js
node --test tests/test_frontend_filters.js
python -B scripts/refresh.py --validate-only
```

On Windows, use the installed Python executable if the `python` WindowsApps alias is unavailable. Package directories must be readable by the executing account. The new standard-library extraction controls always run; graph controls explicitly skip if the optional RDF/SHACL dependencies are unavailable. A skipped control is not a pass.

`KE_LOCAL_DEPS` selects the dependency directory for the existing builder, validator, pilot and tests; when set, the inaccessible historical dependency paths are not inserted into `sys.path`. When unset, their previous dependency defaults remain unchanged. Set the variable in each new PowerShell session; no persistent machine/user environment setting is required. On POSIX, use the prefix's corresponding `lib/pythonX.Y/site-packages` location.

The local Windows repair used all eleven pinned wheels already present in pip's HTTP cache, copied into `learning-local/development-v2-deps/wheels`, and installed offline with `--prefix`, `--ignore-installed`, `--no-index`, `--find-links`, `--no-deps`, `--no-compile`, and `--no-cache-dir`. No cached files or existing dependency files were modified. Cached-wheel identities and SHA-256 values are recorded in ignored `learning-local/development-v2-deps/cached-wheel-provenance.json`.

`--expected` is optional and read only after machine decisions; it cannot provide missing source facts. Outputs are restricted to ignored `learning-local`: `report.md`, `results.json`, `graph.ttl`, `query-results.json`, and `review-queue.json`. The report contains a per-case explanation, original pay units, primary SAR/month display where supported, and evidence locators. JSON preserves all extracted responsibility evidence, missing dimensions, trace chains, source/capture identities, hashes and separate assessments. Repeated runs overwrite only the designated local outputs; run identities/timestamps vary.

SAR/month uses the existing retained `data/curated.json` FX metadata, annual division by 12, monthly identity and half-up rounding to 0.01. Each conversion records the rate, date and source; no live rate retrieval, gross/net assumption, hourly conversion or cross-job comparability claim occurs. Unresolved pay is withheld from normalized salary display.

## Business decisions and boundaries

The pipeline can recommend occupational scope from duties, identify intrinsic pay evidence eligibility independently, explain missing facts, withhold benchmark admission, and write a local review queue. Every case still requires independent human verification before approval or publication. A Core result with eligible international pay is only a benchmark candidate. An Outside Scope result can still have eligible salary evidence; its pay stays outside the specialized KE benchmark. Saudi pay remains separate from international admission. Multiple bands remain separate observations and no preferred band or salary pair is chosen.

The rules are intentionally narrow and deterministic, not a general natural-language understanding system. Unrecognized layouts, verbs, jurisdictions, ambiguous applicability and unresolved evidence can cause abstention or require rule extension. The HTML transform is versioned; locators use Unicode code-point offsets in its normalized block text, not raw-byte offsets. Checksums establish fidelity to the supplied captures, not independent employer authentication, current vacancy status or semantic truth. Responsibility classification is not a substitute for human review, and the opt-in route is not connected to production refresh or website data.

## Observed Development v2 results

| Case | Occupational recommendation and responsibility basis | Independent salary evidence decision | Missing dimensions / action |
| --- | --- | --- | --- |
| DEV2-001 | Core KE: local knowledge graph/schema construction and entity resolution | Eligible; USD 142,000–342,000 annual base; SAR 44,375–106,875/month | Benchmark candidate only; human source, scope and band review |
| DEV2-002 | Core KE: financial KG architecture and relationship models under a Data Engineer title | Insufficient Evidence; original annual base range retained | Currency: source uses `$` without an explicit currency code; hold |
| DEV2-003 | Core KE: schemas, ontologies and expertise relationships | Insufficient Evidence; base range retained | Currency, period and pay-market applicability; hold |
| DEV2-004 | Core KE: RDF/RDFS/OWL schemas and SHACL validation | Insufficient Evidence; annual range retained | Currency, explicit base-pay basis and pay-market applicability; hold |
| DEV2-005 | Core KE: knowledge graph and semantic-model implementation | No disclosed/extracted numeric salary | Numerical pay and context; retain occupational candidate only |
| DEV2-006 | Adjacent technical, provisional: Rust graph service/query/indexing/backend work | Insufficient Evidence; explicit US base range retained | Period; human adjudication of representation ownership and Core/Adjacent boundary |
| DEV2-007 | Outside Scope: ML/NLP modeling and evaluation, despite KG title | Eligible; USD 175,000–250,000 annual base; SAR 54,687.50–78,125/month | Exclude from specialized KE benchmark; keep independent pay evidence |
| DEV2-008 | Outside Scope: ML training/serving/monitoring infrastructure | Eligible; USD 125,000–175,000 annual base; SAR 39,062.50–54,687.50/month | Exclude from specialized KE benchmark; keep independent pay evidence |

Every row needs human verification before any approval/publication. Conversions use the retained 2026-10-20 USD/SAR 3.75 rate. DEV2-002 disagrees with the preliminary complete-salary expectation; USD is not copied from that spreadsheet. DEV2-003/004 share the preliminary insufficient-pay outcome but expose additional currency/market gaps. DEV2-006 remains a boundary recommendation requiring adjudication. Other status agreement is not independently verified accuracy.

Final validation: 69 Python tests passed (22 new controls and 47 existing tests), with no failures or skips in the dependency-enabled run; 31 existing frontend tests and JavaScript syntax check passed; existing `refresh.py --validate-only` passed. Both source-only and assessment-augmented graphs passed the existing SHACL shapes with the HTML locator extension, source/mapping fidelity, eight artifact checksums, 94 passage resolutions and RDF round-trip checks. The five existing queries executed (66 responsibility rows, 53 role-concept rows, 12 salary-context rows, 164 assessment-trace rows, zero comparison pairs). Query rows are joins, not independent jobs, salaries or accuracy cases.

Early controls exposed and led to corrections for funding being mistaken for pay, legitimate Greenhouse URL aliases, and unsupported-currency multi-band extraction. All final controls pass. The original run needed execution outside the sandbox because the old dependencies were unreadable. After the offline prefix reinstall, all 69 Python tests (no skips), all 31 frontend tests, the eight-case processing run, and standalone graph validation passed under the normal sandbox account. The default historical builder/validator/pilot remain unavailable because their private mapping, graph and pilot artifacts are absent; those historical outputs were neither recreated nor counted as passing. No published data, source inputs, frozen artifacts or evaluation protocol were modified.

### Dependency permission investigation

The old `stage6-deps` root had inherited sandbox Modify and user FullControl permissions, while `rdflib` and its `__init__.py` denied sandbox reads, including reading their ACLs. Read-only elevated child-ACL inspection was declined, so the old children's precise ACL entries were not independently retrieved. Inspection of the installed pip implementation showed that `--target` builds in a `tempfile.mkdtemp()` staging tree and then moves package trees to the target. A controlled probe entirely inside the fresh dependency directory reproduced Python 3.13's protected temporary-directory ACL: inheritance disabled, with only OWNER RIGHTS, SYSTEM and Administrators granted FullControl. This supports the diagnosis that private staging permissions followed the cross-account `--target` move; it does not claim direct inspection of the inaccessible children's ACLs.

The fix avoids that move by installing directly into a fresh prefix under the normal sandbox account. Both the new `rdflib` directory and `__init__.py` have inheritance enabled, sandbox Modify and user FullControl; imports and package-version metadata resolve from the fresh prefix. No `Set-Acl`, recursive reset, permission grant, ownership change or ACL modification was executed. The old directory was preserved. Frozen/Held-out material and project source permissions were untouched. Detailed local observations are in ignored `learning-local/development-v2-deps/diagnostics/permission-investigation.md`.

To establish actual KE performance improvement, obtain independent source-only judgments with reviewer identity, time and prior AI exposure; preserve initial judgments and adjudication; freeze the implementation and rubric; and conduct a fair paired frozen-baseline replay on the same designated inputs under the unchanged evaluation protocol. Development v2 agreement with AI expectations is calibration evidence only. Missing historical artifacts remain a reproducibility dependency. No Held-out evidence was opened for this work.

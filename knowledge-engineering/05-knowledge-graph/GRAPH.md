# Stage 5 — Lightweight Knowledge Graph MVP

Executed 22 October 2026. Three real Development cases; local RDFLib implementation only. Stage 3 and Stage 4 are technically reviewed working models pending final team approval. Their files and semantics are unchanged. This graph demonstrates evidence navigation and preservation of uncertainty, not classification accuracy improvement.

## Scope and reproducibility

The fixed cases are `EVAL-0d7b2c3f9f39cbcc`, `EVAL-4847917fd586d111`, and `EVAL-5808d42f328be89c`, confirmed as Development by the public Stage 0 case index. These were the first three selected Development cases inspected, spanning two sources. Scope stayed at three despite empty occupational/comparison answers. Selection was not based on predictions or labels. This is a small illustrative subset, not a representative sample.

Run from the repository root:

```powershell
# One-time local dependency setup, if absent (already completed here):
python -m pip install --target learning-local/stage5-deps rdflib==7.2.1
python knowledge-engineering/05-knowledge-graph/build_graph.py
```

Python 3.13 / RDFLib 7.2.1 were used; local dependencies also include isodate 0.7.2 and pyparsing 3.3.3. No production dependency file changed. The builder has no network calls, API, LLM integration, refresh, or database service.

Private inputs/outputs are under the existing ignored directory `knowledge-engineering/00-baseline/local-corpus/development/stage5/`:

- `mapping.json`: fixed Development allowlist, original identities, three source paths and byte hashes, exact locators, selected values, and source wording. This is an implementation mapping, not evaluation claims or labels.
- `graph.ttl`: private ABox only, with original text and source context.
- `query-results.json`: complete **executed** SPARQL bindings, including empty arrays and null/unbound values.
- `verification.json`: counts and executed query row totals.

The local mapping and case-specific original artifacts are required to reproduce the graph; a public checkout intentionally cannot reconstruct private evidence. The builder fails if they are absent or changed, and never discovers additional cases. Reruns preserve domain IRIs and assertions; assessment generation times change. The run IRI identifies the builder/mapping version by content hash, rather than an individual invocation. Results are ordered by query keys. The script loads the existing [ontology](../04-ontology/ontology.ttl) and [taxonomy](../03-taxonomy/role-taxonomy.ttl) separately into an in-memory query union, without copying either into the ABox or applying entailment.

## Provenance and interpretation

Posting IRIs use `urn:ke-market-observatory:instance:posting:<sourceId>:<sourceJobId>` with percent-encoded components. Roles, duties, observations, passages, and assessments have separate stable suffixes; artifact IRIs contain SHA-256. Case IDs, original source IDs/job IDs, URLs, and titles are retained privately. No requisition identity or duplicate merge is asserted.

Only three case-specific `details/.../<case>.json` or `originals/.../<case>-....json` artifacts are consumed by the builder. These are preserved original source records extracted during Stage 0, **not raw HTTP bytes**. Their own byte hashes and original wrapper capture times are recorded. Shared raw API responses were not opened, since they may contain Held-out records; this run does not reverify their extraction against those responses. Initial inspection opened only these three Development evidence bundles (which also contain legacy Development claim candidates); no claim candidate was used, and no separate private claim specification, full evaluation CSV, prediction, label, or Held-out case was opened.

Passage locators are JSON objects: an RFC 6901 pointer into the case-specific artifact, transform name, and optional zero-based Unicode code-point `[start,end)` offsets. `text-v1` applies HTML unescape once, replaces tags with spaces, unescapes once again, collapses whitespace, and strips edges. `json` serializes the pointed value with sorted keys and Unicode retained. Every stored passage is matched exactly; context passages retain the broader description or related compensation statement. Full context stays private.

Three duties are literal advertised responsibilities, selected from duty sections; titles and qualifications do not create relevance or role assignments. No unsubstantiated `actsOnRepresentation` or `roleConcept` relation is asserted. The three roles remain unmapped in this MVP, which is not a judgment of irrelevance or proof that no concept could apply after review.

Four salary observations represent four statements, **not four independent pay bands**: two prose statements on separate postings, and one structured/prose pair on a third posting. The latter pair has reciprocal context links; it is not pooled. Original period wording is preserved. Missing currency, period, gross/net basis, market, career level, and salary eligibility remain absent. A dollar sign does not become USD; a posting location does not become a pay market. No FX conversion or numeric equity amount is invented. Publisher attribution is separate from hiring-employer eligibility.

Seven `MachineAssessment` records check **source extraction fidelity** for the three duties and four observations. Each targets the corresponding record, cites its evidence, and records the exact-match outcome, restricted rationale, builder checksum, software agent, run, time, and version. This is an additional scoped assessment-kind string permitted by the existing literal property, not a new schema term or protocol label. Exact text/scalar matching does not verify relevance, occupational scope, base-pay eligibility, or semantic claim support. There are no `HumanAssessment`, evaluation `Claim`, `SalaryComparison`, `Requisition`, or `ReviewQueueEntry` instances.

## Actual executed results

All five queries ran successfully against the ABox plus the unchanged schema/taxonomy. Full bindings are in the ignored `query-results.json`; the following is the publication-safe projection of those results. Source excerpts, monetary values, source titles, and private case material are deliberately retained only locally.

| Query | Actual rows | Result and limitation |
| --- | ---: | --- |
| [01-responsibilities](queries/01-responsibilities.rq) | 3 | One evidenced duty per case listed above; each returns action text, passage IRI, and locator. This is a selected subset of duties, not a relevance verdict. |
| [02-role-concepts](queries/02-role-concepts.rq) | 0 | Empty result `[]`. No evidenced occupational assignment was asserted; joining the existing SKOS concepts cannot manufacture one. |
| [03-salary-context](queries/03-salary-context.rq) | 4 | Four source statements with evidence/context links and optional compensation fields; missing values remain unbound. Details below. |
| [04-assessment-trace](queries/04-assessment-trace.rq) | 7 | One source-fidelity assessment per asserted duty/observation; every row returns the target, outcome, passage, locator, original URL, local artifact, checksum, and capture time. |
| [05-comparisons](queries/05-comparisons.rq) | 0 | Empty result `[]`. No designated pairs or comparison assessments were created. |

Executed salary-query binding availability (`—` means unbound, not negative):

| Case / observation suffix | Bounds | Currency | Period | Basis | Market |
| --- | --- | --- | --- | --- | --- |
| `EVAL-0d7b2c3f9f39cbcc` / `salary-prose` | Both | — | — | Bound | — |
| `EVAL-4847917fd586d111` / `salary-prose` | Both | — | Bound | Bound | Bound |
| `EVAL-4847917fd586d111` / `salary-structured` | Both | Bound | Bound | — | — |
| `EVAL-5808d42f328be89c` / `salary-prose` | Both | — | — | Bound | — |

## Verification and CQ limits

Result: **37 distinct ABox subject entities, 231 ABox triples**, excluding 274 ontology and 33 taxonomy triples (538 triples in the query union). Entities: 3 postings, 3 roles, 3 responsibilities, 4 salary observations, 3 artifacts, 10 passages, 7 machine assessments, 2 publisher agents, 1 software agent, and 1 activity. The 7 assessments are also explicitly typed `Assessment`; they are counted once as entities.

There are **14 `evidencePassage` links**: 7 from duties/observations and 7 from assessments. All 10 passage-to-artifact links resolve locally; 7 additional context links connect selected passages with broader evidence. All three artifact hashes match the private mapping. Proper RDFLib Turtle parsing and exact serialization/reparse comparison pass, as do IRI syntax, declared ontology terms, property kinds, domains/ranges, datatype checks, taxonomy reference checks (no role assignments to check), numeric/source-value checks, salary bound ordering, and absence of human assessments/identity merging. These are procedural checks, not SHACL, OWL consistency reasoning, or independent semantic validation.

| CQ | Demonstrated | Still unsupported |
| --- | --- | --- |
| CQ-01 | Posting → role → selected advertised duty → source passage. | Substantive knowledge-representation interpretation and relevance determination. |
| CQ-02 | Distinct work-function records; executable concept/duty join with honest empty result. | Occupational assignments and Core KE / Adjacent technical / Neither judgments. |
| CQ-03 | Separate original compensation statements, optional context, and missing fields. | Eligibility outcomes and complete attribution/unit/band judgments; no automatic eligibility. |
| CQ-04 | Executable comparison query with honest empty result. | Designated pairs, levels, gross-pay/context judgments, endpoints, conversions, comparability. |
| CQ-05 | Machine extraction-assessment → passage → locally preserved source chain. | Approved/versioned evaluation claims and semantic support/contradiction judgments. Complete linkage is not claim correctness. |
| CQ-06 | Machine origin is explicit and human judgments are absent. | Review-need assessments, scoped review questions, actual queue membership, and resolved human review. |

Thus CQ-01, CQ-03, and the assessment-trace portion of CQ-05 are partially demonstrated. No full six-CQ acceptance or accuracy claim is made; CQ-02, CQ-04, and CQ-06 decision answers remain unsupported. No scope expansion was used to make an empty query nonempty.

Git checks confirm only this Stage 5 directory and the existing [DECISIONS.md](../DECISIONS.md) changed among shareable files. Private outputs/dependencies match existing ignore rules. Production classification/salary logic, dashboard, Actions, baseline snapshot, frozen corpus and evaluation artifacts remain unchanged. No live refresh, Ground Truth, metrics, SHACL, commit, or push was performed. Stage 5 stops at this MVP.

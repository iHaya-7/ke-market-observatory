# Stage 0 — Step 0.1: Current-State Audit

Audit date: 21 October 2026 (Asia/Riyadh). Repository HEAD inspected: `002525b2e08f610206b205374ad2244785b9c088`.

Scope: existing tracked implementation, configuration, JSON datasets, generated dashboard, and tests. **Implemented** below means confirmed by code inspection; **verified locally** identifies checks actually executed. Source-page assertions in imported records are not independent verification. No collection, build, deployment, labels, or baseline snapshot were produced.

## 1. Current Architecture — simple pipeline flow

```text
config/sources.json → public Lever / Greenhouse / Workable APIs
                              ↓
                     get_board → normalize
                     relevance / experience / salary rules
                              ↓
data/auto_records.json ← merge_feed (retained normalized history)
                              ↓
data/review_decisions.json → automatic publication gate
data/curated.json ─────────→ assemble_records + build_review_queue
previous public/data/market.json → prior metadata, FX, changes
Frankfurter + configured USD/SAR assumption → updated FX, or last-good FX
                              ↓
                    validate_market → public/data/market.json
                              ↓
web/template.html + app.js + app.css + fonts → build_site.py
                              ↓
                     public/index.html → GitHub Pages
                              ↓
browser: embedded seed / local cache + published JSON polling
```

Implemented orchestration: [scripts/refresh.py](../../scripts/refresh.py), `refresh()` and nested `collect()`. Refresh writes only normalized automatic records and the published JSON through `atomic_json()`; it reads curated evidence without rewriting it. [scripts/build_site.py](../../scripts/build_site.py), module-level build, validates JSON and embeds it with JavaScript, CSS, fonts, and font license into one HTML file.

Browser behavior: [web/app.js](../../web/app.js), `validate()`, initial cache selection, `refresh()`, and final event/timer setup. HTTP views fetch `data/market.json` with a cache-busting timestamp and retain the previous snapshot on failure. Polling is hardcoded to 300,000 ms while visible; manual refresh, becoming visible, and going online also trigger reads. `meta.pollSeconds` is descriptive, not the timer input. File previews use embedded data. Browser reads do not run collection or renew evidence dates.

Automation: [.github/workflows/refresh-and-deploy.yml](../../.github/workflows/refresh-and-deploy.yml), `on`, `concurrency`, `jobs.collect`, and `jobs.deploy`. Configured triggers are manual dispatch, daily `17 5 * * *` (05:17 UTC / 08:17 Riyadh), and filtered pushes to `main`. Collection runs only on `main`, uses Python 3.12, runs Python tests and Node syntax checking, collects, validates, builds, commits/pushes generated JSON/HTML, and uploads `public/`. Deployment depends on collection and uses GitHub Pages with `pages: write` and `id-token: write`; collection has `contents: write`. Concurrency prevents overlapping publication runs. Push filters omit `data/review_decisions.json`, `data/auto_records.json`, `public/**`, and Knowledge Engineering documentation, so a review-decisions-only push does not immediately trigger publication.

## 2. Data Sources and Relevant Files

| File / section | Implemented purpose and inspected contents |
| --- | --- |
| [config/sources.json](../../config/sources.json), `sources[]` | Six enabled boards: Lever Samba TV; Greenhouse Nearform, Tamara, Sapience AI; Workable Envision Employment Solutions and Robusta / RTG. Each has `id`, `company`, `type`, `account`, `enabled`, `scope`, `boardUrl`. Settings: `maxPages: 20`, `maxDetailsPerBoard: 50`, `httpTimeoutSeconds: 20`, `fxEnabled: true`. |
| [data/curated.json](../../data/curated.json), `records[]` | 21 manually maintained references: `KE-001`–`KE-013` salary references and `SA-001`–`SA-008` Saudi records. `origin` identifies previous research HTML or the Saudi reference register; the original research artifact is not among tracked files. Other top-level sections are `schemaVersion`, `meta`, `fx`, `sources`, `reviewQueue`, `changes`. |
| [data/auto_records.json](../../data/auto_records.json), root array | 20 retained normalized records, not raw ATS responses: seven `roleDecision: approved`, seven `pending`, six without that field. Seven approved automatic records yield five additional published rows after two URL matches to curated rows. |
| [data/review_decisions.json](../../data/review_decisions.json), `approved`, `rejected` | Both arrays are currently empty. Role-inclusion overrides by automatic record ID; no reviewer, rationale, or decision date fields. |
| [public/data/market.json](../../public/data/market.json) | Actual published snapshot: 26 records; 30 queue items (13 role relevance, 11 pay basis, six Saudi listing status). `meta.dataVersion` is `502461042f744e2d`; stored last collection/publication is `2026-10-20T19:20:27Z`. All six stored source statuses are `OK`. These are stored results, not live checks by this audit. |
| [public/index.html](../../public/index.html), `#seed-data` | Generated dashboard. Verified locally: embedded JSON equals `public/data/market.json`, and embedded application JavaScript contains the current `web/app.js`. |
| [tests/test_refresh.py](../../tests/test_refresh.py), `CollectorTests`; [tests/test_build_site.py](../../tests/test_build_site.py), `BuildTests` | 45 collector test methods and one packaging test. Fixtures cover relevance, experience, salary units/basis, integrity, preservation, review handling, and temporary-directory refresh/build paths. These are software tests, not Ground Truth. |

Collection implementation: [scripts/refresh.py](../../scripts/refresh.py), `fetch_json()` and `get_board()`:

- Requests use an explicit API-host allowlist, redirect-host checks, a 20 MB response limit, and one retry for selected HTTP failures. Sources are collected with three worker threads. No LinkedIn/browser collector exists; LinkedIn, Gusto, Apple, Accenture, salary publishers, and repost sites occur as curated evidence links rather than configured collectors.
- Lever pages in batches of 100; repeated IDs or reaching the configured pagination cap fail the source check. Greenhouse requests content, checks reported total, then requests pay-transparency details for up to 50 relevant candidates, including pending matches through `classify()`. Detail failures produce warnings; the feed can still succeed. Workable requests `details=true` and rejects recognized pagination indicators rather than following them.
- Curated collection methods are recorded prose. How the prior researcher captured or verified each original source is not implemented in this repository. No raw feed, original description archive, or per-pay-range evidence artifact is persisted by `normalize()` / `refresh()`.

## 3. Current Job Classification Logic

Implemented in [scripts/refresh.py](../../scripts/refresh.py), `SKILLS`, title/evidence regex constants, `assess_role()`, `classify()`, `normalize()`, and `refresh()`:

1. Case-insensitive regex matches over title plus cleaned description produce named `skills`. Recruiting, HR, sales, marketing, and other listed nontechnical title patterns take precedence and are excluded.
2. Explicit Knowledge Engineer, Knowledge Graph Engineer, Ontology Engineer, Ontologist, or Semantic Web Engineer title patterns are automatically approved as `Core KE`, without requiring description evidence.
3. Other titles generally need both an adjacent-domain term and a technical-role term. Without that combination, at least two ontology/graph evidence terms produce a pending `Applied KG / AI` candidate; otherwise the record is excluded.
4. Adjacent technical titles require an action word somewhere in the description. Ontology plus complementary semantic technology approves `Core KE`; Knowledge Graph plus complementary technology approves `Applied KG / AI`. Strong metadata adjacency remains pending `Metadata / Semantic`. Weaker evidence is pending or excluded according to term counts.
5. `normalize()` returns `None` for excluded jobs; their IDs, descriptions, and reasons are not newly saved. Pending records are retained. `refresh()` publishes machine-approved or manually approved automatic IDs, with rejection taking precedence. Missing legacy decisions default to pending. Curated records enter `assemble_records()` directly; they are not reclassified or filtered by those automatic decision arrays.

Automatic `family` is only `Knowledge Engineer` for an exact lowercase title match, otherwise `Related title`; it is not the same classification as `relevance`. Curated families, skills, and relevance are stored values. For example, curated `Knowledge Graphs` and automatic `Knowledge Graph` coexist; curated skill names also extend beyond `SKILLS`.

Experience: `experience_info()` searches the first matching numeric years-of-experience phrase, checks bounds 0–60 and range order, and stores `experience`, `expMin`, `expMax`, `level`, `levelBasis`. Title precedence is Junior/entry/graduate, then Senior/sr/lead/principal/staff/director/head/chief, then explicit mid-level. Otherwise a bounded 0–2 range is Junior, minimum ≥6 is Senior, minimum ≥2 is Mid, and the remainder is `Not specified`. A bare `1 year` becomes `1+ years` but does not automatically become Junior. The regex cannot establish whether years refer to overall or specialized experience; `levelBasis` explicitly requests context verification. Curated levels and year evidence are preserved by `assemble_records()`.

Geography: `location_info()` uses ATS location fields, selected country codes/city keywords, then a limited fallback. It does not use country mentions in the description or title. `region` is `saudi` only when the derived country is Saudi Arabia. This is a heuristic location mapping, not a geographic reference model.

Relevant fixture evidence: `CollectorTests.test_recruiter_with_many_semantic_keywords_excluded`, `test_strong_non_ke_title_match_accepted`, `test_metadata_only_candidate_staged_for_review`, `test_vague_ai_mention_staged_for_review`, `test_experience_pattern`, `test_no_years_not_junior`, and `test_workable_saudi_location`.

## 4. Current Salary Validation and Benchmark Logic

Extraction: [scripts/refresh.py](../../scripts/refresh.py), `salary_info()`:

- Lever reads one structured `salaryRange` plus salary-description wording. Greenhouse reads `pay_input_ranges` and divides cents by 100. Workable has no structured salary adapter. Potential free-text pay is flagged using currency-before-number patterns; no numeric salary is extracted from it.
- Multiple ranges are withheld entirely. Minimum must be finite/nonnegative; an optional maximum must be finite and ≥minimum. Only Annual/Monthly and USD/GBP/EUR/SAR are supported. Unsupported or ambiguous units are withheld; hourly pay is not annualized.
- Explicit wording determines `salaryBasis`: `base`, `total`, or `unknown`. Wording matching both base and total is ambiguous. `salaryBasisVerified` is a parser flag for base/total wording, not human validation. Only base sets automatic `salaryEligible: true`; unknown numeric pay is retained but excluded. Missing pay retains nulls and basis `none`. Curated records additionally use stored values such as `unverified` and `estimate`.

Integrity: `validate_market()` checks schema version 2, record list, unique string IDs, source-URL syntax, finite nonnegative nonboolean salary amounts, ordered bounds, supported units, Saudi country consistency, employer/base/verified conditions for an eligibility flag, positive finite FX, and SAR=1. It is not a complete schema: it does not require human approval evidence, classification enums, evidence dates, decision-array consistency, or even a non-null salary minimum when eligibility is true. Browser `validate()` adds presentation requirements but is a separate, nonidentical validator.

Merge and listing status: `assemble_records()` matches canonical source URLs, preserves curated salary/experience, and copies automatic listing observations onto matching curated records. Salary updates overwrite curated values only for explicit eligible employer base pay. `merge_feed()` preserves first-seen dates; successful absence increments `missingChecks`, first producing `Needs recheck`, then `Not in latest feed`. Failed source checks leave automatic records unchanged. These are retained observations, not confirmed vacancy closure. Refresh restarts published records from curated plus retained automatic data; it does not simply preserve the entire prior published record list.

Review routing: `build_review_queue()` creates role items for unapproved pending/default-pending automatic records; pay items for automatic numeric pay without verified basis and for equivalent employer rows in the assembled published set; and Saudi status items for published Saudi rows marked `Needs recheck` or `Listing visible`. Rejected automatic IDs are skipped in its automatic pass. Items deduplicate by `(id, category)`. Queue membership does not generally remove curated rows from the published dataset. Approving an automatic role does not independently verify pay or listing status.

FX: `refresh()` requests Frankfurter USD→GBP/EUR, takes `usdSar` from curated FX (currently 3.75), and computes SAR conversion rates as `usdSar / foreignCurrencyPerUSD`, rounded to six decimals. Previous published FX is the starting point and retained on fetch failure. Curated FX labels itself an imported SAMA snapshot not reverified in that build.

Benchmark: [web/app.js](../../web/app.js), `isSalary()`, `baseEligible()`, `monthly()`, `graph()`, `filtered()`, `salaryStats()`, `overview()`, `juniorPage()`:

- Eligible base observations must be non-Saudi, not pending, employer evidence, explicitly eligible/base/verified, and have usable salary units and FX. No freshness, current-open, or known-experience requirement exists. Historical references can qualify.
- Monthly SAR = amount × stored FX rate / 12 for annual pay, or amount × rate for monthly pay. Original amounts remain available. No tax, purchasing-power, inflation, or work-hours adjustment exists.
- The chart displays individual ranges. Filtered statistics count eligible rows and distinct country strings, take the lowest monthly minimum and highest available monthly maximum. No mean, median, or market-wide salary estimate is calculated. A missing upper bound is not used as a ceiling statistic. Global filtering can display ineligible numeric references; Junior evidence separately displays non-Saudi Junior rows with pay, including reposts and estimates.
- Verified locally using the actual frontend functions in an isolated Node context: curated and published JSON pass frontend validation, and `baseEligible()` selects only `KE-007` in the published snapshot. This checks current behavior, not the correctness of its employer evidence.

Relevant tests: `CollectorTests.test_salary_units`, `test_greenhouse_cents_and_period`, `test_no_merged_geographic_bands`, `test_no_hourly_assumption`, `test_free_text_review`, `test_salary_total_not_base_benchmark`, `test_unverified_pay_cannot_be_flagged_eligible`, `test_curated_salary_not_erased`, and `test_end_to_end_strict_publish_review_and_salary`.

## 5. Existing Structured Concepts and Relationships

| Concept already represented | Structure / relationship actually present |
| --- | --- |
| Job/source reference | JSON record `id`, `title`, `family`, `relevance`, `roleDecision`, scope summaries. A record can be a job, historical lead, repost, or publisher estimate; it is not necessarily a unique requisition. |
| Experience level | `level`, year bounds, `experience`, `levelBasis`; automatic regex rules and curated analyst groupings. No formal level hierarchy. |
| Skill | Per-record string array `skills`; automatic regex-name dictionary. Membership explicitly associates a record with matched terms, not demonstrated proficiency. No skill IDs, synonym registry, or skill hierarchy. |
| Company | `company` string on sources and records. Automatic company comes from source configuration and can name a recruiter; hiring-client identity is not resolved. |
| Salary observation | Salary bounds, units, basis, eligibility, compensation label and dates embedded in the same record. No separate observation ID, multiple-band model, or complete salary time series. |
| Source and evidence type | `sourceId` links automatic records to source-health `sources[].id`; `sourceJobId` retains ATS identity. `sourceUrl`, `extraUrl`, `sourceLabel`, `evidenceType`, `evidenceMethod`, `origin` attach evidence to records. Company/source ownership remains string-level context. |
| Review / possible overlap | Queue `id` references a source-record ID, category and reason; decision arrays reference automatic IDs. Curated `duplicateGroup` associates possible overlapping records without proving identity. |

Evidence: JSON fields in [data/curated.json](../../data/curated.json), [data/auto_records.json](../../data/auto_records.json), and [public/data/market.json](../../public/data/market.json); construction in `normalize()` / `build_review_queue()`; presentation in `evidenceBadge()`, `detail()`, `saudiCards()` in [web/app.js](../../web/app.js).

Skills, roles, companies, locations, and evidence are structured application data with procedural rules. There is no implemented formal ontology, RDF mapping, triple store, graph traversal, inference engine, or ontology validation. RDF/OWL/SHACL/SKOS are job-description keyword values here. [knowledge-engineering/README.md](../README.md) describes future stages; stage folders contain placeholders and [DECISIONS.md](../DECISIONS.md) is an unfilled template.

## 6. Existing Evidence and Traceability

Implemented provenance: `normalize()` stores canonical URLs, source/ATS IDs, collection method, evidence date, first/last seen, posting date where supplied, and listing notes. Lever publication time is deliberately left null. `salaryVerifiedAt` is set when automatic numeric pay is retained, even if basis is unknown. Thus its name alone does not establish verified base pay. Imported dates describe recorded research, not a new source check.

`canonical()` normalizes scheme/host/path, strips `/apply` and most query parameters, preserves recognized job-ID query keys, and normalizes LinkedIn numeric job URLs. It does not resolve redirects or compare job content. `assemble_records()` uses canonical URLs, not cross-platform job identity; merged curated rows do not inherit every automatic provenance field, such as `sourceJobId`.

`refresh()` records source health, selected new/salary/status events, and caps `changes` at 150. It does not log review decisions, removals, all field changes, or original evidence passages. `content_hash()` hashes only selected record fields; nested `digest()` adds queue IDs/categories. Changes to skills, relevance, eligibility/basis, FX, or evidence dates alone need not change `dataVersion`. Browser refresh compares the full JSON, so its update detection is broader than that version token.

The workflow's `Preserve source history in Git` step can retain generated-file history after successful commits. This audit did not verify cloud runs or completeness of remote history. `detail()`, `exportCSV()`, `saveCopy()`, and `printView()` expose existing evidence; CSV omits several provenance and decision fields, so full JSON is the appropriate evaluation source.

## 7. Potential Weaknesses and Known Limitations

- **Recall/replay gap:** excluded new jobs and original descriptions/pay payloads are discarded (`normalize()`, `refresh()`). Titles and keyword summaries cannot reconstruct classifier input. Configured-board coverage is limited; source `jobCount` / `matchedCount` are not labeled evaluation denominators.
- **Heuristic scope:** `assess_role()` accepts core titles without description corroboration and checks action words anywhere, without tying them to semantic responsibilities. English keyword rules, title-pattern gaps, and phrase context can affect both acceptance and rejection. Stored `approved` is not Ground Truth.
- **Incomplete salary queue:** `salary_info()` can flag free text, multiple ranges, or ambiguous units while keeping `salaryMin: null`; `build_review_queue()` requires a non-null minimum for pay items. Five retained automatic IDs currently have salary-review flags but no queue item, including `AUTO-greenhouse-sapience-e9a7dee0a057`. Detail-request failure flags are also not persisted by `normalize()`.
- **Legacy retention/status ambiguity:** six automatic rows lack `roleDecision` and remain in role review despite `Not in latest feed`; examples include `AUTO-lever-sambatv-bb5cb07f9d37` (recruiter). `merge_feed()` receives normalized candidates, so losing relevance can count as absence even if the raw posting remains in a successful feed. Stored absent status does not establish which happened.
- **Identity and geography conflict:** curated `SA-004` uses `/robusta/j/D8EA0BA357`, Saudi Arabia/Jeddah; automatic `AUTO-workable-robusta-a033b6913e0c` uses `/j/D8EA0BA357`, Egypt/Cairo. Both appear in published records. The shared job token suggests overlap requiring review; `canonical()` / `assemble_records()` do not merge these URLs. Curated `SA-001`/`SA-002` also share a possible-overlap group without identity resolution.
- **Evidence/validation limits:** `SA-005` and `SA-008` have null evidence dates; imported claims are not independently verified here. `validate_market()` does not enforce complete provenance, controlled classification values, or decision-array exclusivity. Automatic `salaryBasisVerified` is lexical evidence. Only one current row passes the frontend base benchmark predicate; that does not establish representative coverage or accuracy.
- **Partial history:** content versioning and event tracking omit material fields (`content_hash()`, nested `digest()`, event loop in `refresh()`). Review decisions lack an outcome audit trail; absence from a later queue is not proof of successful review.

Verification boundary: `node --check web/app.js` passed; read-only Node checks confirmed JSON/embedded consistency and the frontend behavior described above. Python tests were inspected but not rerun: the available `python.exe` alias could not execute; no dependencies or interpreter were installed. [TEST_REPORT.md](../../TEST_REPORT.md) and [TEST_REPORT_V3.md](../../TEST_REPORT_V3.md) document earlier 31/44-test and browser results, not current audit results. Live API availability, current salary claims, vacancy status, GitHub permissions, schedule execution, and deployment were not tested. Stored successful collection metadata confirms only what the repository snapshot records.

## 8. Recommended Baseline Snapshot for Step 0.2

**Recommendations only; no snapshot or labels created.** Freeze full files rather than just dashboard exports or `dataVersion`:

- Exact commit and byte-level checksums for `scripts/refresh.py`, `scripts/build_site.py`, `web/**`, `tests/**`, `.github/workflows/refresh-and-deploy.yml`, and `config/sources.json`.
- All four data artifacts: `data/curated.json`, `data/auto_records.json`, `data/review_decisions.json`, `public/data/market.json`; also the matching `public/index.html`. Keep curated, automatic, merged, and review populations distinct and preserve legacy missing fields.
- Published `meta`, complete `fx` including rates/date/assumption, `sources`, `reviewQueue`, and `changes`. Fix comparison time, freshness threshold, geography rules, record identity mapping, manual overrides, benchmark inclusion policy, and UI filters. Hold FX constant when isolating classification/eligibility impact; evaluate FX changes separately.
- Subject to Step 0.2 approval, establish a fixed input corpus with original descriptions and salary payloads, including approved, pending, and excluded jobs, stable source IDs, and capture times. If historical raw inputs cannot be recovered, describe that limitation and use a separately captured prospective corpus run through both versions. Do not imply the existing normalized files permit historical replay.
- Establish separate human Ground Truth with evidence, reviewer, decision date, uncertainty/adjudication rules, and task-specific labels. Current curated/machine approvals and existing unit fixtures must not be treated as an independent labeled test set. Keep the same held-out items and criteria for before/after evaluation.

| Future evaluation point | Exact available data / output fields | Readiness and missing evidence |
| --- | --- | --- |
| Job relevance precision and recall | Automatic root-array rows: `id`, `sourceId`, `sourceJobId`, `title`, `skills`, `relevance`, `roleDecision`, `roleReviewReason`; curated `records[]`: `family`, `summary`, `notes`, corresponding decisions; published `records[].id`; manual override arrays. Outputs originate in `assess_role()` and `refresh()` publication gate. | Inclusion/predictions are partly available; six automatic decisions are missing. No independent labels, raw description corpus, or complete excluded-job population. Precision needs judged included cases; recall needs judged relevant cases across the fixed input population, including exclusions. Neither accuracy metric is presently justified. |
| Salary eligibility and comparability accuracy | Curated/automatic/published rows: `salaryMin`, `salaryMax`, `currency`, `period`, `compensation`, `salaryBasis`, `salaryBasisVerified`, `salaryEligible`, `evidenceType`, `region`, `roleDecision`, `level`, `expMin`, `expMax`, `country`, `city`, `restrictions`, `reviewRequired`, `reviewReason`; published `fx`. Outputs: `salary_info()`, `baseEligible()`, `monthly()`, `salaryStats()`. | Flags, selected amounts, and deterministic conversions exist. Original bands/labels/geographic applicability and ambiguous/free-text amounts are not fully retained. Human eligibility and comparability judgments are absent. Freeze zero/unknown cases and exclusions, not just numeric salaries. |
| Evidence traceability | `sourceUrl`, `extraUrl`, `sourceLabel`, `sourceId`, `sourceJobId`, `evidenceType`, `evidenceMethod`, `origin`, `evidenceDate`, `salaryVerifiedAt`, `postedAt`, `firstSeenAt`, `lastSeenAt`, `listingStatus`, `statusNote`; source health timestamps/errors. | Field completeness and internal links are inspectable. Supporting passages, immutable source captures, and independent support judgments are absent; a syntactically valid URL is not proof of claim support. Distinguish link/field coverage from evidence correctness. |
| Review queue outcomes | Published `reviewQueue[]`: `id`, `category`, `company`, `title`, `sourceUrl`, `reason`; automatic review flags/reasons; `review_decisions.json`: `approved`, `rejected`. Queue builder and publication gate provide observable outputs. | Current backlog is available; decisions are empty. No reviewer, reviewed-at, prior state, outcome reason, or pay/status resolution history. Need adjudicated outcomes to assess correctness; queue disappearance alone is insufficient. |
| Future Competency Question answers | Existing structured records and dashboard filter/benchmark functions can supply evidence for later questions. | No finalized Competency Questions, answer set, answer-correctness harness, or Ground Truth exists in tracked project files. Define and freeze these before claiming before/after answer improvement; this step does not invent them. |

## 9. Open Questions Requiring Human Review

1. Can the original research HTML and raw ATS descriptions/pay payloads be recovered for the stored observation times? If not, approve a prospective evaluation corpus with a clearly stated historical limitation.
2. Which curated relevance and salary assertions can a reviewer substantiate from original evidence, especially `KE-007`, the sole currently benchmark-eligible reference? What were the actual source-review dates versus import dates?
3. Do the two `D8EA0BA357` references describe one requisition, and which geography applies? Do recruiter/client and `duplicateGroup` overlaps represent separate jobs?
4. How should legacy rows without decisions and jobs that cease matching current rules be interpreted for evaluation? Missing normalized candidates cannot by themselves establish source closure.
5. What are the human definitions of relevant KE work, salary eligibility/comparability, and resolved review outcomes? Who labels, adjudicates disagreements, and handles insufficient evidence?
6. Can maintainers provide historical workflow/deployment evidence and review outcomes separately from stored metadata? The repository snapshot does not establish current hosting health or remote execution history.

Step 0.1 ends here. Step 0.2 requires approval before freezing the baseline or beginning labeling/modeling. This audit changes no production functionality, data, configuration, workflow, or existing Knowledge Engineering documentation.

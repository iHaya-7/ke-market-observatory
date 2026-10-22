# Approved filters — local development implementation

This change reuses `web/app.js`, the existing Arabic/English interface, cards, table, source dialogs, comparison tray and responsive CSS. It changes presentation gates, not collection/classification rules. `scripts/preview_filters.py` reuses the existing builder in a temporary checkout and writes **only** `learning-local/approved-filters-preview/`, which is already ignored. The normal `public/index.html`, published JSON, collector, frozen comparison inputs and all Knowledge Engineering stage artifacts remain untouched. No evaluation directory is read or imported by this feature.

## Display rules

- International default: Knowledge Engineer and its seniority variants, after documented responsibility verification. Junior/entry-level, mid-level, Senior/Sr., Lead, Principal, Staff, Associate, numeric Roman levels and the `(IC)` suffix are recognized as title variants. This is a view grouping, never evidence of KE relevance or career level. Composite titles such as `AI Data & Knowledge Engineer` do not silently enter the default scope.
- Ontology Engineer, Knowledge Graph Engineer and Semantic Web Engineer have individual optional views. A reviewed occupational assignment can identify a specialization even with a composite title. Other verified specializations each get a named view. There is no all-occupations benchmark or pooled “Other” benchmark.
- A default Knowledge Engineer benchmark still requires that advertised title group. A different title assigned general KE responsibilities does not silently widen it. It can belong to Saudi responsibility-based opportunities, or an explicitly reviewed named specialization internationally.
- Headline count/floors/ceilings and overview chart require confirmed relevant work **and**, independently, verified attributable eligible employer base pay. The defensive statistics/graph functions also filter the selected occupation. Verified base pay for an unrelated role is still excluded. Country, reviewed pay market, recorded seniority/basis, original currency/period, source dates, restrictions and evidence remain available. Monthly conversion is a display calculation, not a comparability assessment.
- A zero sample displays dashes and an honest empty message. Samples of one through four display a small-reference warning. This is a display caution, not a statistical reporting gate or accuracy metric. Every sample retains a comparability warning; no like-for-like or market-wide claim follows from a larger count.
- Saudi default: **All KE opportunities**, comprising title/seniority variants, explicit specializations, and all other titles with verified substantive KE duties. No salary is required. Optional category/city/level/listing filters remain available. Existing archive handling is preserved: archived/absent records require the archive toggle or archived-status selection. The default never filters Saudi roles for salary or exact title.
- Unknown/insufficient responsibility evidence is rendered in a separate pending-verification section, outside confirmed cards/counts and headline pay. Clearly negative reviewed roles and existing excluded/rejected records are omitted. Pending references may include legacy saved sources of other occupations; that section explicitly does not widen the benchmark or establish open vacancies. It is not a write to the application's actual review queue.

## Optional review data contract

Existing schemaVersion 2 records continue to load. Existing `relevance`, `family`, `exactTitle`, `roleDecision`, `reviewRequired`, parser pay flags and keyword summaries retain their raw meanings; they are **not** upgraded into responsibility verification. No production JSON is edited by this implementation.

Two optional record properties describe separately documented source reviews. These are presentation inputs, not human evaluation Ground Truth columns. The frontend checks completeness/consistency of the supplied review envelope; it cannot authenticate a reviewer, inspect an upstream page, verify that a quote really resolves, or determine substantive duties from text. A trusted review/publication process must establish those facts before deployment. Setting a field to `verified` does not create that process.

Both `keReview` and `salaryReview` use:

| Field | Contract |
| --- | --- |
| `status` | `verified` for a completed source review; draft/missing data stays unresolved. |
| `origin` | `human`. AI or unknown origin cannot promote a record through these gates. This is authorship metadata, not a guarantee of independent blinded labeling. |
| `reviewer` | Nonempty responsible reviewer identifier. |
| `reviewedAtUtc` | Parseable UTC timestamp ending in `Z` or `+00:00`. |
| `rationale` | Explanation of the scoped judgment, not an inferred keyword match. |
| `evidence` | Nonempty array; every item has HTTP(S) `sourceUrl`, nonempty precise `locator`, and original `quote`. These strings are escaped before display. |
| `outcome` | For `keReview`: Relevant / Not relevant / Insufficient Evidence. For salary: Eligible / Ineligible / Insufficient Evidence. Only Relevant and Eligible respectively enable confirmed roles and headline pay. |

`keReview.occupation`, when supplied, uses `knowledge-engineer`, `ontology-engineer`, `knowledge-graph-engineer`, `semantic-web-engineer` or `other`. `other` additionally requires a specific nonempty `specialization` label; separate labels create separate views. When an assignment is absent, strictly matching title variants can group already-relevant roles into the named views. This is title-based navigation only. An ambiguous/composite title with no reviewed assignment cannot enter an international occupational benchmark. It may still be a confirmed Saudi responsibility-based opportunity. No specialization is inferred from a vendor, incidental word or old machine category.

For headline salary eligibility, `salaryReview` also needs:

| Field | Contract |
| --- | --- |
| `employerName` | Evidenced hiring-employer attribution, distinct from ATS/publisher/recruiter labels. |
| `payMarket` | Evidenced geographic scope of the actual pay band; not inferred from headquarters or remote eligibility. |
| `country` | Evidenced known country, matching the record's country. Unknown/unspecified countries cannot establish a non-Saudi benchmark. Saudi region **or** country excludes international headline pay. |
| `observation` | Object whose `salaryMin`, `salaryMax`, `currency`, `period` match the current record exactly (absent/null ceiling is permitted). A changed amount or unit invalidates an old review rather than transferring it to a different observation. |

The existing record must independently retain `evidenceType: employer`, `salaryEligible: true`, `salaryBasis: base`, `salaryBasisVerified: true`, a finite nonnegative lower amount, optional ordered upper amount, supported currency (USD/GBP/EUR/SAR), Annual/Monthly period and valid FX. These flags alone remain insufficient. Missing facts are not inferred. Gross/net status is not manufactured; original compensation wording and restrictions remain in source details. An explicit total-compensation record is labeled as recorded total pay and never included as base pay.

This envelope does not replace immutable source/capture provenance or solve author authentication, band selection, source versioning, deduplication or unique requisition identity. The publisher must bind reviews to the right original record/band and retain the underlying evidence. Existing collection/persistence was deliberately not changed, so preservation of these optional reviews through future collector refreshes needs a separately agreed integration before deployment.

Stage 7B `ai_*`, `human_*`, Codex analyses and discussion CSVs are not read. No migration script copies them to `keReview`/`salaryReview`. Reusing outcome words in a presentation envelope does not make evaluation labels production data. Verified positive reviews take precedence over old machine categories; without an eligible envelope, missing review stays unresolved, and existing explicit excluded/rejected records remain excluded.

## Local preview and checks

From the repository root on this Windows installation:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -X utf8 scripts/preview_filters.py --serve
```

Open `http://127.0.0.1:8765/`. Ctrl+C stops the server. Without `--serve`, it only builds; `learning-local/approved-filters-preview/index.html` also works offline. No refresh/collector/deployment command is run. The preview marks itself as local, bypasses data caches and makes no live data-refresh requests; the separate source-snapshot JSON is copied byte-for-byte from `public/data/market.json`.

```powershell
node --check web/app.js
node --test tests/test_frontend_filters.js
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -X utf8 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Frontend tests execute the actual app code in a small DOM harness with clearly synthetic records. They exercise both defaults, seniority/title boundaries, single-scope statistics, named specializations, confirmed Saudi roles without pay, negative/unresolved/AI-origin cases, independent pay eligibility, stale observations, invalid units, safe evidence rendering, archives, reset events, export provenance and both UI languages. Synthetic records are never injected into the real-data preview. The isolated preview test checks that generated data exactly equals the real input snapshot and publication files are unchanged.

## Current data and deployment gap

The inspected public snapshot contains 26 records: 18 non-Saudi references and 8 Saudi saved references (2 Saudi records are archived). It has legacy summaries/categories and one legacy base-eligibility flag, but no `keReview` or `salaryReview` envelopes. Those facts do not establish confirmed KE duties, attributable reviewed pay or correct occupational scope. Accordingly the new preview shows **zero confirmed Saudi opportunities and zero headline salary observations**, while retaining saved references in the explicitly separate verification/research areas. Six Saudi pending references are visible by default; the two archived ones remain available with the archive filter. This is a data-readiness result, not a finding that Saudi KE jobs do not exist or that saved sources are irrelevant.

Before deployment: supply source-backed responsibility decisions and occupational assignments; verify employer/base basis and current band/units/pay market independently; retain exact evidence and responsible reviewer/time; decide review persistence/versioning and public/private provenance boundaries. Recorded seniority still needs source interpretation for any like-for-like comparison. No missing data is fabricated to populate the dashboard, and no Before/After improvement is claimed. The frozen experimental comparison remains a separate workflow.

# Baseline Results

These are descriptive counts from the frozen files, not accuracy measurements. No labels were created and no Ground Truth was assumed.

## Record and review counts

| Population | Count |
|---|---:|
| Curated records in frozen `data/curated.json` | 21 |
| Retained automatic records in frozen `data/auto_records.json` | 20 |
| Published records in frozen `public/data/market.json` | 26 |
| Published review-queue items | 30 |
| Manual automatic-record approvals / rejections in `data/review_decisions.json` | 0 / 0 |

Published review queue by category:

| Category | Items |
|---|---:|
| Role relevance | 13 |
| Pay basis | 11 |
| Saudi listing status | 6 |

## Stored role decisions

The retained automatic records have 7 `approved`, 7 `pending`, and 6 records with no `roleDecision` field. These missing legacy decisions remain distinct; they were not inferred or relabeled.

The curated population contains 21 records, and all 26 published rows currently carry `roleDecision: approved`. That published distribution combines curated records and automatic publication output; it is not an independent evaluation of classifier decisions. The two manual override arrays are empty.

## Salary eligibility and benchmark

Counts of stored `salaryEligible` values:

| Population | `true` | `false` | Missing |
|---|---:|---:|---:|
| Curated | 1 | 20 | 0 |
| Retained automatic | 0 | 20 | 0 |
| Published | 1 | 25 | 0 |

Applying the existing frontend `baseEligible` predicate from `web/app.js` to the frozen published records yields **1 benchmark-eligible record**. The predicate requires a non-Saudi record, non-pending role decision, employer evidence, explicitly eligible and verified base pay, a numeric minimum, a supported annual/monthly period, and a finite FX rate. This is an implementation count, not evidence that the salary is accurate, comparable, representative, or currently available.

## Evidence field coverage

Counts below are for the 26 published records. “Nonempty” excludes null, empty strings, and empty arrays; every listed field key is present on all 26 records. This is field coverage only, not a judgment that evidence supports the associated claim.

| Field | Nonempty records / 26 |
|---|---:|
| `sourceUrl` | 26 |
| `extraUrl` | 8 |
| `sourceLabel` | 26 |
| `sourceId` | 7 |
| `sourceJobId` | 5 |
| `evidenceType` | 26 |
| `evidenceMethod` | 26 |
| `origin` | 26 |
| `evidenceDate` | 24 |
| `salaryVerifiedAt` | 13 |
| `postedAt` | 3 |
| `firstSeenAt` | 7 |
| `lastSeenAt` | 7 |
| `listingStatus` | 26 |
| `statusNote` | 26 |

A URL or populated evidence field does not independently establish that the cited source is authentic, accessible, contemporaneous, or supports the record's salary, role, or status. No independent source-support review was performed.

## Evaluation limits

- Excluded job postings and complete historical job descriptions are not retained. Historical recall cannot be reconstructed from these retained records.
- Current machine approvals and curated flags are not independent Ground Truth. The existing review-decision arrays are empty and do not contain reviewer, rationale, date, or adjudication history.
- The retained data does not preserve a complete original ATS salary payload or source passage for every observation. Salary eligibility accuracy and salary comparability correctness therefore cannot be established from these files alone.
- Queue counts describe the current backlog only. Resolutions, reviewer outcomes, and the correctness of prior queue handling are not recorded.
- Evidence coverage measures populated fields, not verified traceability or claim support.
- No precision, recall, F1, salary accuracy, or Competency Question answer accuracy is calculated. These are **Not measurable from current snapshot** without independent labels and a defined evaluation corpus.
- The snapshot's `manifest.json` records the published `dataVersion`, collection timestamps, source statuses, full FX metadata, and whether embedded dashboard data matches the published JSON. Stored status and timestamps are not live-source verification.

## Evaluation integrity requirements

The historical excluded candidates and original full descriptions are absent and must not be recreated from inference. A future evaluation requires a fixed corpus containing original descriptions, relevant excluded candidates, preserved salary evidence, and independently reviewed labels. Use the exact same corpus, labels, and evaluation criteria for both Before and After. Hold FX rates and assumptions constant when isolating changes in salary eligibility or comparability; evaluate FX changes separately.

## Recommended Step 0.2 baseline use

Preserve this snapshot unchanged as the reference. Before any later comparison, freeze and document the evaluation corpus, inclusion and eligibility criteria, label definitions, independent review and adjudication process, time/status rules, and the exact FX object. Keep curated, automatic, published, and review-queue populations separate, and report missing legacy decisions rather than filling them in. Do not treat current counts as quality scores.

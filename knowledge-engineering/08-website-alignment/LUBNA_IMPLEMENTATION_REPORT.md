# Lubna workspace — approved website alignment

22 October 2026. Local implementation and verification only; no deployment, collection, evaluation scoring, commit or push.

## Workspace and implementation

Git was clean at entry. Most requested functionality already existed in this checkout, including evidence-aware international and Saudi filters, bilingual copy, the optional review contract, synthetic frontend tests and an isolated preview builder. It was inspected and reused rather than replaced. Haya's latest checkout was not fetched or inspected, so functional readiness here does not assert byte-for-byte parity with her implementation. No existing local conflict was found.

Reviewed `web/app.js`, `web/app.css`, `web/template.html`, `web/FILTER_CONTRACT.md`, `scripts/build_site.py`, `scripts/preview_filters.py`, frontend/build/collector regression tests, the public schemaVersion 2 snapshot, Stage 1 scope and Stage 3 occupational taxonomy. No private evaluation evidence or reviewer files were needed or opened.

Small changes made in this task:

- Recognize Computational Ontologist / Ontologist seniority variants in the separate ontology specialization, only after a documented positive responsibility review. This follows the taxonomy's computational alternative-label meaning and does not alter the taxonomy.
- Show research-range amounts with their original currency and period instead of an unlabeled converted monthly amount.
- Correct Arabic and English source/review instructions: automatic classification or legacy approval alone does not establish confirmed responsibility evidence or independently verified salary eligibility.
- Add regression tests for these aliases, original pay display, and actual category-change events/counts in both languages.

No CSS, template, font or footer redesign was necessary. IBM Plex Sans Arabic, responsive rules and Haya/Lubna credits remain intact.

## International benchmark

The default is Knowledge Engineer and genuine seniority variants. Responsibility verification is separate from title grouping. Ontology Engineer (including verified computational Ontologist aliases), Knowledge Graph Engineer and Semantic Web Engineer each have optional separate views; they are not pooled into the default benchmark. Reviewed additional specialties remain separately named views.

Headline observations require confirmed relevant responsibilities, matching occupational scope, non-Saudi geography, and a complete independently documented eligible employer base-pay review. The review must retain employer attribution, pay market, country and an observation matching the original amount, currency and period. Existing base-pay policy flags are additionally required; flags alone are insufficient. Missing units, market or attribution are not guessed; equity/bonus/total pay is not added to base pay. A reviewed Eligible outcome must establish band applicability in its source evidence and rationale; the frontend cannot independently decide that semantic question.

Eligibility, occupational relevance and comparability remain distinct. Conversion uses the supplied snapshot FX rates for display; no rates were refreshed. Original amounts/units and source details remain accessible. No median, average or representative-market estimate is introduced. Zero observations produce an honest empty state; 1–4 observations produce a small-reference warning. The numeric threshold is a presentation caution, not a statistical sufficiency claim. Even larger sets retain the comparability warning.

International salary-undisclosed references can be displayed by clearing the existing Disclosed salary only filter, when their responsibility and occupational scope are confirmed. They never contribute to salary statistics. Unresolved records remain separate from confirmed results.

## Saudi opportunities

All KE opportunities is the default category: KE title variants, explicit KE specializations, and other advertised titles with verified substantive representation responsibilities. Original titles remain intact. Salary disclosure and a literal Knowledge Engineer title are not required. Optional category, city, level and listing-status filters remain available; existing archive handling is preserved.

Confirmed cards show responsibility passages, source links, locators and review rationale. Unresolved relevance is presented in a separate pending-verification section, outside confirmed counts. Clearly unrelated records remain excluded. A generic Data Engineer or incidental graph mention is not automatically classified as a specialist. An absent review stays unresolved rather than becoming a negative judgment.

## Current data limits and readiness

The current public snapshot has 26 records: 18 non-Saudi and 8 Saudi. It contains zero `keReview` envelopes and zero structured `salaryReview` envelopes satisfying the new presentation contract. Therefore the real-data preview correctly has **0 headline salary observations and 0 confirmed Saudi opportunities**. Six Saudi saved references appear in the default pending section; two archived references remain accessible through archive controls. This is not evidence that no Saudi KE jobs exist.

Source-backed review inputs are still needed to populate confirmed results. The website checks review completeness and field consistency; it cannot authenticate reviewers, resolve source passages externally, determine semantic correctness or prove band applicability. No synthetic fixture or Development judgment was imported into market data.

The existing collector was deliberately unchanged. Preservation/versioning of the optional review inputs across future collection refreshes remains an integration dependency before deployment. The local implementation is ready for Haya and Lubna to compare functional behavior, but a populated, evidence-approved live benchmark is **not yet data-ready**. This task does not claim improved precision, recall, salary accuracy or Before/After results.

## Executed verification

| Check | Result |
| --- | --- |
| `node --check web/app.js` | Passed |
| `node --test tests/test_frontend_filters.js` | 24 passed, 0 failed |
| `python -B -m unittest discover -s tests -p "test_*.py"` | 47 passed, 0 failed; rerun after edits |
| `python -B scripts/preview_filters.py` | Built real-data local preview successfully |
| Headless Microsoft Edge via local DevTools | 24 page/language/viewport combinations passed: 6 views × English/Arabic × 1440/390 px |
| Browser runtime and layout | 0 JavaScript exceptions, 0 document horizontal overflows, correct RTL/LTR, IBM Plex Sans Arabic retained |
| Preview network | 0 HTTP(S) page requests; no live dataset refresh |
| Isolated builder / preview regression | Embedded JSON equals source JSON; copied preview JSON byte-identical; publication sentinel preserved; four embedded font files and UTF-8 retained |
| `git diff --check` | Passed |
| `git check-ignore` | Preview and browser results confirmed ignored |

Frontend fixtures are synthetic test inputs only. Python collector tests use deterministic fixtures, not live collection. Initial browser startup inside the restricted environment failed; the successful headless check used the approved external browser launch with a dedicated ignored local profile. Browser results are saved at `learning-local/website-alignment-browser-results.json`. The browser was closed after verification. These checks are not an exhaustive visual or accessibility audit.

The normal dashboard builder was exercised in isolated temporary directories through the build/preview checks. `public/index.html` and `public/data/market.json` were not rewritten; the updated local preview embeds exactly the existing public data. Open the preview below to see the updated frontend, rather than the unchanged publication artifact.

## Files and Git status

Changed tracked files:

- `web/app.js`
- `web/FILTER_CONTRACT.md`
- `tests/test_frontend_filters.js`

New untracked deliverable:

- `knowledge-engineering/08-website-alignment/LUBNA_IMPLEMENTATION_REPORT.md`

Generated preview, browser profile and browser results are under ignored `learning-local/`. No Stage 0–7 artifacts, human/AI review results, source evidence, taxonomy, ontology, graph, SHACL, adapters, production salary logic, workflows or published datasets were changed. Nothing was staged, committed, pushed or deployed.

## Exact local preview

From `C:\Users\Lubna\Documents\MoMAH\ke-market-observatory`:

```powershell
python -B scripts/preview_filters.py --serve --port 8765
```

Open `http://127.0.0.1:8765/`. Use the language switch and Global salaries / Saudi Arabia navigation. Ctrl+C stops the local server. This command rebuilds only the ignored preview and does not run collectors or publish. No preview server is left running by this task.

For offline use, open `learning-local/approved-filters-preview/index.html`, already generated during verification.

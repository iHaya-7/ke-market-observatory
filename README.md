# Knowledge Engineering Market Observatory

A Knowledge Engineering market intelligence platform that brings together global salary evidence and Saudi Arabian job opportunities in a bilingual dashboard.

**[View the live dashboard](https://ihaya-7.github.io/ke-market-observatory/)**

## Start Here

- Application: [`web/`](web/) and [`scripts/`](scripts/); source configuration: [`config/sources.json`](config/sources.json).
- Data: [`data/`](data/) contains maintained inputs; [`public/`](public/) contains the generated publication snapshot. Tests are in [`tests/`](tests/).
- Knowledge Engineering: use the [stage and continuation guide](knowledge-engineering/README.md) for the actual work and its current limits.
- In this local workspace, read the [Arabic project explanation](knowledge-engineering/00-baseline/local-corpus/project-audit/PROJECT_EXPLAINED_AR.md) and [evidence audit](knowledge-engineering/00-baseline/local-corpus/project-audit/PROJECT_EVIDENCE_AUDIT.md). These protected reports and other private review materials are Git-ignored and are not included in a public clone.

Use the safe local preview below to view current frontend changes. The generated `public/index.html` can contain an older committed frontend. The [private cleanup execution log](knowledge-engineering/00-baseline/local-corpus/project-audit/CLEANUP_EXECUTION.md) records the removed files and recovery backup.

## Overview

The observatory helps Knowledge Engineering professionals, researchers, and job seekers explore compensation, role requirements, and opportunities involving ontologies, knowledge graphs, and semantic technologies. It combines curated references with automated collection from selected public applicant tracking system (ATS) feeds.

The platform keeps global compensation research separate from Saudi job tracking. Source links, evidence dates, verification labels, and review notes make it possible to assess each record before drawing conclusions about the market.

## Key Features

### Global Salary Benchmarking

- Explore international salary references by country, career level, evidence type, company, role, or skill.
- Compare supported annual and monthly salaries as nominal monthly Saudi riyal (SAR) equivalents while retaining original amounts, currencies, and pay periods; gross/net status is not inferred.
- View salary charts and summary statistics based only on eligible employer disclosures explicitly identified as verified base salary.
- Distinguish base salary, total compensation, secondary evidence, and platform estimates.
- Compare selected roles side by side, including experience requirements, role scope, and source limitations.

Currency conversion supports USD, GBP, EUR, and SAR. The collector refreshes GBP and EUR reference rates through [Frankfurter](https://frankfurter.dev/) and cross-converts using the configured USD/SAR assumption. Rate dates and calculation details are visible in the dashboard.

### Saudi Job Tracking

- Maintain a separate register of Saudi postings related to Knowledge Engineering, applied knowledge graphs and AI, and adjacent metadata or semantic work.
- Search and filter by location, KE category, career level and listing status. The default includes all responsibility-verified KE opportunities, without requiring an exact KE title or salary.
- Inspect source links, detected skills, experience requirements, available salary evidence, publication dates, and observation dates.
- Distinguish recently confirmed feed listings from saved references, records needing rechecking, and archived or absent postings.

For automatically collected records, Saudi classification uses the posting's location fields rather than mentions of Saudi Arabia elsewhere in the description. A recently observed feed listing is evidence of source availability, not a guarantee that applications remain open.

### Job Relevance Validation

The collector applies explicit title and description rules. It accepts core titles such as Knowledge Engineer, Ontology Engineer, and Knowledge Graph Engineer. Related technical roles require implementation or modeling language alongside complementary semantic technology evidence. Recruiting, HR, sales, and marketing titles are excluded even when their descriptions contain relevant keywords.

Uncertain adjacent roles are staged for human review and excluded from published job totals and salary metrics until approved. These rules support screening; they do not replace assessment of the original posting.

### Salary Verification

Structured salary ranges are checked for supported currency, pay period, valid amounts, and explicit base-versus-total compensation wording. Headline salary results additionally require separate source-backed `keReview` and `salaryReview` records and the selected occupational scope, as defined in the [filter contract](web/FILTER_CONTRACT.md). Employer/base/eligibility flags alone are insufficient.

Verified total compensation is displayed separately. Unknown pay basis, multiple pay bands, and potential free-text salary evidence require review. Missing or ambiguous amounts are not replaced with inferred salaries, and an automated verification label reflects the parser's evidence rules rather than an independent employer audit.

### Experience Classification

The collector assigns **Junior**, **Mid**, **Senior**, or **Not specified** using explicit seniority titles and supported experience patterns. It preserves the classification basis and any extracted year requirements. A title can establish seniority without supplying a numeric experience requirement; missing years are never treated as evidence of a junior role.

A dedicated Junior evidence view separates available entry-level references from broader salary data. Curated records retain their documented experience evidence and analyst notes.

### Review Queue

The Review Queue surfaces uncertain role relevance, unverified employer pay basis, and Saudi listings needing a current status check. Each item links to its source and explains why review is needed.

The public dashboard is read-only. Review decisions and evidence corrections are maintained in repository JSON files; approving a role does not independently verify its salary or vacancy status.

### Bilingual Arabic and English Support

The interface includes an Arabic/English language switch, right-to-left layout for Arabic, translated navigation and interface labels, and Arabic summaries for curated references. Automatically collected records use an Arabic skills summary rather than a full translation of the posting. Original job titles and source links are retained, and the language preference is saved locally in the browser.

### Data Access and Portability

- Export records as CSV or download the published dataset as JSON.
- Save a self-contained HTML snapshot for offline viewing.
- Print dashboard views with a source appendix.
- Reload the published dataset through **Refresh data**, automatic polling every five minutes while the tab is visible, and refreshes when returning to the tab or reconnecting.

## Collection Coverage and Limitations

**Automatic collection is limited to configured public ATS boards. It does not comprehensively monitor LinkedIn or the wider job market.** LinkedIn URLs in curated records are saved research references, not evidence of an automated LinkedIn search or continuous monitoring.

The current source configuration includes:

| Employer or recruiter | ATS integration |
| --- | --- |
| Samba TV | Lever |
| Nearform | Greenhouse |
| Tamara | Greenhouse |
| Sapience AI | Greenhouse |
| Envision Employment Solutions | Workable |
| Robusta / RTG | Workable |

Additional boards can be configured in [`config/sources.json`](config/sources.json) using a supported ATS type and public board identifier. Source availability, API changes, incomplete descriptions, and collection limits can affect coverage. The collector does not use LinkedIn credentials, browser scraping, private recruiting systems, or access-control bypasses.

Other interpretation limits include:

- Historical and archived references may remain available for research; tracked posting counts are not counts of confirmed open vacancies.
- Recruiter and employer listings may overlap. Canonical URLs and stable source IDs support deduplication, but similar descriptions do not establish a unique requisition or reveal an undisclosed client.
- Rule-based relevance and experience extraction can misinterpret context. Original postings remain the primary evidence.
- Free-text salary evidence and platform estimates are not continuously refreshed or automatically converted into verified base pay.
- International salary equivalents are nominal conversions; gross/net status is not inferred. They do not represent Saudi market salaries, take-home pay, purchasing-power adjustments, or guaranteed offers.
- The selected references are not a representative market sample. The dashboard does not calculate a market-wide average or infer a junior salary band from missing evidence.

## Data Pipeline and Provenance

1. `scripts/refresh.py` reads the source configuration, curated records, previous collection history, and review decisions.
2. Public ATS records are collected, normalized, classified, and merged with existing evidence. Unreviewed candidates remain outside the published record set.
3. The collector writes persistent automatic records to `data/auto_records.json` and the dashboard dataset to `public/data/market.json`.
4. `scripts/build_site.py` embeds the dataset, styles, and JavaScript into `public/index.html`.
5. GitHub Actions publishes the `public/` directory to GitHub Pages.

Failed source checks retain previously collected records and their observation dates. Missing-posting checks advance only after complete successful feed checks; two successful absences mark a record as **Not in latest feed**, which is not a confirmed closure. Failed exchange-rate updates retain the previous rates.

The dataset separates source publication dates (`postedAt`), collector observations (`firstSeenAt`, `lastSeenAt`), salary evidence dates (`evidenceDate`, `salaryVerifiedAt`), and source health (`lastAttemptAt`, `lastSuccessAt`). Browser refreshes do not renew source evidence dates. The dashboard exposes collection health and uses a configured 48-hour freshness threshold.

**Refresh data reloads the published snapshot; it does not start collection.** Saved and exported copies are independent snapshots.

## Technology Stack

| Layer | Technology |
| --- | --- |
| Dashboard | HTML5, CSS3, and vanilla JavaScript; responsive layout and Arabic RTL support |
| Collection and validation | Python 3.12 standard library, including `urllib`, `json`, `re`, and concurrent source fetching |
| Data storage | Repository-managed JSON for curated evidence, collection history, review decisions, and published data |
| Source integrations | Lever, Greenhouse, and Workable public job endpoints; Frankfurter exchange rates |
| Build | Python script generating a self-contained HTML dashboard |
| Automation and hosting | GitHub Actions and GitHub Pages |
| Verification | Python `unittest`, dataset validation, and Node.js syntax checking |

No third-party Python packages, frontend build framework, database server, or job-search API keys are required for the Observatory product. Separate experimental KE scripts have their own local dependency requirements. The dashboard uses no external JavaScript packages, remote fonts, or analytics.

## Repository Structure

```text
.github/workflows/
    refresh-and-deploy.yml  # Collection, validation, build, and Pages deployment
config/
    sources.json           # Public ATS boards and collection settings
data/
    curated.json           # Curated references and evidence metadata
    auto_records.json      # Persistent automatic collection history
    review_decisions.json  # Approved and rejected automatic record IDs
scripts/
    refresh.py             # Collection, classification, merging, and validation
    build_site.py          # Self-contained HTML generation
    preview_filters.py     # Isolated local preview; does not overwrite public/
web/
    template.html          # Dashboard layout
    app.css                # Responsive styles and RTL support
    app.js                 # Views, filters, translations, exports, and polling
public/
    index.html             # Generated dashboard
    data/market.json       # Published dataset
tests/
    test_*.py              # Collector, isolated build and preview tests
    test_frontend_filters.js # Offline frontend tests
knowledge-engineering/
    README.md              # Stage map, evidence limits and continuation point
README.md
```

## Knowledge Engineering Workspace

The [Knowledge Engineering workspace guide](knowledge-engineering/README.md) maps the frozen baseline, scope/CQs, vocabulary, SKOS taxonomy, ontology, three-case graph experiment, SHACL validation, Stage 7A triage pilot and local Stage 7B calibration. The graph is separate from the production data flow. Some private execution artifacts are missing from this checkout; semantic approval and a valid Before/After evaluation remain incomplete. Resume with the documented Development calibration checkpoint, not another implementation stage.

## Local Setup

### Prerequisites

- Git to clone the repository.
- Python 3.12, matching the GitHub Actions environment.
- A modern browser.
- Node.js for the JavaScript syntax check; it is not required to serve the dashboard.
- Network access when collecting public feeds or refreshing exchange rates.

### Safe Local Preview

```bash
python -B scripts/preview_filters.py --serve
```

If the `python` alias does not work on this Windows installation:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -X utf8 -B scripts/preview_filters.py --serve
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). The command recreates the disposable ignored `learning-local/approved-filters-preview/` from current frontend source and existing public JSON. It uses the builder in isolation, makes no collection or live dataset-refresh requests, and does not overwrite `public/`. Ctrl+C stops the server. Opening `public/index.html` directly instead shows the retained publication snapshot. See the [filter contract](web/FILTER_CONTRACT.md) for evidence gates; machine categories and AI-assisted judgments do not establish production verification.

### Offline Development Workflow (Windows)

From this repository's root, process the saved nine-candidate Development batch and open the existing Observatory preview:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run_observatory.ps1 -SourceRoot . -Results learning-local/saudi-s1-fix-20261029/results/market-eligibility.json -Serve
```

Open [http://127.0.0.1:8766/](http://127.0.0.1:8766/). Ctrl+C stops the server. The launcher prints the exact preview and results directory; the HTML also works offline. Each run creates a fresh ignored `learning-local/observatory-*` directory. An explicit `-Output` must be new; previous results and source captures are never replaced.

This workflow requires the separately transferred private Development fixtures, Python 3.13, and the pinned packages in `knowledge-engineering/06-validation/requirements-local.txt`. The launcher checks existing dependency directories (`KE_LOCAL_DEPS`, `learning-local/stage6-deps`, then `learning-local/development-v2-deps/Lib/site-packages`) and installs nothing. Use `-PythonExecutable` or `-Dependencies` to select another existing compatible environment; relative dependency paths resolve from the repository root. `-SourceRoot` may identify a separate private fixture checkout, while implementation and output remain in this checkout.

The generated preview shows independent market, occupational and salary assessments, source quotations and validation details. Per-record failures remain isolated. Experimental classifications are machine proposals, and unsupported salary dimensions remain unresolved. Local results do not approve records for production or update published market data. No live source collection runs.

### Refresh Source Data

```bash
python scripts/refresh.py
python scripts/build_site.py
```

Collection updates `data/auto_records.json` and `public/data/market.json`; building updates `public/index.html`. Inspect source statuses and `meta.lastRunSummary` to assess collection success: a completed process can still report failed feeds while retaining previous data.

### Run Checks

```bash
python -B -m unittest discover -s tests -p 'test_*.py' -v
python -B scripts/refresh.py --validate-only
node --check web/app.js
node --test tests/test_frontend_filters.js
```

The Python tests use deterministic fixtures and temporary directories without external network requests. They cover parsing, relevance screening, salary eligibility, experience classification, review handling, and preservation of data after collection failures. Live feed health must be assessed separately.

## GitHub Pages Deployment

The repository includes the [`Refresh and Deploy KE Observatory`](.github/workflows/refresh-and-deploy.yml) workflow.

1. In the repository's **Settings > Pages > Build and deployment**, select **GitHub Actions** as the source.
2. Ensure repository policies allow GitHub Actions to commit generated data to `main` and deploy to Pages. The collection job requests `contents: write`; deployment requests `pages: write` and `id-token: write`.
3. Open **Actions > Refresh and Deploy KE Observatory > Run workflow** and select `main`.
4. Check the collection and deployment jobs, then open the [live dashboard](https://ihaya-7.github.io/ke-market-observatory/).

The workflow runs tests and syntax checks, collects sources and exchange rates, validates data, builds the dashboard, commits generated changes, and deploys `public/`. It is configured for daily collection at **05:17 UTC / 08:17 Asia/Riyadh**, manual dispatch, and pushes to `main` affecting the configured source, script, test, curated-data, or workflow paths. Scheduled execution is best effort.

Changes only to `README.md` or `data/review_decisions.json` do not match the current push filters. Run the workflow manually to publish review-decision changes without waiting for the scheduled run. Review collection results in the dashboard's **Sources & updates** section and the workflow logs.

## Maintaining Evidence and Reviews

- Update curated records in [`data/curated.json`](data/curated.json), retaining the original source URL, evidence date, and verification notes.
- After inspecting an automatic candidate's original posting, add its `AUTO-*` ID to either `approved` or `rejected` in [`data/review_decisions.json`](data/review_decisions.json), never both. Approval controls role inclusion; salary and listing verification remain separate checks.
- For confirmed employer base pay, record `salaryBasis: "base"`, `salaryBasisVerified: true`, and `salaryEligible: true`. For verified total compensation, use `salaryBasis: "total"`, `salaryBasisVerified: true`, and `salaryEligible: false`.
- These flags do not replace the separate responsibility/pay reviews required by the [filter contract](web/FILTER_CONTRACT.md). Review persistence and source-version binding across automatic refreshes remain an integration dependency; do not copy evaluation labels into production review fields.
- Rebuild and publish after updating evidence. `public/data/market.json` and `public/index.html` are generated outputs; permanent corrections belong in the source data or collection logic.

## Credits

**Developed by Knowledge Engineers Haya & Lubna**

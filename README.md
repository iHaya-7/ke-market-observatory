# Knowledge Engineering Market Observatory

A Knowledge Engineering market intelligence platform that brings together global salary evidence and Saudi Arabian job opportunities in a bilingual dashboard.

**[View the live dashboard](https://ihaya-7.github.io/ke-market-observatory/)**

## Overview

The observatory helps Knowledge Engineering professionals, researchers, and job seekers explore compensation, role requirements, and opportunities involving ontologies, knowledge graphs, and semantic technologies. It combines curated references with automated collection from selected public applicant tracking system (ATS) feeds.

The platform keeps global compensation research separate from Saudi job tracking. Source links, evidence dates, verification labels, and review notes make it possible to assess each record before drawing conclusions about the market.

## Key Features

### Global Salary Benchmarking

- Explore international salary references by country, career level, evidence type, company, role, or skill.
- Compare supported annual and monthly salaries as gross monthly Saudi riyal (SAR) equivalents while retaining original amounts, currencies, and pay periods.
- View salary charts and summary statistics based only on eligible employer disclosures explicitly identified as verified base salary.
- Distinguish base salary, total compensation, secondary evidence, and platform estimates.
- Compare selected roles side by side, including experience requirements, role scope, and source limitations.

Currency conversion supports USD, GBP, EUR, and SAR. The collector refreshes GBP and EUR reference rates through [Frankfurter](https://frankfurter.dev/) and cross-converts using the configured USD/SAR assumption. Rate dates and calculation details are visible in the dashboard.

### Saudi Job Tracking

- Maintain a separate register of Saudi postings related to Knowledge Engineering, applied knowledge graphs and AI, and adjacent metadata or semantic work.
- Search and filter by location, relevance, career level, listing status, and exact Knowledge Engineer title.
- Inspect source links, detected skills, experience requirements, available salary evidence, publication dates, and observation dates.
- Distinguish recently confirmed feed listings from saved references, records needing rechecking, and archived or absent postings.

For automatically collected records, Saudi classification uses the posting's location fields rather than mentions of Saudi Arabia elsewhere in the description. A recently observed feed listing is evidence of source availability, not a guarantee that applications remain open.

### Job Relevance Validation

The collector applies explicit title and description rules. It accepts core titles such as Knowledge Engineer, Ontology Engineer, and Knowledge Graph Engineer. Related technical roles require implementation or modeling language alongside complementary semantic technology evidence. Recruiting, HR, sales, and marketing titles are excluded even when their descriptions contain relevant keywords.

Uncertain adjacent roles are staged for human review and excluded from published job totals and salary metrics until approved. These rules support screening; they do not replace assessment of the original posting.

### Salary Verification

Structured salary ranges are checked for supported currency, pay period, valid amounts, and explicit base-versus-total compensation wording. Only employer records with `salaryBasis: "base"`, `salaryBasisVerified: true`, and `salaryEligible: true` can enter the global base-salary benchmark.

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
- International salary equivalents are nominal, gross comparisons. They do not represent Saudi market salaries, take-home pay, purchasing-power adjustments, or guaranteed offers.
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

No third-party Python packages, frontend build framework, database server, or job-search API keys are required. The dashboard uses no external JavaScript packages, remote fonts, or analytics.

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
web/
    template.html          # Dashboard layout
    app.css                # Responsive styles and RTL support
    app.js                 # Views, filters, translations, exports, and polling
public/
    index.html             # Generated dashboard
    data/market.json       # Published dataset
tests/
    test_refresh.py        # Adapter, classification, validation, and preservation tests
README.md
```

## Local Setup

### Prerequisites

- Git to clone the repository.
- Python 3.12, matching the GitHub Actions environment.
- A modern browser.
- Node.js for the JavaScript syntax check; it is not required to serve the dashboard.
- Network access when collecting public feeds or refreshing exchange rates.

### Preview the Dashboard

```bash
git clone https://github.com/iHaya-7/ke-market-observatory.git
cd ke-market-observatory
python scripts/refresh.py --validate-only
python scripts/build_site.py
python -m http.server 8000 --directory public
```

Open [http://localhost:8000](http://localhost:8000). This builds from the existing published JSON without collecting new jobs. Opening `public/index.html` directly also displays its embedded offline snapshot.

### Refresh Source Data

```bash
python scripts/refresh.py
python scripts/build_site.py
```

Collection updates `data/auto_records.json` and `public/data/market.json`; building updates `public/index.html`. Inspect source statuses and `meta.lastRunSummary` to assess collection success: a completed process can still report failed feeds while retaining previous data.

### Run Checks

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python scripts/refresh.py --validate-only
node --check web/app.js
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
- Rebuild and publish after updating evidence. `public/data/market.json` and `public/index.html` are generated outputs; permanent corrections belong in the source data or collection logic.

## Credits

**Developed by Knowledge Engineers Haya & Lubna**

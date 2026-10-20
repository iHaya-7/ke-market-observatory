# Knowledge Engineering - Market Observatory

A deployable online dashboard combining global salary evidence and a separate **Knowledge Engineering in Saudi Arabia** opportunity register.

**Delivery status:** implemented and packaged, **not deployed**. No public URL, scheduled cloud job, external account or credential was created. Network access to the source APIs was unavailable in the build environment, so adapters were tested against representative fixtures, not live feeds. The first hosted workflow run is the live integration check.

## Start here: publish a fixed URL

Use a permitted personal or organizational GitHub account. This starter uses **GitHub Pages + GitHub Actions**. It contains public job information only and requires no job-search API key.

1. Create a repository named `ke-market-observatory`, with default branch **main**. Choose **Public** for the simple GitHub Free Pages route. A public repository and Pages site are visible to others: do not add internal notes, personal contact data or confidential compensation details.
2. Upload the **contents** of this project, not the outer folder and not just `public/index.html`. Include the hidden `.github/workflows/refresh-and-deploy.yml` file. On Windows, display hidden items or create this path explicitly using **Add file > Create new file**. GitHub does not unpack a ZIP uploaded as one file.
3. Under **Settings > Pages > Build and deployment**, set **Source = GitHub Actions**.
4. If your account permits it, go to **Settings > Actions > General > Workflow permissions** and allow the workflow to write repository contents. Its own job-level permissions are restricted to the steps that need them. A branch policy may still block its history commit; ask the repository owner rather than weakening organization controls without approval.
5. Open **Actions > Refresh and deploy KE Observatory > Run workflow** and choose **main**. A push may have started the first run before Pages was enabled; simply rerun after configuration.
6. Open the actual URL shown in **Settings > Pages** or the successful `github-pages` deployment. The expected shape is `https://YOUR-USERNAME.github.io/ke-market-observatory/` (an example, not an activated URL).

After activation, the workflow attempts collection daily at about **08:17 Asia/Riyadh**. GitHub schedules are best effort; delays and missed runs are possible. Public-repository schedules may be disabled after 60 days of inactivity. Check **Sources & updates** and the workflow logs; the dashboard marks stale data after 48 hours.

If a work GitHub account, Pages or Actions is restricted, use only an account and deployment route your organization permits. This package does not bypass those controls. For private sharing, use an approved authenticated host rather than assuming a private repository makes the Pages site private.

## What automatically changes

| Data | Behavior after deployment |
|---|---|
| New matching posts on configured boards | Collected into the shared dataset automatically. Titles, location, detected skills and source links are preserved. |
| Existing posts still present | Source-observation dates and listing status update after a successful complete fetch. |
| Explicit supported structured salaries | Retained with currency and period. Only explicit base pay is eligible for employer benchmark statistics. |
| Ambiguous salaries / multiple pay bands | Routed to review; never filled with invented amounts. |
| GBP/EUR FX | Frankfurter reference rates are cross-converted through the configured USD/SAR assumption. Source rate date is preserved, including weekends. |
| Saved manual references | Historical salary evidence remains. If the same canonical URL appears in a feed, status and supported salary changes can be updated. |
| Open browser | Polls the same-origin `data/market.json` every five minutes, and when returning to the tab. |

**Refresh data** reloads the published snapshot. It does **not** run the job collector or scrape LinkedIn.

## What does not happen automatically

- There is no exhaustive web or LinkedIn search. The default coverage is six configured employer/recruiter boards.
- LinkedIn login sessions, private recruiting systems, blocked pages and site access controls are not bypassed.
- A hidden client name is not inferred from a similar description. Recruiter and employer listings may overlap; counts are posting counts, not unique requisitions.
- Years not specified is not converted to Junior. A skill-specific experience sentence still needs source context.
- Free-text salary platforms and the existing estimates are not continuously refreshed.
- There is no email notification or CV/application submission.
- The public dashboard is read-only; it does not provide a shared authenticated editor. Edits are made centrally in repository data.

## Configured sources

- Samba TV: Lever
- Nearform: Greenhouse
- Tamara: Greenhouse
- Sapience AI: Greenhouse
- Envision Employment Solutions: Workable
- Robusta / RTG: Workable

Identifiers come from public career-page URLs. Access and schema behavior must be confirmed by the first hosted collection. If a board fails, the dataset keeps last-good records and exposes the error. Additional companies can be added in `config/sources.json` using a supported ATS and a verified public board identifier.

## Data quality and provenance

The starter includes **13 imported global salary references** and **8 Saudi posting references**. Some are historic or not independently reverified; per-record labels distinguish this. Two Saudi URLs redirected away from their original jobs during research and are archived. This is a source register, not a guaranteed-open job list.

- `postedAt`: source publication date only. Not backfilled from collection time.
- `firstSeenAt`: first observation by this collector. A newly tracked label is not a newly posted claim.
- `lastSeenAt`: latest successful observation in a source feed.
- `evidenceDate` / `salaryVerifiedAt`: underlying evidence date; not reset by browser refresh or FX updates.
- `lastAttemptAt` / `lastSuccessAt`: source health, kept separate.
- `salaryEligible`: base-pay comparability flag; unknown or ambiguous amounts do not drive statistics.
- `missingChecks`: counts complete successful absences; errors do not count as absences.

Only an exact canonical URL or durable API ID is used for automated deduplication. Cross-company similarity is not proof of identical jobs. Canonicalization preserves query-based requisition IDs.

Keep the international and Saudi sections separate. A converted monthly international salary is gross nominal currency equivalence, not Saudi market pricing, take-home pay or employer total cost. No market-wide average or artificial Junior pay band is calculated.

## Editing and review

- Correct an approved reference in `data/curated.json`, commit to `main`, and let the workflow rebuild.
- Add/remove monitored employers in `config/sources.json`.
- Review ambiguous rows in the dashboard's **Sources & updates** section. To approve a pay record, copy its record into `data/curated.json`, use the same canonical `sourceUrl`, correct the fields from the source, set `salaryEligible: true` only when supported, and record an evidence date and method.
- Do not edit `public/data/market.json` as a permanent override; it is generated.
- Git commits retain the change history. Revert a bad data commit or correct the source record.
- Saved HTML and exported JSON/CSV are portable snapshots, not synchronized collaborative copies.

## Local preview and tests

Python 3.12 is sufficient for collection, validation and building; no pip packages are required.

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
node --check web/app.js
python scripts/refresh.py --validate-only
python scripts/build_site.py
python -m http.server 8000 --directory public
```

Open `http://localhost:8000`. This tests HTTP snapshot loading, but does not create a permanent website. Opening `public/index.html` directly displays the embedded offline snapshot.

To manually test public feeds from a network-enabled machine:

```bash
python scripts/refresh.py
python scripts/build_site.py
```

The collector deliberately retains data when network checks fail. Look at `sources[*].status` and `meta.lastRunSummary`, not just the process exit code, to know whether collection succeeded.

## Project layout

```
.github/workflows/refresh-and-deploy.yml   Daily collection + deployment
config/sources.json                     Public board registry
scripts/refresh.py                      Collection, normalization, safeguards
scripts/build_site.py                   Single-file HTML build
web/template.html                       Layout
web/app.css                             Responsive styles
web/app.js                              Client-side UI and polling
data/curated.json                       Approved seed/reference records
data/auto_records.json                  Persistent collected records
public/index.html                       Published dashboard
public/data/market.json                  Published shared dataset
tests/test_refresh.py                   Parser and failure-preservation tests
```

## Official implementation references

- GitHub Pages custom workflows: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- GitHub schedule behavior and inactivity: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- Lever public Postings API: https://github.com/lever/postings-api
- Greenhouse public Job Board API: https://docs.greenhouse.io/job-board.html
- Workable public jobs endpoint: https://workable.readme.io/reference/jobs-1
- Frankfurter exchange-rate API: https://frankfurter.dev/

No external fonts, analytics, remote JavaScript packages or secret keys are embedded in the dashboard. The source code is provided for modification; source job content remains the property of its respective owner.

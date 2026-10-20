# Validation report

Build date: 20 October 2026.

## Passed

- **31 deterministic Python unit tests**: API-format fixtures, relevance and geography, explicit experience, currency/period handling, Greenhouse cents, salary ambiguity, finite amount validation, canonical IDs, feed pagination, deduplication, first/last-seen preservation, and failed-feed/FX retention.
- JavaScript syntax check via `node --check web/app.js`.
- Full seed schema validation and self-contained HTML build: 21 source records.
- Chromium rendering: desktop 1480 x 1000 and mobile 390 x 844.
- Five navigation views, Saudi archive toggle, empty exact-title filter, detail dialogs, two-role comparison, keyword filters and CSV download.
- No page-level horizontal overflow in the five mobile views.
- No JavaScript page errors in the browser smoke test.
- The refresh function accepted a simulated new snapshot and retained it after a simulated transport failure. Test-only records were created in browser memory and are **not included** in the delivered dataset.

## Not verified in this environment

- Public deployment or an actual fixed website URL.
- GitHub Actions cloud execution and permissions.
- Live collection from the configured ATS APIs or the FX endpoint. Network requests were unavailable in the build environment; source identifiers are based on public source URLs, and adapters used deterministic fixtures.
- Browser HTTP navigation, which was blocked by the environment. Visual rendering used an isolated HTML document; refresh behavior was exercised using mocked responses, not by claiming a real HTTP poll succeeded.
- Continuing validity of every historical salary amount. Imported references retain their original evidence labels and dates.

## Acceptance checks after deployment

1. Confirm the actual GitHub Pages URL loads the dashboard.
2. Confirm `data/market.json` is served from the same site.
3. Check `Sources & updates` for the first successful source and FX timestamps.
4. Correct or disable any board that rejects the public endpoint; check logs before interpreting an empty source.
5. Confirm a later run updates the published dataset without changing the website URL.
6. Ensure the page's five-minute refresh reads that new dataset; the Refresh button alone does not run the collector.
7. Review uncertain salary evidence before presenting it as a management benchmark.

Tests protect parsing and preservation behavior. They are not an audit of employer salary claims, hiring status, API availability, or hosting uptime.

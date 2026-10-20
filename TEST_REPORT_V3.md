# Knowledge Engineering Market Observatory v3 — QA

- Automated unit tests: 44 passed (Python `unittest`).
- JavaScript syntax: `node --check web/app.js` passed.
- HTML packaging: `python scripts/build_site.py` passed.
- Browser smoke tests: Chromium/Playwright checked both 1440px desktop and 390px mobile.
- Language switch: English to Arabic, document `lang=ar` / `dir=rtl`, header/sidebar/footer translations.
- Functional smoke tests: Overview, Global Salaries, Saudi Arabia, Review Queue, 14 prepared review items, no page-level JS exceptions.
- Strict relevance tests: recruiter title excluded despite RDF/OWL/Neo4j mention; strong ontology/data-engineering match accepted; adjacent metadata and vague AI roles sent for review.
- Salary tests: only explicitly proven employer base pay can enter primary statistics; totals, ambiguous bases, estimate/repost distinct; unverified pay rejected from benchmark.
- Experience tests: Junior, Mid, Senior and Not specified; senior title does not fabricate years.
- Saudi status: archived, needs-recheck, and fresh feed-verified categories remain distinct.

**Important:** These are offline deterministic tests. Live job-source connectivity and successful GitHub deployment must be checked following the user upload. No claims are made that current LinkedIn postings have been manually verified open.

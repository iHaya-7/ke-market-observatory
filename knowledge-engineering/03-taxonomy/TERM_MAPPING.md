# Stage 3 — Production terminology mapping proposal

21 October 2026 · Team approval pending. Mapping statuses concern **terms**, never job relevance, evidence support, or Ground Truth.

Sources inspected: distinct `title` and `family` strings in [curated](../../data/curated.json), [automatic](../../data/auto_records.json), and [published](../../public/data/market.json) production records; `CORE_TITLE`, adjacent-title patterns, and `assess_role()` in [refresh.py](../../scripts/refresh.py). No descriptions or evaluation materials were needed. The [Stage 2 dictionary](../02-vocabulary-metadata/METADATA_DICTIONARY.md) already distinguishes these fields from role scope and human assessments.

**Exact** means the literal term matches a preferred label in this proposed scheme; it does not establish the posting's responsibilities. **Possible** means a candidate interpretation needs source evidence. **Ambiguous** means the term permits multiple meanings or is not an occupational concept. **Unmapped** means no concept is proposed within this bounded scheme, not that a job is irrelevant. These statuses are not `skos:exactMatch` or other formal mapping assertions: raw title strings are not concepts in another scheme.

| Existing terminology / location | Status | Proposed target or treatment | Reason / evidence needed |
| --- | --- | --- | --- |
| `Knowledge Engineer` — title/family | Exact (lexical) | `role:knowledge-engineer` | Verify advertised work against definition; title is not a classifier. |
| `Knowledge Graph Engineer` — title/family | Exact (lexical) | `role:knowledge-graph-engineer` | Require domain-meaning graph work, not a generic graph keyword. |
| `Ontology Engineer` — explicit title rule | Exact (lexical) | `role:ontology-engineer` | Compound retained titles are addressed below. |
| `Semantic Web Engineer` — explicit title rule | Exact (lexical) | `role:semantic-web-engineer` | Rule vocabulary supports the term; no retained-title occurrence is claimed. |
| `Ontologist` — title rule; appears within retained titles | Possible, scoped alternative | `role:ontology-engineer` | Proposed `altLabel` in computational occupational sense, not philosophical ontology. |
| `Entry Level Knowledge Engineer`, `Entry-level Knowledge Engineer`, `Senior Knowledge Engineer`, `Senior Knowledge Engineer (IC)` | Possible | `role:knowledge-engineer` | Level/employment modifiers are not new role concepts or automatic evidence of career level. Preserve original titles. |
| `AI Data & Knowledge Engineer`; family `AI + Knowledge Engineer` | Ambiguous composite | Candidate `role:knowledge-engineer` | Could combine multiple functions; inspect duties rather than treating AI/data as synonyms. |
| `Ontology Engineer-Knowledge Graph & Identity`, `Senior Ontologist - Knowledge Graph & Identity` | Possible | Candidate `role:ontology-engineer`; graph specialization only if separately substantiated | Title indicates an area, not proof of multiple role assignments. |
| `Ontology, Knowledge Graph & Semantic Layer Lead` | Ambiguous composite | Candidates ontology/graph concepts | Leadership, modeling, engineering, and governance may differ; no forced single mapping. |
| `Palantir Foundry Ontology Engineer, Junior` | Possible | Candidate `role:ontology-engineer` | A product's “ontology” name must be checked against conceptual-model duties; no vendor-specific child. |
| `Scientist/Sr Scientist - Ontology - Europe - Remote` | Possible | Candidate `role:ontology-engineer` | Research or engineering function and computational meaning require evidence. Location is not a role branch. |
| `AI/ML Data Knowledge Graph Engineer` | Possible | Candidate `role:knowledge-graph-engineer` | Compound title; verify graph representation/integration responsibilities. |
| Family `Ontology / Ontologist` | Ambiguous | Candidate `role:ontology-engineer` | Mixes an artifact/topic and an occupation; not an exact synonym. |
| `Data Governance Lead`; `Metadata / Semantic` category | Ambiguous | No direct mapping | Governance can concern policy/catalog operations without knowledge-representation engineering. A precise occupational concept needs separate justification. |
| `Senior Data Engineer` and retained Hybrid/KSA/contract/RTG variants | Possible | Candidate knowledge/graph engineering only with explicit duties | Generic data engineering is not a narrower knowledge-engineering occupation by title alone. |
| `Data Scientist`, `Senior Data Scientist`, `Data Science Specialist (1417)`, `Foundational Model Research Data Scientist` | Possible | No direct target; investigate only with representation duties | Modeling or research alone does not establish any scheme concept. |
| `AI Model Training Quality Engineer`, `Applied AI-Agent Engineer`, `Forward Deployed Backend AI Engineer`, `Head of Neuro-Symbolic AI` | Possible | No direct target | AI, reasoning, or quality wording can coexist with several functions; no blanket adjacent-role concept. |
| `Architect`, `Agentic AI Architect`, `Principal AI Systems Architect`, `AI LLM Technology Architecture Associate Director`, `Head of Engineering`, `Senior Product Manager` | Ambiguous | No direct mapping | Broad technical/leadership titles do not specify one of these occupations. |
| Family `Related title` | Unmapped | Preserve as legacy grouping | A residual display family is not an occupational meaning or synonym. |
| `Core KE`, `Applied KG / AI`, `Metadata / Semantic` — machine categories | Ambiguous/non-occupational | No scheme mapping | Existing categories are not the protocol's human role-scope determinations; no automatic translation. |
| `Adjacent technical` — protocol assessment | Unmapped as occupation | Keep outside taxonomy | Contextual assessment of actual work, not a role superclass. |
| `Associate GTM Recruiter`, `Talent Acquisition Partner`, `Forward Deployed AI Sales Engineer`, `Associate Partner Activation Manager` | Unmapped | No concept proposed | Retained terminology is outside the selected occupational vocabulary. This table does not reproduce or endorse current title-exclusion decisions. |

“Knowledge Engineering” and knowledge-graph/ontology/semantic technology keywords in the rules name disciplines or artifacts, not justified alternative occupational labels. No aliases such as “AI Engineer,” “Data Engineer,” or “Semantic Engineer” are added to the four concepts. No Arabic translations are invented.

Before use, Haya and Lubna should approve lexical targets and scoped alternatives, review composite/vendor/governance ambiguities, and accept that some terms remain unmapped. Any future posting assignment needs original responsibilities and evidence, separate from this table. No production values are rewritten, no matching algorithm is implemented, and no unresolved Stage 0 decision is approved here.

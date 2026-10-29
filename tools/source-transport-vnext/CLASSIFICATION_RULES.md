# Experimental job classification vNext 1

Inputs are verified responsibility nodes from the six saved Development graphs.
Titles, salary, keyword frequency, source names, expected labels and human reviews
are not classification features. Exact source clauses and their field/span
references accompany every positive mapping. Existing ontology/taxonomy terms
retain their recorded proposal status; this prototype does not approve them.

- **C1 — direct representation engineering:** an imperative action directly
  operates on ontologies, knowledge graphs, semantic models, RDF schemas or SHACL
  constraints. Generic APIs, product names, presentations about ontologies and
  qualifications do not qualify. The existing occupational concept definitions
  provide candidate meanings; `ke:KnowledgeRepresentation`,
  `ke:Responsibility` and `ke:actsOnRepresentation` explain the action/object basis.
- **C2 — proposed Core KE:** C1 includes explicit ownership (`Own`) or at least
  two nonduplicate responsibility statements directly engineering representations.
  A single incidental direct task is insufficient for the job-level proposal.
- **A1 — proposed Adjacent Technical:** a technical component explicitly feeds
  semantic reasoning engines or serves a knowledge graph, in the same duty
  clause. Generic AI, backend, graph database or DevOps work does not supply this
  link. The additional supporting-work concept is experimental, separate from
  the frozen occupational taxonomy; it does not assert representation ownership.
- **N1/N2/N3 — proposed Neither:** at least two independent commercial account,
  advertising-reporting or sales-delivery responsibilities, without competing
  technical/representation evidence or unresolved representation mentions. This
  is positive alternative-function evidence, not an inference from absent KE
  terms, and not an exhaustive claim about unextracted duties.
- **U1 — Insufficient Evidence:** unsupported mappings, conditional/negated or
  qualification-like statements, insufficient ownership/independent duties, or
  conflicting commercial and representation-related functions. Missing support
  never defaults to Neither. A conditional section qualifier blocks its duties
  from supporting a primary-function decision.

Clause boundaries, action/object templates and explicit token guards are in
`classify_jobs_vnext.py`; the runtime exports the exact rule catalog and concept
definitions. Repeated field representations of the same duty do not count as
independent evidence. These narrow templates can miss valid paraphrases and do
not establish full coverage, confidence, accuracy or human ground truth.

Run the new classifier with the same saved graph/packet/result paths used by the
RDF query tool and a fresh ignored output directory:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe" -B tools/source-transport-vnext/classify_jobs_vnext.py --graph-dir learning-local/source-graph-vnext-layouts-20261028-f413eb2022 --packet-dir learning-local/source-transport-vnext-layouts-20261028-f413eb2022 --blocked-results learning-local/haya-development-replay-20261028-d0a8eefdb1/development-split/compatibility.json --output-dir learning-local/job-decisions-vnext-NEW
```

`decisions.html` is a local, self-contained six-card page with all supporting and
considered evidence. `human-ground-truth.csv` contains only blank human judgment
fields, with no machine proposal copied into a human field. No existing RDF graph
or review file is changed, and no frozen Before comparison or evaluation runs.

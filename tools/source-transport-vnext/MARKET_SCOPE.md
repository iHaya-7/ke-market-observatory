# User-authorized geographic market eligibility — 29 October 2026

`market_eligibility_vnext.py` evaluates original, hash-verified Development
captures individually. Case IDs and human reference decisions do not enter the
rule function. Same job IDs or titles in different countries do not share results.

- **Global G1:** require a clearly named KE profession in the original title.
  The explicit title-family list includes the user's examples and named KE
  equivalents; seniority/level/location suffixes are allowed. Generic Data/AI,
  Software or Architecture titles cannot qualify from description terminology.
- **Saudi S1:** require an actual responsibility directly creating, curating,
  maintaining, validating, governing or integrating a knowledge representation,
  ontology, knowledge graph, semantic layer, taxonomy or semantic model.
  Implementation `saudi-s1-responsibility-2` handles coordinated design/develop/
  maintain verbs, combined Semantic and Data Mart layers, explicit leadership
  of Semantic Layer developers, and governance across the Semantic Layer.
  Paragraph bullets are read only within bounded responsibility sections;
  original text, field boundaries and evidence offsets remain unchanged.
  Qualifications, incidental mentions, report/dashboard usage and generic
  data engineering do not qualify. Frozen graph extraction is unchanged.
- **Saudi S2:** accept substantive pipeline/ingestion implementation explicitly
  feeding semantic reasoning engines only when same-field role/platform source
  context explicitly connects the work to knowledge graphs/ontologies/semantic
  knowledge models. Generic AI pipelines or incidental mentions do not qualify.
- **Location L0:** unresolved/conflicting location stays unresolved and excluded
  from confirmed eligibility. Structured country/location data, never a title's
  KSA/remote text, determines geography.

Job market eligibility, occupational Core/Adjacent/Neither/Insufficient Evidence
and salary eligibility/availability remain separate dimensions. The classifier
CLI now writes a separate capture-specific market eligibility file alongside its
unchanged occupational decision schema; it does not gate jobs on pay or promote
human eligibility decisions into occupational ground truth.

The private ten-case human reference is user-provided and non-blind. Each decision
is bound to a primary original capture hash and country. The Saudi acceptance
does not label an Egyptian variant. Neither historical review templates nor
blinded occupational fields are overwritten. Comparison reports raw agreements
and disagreements only, without frozen Before/After comparisons or metrics.

Run `market_eligibility_vnext.py --human-reference <private-reference.json>
--output-dir learning-local/<NEW-directory>` from the repository root. Outputs
are capture decisions and a ten-row primary-posting comparison CSV, with no UI.

For a new employer batch, use `scripts/process_experimental_batch.py
--rerun-results <saved-results.json> --output learning-local/<fresh-directory>`.
This authenticates and reuses the existing capture bytes and writes separate
machine predictions. User-provided, non-blind eligibility judgments are saved
separately and are never inputs to the rules.

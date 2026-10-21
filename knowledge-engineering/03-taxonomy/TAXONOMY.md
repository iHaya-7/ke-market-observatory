# Stage 3 — Proposed role taxonomy

21 October 2026 · Version 0.1 · Haya and Lubna's approval pending. Stages 1–2 are the working basis, not silently treated as team-approved.

## Scope and structure

The [SKOS file](role-taxonomy.ttl) contains **one ConceptScheme and four occupational concepts**, with one top concept and three specialization links:

```text
Knowledge Engineer
  Ontology Engineer (alternative label: Ontologist)
  Knowledge Graph Engineer
  Semantic Web Engineer
```

The broader concept means engineering explicit representations of knowledge and meaning. Under that definition, each child is a type of that engineering work, specialized respectively by conceptual modeling, graph representation/integration, or Semantic Web interoperability. These are occupational meanings, not organizational reporting lines, skill dependencies, or assessments of individual jobs. No child is made broader than another: none necessarily subsumes the others. No `skos:related` links are added merely because siblings can collaborate.

All four preferred labels occur in production titles/families or the explicit `CORE_TITLE` rule in [refresh.py](../../scripts/refresh.py). “Ontologist” is attested in production titles and is proposed as an alternative only within the computational scope note. Semantic Web Engineer is rule-supported, not asserted to occur in the inspected retained titles. Definitions and evidence-dependent mappings are documented in [TERM_MAPPING.md](TERM_MAPPING.md).

Metadata / Semantic Governance and Adjacent Data / AI are **not** added as occupational catch-all categories. They combine different functions and contextual involvement, and the existing terminology does not justify a single precise role concept. Generic Data Engineer, Data Scientist, Architect, and governance titles remain outside this small scheme unless evidence supports a candidate role interpretation. Unmapped does not mean irrelevant. This is intentionally not an exhaustive or mutually exclusive classifier of all Observatory jobs; one posting may describe several functions.

## Method and identifiers

The accessible local [Ontology Pipeline](../../../Ontology-Pipeline/Ontology-Pipeline.md), “From coverage model to hierarchy,” “The Is-a test” (around lines 2897–2960), and “Formal concept schemes” / “Documentation properties” (3385–3408), informs the design: use existing terms, require a type-of justification, define boundaries, and keep identifiers separate from labels. Its general exhaustiveness/exclusivity guidance is bounded here to a small role vocabulary; it does not justify forcing overlapping job responsibilities into artificial branches.

Stable proposed identifiers use `urn:ke-market-observatory:role:` with descriptive local names. These local URNs do not claim a hosted namespace. Keep identifiers stable when labels change; changes in meaning or a future hosted namespace require an explicit version/migration decision. The file uses only SKOS concepts and scheme membership, labels, definitions, notes, and broader/narrower links. No OWL classes, custom properties, posting instances, external scheme equivalences, or executable classification rules are introduced.

## CQ fit and limits

| Question | Contribution | Still required |
| --- | --- | --- |
| CQ-01: genuine responsibilities | Consistent names for candidate occupational meanings and boundaries. | Actual responsibility passages, action/object interpretation, source support, and relevance assessment. |
| CQ-02: core versus adjacent | Distinguishes occupational specializations without conflating current category names. | Evidence of primary versus supporting work. Core KE and Adjacent technical are contextual assessments, never parent/child concepts here. |
| CQ-04: comparison | A shared role vocabulary can describe one comparison dimension. | Materially similar responsibilities, evidenced level, market, eligible pay, endpoints, and approved pairs. Same concept is not sufficient. |
| CQ-03, CQ-05, CQ-06 | Terms can identify the role under discussion. | The taxonomy cannot establish salary eligibility, claim support, provenance, review need, or queue membership. |

Refer to [Scope](../01-scope/SCOPE.md), [CQs](../01-scope/COMPETENCY_QUESTIONS.md), and [CQ coverage](../02-vocabulary-metadata/CQ_COVERAGE.md). Later evidence relationships are outside Stage 3. No accuracy improvement is asserted.

## Validation and approval

The Turtle uses a deliberately small subset: prefix declarations and single subject–predicate–object statements with named nodes or English string literals. Validation used the already-installed Python `pyparsing` library to parse the entire file against that subset, resolve prefixes, and check scheme membership, labels, references, reciprocal broader/narrower links, and absence of cycles. Results: **syntax-subset check passed; one scheme, four concepts, three broader links**. A full RDF-parser validation was not available: RDFLib, PyOxigraph, Node N3/RDFLib, and command-line RDF parsers were unavailable. No dependency was installed. This is not a claim of complete SKOS entailment/conformance validation; parsing also does not approve occupational semantics.

Team decisions: approve the broad Knowledge Engineer definition and three specialization links; the scoped Ontologist alternative; rule-only support for Semantic Web Engineer; deferred governance/adjacent terminology; and the identifier policy. No held-out cases, claim specifications, labels, or predictions were inspected. Only production terminology and existing rules were used; no case examples or assignments were necessary. Frozen artifacts, production rules/data, and review decisions remain unchanged. Stop at this proposal.

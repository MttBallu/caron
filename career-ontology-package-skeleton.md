---
kind: package_skeleton
status: m0_consolidated_baseline
architecture_contract: 0.2
implementation_status: semantic_query_temporal_and_viewer_regressions_consolidated
---

# Career Ontology — First Executable Spine

## 1. Purpose and current scope

This directory contains the first maintained executable spine. The distribution and import package are both named `caron`.

The maintained implementation includes:

- an explicit, immutable ontology schema;
- generic immutable entity and relation records;
- a candidate form that can represent invalid input;
- structured diagnostics at ontology, local-record, and realisation layers;
- an immutable validated realisation constructible only through validation;
- semantic rules for the first executable encoding of career model 4.
- a distinct career model v0.5 schema with month-level context temporality;
- immutable temporal values and local and transitive containment validation;
- typed temporal predicates and covered-month results with explicit epistemic classifications;
- witness-preserving immutable `GraphView` query selections;
- a private witness-carrying binding algebra preserving accepted composition regressions;
- versioned ontology-schema inspection derived directly from `OntologySchema`.

General retrieval, persistence, serialization, application orchestration, and CLI behavior remain absent. The temporal query catalogue is deliberately small. An interaction-layer visualization experiment exists under `examples/`, but it is not part of the public package API.

## 2. Project tree

```text
career-ontology/
├── CURRENT.md
├── career-ontology-package-skeleton.md
├── pyproject.toml
├── uv.lock
├── caron/
│   ├── __init__.py
│   ├── ontology.py
│   ├── entities.py
│   ├── relations.py
│   ├── realisations.py
│   ├── temporal.py
│   ├── queries.py
│   ├── _query_algebra.py
│   ├── views.py
│   ├── diagnostics.py
│   └── validation.py
├── docs/
│   ├── career-model-v0.5-temporal-contract.md
│   ├── career-model-v0.5-temporal-contract-review.md
│   ├── career-model-v0.5-temporal-instantiation-experiment.md
│   ├── career-ontology-entity-representation-pseudocode.md
│   ├── career-ontology-m1a-reconciliation.md
│   ├── career-ontology-m1b-semantic-decisions.md
│   └── career-ontology-package-boundaries.md
├── examples/
│   ├── __init__.py
│   ├── semantic_spine.py
│   ├── temporal_queries.py
│   ├── two_contexts.py
│   ├── cytoscape_html.py
│   ├── cytoscape_template.html
│   ├── ontology_schema_html.py
│   └── ontology_schema_template.html
├── tools/
│   └── verify.py
└── tests/
    ├── fixtures/
    ├── unit/
    │   ├── test_cytoscape_example.py
    │   ├── test_ontology_schema_example.py
    │   ├── test_ontology.py
    │   ├── test_query_algebra.py
    │   ├── test_temporal_queries.py
    │   ├── test_temporal_validation.py
    │   ├── test_temporal_values.py
    │   ├── test_two_contexts_example.py
    │   └── test_validation.py
    └── invariants/
        ├── test_temporal_invariants.py
        └── test_validation_invariants.py
```

The package uses a direct layout: importable sources live in `caron/`, not `src/caron/`. The `uv_build` configuration therefore sets `module-root = ""` explicitly.

## 3. Boundary map

| Module | Owns | Must not own |
|---|---|---|
| `ontology.py` | Concept and relation definitions, value kinds, relation requirements, model identity | Concrete career records, persistence, retrieval evaluation |
| `entities.py` | Entity records, identifiers, values, entity references | Relation semantics, validation policy |
| `relations.py` | Relation assertions and qualifiers | Traversal algorithms, interpretation |
| `realisations.py` | Candidate and validated forms, coverage, direct immutable reads | Decoding, storage, narrative answers |
| `temporal.py` | `YearMonth`, temporal end states, extents, and windows | Graph traversal, query evaluation, rendering |
| `queries.py` | Typed temporal predicates, window selection, covered-month results, and private constraint composition | Persistence, serialization, prose answers |
| `_query_algebra.py` | Private joins, optional matching, union, projection, ordering, and witness-derived views | Stable public plan AST, schema validation, persistence |
| `views.py` | Immutable `GraphView`, bindings, and witnesses | Query evaluation and renderer-specific state |
| `diagnostics.py` | Stable codes, severity, layer attribution | Validation control flow |
| `validation.py` | Ontology, local-record, and whole-realisation validation | Parsing, database access, query evaluation |
| `__init__.py` | Deliberate public re-exports | Private implementation details |

Rules such as activity agency and contextual grounding are declared as ontology `RelationRequirement` values. The validator interprets those values; it does not hard-code career questions or interaction behavior.

## 4. Implemented public surface

```yaml
ontology:
  - OntologySchema
  - ConceptDefinition
  - RelationDefinition
  - RelationRequirement
  - model4_ontology
  - model_v0_5_ontology

semantic_records:
  - Entity
  - EntityRef
  - Property
  - RelationAssertion
  - Qualifier
  - RealisationCandidate
  - ValidatedRealisation
  - Coverage
  - YearMonth
  - TemporalExtent
  - TemporalWindow

validation:
  - validate_ontology
  - validate_candidate
  - Accepted
  - Rejected
  - Diagnostic

queries:
  - covered_months
  - before
  - overlaps
  - select_activities_in_window
  - GraphView
  - QueryWitness
```

The root API is intentionally small. Internal aliases and implementation helpers remain owned by their modules.

## 5. Validation semantics

The boundary is explicit:

```text
RealisationCandidate + OntologySchema
    -> Accepted(ValidatedRealisation)
    |  Rejected(tuple[Diagnostic, ...])
```

Validation covers schema coherence, ontology identity and version, unique record identifiers, known concepts and relations, properties and qualifiers, runtime value kinds, reference closure, endpoint compatibility, and realisation-level cardinality requirements.

Both executable schemas require each `Activity` to have at least one incoming `performs` relation and exactly one outgoing `occurs_in` relation. `exposed_to` and `learns` require a context reference qualifier. Model v0.5 additionally validates month-level temporal extents and the consistency of direct and transitive `part_of` containment.

## 6. Test strategy

All tests run through pytest:

- deterministic unit tests provide small examples and regressions;
- Hypothesis tests generate cases and search for counterexamples to invariants.

The suite combines deterministic cases with Hypothesis invariants. In addition to the original schema, validation, and visualization behavior, it checks canonical `YearMonth` values, temporal immutability, extent consistency, direct and transitive containment, exact and bounded covered-month results, ongoing observations, temporal ordering, overlap, possible versus unknown matches, witness paths, and `GraphView` closure.

Hypothesis increases confidence in invariants; it is not a formal proof system.

Run the complete verification set with one command:

```bash
uv run --locked --all-groups python tools/verify.py
```

Run the executable guided example with:

```bash
uv run python examples/semantic_spine.py
uv run python -m examples.temporal_queries
```

The example constructs a small PhD activity graph, validates it, performs direct reads over the immutable result, and then removes the activity's contextual grounding to demonstrate structured rejection diagnostics.

Generate the interactive visualization example with:

```bash
uv run python -m examples.ontology_schema_html
uv run python -m examples.ontology_schema_html --version 4
uv run python -m examples.cytoscape_html
uv run python -m examples.cytoscape_html --example two-contexts
uv run python -m examples.cytoscape_html --example temporal-window
```

Then open the generated `examples/*_graph.html` file in a browser. Generated graph files are ignored by Git. The ontology-schema views display the exact executable concepts, properties, relation signatures, qualifiers, and requirements for version `0.5` or `4`; they do not display a realisation. The cross-context realisation example connects ALICE collision-data analysis during an MSc and synthetic-training-data construction during a PhD through one shared Python entity. Each activity remains grounded in its own context and concrete evidence; no transfer relation is asserted. The temporal-window example renders the possible activity matches for 2022 together with the temporal properties and witnesses retained by the query result. The generated pages load the pinned Cytoscape.js 3.34.1 browser library from jsDelivr, so this first experiment requires an internet connection when a page is opened.

## 7. Visualization experiment boundary

The realisation viewer implements:

```text
ValidatedRealisation
    -> typed query
    -> immutable GraphView
    -> renderer-specific Cytoscape JSON
    -> generated HTML
    -> graph canvas + inspector state
```

The schema viewer has a parallel but distinct projection:

```text
OntologySchema
    -> renderer-specific Cytoscape JSON
    -> generated HTML
    -> rule graph + inspector state
```

It expands each relation definition into all admissible source-kind/target-kind
pairs while retaining the complete definition on every displayed edge. It also
retains concept properties, relation qualifiers, and endpoint cardinality
requirements. The graph therefore reports executable expressivity without
claiming that any entity or relation has been asserted in a realisation.

The renderer preserves all selected entity properties and relation qualifiers. It serializes `TemporalExtent` as structured JSON and retains typed temporal query results, bindings, witnesses, diagnostics, source-realisation identity, and coverage as renderer metadata. A relation carrying a context qualifier is projected as a renderer-only relation-occurrence node connected to its source, target, and context; this prevents the n-ary semantics of relations such as `learns` from appearing as an unqualified binary edge. The browser presents long values such as proposition `content` in collapsed disclosure sections, supports entity and relation filters, highlights a selected neighborhood, and exposes temporal match classifications in the inspector.

The selected element, collapsed properties, focus, filters, display strings, colors, and line styles are presentation state. They do not mutate the `GraphView` or turn derived temporal results into asserted relations. Renderer-specific JSON remains outside the model and query contracts and is not a persistence format.

## 8. Deliberately deferred

```yaml
not_created_yet:
  - public graph-pattern language
  - public relational algebra
  - repository abstraction
  - storage backend
  - serialization codec
  - application service layer
  - maintained interaction package
  - CLI
  - interpretation framework
```

No empty packages are created for future features. Structure should appear only with behavior and tests that justify it.

## 9. Next executable increment

The next increment should be chosen from observed use rather than by filling the package map. Strong candidates are period controls backed by temporal queries and a chronological projection for the use of a selected technology or skill. Either increment must preserve uncertainty and witnesses without turning display order into asserted `before` relations.

That increment should not introduce a public query language, general optimizer, storage abstraction, or narrative interpretation inside the query engine.

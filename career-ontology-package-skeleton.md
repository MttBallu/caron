---
kind: package_skeleton
status: implemented_semantic_spine
architecture_contract: 0.2
implementation_status: semantic_validation_complete
---

# Career Ontology — First Executable Spine

## 1. Purpose and current scope

This directory contains the first maintained executable spine. The distribution and import package are both named `caron`.

The current increment implements:

- an explicit, immutable ontology schema;
- generic immutable entity and relation records;
- a candidate form that can represent invalid input;
- structured diagnostics at ontology, local-record, and realisation layers;
- an immutable validated realisation constructible only through validation;
- semantic rules for the first executable encoding of career model 4.

Retrieval, `GraphView`, persistence, serialization, application orchestration, and CLI behavior are deliberately absent. An interaction-layer visualization experiment exists under `examples/`, but it is not part of the public package API.

## 2. Project tree

```text
career-ontology/
├── career-ontology-package-skeleton.md
├── pyproject.toml
├── uv.lock
├── caron/
│   ├── __init__.py
│   ├── ontology.py
│   ├── entities.py
│   ├── relations.py
│   ├── realisations.py
│   ├── diagnostics.py
│   └── validation.py
├── docs/
│   ├── career-ontology-entity-representation-pseudocode.md
│   └── career-ontology-package-boundaries.md
├── examples/
│   ├── __init__.py
│   ├── semantic_spine.py
│   ├── two_contexts.py
│   ├── cytoscape_html.py
│   └── cytoscape_template.html
└── tests/
    ├── fixtures/
    ├── unit/
    │   ├── test_cytoscape_example.py
    │   ├── test_ontology.py
    │   ├── test_two_contexts_example.py
    │   └── test_validation.py
    └── invariants/
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

semantic_records:
  - Entity
  - EntityRef
  - Property
  - RelationAssertion
  - Qualifier
  - RealisationCandidate
  - ValidatedRealisation
  - Coverage

validation:
  - validate_ontology
  - validate_candidate
  - Accepted
  - Rejected
  - Diagnostic
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

The first ontology requires each `Activity` to have at least one incoming `performs` relation and exactly one outgoing `occurs_in` relation. `exposed_to` and `learns` require a context reference qualifier.

## 6. Test strategy

All tests run through pytest:

- deterministic unit tests provide small examples and regressions;
- Hypothesis tests generate cases and search for counterexamples to invariants.

The implemented suite has 16 deterministic cases and 3 generative invariant tests. It checks ontology coherence, valid construction, immutability, guarded construction, invalid concepts and endpoints, activity cardinality, contextual qualifiers, reference kinds, runtime integer typing, dangling endpoints, endpoint-kind compatibility, record-order independence, renderer data preservation, HTML generation, and reuse of one technology across activities in distinct contexts.

Hypothesis increases confidence in invariants; it is not a formal proof system.

Run the complete verification set with:

```bash
uv sync --all-groups
uv run ruff format --check .
uv run ruff check .
uv run mypy caron tests examples
uv run pytest
uv build
```

Run the executable guided example with:

```bash
uv run python examples/semantic_spine.py
```

The example constructs a small PhD activity graph, validates it, performs direct reads over the immutable result, and then removes the activity's contextual grounding to demonstrate structured rejection diagnostics.

Generate the interactive visualization example with:

```bash
uv run python -m examples.cytoscape_html
uv run python -m examples.cytoscape_html --example two-contexts
```

Then open `examples/career_graph.html` or `examples/two_contexts_graph.html` in a browser. Generated graph files are ignored by Git. The two-context example represents two activities connected to a single shared Python entity. The generated pages load the pinned Cytoscape.js 3.34.1 browser library from jsDelivr, so this first experiment requires an internet connection when a page is opened.

## 7. Visualization experiment boundary

The experiment implements:

```text
ValidatedRealisation (temporary GraphView stand-in)
    -> renderer-specific Cytoscape JSON
    -> generated HTML
    -> graph canvas + inspector state
```

The renderer preserves all entity properties and relation qualifiers. The browser presents long values such as proposition `content` in collapsed disclosure sections, supports entity and relation filters, and highlights a selected neighborhood.

The selected element, collapsed properties, focus, and filters are presentation state. They do not mutate the validated semantic value. When the query layer introduces `GraphView`, the adapter input will change from `ValidatedRealisation` to `GraphView`; the renderer-specific JSON must remain outside the model and query contracts.

## 8. Deliberately deferred

```yaml
not_created_yet:
  - retrieval evaluator
  - GraphView and query result types
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

Implement one typed `ActivitiesInContext` retrieval end to end. It should return useful information rather than a prose answer: bindings, witnesses, coverage, diagnostics, and an immutable, semantically closed `GraphView`.

That increment should add only the smallest justified retrieval/result surface. It should not introduce a public query language, general optimizer, storage abstraction, or interaction-layer translation.

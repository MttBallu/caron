---
kind: package_implementation_overview
status: ontology_5_0_accepted
architecture_contract: 0.3
package_version: "0.2.0"
ontology_generation: "5.0"
runtime_schema_version: "5.0"
---

# caron — Implementation Overview

## 1. Current scope

`caron` is a Python 3.12 package for representing and validating career
evidence as an ontology-governed graph. Package version `0.2.0` contains the
accepted Career Ontology identity `caron.career-model` / `5.0`, exposed by the
public `career_ontology_v5_0()` factory. Earlier executable ontology versions
`4` and `0.5` are historical predecessors preserved in documents and Git
history, not runtime schemas in `0.2.0`.

The maintained implementation includes:

- an explicit immutable ontology schema with 13 concepts, 31 relation rules,
  six endpoint cardinalities, and eight declared global invariants;
- generic immutable entity and relation records, including qualified relation
  assertions for contextual and other n-ary facts;
- a candidate form that keeps invalid input representable and diagnosable;
- staged ontology, record, and graph validation producing stable structured
  diagnostics;
- immutable validated realisations constructible only through validation;
- immutable month-level temporal values and local and transitive temporal
  consistency checks;
- a small typed temporal-query catalogue with explicit epistemic
  classifications and retained witnesses;
- renderer-independent immutable `GraphView` selections;
- a private witness-carrying query-algebra experiment;
- a single-file YAML reader and tagged-value binder that feed the existing
  candidate validator, with file-aware load findings; and
- schema and realisation viewers derived from the executable model.

The package does not yet provide a writer, canonical serialization, durable
storage, migration, a public query language, an application service, or a CLI.

## 2. Source layout

```text
caron/
├── CURRENT.md
├── README.md
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
│   ├── diagnostics.py
│   ├── validation.py
│   ├── yaml_reader.py
│   ├── _bundled_realisation.py
│   ├── data/
│   │   └── career-across-contexts-v0.1.yaml
│   ├── queries.py
│   ├── views.py
│   ├── _invariants.py
│   ├── _career_v5_invariants.py
│   └── _query_algebra.py
├── docs/
│   ├── career-ontology-v5.0-specification.md
│   ├── career-ontology-v5.0-implementation-plan.md
│   ├── career-ontology-package-boundaries.md
│   └── historical decision, reconciliation, and temporal documents
├── examples/
│   ├── semantic_spine.py
│   ├── temporal_queries.py
│   ├── two_contexts.py
│   ├── cytoscape_html.py
│   └── ontology_schema_html.py
├── tests/
│   ├── conformance/
│   ├── fixtures/
│   ├── invariants/
│   └── unit/
└── tools/
    └── verify.py
```

Importable sources live directly in `caron/`; the `uv_build` configuration
therefore uses `module-root = ""`.

## 3. Ownership boundaries

| Module | Owns | Excludes |
|---|---|---|
| `ontology.py` | Meta-model records, concept constants, and the public exact `5.0` catalogue | Concrete career facts, query evaluation, persistence |
| `entities.py` | Generic entities, stable references, and property values | Ontology policy and relation semantics |
| `relations.py` | Identified relation assertions and qualifiers | Traversal and interpretation |
| `realisations.py` | Candidate and validated graphs, coverage, immutable reads | Decoding, storage, narratives |
| `temporal.py` | `YearMonth`, temporal end states, extents, and windows | Graph traversal and rendering |
| `_invariants.py` | Private staged invariant registry and local handlers | Public schema declarations |
| `_career_v5_invariants.py` | Private ontology `5.0` graph-invariant implementations | Schema identity and public queries |
| `validation.py` | Ontology self-validation and the candidate-to-validated boundary | Parsing, persistence, interpretation |
| `yaml_reader.py` | Single-file YAML read, typed binding, source locations and load outcomes | Ontology-specific semantic validation, writing, migrations |
| `_bundled_realisation.py` and `data/` | Internal path and one installed, selective career file | Public semantic imports, multi-file assembly, writer |
| `queries.py` | Typed temporal operations and explicit whole-graph selection | General public plan language |
| `_query_algebra.py` | Private joins, optional matching, union, extension, projection, ordering, and witness derivation | Stable public query-plan contract |
| `views.py` | Immutable `GraphView`, bindings, witnesses, and coverage | Evaluation and presentation state |
| `diagnostics.py` | Stable diagnostic codes, severity, and semantic layers | Validation control flow |
| `__init__.py` | Deliberate semantic re-exports | Private factories, registries, algebra, renderers, and deferred capabilities |

Schema declarations name global invariant identifiers; executable callbacks
remain in private registries. This keeps the ontology inspectable without
putting Python functions into schema data.

## 4. Public API boundary

The root package exposes the types needed to build and inspect ontology-aware
data:

```yaml
ontology_meta_model:
  - concept constants
  - career_ontology_v5_0
  - OntologySchema
  - ConceptDefinition
  - PropertyDefinition
  - RelationDefinition
  - QualifierDefinition
  - RelationRequirement
  - InvariantDefinition
  - EndpointPosition
  - ValueKind

semantic_records:
  - Entity
  - EntityRef
  - Property
  - RelationAssertion
  - Qualifier
  - RealisationCandidate
  - ValidatedRealisation
  - Coverage
  - temporal value records

validation_and_queries:
  - Accepted
  - Rejected
  - Diagnostic
  - validate_ontology
  - validate_candidate
  - covered_months
  - before
  - overlaps
  - select_activities_in_window
  - select_whole_realisation
  - GraphView
  - QueryBinding
  - QueryWitness
```

The public factory exposes the one maintained exact ontology. Invariant
handlers and registries, internal query plans, renderer adapters, storage or
codec interfaces, and migration functions are not re-exported. This is the
minimum current root surface that supports schema inspection, candidate
construction, validation, the accepted typed queries, and interaction-layer
projections.

## 5. Validation contract

```text
RealisationCandidate + OntologySchema
    -> Accepted(ValidatedRealisation)
    |  Rejected(tuple[Diagnostic, ...])
```

Validation is staged so malformed records do not reach graph-wide checks. It
covers schema coherence; ontology identity and version; lexical and unique
record identifiers; required non-blank text; known concepts, relations,
properties, and qualifiers; runtime value kinds; reference closure; endpoint
compatibility; semantic relation-fact uniqueness; activity and credential
cardinalities; Context and Organization acyclicity; Proposition locality;
`bears_on` roles and locality; and temporal consistency.

The current ontology represents `Credential` as an entity with an optional
month-level `awarded_in` value and explicit recipient, awarder, context, and
evidence relations. `Place` remains a first-class CV-oriented entity reached
through `Context` `occurs_at` assertions. N-ary facts use identified relation
assertions plus typed qualifiers rather than creating a new entity for every
relation occurrence.

## 6. Query and interaction boundary

The maintained public query catalogue is intentionally small:
`covered_months`, `before`, `overlaps`, `select_activities_in_window`, and
`select_whole_realisation`. Temporal results distinguish entailed, possible,
excluded, and unknown outcomes and retain the direct or inherited witnesses
that justify them.

`GraphView` is the immutable hand-off between semantic queries and interaction
adapters. It retains selected entities and relations, bindings, witnesses,
coverage, source-realisation identity, typed results, and diagnostics. The
browser viewer then creates renderer-specific Cytoscape JSON and presentation
state. That JSON is not a semantic serialization or persistence format.

The schema viewer follows a separate projection:

```text
OntologySchema
    -> renderer-specific rule graph
    -> generated HTML
    -> graph canvas and inspector state
```

It expands relation endpoint unions into 41 admissible source/target pairs and
displays concept properties, qualifier definitions, six cardinality rules,
and eight global invariants. It describes what the executable ontology can
express; it does not claim that any career facts have been asserted.

## 7. Running and verifying

Run the complete maintained gate:

```bash
uv run --locked --all-groups python tools/verify.py
```

Run the semantic and temporal examples:

```bash
uv run python -m examples.semantic_spine
uv run python -m examples.temporal_queries
```

Generate the current schema and realisation viewers:

```bash
uv run python -m examples.ontology_schema_html
uv run python -m examples.cytoscape_html
uv run python -m examples.cytoscape_html --example two-contexts
uv run python -m examples.cytoscape_html --example temporal-window
```

Generated graph files are ignored by Git. The pages load the pinned
Cytoscape.js 3.34.1 library from jsDelivr when opened.

The verification command checks formatting, Ruff, strict mypy, deterministic
and Hypothesis tests, maintained examples, all viewers, source and wheel
builds, a clean wheel installation, and the installed public API.

## 8. Compatibility and deferred capabilities

`caron` remains experimental throughout the `0.x` line. Breaking changes are
permitted, and stable compatibility guarantees begin no earlier than `1.0`.
Package and ontology versions are independent: one package release can contain
multiple ontology changes, and an ontology version never implies the package
version.

No compatibility shim or automatic migration exists for ontology `4` or
`0.5`. Migration remains a separate capability requiring its own contract,
diagnostics, and tests; legacy realisations must not be silently relabelled as
`5.0`.

The following remain deliberately deferred:

- a public graph-pattern language or relational algebra;
- schema-aware validation for public query plans;
- canonical semantic serialization and decoding;
- repository and storage abstractions;
- data migration;
- application services and a CLI;
- maintained interaction packaging; and
- narrative or other interpretation frameworks.

Modules for these capabilities should appear only when behavior and tests
justify them.

## 9. Acceptance status

Phase 10 reviews every section 16.1 obligation in the accepted specification,
runs the complete conformance and distribution gate, installs the wheel in a
clean environment, and smoke-tests the installed public API. The accepted
result is the public `career_ontology_v5_0()` factory with exact schema version
`5.0` in package `0.2.0`.

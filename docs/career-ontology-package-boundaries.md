---
kind: package_boundary_note
status: accepted_and_implemented_through_ontology_5_0_final_acceptance
architecture_contract: 0.3
---

# Package Boundary Decisions

## Accepted and implemented

```yaml
decisions:
  distribution_name: caron
  import_package: caron
  package_layout: direct root package
  dependency_manager: uv
  build_backend: uv_build
  python: "3.12"
  package_shape: flat first package
  entity_representation: generic immutable records
  ontology_authority: explicit immutable schema
  relation_representation: separate generic assertions
  candidate_boundary: invalid input remains representable and diagnosable
  validated_boundary: immutable and created only through validation
  immutable_records: frozen slotted dataclasses
  validation_api: Accepted | Rejected result object
  diagnostics: stable codes with explicit semantic layer
  global_invariants: declarative RelationRequirement records
  deterministic_tests: pytest
  invariant_tests: hypothesis through pytest
  temporal_values: immutable month-level value objects
  temporal_validation: local extent and transitive containment checks
  temporal_queries: small typed catalogue with explicit result classifications
  query_algebra: private witness-carrying execution experiment
  graph_view: immutable query selection retaining ontology, witnesses, and coverage
  realisation_visualization_input: GraphView rather than ValidatedRealisation
  schema_visualization_input: OntologySchema
  visualization_projection: renderer-specific JSON outside semantic contracts
  maintained_ontology_generation: "5.0"
  runtime_identity: "5.0"
  public_schema_factory: career_ontology_v5_0
  historical_executable_predecessors:
    - "4"
    - "0.5"
  compatibility_guarantees: no earlier than caron 1.0
  migration: explicitly deferred
```

## Accepted and implemented retrieval boundary

```yaml
retrieval_boundary:
  api: small typed catalogue
  execution_algebra: implemented, private, unchecked, and replaceable
  graph_view: immutable query-result projection
  whole_realisation_view: explicit selection that retains source coverage
  interpretation: interaction-layer responsibility
```

## Still undecided

```yaml
open_implementation_choices:
  - retrieval indexing strategy
  - adapter and codec APIs
  - CLI framework
```

Internal indexing remains absent until retrieval pressure requires it. No repository protocol is introduced around a single in-memory implementation.

The internal algebra is retained because its joins, optional matches, unions,
ordering, and witness propagation have accepted regression value. It is not a
public query-plan API. Candidate/validated plan forms and schema-aware plan
diagnostics remain a later contract.

## Runtime and release boundary

Ontology `5.0` is the current maintained executable model. The complete schema
is available through the public `career_ontology_v5_0()` factory and carries
the exact identity `caron.career-model` / `5.0` after the Phase 10 conformance
gate.

Executable ontology versions `4` and `0.5` are historical predecessors. Their
meaning remains documented, but their factories, compact vocabulary, and
runtime compatibility surface are not part of `caron` `0.2.0`. The package
does not relabel or silently accept their realisations.

The package remains experimental before `1.0`. Breaking changes are permitted
through the `0.x` series, and stable compatibility guarantees begin no earlier
than `caron` `1.0`. Migration is a separately accepted capability and is
explicitly absent from `0.2.0`.

## Public surface boundary

The root package exports the records and enums required to construct, inspect,
validate, and query semantic data: ontology meta-model records and concept
constants; entity, relation, realisation, and temporal records; diagnostics and
validation results; typed temporal queries; and renderer-independent graph
views with bindings and witnesses.

The root package exports the exact ontology `5.0` factory. It does not export
invariant registries or handlers, query-algebra plans or evaluators, renderer
adapters, storage or serialization contracts, or migration machinery.

## Boundary rule

The package map is not permission to create every anticipated module. A module appears only alongside the behavior and tests that justify it. In particular, query results provide semantic information and traceability; turning that information into a concrete answer remains outside the query engine.

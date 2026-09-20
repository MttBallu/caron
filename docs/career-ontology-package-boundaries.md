---
kind: package_boundary_note
status: accepted_and_implemented_through_graph_view_visualization_projection
architecture_contract: 0.2
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
  graph_view: immutable query selection retaining ontology, witnesses, and coverage
  visualization_input: GraphView rather than ValidatedRealisation
  visualization_projection: renderer-specific JSON outside semantic contracts
```

## Accepted and implemented retrieval boundary

```yaml
retrieval_boundary:
  api: small typed catalogue
  execution_algebra: private and replaceable
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

## Boundary rule

The package map is not permission to create every anticipated module. A module appears only alongside the behavior and tests that justify it. In particular, query results provide semantic information and traceability; turning that information into a concrete answer remains outside the query engine.

---
kind: contract_review
status: accepted
reviewed_contract: career-model-v0.5-temporal-contract.md
reviewed_contract_version: "0.2"
review_date: 2026-09-18
review_scope:
  - logical_consistency
  - ontology_boundaries
  - month_level_semantics
  - incomplete_information
  - query_consequences
  - reference_instantiation
---

# Review — Career Model v0.5 Temporal Extent Contract

## 1. Conclusion

Contract version 0.2 is accepted for the first temporal implementation. The ALICE, PhD synthetic-data, and `jax-geopro` instantiation supplies a consistent executable test of its central semantics.

The review found no remaining contradiction between the temporal extension and the existing separation among ontology model, realisation, query engine, `GraphView`, and interaction layer.

## 2. Accepted semantic choices

### R1 — `temporal_extent` is intrinsic to `Context`

The property describes the context’s own calendar envelope. It does not qualify `part_of`, `participates_in`, or another relation. A period that describes only a person’s participation would be a relation qualification and remains deferred.

### R2 — The temporal domain has one resolution

All temporal boundaries use canonical `YearMonth` values in `YYYY-MM` form. Year-only and day-level values are outside v0.5, and migration must not invent a month.

This removes the mixed-precision reasoning that made the earlier draft unnecessarily complex.

### R3 — An extent is a calendar envelope, not active effort

A connected extent locates a context and supports ordering and selection. It does not assert continuous work, constant intensity, or effort in every represented month.

### R4 — End states remain distinct

Known end, unknown end, and ongoing observation have different semantics. `ongoing_as_of` is tied to a recorded month and must never advance with the system clock.

### R5 — Temporal existence does not require asserted boundaries

Every `Context` and `Activity` has a nonempty temporal occurrence. Absence of `temporal_extent` means unknown intrinsic boundaries, not absence of time.

This permits `part_of` and `occurs_in` to constrain undated entities without copying a parent extent onto them.

### R6 — `part_of` entails temporal containment

The occurrence of a child context must fit within the occurrence of its parent. Direct and transitive constraints must admit at least one interpretation.

An undated child of a dated parent receives bounds but does not acquire the parent’s intrinsic property or exact duration.

### R7 — Activity time remains relational

`occurs_in(activity, context)` constrains the activity occurrence to the context. It does not make the activity coextensive with the context and does not add a temporal property to `Activity`.

### R8 — Covered months are derived and inclusive

For a closed extent, `covered_month_count` counts the represented months inclusively. The ALICE project therefore covers 4 months and the PhD covers 37 months at model resolution.

An undated nonempty child inside the PhD has a bounded possible count of 1 through 37 months, not an exact count of 37. An ongoing count is explicitly tied to its observation month.

Covered months measure the calendar envelope, not workload or uninterrupted activity.

### R9 — Query classification has four observable outcomes

Temporal predicates distinguish `entailed`, `possible`, `excluded`, and `unknown`.

`possible` requires usable temporal constraints that admit both matching and nonmatching interpretations. `unknown` records insufficient temporal evidence and prevents an unconstrained entity from appearing as a possible match for every window.

### R10 — Derived results remain outside the asserted graph

Ordering, overlap, window matches, and covered-month results are query outputs. A `GraphView` carries them as result metadata with their witnesses; it does not insert them as asserted career relations.

## 3. Reference-case conclusions

The accepted dates are:

| Context | Temporal information |
|---|---|
| ALICE data-analysis project | `2021-11` through `2022-02` |
| PhD | `2022-10` through `2025-10` |
| Synthetic-data work | Undated child of the PhD |
| `jax-geopro` | Started `2026-04`, ongoing as observed in `2026-09` |

These facts entail the following contextual order:

```text
ALICE project < synthetic-data work < jax-geopro
```

The ordering of the corresponding activities is derived through `occurs_in` and `part_of`; no dates are copied onto the activities.

## 4. Implementation boundary confirmed by review

The first implementation may provide:

- immutable `YearMonth` and temporal extent values;
- v0.5 schema attachment to `Context`;
- local extent and transitive containment validation;
- `covered_months`, `before`, `overlaps`, and temporal-window selection;
- explicit result classifications and witnesses;
- immutable, renderer-independent `GraphView` values.

The following remain deferred:

- temporal extents on activities;
- temporal qualifiers on relations and participation periods;
- recurring or disconnected extents;
- approximate or probabilistic dates;
- active-effort duration;
- a complete interval algebra;
- serialization, persistence, CLI, and visualization policy.

## 5. Final assessment

The contract is sufficiently precise for implementation and remains proportionate to the competency questions. It adds useful temporal selection and chronology without requiring a general temporal reasoner or shifting concrete answer construction into the query engine.

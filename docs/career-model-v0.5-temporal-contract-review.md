---
kind: contract_review
status: accepted
reviewed_contract: career-model-v0.5-temporal-contract.md
review_date: 2026-09-17
review_scope:
  - logical_consistency
  - ontology_boundaries
  - incomplete_information
  - query_consequences
  - migration
---

# Review — Career Model v0.5 Temporal Extent Contract

## 1. Review conclusion

The contract is logically coherent and sufficiently bounded for a first
implementation.

No remaining contradiction was found between its temporal semantics and the
existing entity–relation model. The review did identify several failure modes
that would have been easy to introduce with a simpler start/end design. They
have been addressed in the reviewed contract.

The contract is accepted for implementation with two deliberate limitations:

- activity time is constrained through context rather than represented
  directly;
- participation and other relations are not independently timed.

These limitations reduce precision but do not make the supported answers
unsound.

## 2. Review method

The review checked the proposal against:

1. the current generic immutable entity and relation representation;
2. the separation between model, query engine, `GraphView`, and interaction;
3. the existing `part_of`, `occurs_in`, and `participates_in` semantics;
4. exact, coarse, missing, unknown-end, and ongoing dates;
5. nested contexts and contradictory intervals;
6. activity and technology selection through relation composition;
7. model-version isolation and migration.

The central criterion was not merely whether a date could be represented, but
whether useful temporal expressions could be constructed without producing
stronger claims than the evidence supports.

## 3. Findings resolved in the contract

### R1 — Duration alone cannot establish chronology

A numeric duration does not locate a context in time. Storing duration beside
start and end would also permit disagreement.

**Resolution:** store a temporal extent and derive exact or ranged duration.

### R2 — Partial dates can create false precision

Mapping a year to 1 January or 31 December would fabricate a date and could
produce false ordering or overlap results.

**Resolution:** a partial boundary denotes a set of compatible calendar days.
Queries distinguish entailed, possible, and excluded results.

### R3 — An undated open end is ambiguous

A missing end could mean ongoing, ended at an unknown time, or simply missing
data. Treating all three as ongoing would be unsound.

**Resolution:** known end, unknown end, and ongoing observation are distinct end
states.

### R4 — “Ongoing” cannot depend on the current clock

If an ongoing value merely had an open end, a realisation loaded years later
would appear to assert continued activity without new evidence.

**Resolution:** ongoing carries an exact `as_of` observation day. Queries
cannot advance it automatically.

### R5 — Context time is not activity duration

Copying a context extent to all contained activities would claim that every
activity lasted for the entire degree, project, or employment.

**Resolution:** `occurs_in` supplies a containment constraint only. The query
witness must expose that indirection.

### R6 — Binary temporal answers are too strong for coarse dates

With year- or month-precision boundaries, two contexts may admit several
relative orders. Returning only true or false would confuse absence of proof
with proof of absence.

**Resolution:** temporal predicates distinguish entailed, possible, and
excluded outcomes.

### R7 — Nested contexts introduce graph-level consistency constraints

Independent validation of two extents would not detect a child context dated
entirely outside its parent.

**Resolution:** `part_of` introduces temporal containment. Validation rejects
when no consistent interpretation exists; otherwise the assertion restricts
the valid interpretations to those satisfying containment. Exact dates may
remain indeterminate, but containment itself is entailed.

### R8 — Missing intrinsic dates do not imply temporal unconstrainedness

An undated child context may still be temporally bounded by a dated parent.
Saying that absence of `temporal_extent` means "no temporal assertion" would
ignore constraints carried by relations.

**Resolution:** absence means no intrinsic boundary assertion. Relation-derived
constraints remain available and retain their witnesses.

### R9 — Derived relations could be mistaken for asserted facts

Persisting every `before`, `overlaps`, or duration result would duplicate
information and become stale after a date correction.

**Resolution:** temporal relations remain derived query results with witnesses.
They are not inserted into the asserted graph.

### R10 — The existing `status` field is semantically ambiguous

A free-text status cannot safely determine whether a context is temporally
ongoing, completed, or simply documented.

**Resolution:** `status` has no temporal meaning in v0.5. Temporal end state is
part of the typed extent.

### R11 — The version naming could silently reinterpret old candidates

The current executable ontology uses the exact version string `4`, while the
new design uses `0.5`. Reusing the same schema object or accepting both
strings as equivalent would change existing data semantics.

**Resolution:** version identifiers are exact. The predecessor and v0.5 remain
separate schemas, and migration is explicit.

## 4. Logical walkthroughs

### 4.1 Exact order

Context A ends on 30 June 2022. Context B starts on 1 September 2022.

Every valid interpretation places A before B. The result is entailed and a
timeline may display that order.

### 4.2 Coarse order

Context A ends in 2022. Context B starts in 2022.

Some compatible dates place A before B, some make them overlap, and some place B
first. None of those relations is entailed. A query may report possible order
but cannot assert it.

### 4.3 Ongoing observation

A project started in April 2026 and was ongoing as of 17 September 2026.

The model establishes continuation through 17 September. A query executed in
December 2026 cannot claim that the project was active in December unless the
realisation has been updated.

### 4.4 Activity selection

An activity occurs in a context spanning 2022–2025 but has no direct date.

For a query covering the whole 2022–2025 extent, the activity is definitely
situated inside the selected period. For a query restricted to 2024, it is only
a possible match. It must not be described as a year-long activity in 2024.

### 4.5 Nested contradiction

A child context is known to start in 2025 and end in 2026. Its parent is known
to end in 2024.

No temporal interpretation satisfies `part_of(child, parent)`; the
realisation is invalid.

### 4.6 Unknown end

A context started in 2022 and has an unknown end.

It may overlap 2024, but that overlap is not entailed. It must not be labelled
ongoing. The answer remains possible unless other evidence constrains the end.

## 5. Boundary review

The proposal respects the implementation architecture:

- the ontology owns temporal meaning;
- candidates may still carry invalid combinations for diagnostic validation;
- `ValidatedRealisation` remains the trusted boundary;
- queries derive temporal information and retain witnesses;
- `GraphView` remains an immutable selection rather than a presentation;
- the interaction layer chooses timeline or prose rendering.

The temporal value is not an entity because it has no independent identity,
relations, or reuse requirement. Making it a graph node would add navigation
without adding semantic power at this stage.

The proposal also avoids embedding relations in entity fields. The only new
entity property is a typed value; activity–context structure remains expressed
by `occurs_in`.

## 6. Residual limitations and risks

### 6.1 Query API complexity

Entailed/possible/excluded results are more complex than boolean predicates.
The complexity is justified by coarse dates and should be hidden behind small
typed query operations rather than exposed as ad hoc flags everywhere.

### 6.2 Limited activity chronology

Without direct activity extents, the model cannot precisely order two
activities inside one context. This is an acknowledged v0.5 limitation, not an
incorrect inference.

### 6.3 Untimed participation

The model cannot express that a person joined a context late or left early.
No query may infer full-duration participation from `participates_in`.

### 6.4 One connected extent

Seasonal, interrupted, or resumed undertakings require multiple contexts. This
may become awkward, but no current example demonstrates that a union type is
necessary.

### 6.5 Calendar-only resolution

Sub-day events cannot be represented. Career-selection questions do not
currently require them.

## 7. Recommended implementation sequence

1. Introduce and validate the temporal value independently.
2. Add the optional `Context.temporal_extent` property to ontology v0.5.
3. Implement local and `part_of` consistency checks.
4. Add exact and coarse temporal comparison operations.
5. Add context-window selection with explicit match mode.
6. Add activity selection through `occurs_in` witnesses.
7. Update the two-context example and visualization.
8. Add migration diagnostics for legacy `start`, `end`, and `status`.

## 8. Final assessment

The reviewed contract avoids the obvious logical mistakes:

- duration is not confused with location in time;
- missing end is not confused with ongoing;
- coarse dates are not treated as exact;
- activity duration is not copied from context;
- derived order is not stored as fact;
- nested contexts cannot be temporally contradictory;
- old schema versions are not silently reinterpreted.

The remaining limitations are explicit and safe. The contract is ready to guide
the v0.5 implementation.

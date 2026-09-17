---
kind: model_extension_contract
status: reviewed
contract_version: "0.1"
target_ontology_id: caron.career-model
target_ontology_version: "0.5"
predecessor_ontology_version: "4"
scope: context_temporality
---

# Career Model v0.5 — Temporal Extent Contract

## 1. Purpose

Model v0.5 adds a minimal temporal dimension to career realisations.

The extension must support useful chronological selection and comparison without
inventing precision, treating presentation order as semantic order, or creating
a second relation system inside entities.

The first temporal carrier is `Context`. Activities obtain temporal
constraints through `occurs_in`; they do not acquire the full duration of
their context.

This contract specifies model semantics and the observable obligations of
queries. It does not prescribe Python classes, serialization syntax, indexes,
CLI commands, or visualization layout.

## 2. Decisions

Model v0.5 makes the following decisions:

1. A `Context` may have one optional `temporal_extent`.
2. `temporal_extent` is one typed value, not three independent `start`,
   `end`, and `status` properties.
3. A temporal extent describes one connected period.
4. Calendar precision is preserved at year, month, or day granularity.
5. Partial dates constrain a boundary; they are not expanded into falsely exact
   asserted dates.
6. A known end, an unknown end, and an ongoing observation are distinct states.
7. Duration and temporal relations are derived by the query engine.
8. Derived temporal relations are not persisted as ontology assertions.
9. `occurs_in` constrains an activity to its context without assigning the
   context's duration to the activity.
10. Temporal presentation remains an interaction-layer concern.

## 3. Architectural boundary

| Layer | Responsibility |
|---|---|
| Ontology model | Define the temporal value, where it may occur, and the constraints it entails |
| Realisation | Assert known temporal facts while preserving their precision |
| Validation | Reject contradictions and report incomplete or indeterminate temporal information |
| Query engine | Derive comparisons, duration ranges, selections, bindings, and witnesses |
| `GraphView` | Carry the selected asserted facts and the evidence for temporal query results |
| Interaction layer | Choose timelines, ordering, labels, prose, and visual layout |

A renderer may sort contexts by a temporal key, but that display order is not an
asserted `before` relation.

## 4. Temporal domain

### 4.1 Calendar domain

The first temporal domain is the proleptic Gregorian calendar at day
granularity. Time of day and time zones are outside v0.5.

A temporal boundary contains:

- a calendar value;
- a precision: `year`, `month`, or `day`.

The boundary denotes the set of days compatible with the asserted value:

| Boundary | Compatible days |
|---|---|
| `2022` | Any day in calendar year 2022 |
| `2022-06` | Any day in June 2022 |
| `2022-06-15` | The single day 15 June 2022 |

Consequently, the model does not silently interpret `2022` as either
1 January or 31 December. Queries reason over all compatible days.

Precision and uncertainty are not the same concept. Model v0.5 supports
incomplete calendar precision. Expressions such as "approximately June 2022"
or probability distributions over dates remain outside scope.

### 4.2 Temporal extent

A temporal extent contains:

- one required start boundary;
- exactly one end state.

The end state is one of:

- **known end** — an end boundary is asserted;
- **unknown end** — no end and no continuing status are known;
- **ongoing as of** — the context is asserted to be continuing on a recorded,
  exact observation day.

An extent denotes the set of continuous, inclusive day intervals compatible
with its boundaries and end state.

For a known end, a valid interpretation chooses a start day from the start
boundary and an end day from the end boundary such that the start is not after
the end.

For an unknown end, the context is known to have started, but the available
facts do not establish when it ended or whether it continues.

For an ongoing observation, `ongoing_as_of` records the day on which the
context was known to be active. It entails that the context did not end before
that day. It does not assert that the context remains active forever, and its
meaning must not move forward with the system clock.

An ongoing observation therefore carries its own `as_of` day. A query run
later may report that the observation is stale; it may not extend the assertion
without new evidence.

### 4.3 Why duration is not stored

Duration is a result of an extent, not an independent fact in the first model.

When both boundaries identify exact days, an exact elapsed duration can be
derived. With coarse boundaries, the query engine derives a range of possible
durations. For an ongoing context, it may derive duration-so-far as of the
recorded observation day. For an unknown end, a useful duration may be
indeterminate.

Storing both extent and duration would introduce redundant values that could
disagree.

## 5. Attachment to `Context`

A `Context` may carry zero or one `temporal_extent`.

Absence of the property means that the realisation makes no intrinsic boundary
assertion about that context. It does not mean timeless, instantaneous, or
current. Relations such as `part_of` may still constrain its possible time.

One extent represents one connected period. If the same named undertaking has
two genuinely disjoint periods, the first modelling choice is two related
contexts. A future union-of-intervals value may be introduced only if concrete
cases show that separate contexts distort identity.

The existing free-text `status` property has no temporal semantics in v0.5.
It must not be used to infer that a context is ongoing or complete. If retained
for another purpose, that purpose requires a separate definition.

## 6. Semantics of existing relations

### 6.1 `part_of`

If `part_of(child, parent)` is asserted, the child's temporal extent is
constrained to lie within the parent's temporal extent whenever both are
present.

Because boundaries may be coarse or incomplete, the assertion acts as a
constraint on valid interpretations:

- reject the candidate if no interpretation can satisfy temporal containment;
- otherwise retain only interpretations in which the child is contained in the
  parent.

The relation itself therefore entails containment. Coarse boundaries may leave
the exact child and parent dates indeterminate, but interpretations that violate
`part_of` are not valid interpretations of the complete realisation.

The relation does not manufacture intrinsic boundary values. An undated child
of a dated parent remains without its own asserted extent, although
`part_of` bounds its possible time and supplies a query witness.

### 6.2 `occurs_in`

For:

$$
occurs\_in(a, c)
$$

the activity has some occurrence interval contained in the context:

$$
time(a) \subseteq extent(c)
$$

This is a constraint, not an assertion that:

$$
time(a) = extent(c)
$$

Model v0.5 does not add a direct temporal-extent property to `Activity`.
Therefore, the exact date and duration of an activity may remain unknown even
when its context is dated.

If the context has no temporal extent, `occurs_in` supplies no concrete date.

### 6.3 `participates_in`

`participates_in(person, context)` asserts participation in the context. It
does not assert that the person participated throughout the context's full
extent.

Temporal qualification of participation is deferred. Chronology does not make
`performs` derivable from `participates_in` and `occurs_in`.

### 6.4 Other relations

Relations such as `uses`, `takes_input`, `draws_on`, and `produces`
receive temporal relevance through their activity and its `occurs_in`
witness. They do not gain independent timestamps in v0.5.

This permits queries such as "technologies used in contexts overlapping 2024"
without claiming that each technology was used throughout every matching
context.

## 7. Validation obligations

A v0.5 validator must enforce or diagnose the following rules.

### 7.1 Local value rules

1. Every calendar value is valid for its declared precision.
2. A temporal extent has one start and exactly one end state.
3. A known-end extent has at least one compatible interval with
   `start <= end`.
4. An ongoing observation contains an exact `as_of` day and has at least one
   compatible start day not after that observation.
5. An unknown end is not treated as an ongoing observation.
6. A context has at most one temporal extent.
7. A stored duration is not part of the v0.5 temporal contract.

### 7.2 Graph-level rules

1. Temporal constraints introduced by `part_of` must have at least one
   consistent interpretation.
2. Nested `part_of` constraints are considered transitively when checking for
   contradictions.
3. `occurs_in` must not copy a temporal extent onto an activity.
4. A missing temporal extent is incomplete information, not invalidity.
5. Career time is distinct from provenance time such as import, creation, or
   revision timestamps.

Validation should distinguish:

- **invalid** — the asserted facts have no consistent interpretation;
- **indeterminate** — multiple interpretations remain;
- **incomplete** — information useful to a query is absent.

Only invalidity necessarily prevents construction of a
`ValidatedRealisation`. Whether indeterminate or incomplete conditions emit
diagnostics depends on the operation and requested coverage.

## 8. Query semantics

### 8.1 Entailed and possible answers

Temporal predicates are evaluated over all valid interpretations of the
asserted temporal facts.

A result may be:

- **entailed** — true in every valid interpretation;
- **possible** — true in at least one valid interpretation but not all;
- **excluded** — true in no valid interpretation.

For example:

- `definitely_before(A, B)` holds only when every valid interpretation places
  A before B;
- `possibly_before(A, B)` holds when at least one interpretation does;
- overlap and containment follow the same distinction.

The query engine must not collapse `possible` into `entailed`.

### 8.2 Window selection

Temporal selection supports an explicit match mode:

- **definite** — include only results entailed to match the window;
- **possible** — include results with at least one matching interpretation.

The result must expose which mode was used.

For an activity without its own extent:

- if its dated context is wholly constrained inside the query window, the
  activity is definitely situated within the window;
- if its context only partly overlaps the window, the activity is a possible
  match;
- if the context is definitely disjoint, the activity is excluded;
- if the context is undated, the temporal match is unknown rather than false.

### 8.3 Ordering

The query engine may derive a strict partial order from entailed `before`
comparisons.

Overlapping or temporally indeterminate contexts remain unordered by that
semantic relation. A query may additionally return a deterministic display key,
but it must identify that key as presentation support rather than temporal
evidence.

### 8.4 Duration

Duration queries return:

- an exact duration when entailed;
- a bounded range when coarse boundaries permit it;
- duration-so-far tied to a recorded ongoing observation;
- an indeterminate result when no useful bound follows.

Human forms such as "three years" are interaction-layer renderings of those
results.

### 8.5 Witnesses

Every derived temporal result must retain a witness sufficient to explain it.

An activity selected through its context includes at least:

- the activity;
- its `occurs_in` assertion;
- the context;
- the asserted temporal extent;
- the temporal operation and match classification.

A technology selected through an activity additionally retains the relevant
`uses` assertion. This makes uncertainty and inference paths inspectable.

## 9. `GraphView` consequences

A temporal query may return an immutable `GraphView` containing the selected
entities and assertions together with query bindings, witnesses, coverage, and
diagnostics.

The view must not insert `before`, `overlaps`, or duration as though they
were asserted career facts. Derived results belong to query metadata or an
explicit derived-result structure.

A renderer may use the metadata to produce:

- a timeline;
- chronological grouping;
- an activity-centred flow;
- temporal filters;
- warnings for possible or stale results.

Those representations remain replaceable interaction-layer choices.

## 10. Required model scenarios

The contract must be tested against at least these semantic scenarios:

1. Two closed contexts with exact, non-overlapping dates are definitely ordered.
2. Two coarse contexts may be possibly ordered without being definitely
   ordered.
3. An ongoing context records the day on which continuation was observed and
   does not advance automatically.
4. A context with unknown end is not presented as ongoing.
5. A dated child context that cannot fit within its dated parent is invalid.
6. Coarse child and parent dates with at least one containing interpretation
   remain valid; `part_of` removes non-containing interpretations while exact
   dates may remain indeterminate.
7. An activity in a dated context receives a temporal constraint but not the
   context's duration.
8. An activity whose context partly overlaps a window is a possible rather than
   definite match.
9. An undated context remains queryable non-temporally.
10. Temporal facts and provenance timestamps can coexist without being
    confused.

## 11. Versioning and migration

The target ontology identifier remains `caron.career-model`; the new exact
version identifier is `0.5`.

The executable predecessor currently identifies itself with the legacy version
string `4`. Version strings are exact schema identifiers, not numbers to be
compared arithmetically. The predecessor remains a distinct schema; a v0.5
candidate must not be validated silently against it.

The change is not data-compatible for contexts using independent `start`,
`end`, or temporal `status` properties. Migration must be explicit:

- an integer `start` or `end` may become a year-precision boundary;
- a known pair may become a known-end extent if it is consistent;
- free-text `status` must not be converted to an ongoing observation unless a
  dated source supports an `as_of` assertion;
- ambiguous data produces a migration diagnostic rather than an invented date.

Existing validated v4 realisations remain v4 realisations. Validation does not
retroactively change their meaning.

## 12. Deferred concerns

The following are outside v0.5:

- direct temporal extents on activities;
- temporal qualifiers on relations;
- recurring or disconnected extents in one value;
- approximate, fuzzy, or probabilistic dates;
- time of day and time zones;
- a complete implementation of Allen's interval algebra;
- persistence and serialization formats;
- timeline-specific `GraphView` fields;
- reconsideration of `performs`.

## 13. Acceptance criteria

The contract is ready for implementation when:

1. all required scenarios have deterministic examples;
2. generators can exercise valid and invalid temporal values;
3. no query treats coarse precision as exact;
4. no query advances an ongoing observation using the wall clock;
5. activity temporal results retain their `occurs_in` witness;
6. v4 and v0.5 candidates cannot be confused at validation;
7. the interaction layer can render chronology without adding model assertions.

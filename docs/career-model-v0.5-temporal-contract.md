---
kind: model_extension_contract
status: accepted
contract_version: "0.2"
target_ontology_id: caron.career-model
target_ontology_version: "0.5"
predecessor_ontology_version: "4"
scope: context_temporality
---

# Career Model v0.5 — Temporal Extent Contract

## 1. Purpose

Model v0.5 adds a minimal temporal dimension to career realisations.

The extension must support useful chronological selection, comparison, and presentation without inventing precision, treating presentation order as semantic order, or introducing a second relation system inside entities.

The first explicit temporal carrier is `Context`. Activities receive temporal constraints through `occurs_in`; they do not acquire the full temporal extent of their context.

This contract specifies model semantics and the observable obligations of validation and queries. It does not prescribe Python classes, serialization syntax, indexes, CLI commands, or visualization layout.

## 2. Decisions

Model v0.5 makes the following decisions:

1. Every `Context` and `Activity` has a nonempty temporal occurrence, whether or not its boundaries are known.
2. A `Context` may assert zero or one optional `temporal_extent`.
3. `temporal_extent` is one typed value, not a collection of independent `start`, `end`, and `status` properties.
4. A temporal extent describes one connected calendar envelope.
5. A calendar envelope does not assert continuous activity, constant intensity, or effort throughout the represented period.
6. Calendar values use month-level precision and the canonical `YYYY-MM` representation.
7. A known end, an unknown end, and an ongoing observation are distinct states.
8. Relations such as `part_of` and `occurs_in` constrain temporal occurrences without copying temporal extents between entities.
9. Temporal relations and covered-month results are derived by the query engine.
10. Derived temporal information is not persisted as ontology assertions.
11. Temporal presentation remains an interaction-layer responsibility.

## 3. Architectural boundary

| Layer | Responsibility |
|---|---|
| Ontology model | Define temporal values, where they may occur, and the constraints they entail |
| Realisation | Assert known temporal facts without inventing missing months |
| Validation | Reject contradictions and report incomplete or indeterminate temporal information |
| Query engine | Derive comparisons, temporal selections, covered-month results, bindings, and witnesses |
| `GraphView` | Carry selected asserted facts and the evidence for temporal query results |
| Interaction layer | Choose timelines, ordering, labels, prose, and visual layout |

A renderer may sort contexts by a temporal key, but that display order is not an asserted `before` relation.

## 4. Temporal domain

### 4.1 `YearMonth`

The temporal value used by model v0.5 is `YearMonth`.

A `YearMonth` identifies one calendar month in the proleptic Gregorian calendar and is serialized canonically as `YYYY-MM`.

Examples include `2021-11`, `2022-02`, and `2025-10`.

The month component must be between `01` and `12`. Year-only values, day-level values, time-of-day values, and time zones are outside v0.5.

A value such as `2022` must not be interpreted as either `2022-01` or `2022-12`. If the source does not establish a month, the realisation must omit the temporal boundary or report incomplete source information rather than inventing one.

The ordering of `YearMonth` values is their ordinary chronological ordering.

### 4.2 Temporal occurrence

Every `Context` and `Activity` is understood to have some nonempty temporal occurrence.

This occurrence exists as part of the semantics of the entity. Its boundaries do not need to be explicitly known or stored.

An absent `temporal_extent` means that the realisation does not assert intrinsic boundaries for the entity. It does not mean that the entity is timeless, instantaneous, or current.

Relations may constrain an otherwise undated occurrence. For example, an undated child context may be constrained to occur within a dated parent context.

### 4.3 Temporal extent

A temporal extent is an asserted calendar envelope containing one required start month and exactly one end state.

The end state is one of:

- **known end** — an end month is asserted;
- **unknown end** — no end month and no continuing observation are known;
- **ongoing as of** — the context is asserted to be continuing during a recorded observation month.

A known-end extent includes both its start and end months.

```yaml
temporal_extent:
  start: 2021-11
  end:
    known: 2022-02
```

This example represents the calendar envelope containing November 2021, December 2021, January 2022, and February 2022.

The envelope does not assert that activity occurred continuously during every represented month. It establishes temporal location and coverage, not workload or intensity.

For an unknown end, the context is known to have started, but the available facts do not establish when it ended or whether it continues.

For an ongoing observation, `ongoing_as_of` records the month during which the context was known to continue. It entails that the context did not end before that month. It does not assert that the context continues indefinitely.

```yaml
temporal_extent:
  start: 2026-04
  end:
    ongoing_as_of: 2026-09
```

The meaning of an ongoing observation must not advance with the system clock. A later query may report that the observation is stale, but it may not extend the assertion without new evidence.

### 4.4 Connected envelopes

One temporal extent represents one connected calendar envelope.

If the same named undertaking has two genuinely disjoint periods and the gap matters to the questions being asked, the preferred modelling choice is to represent two related contexts.

A future union-of-intervals value may be introduced only if concrete cases show that separate contexts distort the identity of the undertaking.

## 5. Attachment to `Context`

A `Context` may carry zero or one `temporal_extent`.

The temporal extent is an intrinsic property of the context because it describes the calendar envelope of that context itself.

It is not a qualification of `part_of`, `participates_in`, or another relation. A period describing only a person’s participation in a longer context would instead qualify the participation relation and remains outside v0.5.

The existing free-text `status` property has no temporal semantics in v0.5. It must not be used to infer that a context is ongoing or complete.

## 6. Semantics of existing relations

### 6.1 `part_of`

If `part_of(child, parent)` is asserted, the temporal occurrence of the child is contained in the temporal occurrence of the parent:

$$
time(child) \subseteq time(parent)
$$

When both contexts have asserted temporal extents, the child’s envelope must fit within the parent’s envelope.

A candidate is invalid if the asserted extents make containment impossible.

The relation does not manufacture intrinsic boundary values. An undated child of a dated parent remains without its own asserted `temporal_extent`, although its possible occurrence is bounded by the parent and that constraint may support query results.

Nested `part_of` relations constrain time transitively.

### 6.2 `occurs_in`

If `occurs_in(activity, context)` is asserted, the temporal occurrence of the activity is contained in the temporal occurrence of the context:

$$
time(activity) \subseteq time(context)
$$

This does not entail:

$$
time(activity) = time(context)
$$

Model v0.5 does not add a direct `temporal_extent` property to `Activity`. The exact date and duration of an activity may therefore remain unknown even when its context is dated.

If the immediate context is undated but is transitively contained in a dated parent context, the parent may still provide useful temporal bounds for the activity.

### 6.3 `participates_in`

`participates_in(person, context)` asserts participation in the context. It does not assert that the person participated throughout the context’s full temporal extent.

Temporal qualification of participation is deferred.

Chronology does not make `performs` derivable from `participates_in` and `occurs_in`. A person may participate in a context without performing every activity that occurs within it.

### 6.4 Activity-related relations

Relations such as `uses`, `takes_input`, `draws_on`, and `produces` receive temporal relevance through their source activity and the activity’s `occurs_in` witness.

They do not receive independent timestamps in v0.5.

This supports queries such as “technologies used in contexts overlapping 2024” without asserting that a technology was used throughout every matching context.

## 7. Covered-month results

A stored duration is not part of the v0.5 model.

For a known-end extent, the query engine derives an inclusive `covered_month_count`:

```text
covered_month_count = end_month_index - start_month_index + 1
```

For an ongoing context, the query engine derives `covered_month_count_as_of` using the recorded observation month.

For a context with an unknown end, no final covered-month count can be derived.

For an undated child temporally contained in a dated parent, the parent does not supply an exact count. The query engine may instead derive bounds when they are useful. A nonempty child contained in a 37-month parent has a possible covered-month count from 1 through 37 months.

| Temporal information | Derived result |
|---|---|
| Known start and known end | Exact `covered_month_count` |
| Known start and `ongoing_as_of` | Exact `covered_month_count_as_of` tied to the observation month |
| Known start and unknown end | Indeterminate final count |
| Undated nonempty child inside a closed parent | Bounded possible count, not an exact count |
| No usable temporal bound | Unknown count |

A covered-month result describes the size of a calendar envelope at model resolution. It is not a measure of continuous work, effort, or active time.

Human expressions such as “three years” are interaction-layer renderings and must not change the model-level value or imply uninterrupted activity.

## 8. Validation obligations

### 8.1 Local value rules

A v0.5 validator must enforce the following rules:

1. Every temporal value is a canonical, valid `YearMonth`.
2. A temporal extent has one start month and exactly one end state.
3. A known-end extent satisfies `start <= end`.
4. An ongoing extent satisfies `start <= ongoing_as_of`.
5. An unknown end is not treated as an ongoing observation.
6. A context has at most one temporal extent.
7. A stored duration or covered-month result is not part of the v0.5 model.
8. Year-only or day-level boundaries are not valid v0.5 temporal values.

### 8.2 Graph-level rules

A v0.5 validator must enforce or diagnose the following rules:

1. Temporal constraints introduced by `part_of` must admit at least one consistent interpretation.
2. Nested `part_of` constraints must be considered transitively.
3. `occurs_in` must not copy a temporal extent onto an activity.
4. Missing intrinsic boundaries are incomplete information, not invalidity.
5. Career time must remain distinct from provenance time such as import, creation, or revision timestamps.

Validation distinguishes:

- **invalid** — the asserted facts have no consistent interpretation;
- **indeterminate** — the asserted constraints admit multiple relevant interpretations;
- **incomplete** — information useful to an operation is absent.

Only invalidity necessarily prevents construction of a `ValidatedRealisation`. Indeterminate or incomplete conditions may produce diagnostics depending on the requested operation.

## 9. Query semantics

### 9.1 Temporal result classification

A temporal predicate produces one of four observable classifications:

- **entailed** — the predicate holds under every valid interpretation supported by the realisation;
- **possible** — available temporal constraints provide a witness for the predicate in some valid interpretations but not all;
- **excluded** — the predicate holds under no valid interpretation;
- **unknown** — the realisation does not provide enough temporal constraint to evaluate the predicate usefully.

`possible` is reserved for bounded indeterminacy supported by temporal evidence. A completely undated and unconstrained context is classified as `unknown`, rather than being returned as a possible match for every temporal window.

The query engine must not collapse `possible` or `unknown` into `entailed`.

### 9.2 Temporal ordering

For two known closed extents, `before(A, B)` is entailed when `end(A) < start(B)`.

Because both endpoint months are included, two extents that contain the same calendar month are not strictly ordered at model resolution.

The query engine may derive a strict partial order from entailed `before` results.

Overlapping, possibly ordered, or unknown contexts remain unordered by that strict partial order.

A query may additionally return a deterministic display key, but the result must identify it as presentation support rather than temporal evidence.

### 9.3 Window selection

A temporal window is itself an inclusive pair of `YearMonth` values.

Window selection supports at least two match modes:

- **definite** — return only entities whose match is entailed;
- **possible** — return entities whose match is entailed or possible.

Unknown results are not included by default. An operation may expose an explicit `include_unknown` option when the interaction layer needs to show missing temporal coverage.

The result must expose the selected mode and the classification of each returned match.

For an activity without its own temporal extent:

- if its constraining context is wholly contained within the query window, the activity is an entailed match;
- if its constraining context partly overlaps the window, the activity may be a possible match;
- if its constraining context is definitely disjoint from the window, the activity is excluded;
- if no usable temporal constraint is available, the activity’s match is unknown.

The constraining context may be reached through `occurs_in` followed by one or more `part_of` relations.

### 9.4 Derived temporal relations

Relations such as `before`, `overlaps`, and `contained_in_window` are query results, not asserted ontology facts.

The first implementation does not need to expose a complete interval algebra. It only needs the temporal predicates justified by concrete competency questions.

### 9.5 Witnesses

Every derived temporal result must retain a witness sufficient to explain it.

An activity selected through its immediate context includes at least the activity, its `occurs_in` assertion, the context, the asserted temporal extent used as evidence, the temporal operation, and the result classification.

When a dated ancestor context supplies the bound, the witness additionally includes the relevant `part_of` path.

A technology selected through an activity additionally includes the relevant `uses` assertion.

This makes inference paths, missing information, and uncertainty inspectable.

## 10. `GraphView` consequences

A temporal query may return an immutable `GraphView` containing selected entities and assertions together with query bindings, witnesses, coverage information, and diagnostics.

The view must not insert `before`, `overlaps`, or covered-month results as though they were asserted career facts.

Derived temporal results belong to query metadata or an explicit derived-result structure.

A renderer may use this metadata to produce a timeline, chronological grouping, an activity-centred flow, temporal filters, or warnings for possible, unknown, or stale results.

These representations remain replaceable interaction-layer choices.

## 11. Reference instantiation

```yaml
contexts:
  alice_project:
    temporal_extent:
      start: 2021-11
      end:
        known: 2022-02

  phd:
    temporal_extent:
      start: 2022-10
      end:
        known: 2025-10

  synthetic_data_work:
    part_of: phd
```

The reference instantiation entails `before(alice_project, phd)` and excludes `overlaps(alice_project, phd)`.

An activity occurring in `synthetic_data_work` is temporally constrained through `activity → occurs_in → synthetic_data_work → part_of → phd`.

Consequently, an activity occurring in the ALICE project is entailed to precede an activity occurring in the synthetic-data context, even though the synthetic-data context has no intrinsic temporal extent.

The witness for that conclusion must include both activities, both contexts, the `occurs_in` assertions, the `part_of` assertion, and the two asserted temporal extents that establish the ordering.

## 12. Required model scenarios

The contract must be tested against at least these semantic scenarios:

1. The ALICE project from `2021-11` through `2022-02` is definitely before the PhD from `2022-10` through `2025-10`.
2. The ALICE project has an exact `covered_month_count` of 4 and the PhD has an exact count of 37.
3. An undated synthetic-data context contained in the PhD does not inherit the PhD’s exact count; its possible count is bounded from 1 through 37 months.
4. Two contexts containing the same month are not strictly ordered at month resolution.
5. A known-end extent with an end before its start is invalid.
6. An ongoing context records the month in which continuation was observed and does not advance automatically.
7. A context with an unknown end is not presented as ongoing.
8. A dated child context that cannot fit within its dated parent is invalid.
9. An undated child context is temporally bounded by its dated parent without receiving copied intrinsic boundaries.
10. An activity in a dated context receives a temporal constraint but not the context’s complete extent or covered-month count.
11. An activity constrained through an undated child and a dated ancestor retains the complete `occurs_in` and `part_of` witness path.
12. An activity whose constraining context partly overlaps a window is a possible rather than entailed match.
13. A temporally unconstrained context produces an unknown temporal result rather than a false result.
14. Temporal facts and provenance timestamps coexist without being confused.

## 13. Versioning and migration

The ontology identifier remains `caron.career-model`. The new exact version identifier is `0.5`.

The executable predecessor currently identifies itself with the legacy version string `4`. Version strings are exact schema identifiers and are not compared arithmetically.

A v0.5 candidate must not be validated silently against the predecessor schema.

The change is not data-compatible for contexts using independent `start`, `end`, or temporal `status` properties.

Migration must be explicit:

- an existing canonical month value may become a v0.5 `YearMonth`;
- a known pair of month values may become a known-end extent if it is consistent;
- a year-only value must not be assigned an invented month;
- a free-text status must not be converted to an ongoing observation unless a dated source supports an `ongoing_as_of` month;
- ambiguous or insufficient source data produces a migration diagnostic.

Existing validated v4 realisations remain v4 realisations. Validation does not retroactively change their meaning.

## 14. Deferred concerns

The following remain outside v0.5:

- direct temporal extents on activities;
- temporal qualifiers on relations;
- participation periods;
- recurring or disconnected extents in one value;
- year-only, day-level, time-of-day, or time-zone values;
- approximate, fuzzy, or probabilistic dates;
- active-effort or workload duration;
- a complete implementation of interval algebra;
- persistence and serialization formats;
- timeline-specific `GraphView` fields;
- reconsideration of `performs`.

## 15. Acceptance criteria

The contract is ready for implementation when:

1. all required scenarios have deterministic examples;
2. generators can exercise valid and invalid `YearMonth` values and temporal extents;
3. no operation invents a month from a year-only source;
4. no operation interprets a calendar envelope as continuous effort;
5. no query advances an ongoing observation using the wall clock;
6. temporal query results distinguish entailed, possible, excluded, and unknown;
7. exact and bounded covered-month results remain distinguishable;
8. activity temporal results retain their complete `occurs_in` and `part_of` witness paths;
9. derived temporal relations and covered-month results remain separate from asserted ontology facts;
10. v4 and v0.5 candidates cannot be confused during validation;
11. the interaction layer can render chronology without adding model assertions.

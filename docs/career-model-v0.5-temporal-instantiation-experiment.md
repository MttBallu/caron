---
kind: model_instantiation_experiment
status: completed
model_id: caron.career-model
model_version: "0.5"
contract_version: "0.2"
implementation_at_time: not_implemented
---

# Career Model v0.5 — Temporal Instantiation Experiment

## 1. Objective

This experiment tests whether the v0.5 temporal contract produces useful query information from a small career realisation without placing presentation logic in the query engine.

The experiment uses three career periods connected by practical use of Python: the ALICE data-analysis project, PhD synthetic-data work, and the `jax-geopro` project.

No Python implementation is exercised. The experiment evaluates the model, the realisation, the expected query classifications, and the witnesses a future query engine must return.

The experiment was subsequently implemented as the first v0.5 executable temporal slice. This report retains the pre-implementation reasoning against which that implementation is tested.

## 2. Realisation under test

### 2.1 Entities

```yaml
entities:
  - id: person:matteo
    kind: Person
    label: Mattéo

  - id: context:alice-project
    kind: Context
    label: ALICE data-analysis project
    temporal_extent:
      start: 2021-11
      end:
        known: 2022-02

  - id: context:phd
    kind: Context
    label: PhD in nuclear physics
    temporal_extent:
      start: 2022-10
      end:
        known: 2025-10

  - id: context:synthetic-data-work
    kind: Context
    label: Synthetic-data generation work

  - id: context:jax-geopro
    kind: Context
    label: jax-geopro project
    temporal_extent:
      start: 2026-04
      end:
        ongoing_as_of: 2026-09

  - id: activity:analyse-alice-data
    kind: Activity
    label: Analyse ALICE collision data

  - id: activity:build-synthetic-dataset
    kind: Activity
    label: Build a labelled synthetic training dataset

  - id: activity:implement-discrete-measure-losses
    kind: Activity
    label: Implement losses for discrete measures

  - id: technology:python
    kind: Technology
    label: Python

  - id: technology:jax
    kind: Technology
    label: JAX

  - id: artifact:training-dataset
    kind: Artifact
    label: Labelled synthetic training dataset
```

### 2.2 Asserted relations

```yaml
relations:
  - kind: part_of
    source: context:synthetic-data-work
    target: context:phd

  - kind: participates_in
    source: person:matteo
    target: context:alice-project

  - kind: participates_in
    source: person:matteo
    target: context:phd

  - kind: participates_in
    source: person:matteo
    target: context:jax-geopro

  - kind: performs
    source: person:matteo
    target: activity:analyse-alice-data

  - kind: performs
    source: person:matteo
    target: activity:build-synthetic-dataset

  - kind: performs
    source: person:matteo
    target: activity:implement-discrete-measure-losses

  - kind: occurs_in
    source: activity:analyse-alice-data
    target: context:alice-project

  - kind: occurs_in
    source: activity:build-synthetic-dataset
    target: context:synthetic-data-work

  - kind: occurs_in
    source: activity:implement-discrete-measure-losses
    target: context:jax-geopro

  - kind: uses
    source: activity:analyse-alice-data
    target: technology:python

  - kind: uses
    source: activity:build-synthetic-dataset
    target: technology:python

  - kind: uses
    source: activity:implement-discrete-measure-losses
    target: technology:python

  - kind: uses
    source: activity:implement-discrete-measure-losses
    target: technology:jax

  - kind: produces
    source: activity:build-synthetic-dataset
    target: artifact:training-dataset
```

Only the three outer career contexts assert temporal extents. The synthetic-data context and all activities remain intrinsically undated.

## 3. Experiment A — Validate the realisation

### Question

Does the realisation satisfy the local and graph-level temporal constraints?

### Result

The expected result is `valid`.

- Each asserted value is a canonical `YearMonth`.
- Every known end is not earlier than its start.
- The ongoing observation is not earlier than its start.
- The undated synthetic-data context is allowed.
- `part_of(synthetic_data_work, phd)` has consistent temporal interpretations.
- No extent is copied onto the synthetic-data context or its activity.

### Adversarial variation

If `synthetic_data_work` asserted `2025-11` through `2026-01`, validation would fail because no interpretation could place that child extent inside the PhD ending in `2025-10`.

## 4. Experiment B — Derive covered-month results

### Query

Return the covered-month result for each context.

### Expected result

| Context | Result kind | Value | Basis |
|---|---|---:|---|
| ALICE project | exact | 4 months | `2021-11` through `2022-02`, inclusive |
| PhD | exact | 37 months | `2022-10` through `2025-10`, inclusive |
| Synthetic-data work | bounded possible | 1–37 months | Nonempty occurrence contained in the PhD |
| `jax-geopro` | exact as of observation | 6 months | `2026-04` through `2026-09`, inclusive |

The synthetic-data result must not be reported as exactly 37 months. Temporal containment supplies an upper bound, not equality with the parent extent.

The `jax-geopro` result is tied to `ongoing_as_of: 2026-09`. Running the same query later must still return 6 months until the observation is explicitly updated.

## 5. Experiment C — Order the contexts

### Query

Return entailed strict temporal ordering between the contexts.

### Expected result

```text
alice_project < phd < jax_geopro
alice_project < synthetic_data_work < jax_geopro
```

The order between `synthetic_data_work` and its parent `phd` is not strict: the child is contained in the parent and may share either or both boundary months.

### Witness for ALICE before synthetic-data work

```text
extent(alice_project) ends 2022-02
extent(phd) starts 2022-10
part_of(synthetic_data_work, phd)
therefore time(synthetic_data_work) is contained in 2022-10..2025-10
therefore before(alice_project, synthetic_data_work) is entailed
```

This confirms that useful ordering can be derived through relation composition without assigning invented dates to the child context.

## 6. Experiment D — Reconstruct the Python trajectory

### Question

What evidence shows practical use of Python, and what temporal order can be established between those uses?

### Expected selection

The query selects the shared `technology:python`, the three activities using it, their contextual paths, and the temporal evidence needed to situate those activities.

| Activity | Contextual path | Temporal classification |
|---|---|---|
| Analyse ALICE collision data | `occurs_in → alice_project` | Bounded by `2021-11..2022-02` |
| Build a labelled synthetic training dataset | `occurs_in → synthetic_data_work → part_of → phd` | Bounded by `2022-10..2025-10` |
| Implement losses for discrete measures | `occurs_in → jax_geopro` | Not before `2026-04`; the ongoing observation does not supply a final upper bound for the activity |

The following ordering is entailed:

```text
analyse_alice_data
    < build_synthetic_dataset
    < implement_discrete_measure_losses
```

The result does not create a primitive `PythonExperience` entity and does not assert a direct transfer relation between contexts. The shared Python node and the composed temporal witnesses are sufficient.

### Required `GraphView` content

The immutable result view must contain the selected entities and asserted relations, plus derived metadata recording the ordering, classifications, and witnesses.

The renderer may translate that result into a chronological trajectory, but it must not add `before` edges to the asserted graph.

## 7. Experiment E — Select activities by temporal window

### Window 1: `2021-11` through `2022-02`

| Activity | Classification | Reason |
|---|---|---|
| Analyse ALICE collision data | entailed | Its entire constraining context lies inside the window |
| Build a labelled synthetic training dataset | excluded | Its parent temporal bound starts after the window |
| Implement losses for discrete measures | excluded | Its context starts after the window |

### Window 2: `2022-01` through `2022-12`

| Activity | Classification | Reason |
|---|---|---|
| Analyse ALICE collision data | possible | Its context partly overlaps the window, but the activity itself is undated |
| Build a labelled synthetic training dataset | possible | Its parent bound overlaps the window, but the child and activity are undated |
| Implement losses for discrete measures | excluded | Its context starts in 2026 |

### Window 3: `2022-10` through `2025-10`

| Activity | Classification | Reason |
|---|---|---|
| Analyse ALICE collision data | excluded | Its context ends before the window |
| Build a labelled synthetic training dataset | entailed | Its complete possible occurrence is constrained inside the PhD window |
| Implement losses for discrete measures | excluded | Its context starts after the window |

These cases confirm that an activity inherits constraints from its context without inheriting the context’s exact extent.

## 8. Experiment F — Distinguish possible and unknown

Add an undated standalone context with no dated parent and an activity occurring in it.

For every temporal window, that activity receives the classification `unknown`, not `possible` or `excluded`.

By contrast, the synthetic-data activity can receive `possible` because the PhD supplies a finite evidential bound.

This distinction prevents temporally unconstrained entities from polluting every possible-match query.

## 9. Findings

### 9.1 Successful aspects

The month-level temporal domain is sufficient for the tested career questions. It supports chronology, temporal windows, ongoing observations, and readable CV-scale results without day-level precision.

The distinction between intrinsic extents and relational constraints works as intended. The synthetic-data context remains intrinsically undated while still receiving useful temporal bounds through `part_of`.

The experiment demonstrates the relevance of relation composition. The query engine can derive an ordered Python trajectory through `uses`, `occurs_in`, and `part_of` without adding domain-specific transfer relations.

`covered_month_count` is useful when its result shape preserves epistemic status. Exact, observation-relative, bounded, indeterminate, and unknown results must remain distinguishable.

### 9.2 Important limitation

An activity constrained by a dated context is not assumed to occupy the complete context. Consequently, partial overlap between the context and a query window generally produces a possible activity match rather than an entailed one.

This is not missing information that the query engine should hide. It is an important semantic distinction that the `GraphView` and interaction layer should be able to explain.

### 9.3 Contract adjustment confirmed by the experiment

The duration operation should be named and represented as a covered-month result rather than generic duration. For an undated child inside a dated parent, the appropriate result is a bound such as `1..37`, not the parent’s exact value.

No additional temporal entity type or relation qualifier is required for the tested cases.

## 10. Conclusion

The v0.5 temporal contract is adequate for the first executable spine once it supports exact and bounded covered-month results as distinct query outputs.

The next implementation slice can remain small: `YearMonth`, `TemporalExtent`, local validation, containment validation, covered-month result values, basic ordering and window predicates, and witness-preserving `GraphView` metadata.

This experiment does not justify activity extents, relation-level temporal qualifiers, a complete interval algebra, or temporal persistence decisions.

---
kind: query_contract_experiment
status: draft
date: 2026-09-22
milestone: M2-A
ontology_id: caron.career-model
ontology_version: "5.0"
proposed_query: ReusableEntityEvidence
---

# M2-A — Reusable Entity Evidence: Contract Experiment

## 1. Question and method

The motivating question was: “Which activities demonstrate a person’s use or
learning of a technology, method, subject, or language—and in what context?”
Ontology `5.0` exposes a problem with that formulation: `learns` identifies a
Person, a Learnable target, and a Context, but need not identify an Activity.
The first query question is therefore:

> Which represented facts connect this person to this Technology, Method,
> Subject, or Language through learning or through an activity involving it,
> and in what local context does each fact occur?

This experiment starts with small positive and adversarial realisations. It
specifies the expected answer and witness for each case, then proposes the
smallest typed request that produces them. Failure is diagnosed at the source,
ontology, query, interpretation, or presentation layer before considering an
ontology change. The query returns represented structural support. It does not
evaluate ability, mastery, provenance, or truth of the source account.

Sources of current authority: [ontology `5.0`](career-ontology-v5.0-specification.md),
[`CURRENT.md`](../CURRENT.md), and the private
[`test_query_algebra.py`](../tests/unit/test_query_algebra.py) experiment.

## 2. The two permitted evidence shapes

```yaml
learning:
  asserted_fact: learns(Person, Learnable; context=Context)
  returned_context: the assertion's required context qualifier
  witness: the identified learns assertion, including its qualifier
  activity: unspecified

activity_involving_resource:
  joined_asserted_facts:
    - performs(Person, Activity)
    - occurs_in(Activity, Context)
    - activity_resource_relation(Activity, Learnable)
  returned_context: the Activity's unique most-local occurs_in target
  witness: all three identified assertions
  attribution: >
    The Person performed an Activity involving the target. With several
    performers, this does not identify which performer individually handled it.
```

The allowed activity-resource relation depends on the target kind:

| Target kind | Allowed relation kind(s) | Meaning retained in the row |
| --- | --- | --- |
| `Technology` | `uses_technology` | practical use by the Activity |
| `Language` | `uses_language` | language used by the Activity |
| `Method` | `applies`, `draws_on` | operational application or conceptual reliance, respectively |
| `Subject` | `draws_on` | conceptual or intellectual reliance |

`exposed_to` and `native_language` do not produce a row in this request.
`uses_artifact` targets an Artifact and is outside the target domain. The
activity relation does not entail `learns`, and `learns` does not entail any
activity relation. The word *use* must not flatten `draws_on` into `applies`.

## 3. Ten-case expected-result suite

The following YAML describes minimal **separate** valid realisations. IDs such
as `p`, `x`, and `u1` are fixture-local. Each case requests `person_id: p` and
`target_id: x`. Every entity has its required `label`,
omitted here because labels do not affect these matches. Each activity has at
least one `performs` and exactly one `occurs_in` fact. A row's `relations` list
is its complete minimal structural witness. A row's `entities` list includes
every entity referenced by those assertions, including qualifiers. Every
`properties` witness is empty because this request performs no property lookup.
Fixture row labels are test
handles, not promised persistent query-result identifiers.

```yaml
cases:
  - id: C01_learning_without_activity
    entities: {p: Person, x: Technology, c: Context}
    facts:
      l1: {kind: learns, source: p, target: x, qualifiers: {context: c}}
    expected_rows:
      - {label: learning, kind: learning, context: c,
         relations: [l1], entities: [p, x, c]}
    forbidden: [invented_activity, inferred_uses_technology]

  - id: C02_activity_without_learning
    entities: {p: Person, x: Technology, a: Activity, c: Context}
    facts:
      p1: {kind: performs, source: p, target: a}
      o1: {kind: occurs_in, source: a, target: c}
      u1: {kind: uses_technology, source: a, target: x}
    expected_rows:
      - {label: activity, kind: activity_involving_resource, activity: a,
         context: c, involvement: uses_technology, relations: [p1, o1, u1],
         entities: [p, a, c, x]}
    forbidden: [inferred_learns, materialized_person_uses_technology]

  - id: C03_coexistence_without_sequence
    entities: {p: Person, x: Technology, a: Activity, c: Context}
    facts:
      l1: {kind: learns, source: p, target: x, qualifiers: {context: c}}
      p1: {kind: performs, source: p, target: a}
      o1: {kind: occurs_in, source: a, target: c}
      u1: {kind: uses_technology, source: a, target: x}
    expected_rows:
      - {label: learning, kind: learning, context: c,
         relations: [l1], entities: [p, x, c]}
      - {label: activity, kind: activity_involving_resource, activity: a,
         context: c, involvement: uses_technology, relations: [p1, o1, u1],
         entities: [p, a, c, x]}
    forbidden: [learned_through_a, learning_preceded_a, a_caused_learning]

  - id: C04_method_has_two_distinct_roles
    entities: {p: Person, x: Method, a: Activity, c: Context}
    facts:
      p1: {kind: performs, source: p, target: a}
      o1: {kind: occurs_in, source: a, target: c}
      m1: {kind: applies, source: a, target: x}
      m2: {kind: draws_on, source: a, target: x}
    expected_rows:
      - {label: application, kind: activity_involving_resource, activity: a,
         context: c, involvement: applies, relations: [p1, o1, m1],
         entities: [p, a, c, x]}
      - {label: reliance, kind: activity_involving_resource, activity: a,
         context: c, involvement: draws_on, relations: [p1, o1, m2],
         entities: [p, a, c, x]}
    forbidden: [merged_generic_method_use]

  - id: C05_exposure_only
    entities: {p: Person, x: Technology, c: Context}
    facts:
      e1: {kind: exposed_to, source: p, target: x, qualifiers: {context: c}}
    expected_rows: []
    coverage: {status: selective, scope: fixture_career}
    forbidden: [inferred_learning, inferred_activity_use, career_absence_claim]

  - id: C06_shared_activity
    entities: {p: Person, group: Collective, x: Technology,
               a: Activity, c: Context}
    facts:
      p1: {kind: performs, source: p, target: a}
      p2: {kind: performs, source: group, target: a}
      o1: {kind: occurs_in, source: a, target: c}
      u1: {kind: uses_technology, source: a, target: x}
    expected_rows:
      - {label: shared_activity, kind: activity_involving_resource,
         activity: a, context: c, involvement: uses_technology,
         relations: [p1, o1, u1], entities: [p, a, c, x]}
    excluded_from_minimal_witness: [p2]
    forbidden: [p_personally_operated_x]
    variant:
      remove_facts: [p1]
      add_fact:
        membership: {kind: collective_membership, source: p, target: group,
                     qualifiers: {context: c, role: member}}
      expected_rows: []
      reason: Membership does not imply personal performance.

  - id: C07_same_displayed_binding_two_supports
    entities: {p: Person, x: Technology, a1: Activity, a2: Activity,
               c: Context}
    facts:
      p1: {kind: performs, source: p, target: a1}
      o1: {kind: occurs_in, source: a1, target: c}
      u1: {kind: uses_technology, source: a1, target: x}
      p2: {kind: performs, source: p, target: a2}
      o2: {kind: occurs_in, source: a2, target: c}
      u2: {kind: uses_technology, source: a2, target: x}
    expected_rows:
      - {label: first, kind: activity_involving_resource, activity: a1,
         context: c, involvement: uses_technology, relations: [p1, o1, u1],
         entities: [p, a1, c, x]}
      - {label: second, kind: activity_involving_resource, activity: a2,
         context: c, involvement: uses_technology, relations: [p2, o2, u2],
         entities: [p, a2, c, x]}
    grouped_display_if_requested:
      binding: {person: p, target: x, context: c}
      alternative_support_sets: [[p1, o1, u1], [p2, o2, u2]]
    forbidden: [silent_distinct_or_union_of_witnesses_as_one_path]

  - id: C08_empty_selective_realisation
    entities: {p: Person, x: Technology}
    facts: {}
    coverage: {status: selective, scope: fixture_career}
    expected_rows: []
    expected_view: {entities: [], relations: []}
    forbidden: [person_never_learned_x, person_never_used_x]

  - id: C09_nested_contexts_do_not_merge_local_facts
    entities: {p: Person, x: Technology, a: Activity,
               child: Context, parent: Context}
    facts:
      l1: {kind: learns, source: p, target: x,
           qualifiers: {context: parent}}
      p1: {kind: performs, source: p, target: a}
      o1: {kind: occurs_in, source: a, target: child}
      u1: {kind: uses_technology, source: a, target: x}
      h1: {kind: part_of, source: child, target: parent}
    expected_rows:
      - {label: learning, kind: learning, context: parent,
         relations: [l1], entities: [p, x, parent]}
      - {label: activity, kind: activity_involving_resource, activity: a,
         context: child, involvement: uses_technology,
         relations: [p1, o1, u1], entities: [p, a, child, x]}
    excluded_from_local_witness: [h1]
    forbidden: [rewritten_activity_context_parent, same_local_context_claim]

  - id: C10_overlapping_context_extents_do_not_order_facts
    entities:
      p: {kind: Person}
      x: {kind: Technology}
      a: {kind: Activity}
      learning_context: {kind: Context,
                         temporal_extent: {start: 2024-01, end: 2024-06}}
      activity_context: {kind: Context,
                         temporal_extent: {start: 2024-03, end: 2024-12}}
    facts:
      l1: {kind: learns, source: p, target: x,
           qualifiers: {context: learning_context}}
      p1: {kind: performs, source: p, target: a}
      o1: {kind: occurs_in, source: a, target: activity_context}
      u1: {kind: uses_technology, source: a, target: x}
    expected_rows:
      - {label: learning, kind: learning,
         context: learning_context, relations: [l1],
         entities: [p, x, learning_context]}
      - {label: activity, kind: activity_involving_resource, activity: a,
         context: activity_context, involvement: uses_technology,
         relations: [p1, o1, u1], entities: [p, a, activity_context, x]}
    forbidden: [learning_preceded_activity, established_transfer]
```

The C02 activity shape is also parametrically tested with `Language` and
`uses_language`, `Method` and either of its two permitted roles, and `Subject`
with `draws_on`. C01 learning is valid for all four target kinds. These variants
verify the endpoint family without introducing four different public queries.

The `temporal_extent` mapping in C10 is descriptive fixture notation: an
executable fixture constructs the exact `TemporalExtent` value objects before
validation. None of the ten cases assumes that a relation holds throughout its
context extent.

## 4. Candidate typed public request

```yaml
name: ReusableEntityEvidence
profile_status: proposed for M2-A; no accepted public version yet
input:
  source: ValidatedRealisation of exact caron.career-model/5.0
  person_id: existing Person entity identifier
  target_id: existing Technology, Method, Subject, or Language identifier
selection:
  contexts: all represented local contexts
  evidence: learns and directly performed activities involving the target
  temporal_filter: none in this first request
  inherited_context_projection: none in this first request
output:
  source_ontology_id_and_version: exact values from the source
  source_realisation_id: exact value from the source
  request_identity_and_parameters: retained
  rows: one per distinct minimal support described in section 2
  graph_view: reference-closed selection from the surviving row witnesses
  coverage: unchanged source coverage, with query scope made explicit
  diagnostics: structured findings; empty rows are a successful evaluation
```

`Person` and target validation occurs after binding the typed request to the
validated realisation. A public request does not contain a graph pattern or
raw algebra plan. Internal plans must be checked against the source schema
before the evaluator receives them; the plan representation is not part of
this proposed public compatibility surface.

`LearningEvidence` contains the `learns` assertion ID and the Context
reference from its qualifier. `ActivityEvidence` contains the three assertion
IDs and the activity-resource relation kind. The result never emits a new
positive Person-to-resource assertion. Row order has no temporal meaning.
The initial request returns all minimal rows; a later grouping operation may
show one displayed binding only if it retains each alternative support set.

The graph view contains every entity and relation referenced by a surviving
row and closes over entity-reference qualifiers and selected reference-valued
properties. Its relation records retain their original directions and kinds.
The view may contain a union of several rows' records, while the rows retain
the exact witness-to-answer mapping. With no rows the evidence view is empty;
the request parameters and coverage remain in the result envelope.

## 5. Request diagnostics and absence behavior

These codes are **proposed** for this experiment. A structurally well-formed
request is validated against the selected realisation before evaluation.
Rejected requests have no evidence rows or graph view. Tests should depend on
codes and target identities, not diagnostic prose.

| Condition | Proposed code | Outcome |
| --- | --- | --- |
| The source ontology ID or exact version is unsupported | `query.unsupported_ontology` | Reject request |
| `person_id` does not resolve | `query.unknown_person` | Reject request |
| `person_id` resolves to another concept kind | `query.invalid_person_kind` | Reject request |
| `target_id` does not resolve | `query.unknown_target` | Reject request |
| `target_id` resolves outside `Learnable` | `query.invalid_target_kind` | Reject request |
| Valid request, no matching facts | No error code; `rows: []` | Successful empty result |
| Selective or unknown coverage | Preserve coverage; no automatic absence diagnostic | Qualification of interpretation |

Cases C01–C04, C06–C07, and C09–C10 succeed with the rows specified above and
no diagnostic. C05, C08, and the collective-only variant of C06 succeed with
empty rows and no error diagnostic. Their coverage remains in the result.
Separate request-boundary probes supply an unknown `person_id`, a non-Person
`person_id`, an unknown `target_id`, a target of kind `Artifact`, and a source
realisation of another ontology version; each must produce the corresponding
code above before evaluation. A caller offering an unsupported operation to an
application dispatcher is outside this single typed request's boundary.

The source is already a `ValidatedRealisation`. Invalid relation endpoints,
missing required qualifiers, duplicate semantic facts, and invalid activity
cardinality belong to candidate validation, not query diagnostics. Unsupported
or ill-typed private execution plans belong to a separate schema-aware plan
validation gate; they cannot silently reach the evaluator.

An empty result under `complete_within_scope` still needs a scope applicable to
the requested person, target, and relation kinds before an absence statement
can be licensed. The current `Coverage` value carries a status and free-text
scope, so this request does not itself make machine-checked absence claims.

## 6. Acceptance checks and remaining choices

```yaml
acceptance_checks:
  - All ten cases yield exactly the specified rows and minimal relation witnesses.
  - Learning-only rows include their qualifier Context in witness and view closure.
  - The four Learnable kinds produce only their licensed activity relation kinds.
  - Direct personal performance is required for an activity row.
  - Distinct support sets survive projection, grouping, and graph-view creation.
  - Every selected relation retains its source identity and semantic references.
  - Empty successful results retain source identity, request, and coverage.
  - No unchecked internal plan reaches evaluation.
  - No result creates a positive ontology assertion or ability claim.

deferred_to_later_queries:
  - encountered-resource histories that explicitly include exposed_to
  - context ancestry or multi-parent path alternatives in displayed scope
  - temporal-window selection and partial ordering of learning and activities
  - causal transfer, expertise, relevance, or ability interpretation
  - provenance and truth assessment of the asserted career facts
```

The current private algebra covers the C01/C02 union and C08 coverage behavior
for a GEANT4 fixture, but its public `BindingTable` values do not themselves
identify the witness carried by each algebra row. Its experimental history
pattern also omits `uses_language`. This draft tests those gaps and the
multi-performer, alternative-support, and temporal counterexamples before an
API shape is stabilized. No ontology `5.0` change is indicated by these cases.

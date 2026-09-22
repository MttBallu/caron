---
kind: ontology_specification
status: proposed_for_m1c_acceptance
date: 2026-09-21
ontology_id: caron.career-model
ontology_version: "5.0"
concept_count: 13
relation_count: 31
conceptual_predecessor: Career Model 4.2
executable_predecessors:
  - "4"
  - "0.5"
decision_record: career-ontology-m1b-semantic-decisions.md
implementation_status: not_implemented
current_package_version: "0.1.0"
next_gate: m1c_review_and_acceptance
---

# Career Ontology 5.0 — Normative Specification

## 1. Status and purpose

This document specifies the exact ontology identified by:

```yaml
ontology:
  id: caron.career-model
  version: "5.0"
```

It integrates the adopted semantic vocabulary of Career Model 4.2, the
month-level temporal contract implemented by ontology `0.5`, and the decisions
accepted in the
[M1-B semantic decision record](career-ontology-m1b-semantic-decisions.md).

The source authority order for this integration is:

1. this specification, once accepted, for exact ontology `5.0` meaning;
2. M1-B for the semantic choices that produced it;
3. the [M1-A reconciliation](career-ontology-m1a-reconciliation.md) for the
   classified lineage and gaps;
4. the
   [ontology `0.5` temporal contract](career-model-v0.5-temporal-contract.md)
   for the incorporated temporal semantics;
5. Career Model 4.2 for the adopted conceptual inventory.

Earlier documents remain authoritative for their own historical artifacts and
preserved ontology versions. They do not override this specification's `5.0`
clauses after acceptance.

This is an ontology specification, not an implementation description. It
defines the concepts, properties, relations, qualifiers, invariants, and
non-inferences that determine whether a candidate is a valid ontology `5.0`
realisation. It does not prescribe Python classes, serialization syntax,
storage, query plans, visual layout, or interaction workflows.

The current `caron` package remains version `0.1.0` and does not yet implement
this ontology. A package must not expose `5.0` as an accepted schema until all
conformance obligations in section 16 are implemented and tested.

The terms **MUST**, **MUST NOT**, **SHOULD**, and **MAY** express normative
requirements in this document.

## 2. Modeling boundary

Ontology `5.0` preserves four distinct layers:

| Layer | Responsibility |
|---|---|
| Meta-model | Defines constructs such as concept, property, relation, qualifier, cardinality, and invariant |
| Ontology | Defines the exact career-domain vocabulary and validity rules in this document |
| Realisation | Contains particular entities and positive relation assertions conforming to the ontology |
| Query and interpretation | Derives selections, histories, claims, patterns, narratives, and explanations with witnesses |

Assertions carrying polarity, confidence, provenance, or source-state version
remain outside the positive realisation contract. Realisation evolution,
transactions, serialization, persistence, and application state also remain
separate contracts.

In particular, ontology `5.0` does not introduce primitive entities for
`Skill`, `Experience`, `Ability`, `Capability`, `Expertise`, `Transfer`,
`RecurringPattern`, `CareerNarrative`, or an external job requirement. These
are derived or interpretive constructs.

## 3. Identity, lineage, and compatibility

The ontology family identifier is stable; exact version strings identify
immutable schemas.

| Identifier | Status in this lineage |
|---|---|
| Model 4.2 | Historical conceptual predecessor and semantic inventory |
| `caron.career-model` version `4` | Preserved compact compatibility schema |
| `caron.career-model` version `0.5` | Preserved compact schema with accepted month-level temporality |
| `caron.career-model` version `5.0` | This integrated ontology generation |

The strings `4`, `0.5`, and `5.0` MUST be compared exactly, not numerically.
Existing `4` and `0.5` realisations retain their original meaning. They MUST
NOT be relabelled as `5.0` without explicit migration and validation.

Ontology versions and `caron` distribution versions are independent. One
package release MAY support several exact ontology versions and migrations.

## 4. Core semantic hypothesis

> A career is a non-linear graph of meaningful contexts in which agents
> participate and perform activities. Activities use resources, produce or
> modify artifacts, and participate in intentional, epistemic, and explanatory
> structures. Reusable entities retain identity across contexts and thereby
> permit cross-context histories to be reconstructed.

Ontology `5.0` represents contextual career evidence. It does not store a
decontextualized mutable skill profile or a universal linear progression.
Higher-level answers MUST remain traceable to represented entities and
relation assertions, and graph composition MUST NOT manufacture stronger
meaning than the asserted relations license.

## 5. Meta-model profile and record identity

Ontology `5.0` is expressed using:

- concept definitions with typed properties;
- identified binary relation assertions with typed endpoints;
- typed relation qualifiers;
- local cardinality requirements;
- global graph and semantic invariants.

A realisation entity has a stable nonempty identifier, exactly one concept
kind, and the properties allowed for that concept. A relation assertion has a
stable nonempty identifier, exactly one relation kind, one source reference,
one target reference, and the qualifiers allowed for that relation kind.

Entity identifiers MUST be unique within the entity namespace of one
realisation. Relation assertion identifiers MUST be unique within the relation
namespace. An entity property or relation qualifier name MUST occur at most
once on its owning record.

All entity and qualifier references MUST resolve to entities present in the
same candidate and of an allowed kind. Unknown concepts, properties, relation
kinds, qualifiers, or value kinds make a candidate invalid.

One identified relation assertion represents one complete qualified fact.
Qualifier legs MUST NOT be decomposed into independent assertions that could
be added, removed, or versioned separately from that fact.

## 6. Value domains

### 6.1 Text

Required text values MUST contain at least one non-whitespace character.
Ontology `5.0` uses text for human-readable labels, proposition content, and
open role vocabularies.

### 6.2 Entity reference

An entity reference identifies another entity in the same candidate.
Reference-valued properties and qualifiers participate in endpoint closure and
kind validation even though they are not separate relation assertions.

### 6.3 `YearMonth`

`YearMonth` identifies one calendar month in the proleptic Gregorian calendar.
Its canonical lexical form is `YYYY-MM`, with a month from `01` through `12`.
Year-only, day-level, time-of-day, and timezone values are not valid `YearMonth`
values. Missing precision MUST NOT be replaced by an invented month.

### 6.4 `TemporalExtent`

A `TemporalExtent` represents one connected, inclusive calendar envelope. It
contains one required start month and exactly one of these end states:

- `known`: an asserted end month;
- `unknown`: no end or continuing observation is known;
- `ongoing_as_of`: continuation was observed in the stated month.

For a known end, `start <= known` MUST hold. For an ongoing observation,
`start <= ongoing_as_of` MUST hold. An ongoing observation is fixed evidence
and MUST NOT advance with the system clock.

A temporal extent locates an occurrence in calendar time. It does not assert
continuous work, constant intensity, workload, or effort throughout the
envelope. Covered-month counts and temporal relations such as `before` or
`overlaps` are derived query results, not stored ontology facts.

## 7. Concept catalogue

Every entity has exactly one required nonempty `label` text property. The
additional properties below are exact; ontology `5.0` has no generic
`Context.status`, independent `start` or `end`, or direct credential date
property.

If future cases require non-temporal states such as planned, paused, or
abandoned, their domain meaning must be specified separately. They MUST NOT be
reintroduced through an unconstrained status field that acts as a temporal
proxy.

| Concept kind | Meaning | Additional properties |
|---|---|---|
| `Person` | An individual participating in the represented career graph | none |
| `Collective` | A group that may participate in or perform work as an agent | none |
| `Context` | A meaningful situation or body of activity supplying local interpretation | optional `temporal_extent: TemporalExtent` (`0..1`) |
| `Activity` | A meaningful occurrence of work performed by one or more agents | none |
| `Technology` | A reusable tool, programming language, framework, library, platform, or technical system | none |
| `Method` | A reusable procedure, technique, formalism, or operational approach | none |
| `Subject` | A reusable body, domain, or object of knowledge | none |
| `Language` | A human language used or learned in career-relevant circumstances | none |
| `Artifact` | A persistent identifiable thing used, produced, or modified through work | none |
| `Proposition` | Selective reified semantic content with one local context | required `content: text`; required `context: EntityReference[Context]` |
| `Organization` | A reusable institutional entity | none |
| `Place` | A reusable location relevant to a context | none |
| `Credential` | One particular formally awarded qualification | none |

`label` supports identification and presentation; it is not the entity's
stable identity. Two entities MAY share a label and still remain distinct.

A `Proposition` is used selectively for content that participates in an
intentional, outcome, epistemic, or explanatory structure. Ordinary structural
facts SHOULD remain ordinary relation assertions rather than being reified as
propositions.

A `Credential` represents one particular award to one person. It is not a
reusable credential type and is distinct from any diploma, thesis, certificate,
or other artifact that evidences it.

## 8. Schema families

The first three names abbreviate endpoint-kind unions. They are not additional
entity kinds and MUST NOT appear as entity `kind` values.

| Family | Members |
|---|---|
| `Agent` | `Person`, `Collective` |
| `Learnable` | `Technology`, `Method`, `Subject`, `Language` |
| `IntellectualResource` | `Method`, `Subject` |

The relation family `ActivityOutcomeRelation` abbreviates `results_in`,
`establishes`, `supports`, and `contradicts` where the `bears_on` constraints
refer to any activity-outcome relation.

## 9. Relation catalogue

The machine identifiers in this section are exact ontology `5.0` relation
kinds. Conceptual names are explanatory labels. A relation for which no
qualifiers are listed permits no qualifiers.

### 9.1 Structure, agency, and social context

| Conceptual relation | Kind | Source | Target | Qualifiers | Meaning |
|---|---|---|---|---|---|
| `PartOf` | `part_of` | `Context` | `Context` | none | The source is a structurally contained part of the target |
| `SuborganizationOf` | `suborganization_of` | `Organization` | `Organization` | none | The source organization is structurally contained in the target organization |
| `Performs` | `performs` | `Agent` | `Activity` | none | The source agent performed the activity |
| `OccursIn` | `occurs_in` | `Activity` | `Context` | none | The activity occurs in its most-local represented context |
| `Participation` | `participates_in` | `Agent` | `Context` | required `role: text`; optional `organization: EntityReference[Organization]` | The agent participates in the context in the stated role, optionally through the stated organization |
| `CollectiveMembership` | `collective_membership` | `Person` | `Collective` | required `context: EntityReference[Context]`; required `role: text` | The person belongs to the collective in the stated contextual role |
| `OrganizationAssociation` | `organization_association` | `Organization` | `Context` | required `role: text` | The organization is associated with the context in the stated role |
| `OccursAt` | `occurs_at` | `Context` | `Place` | none | The context has the stated career-relevant location |

Role qualifiers use relation-specific open vocabularies. Values such as
`employee`, `doctoral_researcher`, `supervisor`, `student_member`, `funder`,
`host_department`, or `experimental_facility` are examples, not closed enums.
An implementation MAY offer authoring suggestions but MUST accept any nonempty
role text.

The optional organization on `participates_in` qualifies that participation.
It does not replace an independent `organization_association` fact about the
context.

`occurs_at` provides reusable locations for CV and similar views. Ontology
`5.0` defines no place containment, coordinates, distance, spatial inference,
or temporal meaning for this relation.

### 9.2 Exposure, learning, and reusable resources

| Conceptual relation | Kind | Source | Target | Qualifiers | Meaning |
|---|---|---|---|---|---|
| `Exposure` | `exposed_to` | `Person` | `Learnable` | required `context: EntityReference[Context]` | The person encountered the target in the stated context |
| `Learning` | `learns` | `Person` | `Learnable` | required `context: EntityReference[Context]` | Meaningful acquisition, development, or deepening occurred in the stated context |
| `UsesTechnology` | `uses_technology` | `Activity` | `Technology` | none | The activity practically uses the technology |
| `UsesArtifact` | `uses_artifact` | `Activity` | `Artifact` | none | The activity uses the artifact as a resource |
| `UsesLanguage` | `uses_language` | `Activity` | `Language` | none | The activity uses the human language |
| `Applies` | `applies` | `Activity` | `Method` | none | The activity operationally applies the method |
| `DrawsOn` | `draws_on` | `Activity` | `IntellectualResource` | none | The activity draws conceptually or intellectually on the method or subject |
| `NativeLanguage` | `native_language` | `Person` | `Language` | none | The language is native to the person |

Practical use remains activity-grounded. Ontology `5.0` has no primitive
`Person uses Technology` relation. Cross-context histories are derived by
following shared reusable entities through activities, contexts, and agents.

### 9.3 Artifact roles

| Conceptual relation | Kind | Source | Target | Meaning |
|---|---|---|---|---|
| `TakesInput` | `takes_input` | `Activity` | `Artifact` | The artifact is an input to the activity |
| `Produces` | `produces` | `Activity` | `Artifact` | The activity creates the artifact represented by the target identity |
| `Modifies` | `modifies` | `Activity` | `Artifact` | The activity changes an already identified artifact |

Ontology `5.0` does not define a primitive `Maintains` relation. Maintenance
is represented through meaningful activities and existing artifact roles until
a demonstrated query failure justifies a distinct relation.

### 9.4 Credentials

| Conceptual relation | Kind | Source | Target | Meaning |
|---|---|---|---|---|
| `AwardedTo` | `awarded_to` | `Credential` | `Person` | The credential was awarded to the person |
| `AwardedBy` | `awarded_by` | `Credential` | `Organization` | The organization jointly or independently awarded the credential |
| `ObtainedThrough` | `obtained_through` | `Credential` | `Context` | The credential was obtained through the context |
| `EvidencedBy` | `evidenced_by` | `Credential` | `Artifact` | The artifact provides evidence of the credential |

### 9.5 Intentional, outcome, and explanatory structure

| Conceptual relation | Kind | Source | Target | Meaning |
|---|---|---|---|---|
| `AimsAt` | `aims_at` | `Context` | `Proposition` | The proposition expresses something the context seeks to bring about |
| `Addresses` | `addresses` | `Activity` | `Proposition` | The activity is directed toward the proposition |
| `Motivates` | `motivates` | `Proposition` | `Activity` or `Context` | The proposition provides a reason for undertaking the target |
| `ResultsIn` | `results_in` | `Activity` | `Proposition` | The activity has the proposition as a consequence without necessarily making an epistemic claim |
| `Establishes` | `establishes` | `Activity` | `Proposition` | The activity establishes the proposition |
| `Supports` | `supports` | `Activity` | `Proposition` | The activity provides support for the proposition |
| `Contradicts` | `contradicts` | `Activity` | `Proposition` | The activity provides evidence against the proposition in its stated scope |
| `BearsOn` | `bears_on` | `Proposition` | `Proposition` | The source outcome proposition is relevant to evaluating the target aim proposition |

`results_in`, `establishes`, `supports`, and `contradicts` remain distinct.
Proposition content carries the substantive result, limitation, hypothesis, or
question; ontology `5.0` does not impose a universal outcome-status field.

## 10. Cardinality requirements

Cardinalities apply to included entities in every candidate, irrespective of
the candidate's coverage scope.

| Subject | Relation position | Cardinality |
|---|---|---:|
| `Activity` | target of `performs` | `1..*` |
| `Activity` | source of `occurs_in` | exactly `1` |
| `Credential` | source of `awarded_to` | exactly `1` |
| `Credential` | source of `awarded_by` | `1..*` |
| `Credential` | source of `obtained_through` | `1..*` |
| `Credential` | source of `evidenced_by` | `0..*` |

The sole `occurs_in` target is the activity's most-local represented context.
Ancestor contexts are recovered through `part_of`. An activity genuinely
spanning unrelated local contexts MUST be split into meaningful activities or
placed in an explicit shared context.

Multiple performers MAY be persons, collectives, or both. Multiple awarding
organizations support jointly awarded credentials.

Selective coverage MAY omit an unknown activity or credential. It MUST NOT
relax the invariants of an included entity.

## 11. Global validity rules

### 11.1 Structural closure and acyclicity

1. Every relation endpoint and entity-reference property or qualifier MUST
   resolve to a present entity of an allowed kind.
2. The `part_of` graph MUST be acyclic. A context MAY have more than one parent
   when the resulting structure remains a directed acyclic graph.
3. The `suborganization_of` graph MUST be acyclic.
4. A proposition's required `context` reference is its sole locality authority.
   Ontology `5.0` defines no duplicate proposition-context relation.

### 11.2 `BearsOn` role and locality constraints

For every `bears_on(source, target)` assertion:

1. `source` MUST be the target of at least one `results_in`, `establishes`,
   `supports`, or `contradicts` assertion;
2. `target` MUST be the target of at least one `aims_at` assertion;
3. `source` and `target` MUST be distinct propositions;
4. the source proposition's context MUST equal the target proposition's
   context, or the source context MUST reach the target context through one or
   more `part_of` assertions.

Context compatibility validates an explicit `bears_on` assertion. It never
infers one. An outcome in a broader context does not automatically bear on an
aim in a narrower context. Sibling or otherwise incomparable proposition
contexts are invalid for `bears_on`.

### 11.3 Temporal consistency

Every `Context` and `Activity` has a semantically nonempty temporal occurrence,
whether or not its boundaries are known.

If `part_of(child, parent)` is asserted:

$$
time(child) \subseteq time(parent)
$$

If `occurs_in(activity, context)` is asserted:

$$
time(activity) \subseteq time(context)
$$

All direct and transitive temporal constraints MUST admit at least one
consistent interpretation. Contradictory asserted extents make the candidate
invalid. Containment MUST NOT copy a parent's intrinsic extent onto a child or
an activity.

Missing intrinsic temporal boundaries are incomplete information, not
invalidity. Career-domain time MUST remain distinct from import, file,
realisation-version, or provenance timestamps.

Validation distinguishes:

- **invalid**: the asserted facts admit no consistent interpretation;
- **indeterminate**: several relevant interpretations remain possible;
- **incomplete**: information required by a requested operation is absent.

Only invalidity necessarily prevents construction of a validated realisation.
An operation MAY report indeterminate or incomplete diagnostics without
changing the candidate's asserted facts.

Context-qualified `participates_in`, `collective_membership`,
`organization_association`, `exposed_to`, and `learns` assertions do not state
that the fact holds throughout the context's entire extent. Activity-grounded
relations receive temporal relevance through their source activity and its
`occurs_in` path; they do not receive independent timestamps.

`obtained_through` does not establish an exact credential award month from the
context's extent.

## 12. Required non-inferences

An ontology `5.0` implementation MUST preserve at least these boundaries:

1. `part_of` does not imply shared purpose, causal contribution, proposition
   propagation, participation, or performance.
2. `participates_in` does not imply `performs` for activities in the context.
3. A person's `collective_membership`, combined with a collective's
   `performs`, does not imply personal performance or personal production.
4. `organization_association` does not imply a person's employment or
   participation through that organization.
5. `exposed_to` does not imply `learns`, practical use, retention, or mastery.
6. `learns` does not imply first acquisition, permanent retention, mastery, or
   a current expertise level.
7. `uses_language` does not imply `native_language`, and `native_language` does
   not imply contextual language use.
8. `uses_artifact` does not imply `takes_input`; `takes_input` does not imply
   `modifies`; `modifies` does not imply `produces`.
9. `supports` does not imply `establishes`; `contradicts` does not establish
   universal falsehood; `establishes` does not classify desirability or
   success.
10. An activity occurring in a context does not automatically `addresses`
    every aim of that context.
11. An activity-mediated path from an aim to an outcome is only candidate
    evidence for purpose evaluation; exact CQ7 evidence requires explicit
    `bears_on`.
12. `bears_on` does not classify achievement, failure, support, contradiction,
    polarity, desirability, or completeness.
13. Temporal containment does not imply equality of extents, continuous work,
    effort, or active duration.
14. Shared reusable identity permits a history to be queried; it does not
    assert a primitive `Experience`, `Transfer`, `Ability`, or `Capability`.
15. Absence of an entity or relation is not explicit negation. Conclusions from
    absence additionally depend on declared realisation coverage.

## 13. Coverage and derived results

Coverage describes how much of a stated scope a realisation contains. It does
not change ontology validity. At minimum, the statuses `selective`,
`complete_within_scope`, and `unknown` remain distinguishable.

Query results MAY derive temporal classifications, covered-month values,
histories, paths, bindings, or renderer-neutral graph projections. Derived
results MUST remain separate from positive ontology assertions and SHOULD carry
witnesses sufficient to inspect the represented evidence and relation paths.

The temporal classifications remain:

- `entailed`: true under every valid interpretation supported by the
  realisation;
- `possible`: supported by some but not all valid interpretations;
- `excluded`: supported by no valid interpretation;
- `unknown`: insufficient useful temporal constraint.

### 13.1 Covered-month results

For a known closed extent, the inclusive covered-month count is:

```text
covered_month_count = end_month_index - start_month_index + 1
```

An ongoing extent has an exact count only as of its recorded observation
month. A known start with an unknown end has no final count. An undated
nonempty child within a closed parent MAY have a bounded possible count but
MUST NOT inherit the parent's exact count. A completely unconstrained
occurrence has an unknown count.

Covered-month values describe calendar envelopes, not continuous activity or
effort.

### 13.2 Temporal ordering and window selection

For two known closed extents, `before(A, B)` is entailed when `end(A) <
start(B)`. Extents containing the same month are not strictly ordered at model
resolution.

A temporal window is an inclusive pair of `YearMonth` values. A definite-mode
selection includes only entailed matches. A possible-mode selection includes
entailed and possible matches. Unknown matches are excluded unless an
interaction explicitly asks to inspect missing temporal coverage.

An activity is evaluated through its `occurs_in` relation and any relevant
`part_of` ancestor path. This supplies temporal constraints, not a copied
activity extent.

### 13.3 Witnesses and graph projection

Every derived temporal result SHOULD retain the activity or context, the
temporal extent used, the relevant `occurs_in` and `part_of` path, the operation,
and the result classification. A reusable-resource result additionally retains
the relation connecting the activity to that resource.

`GraphView` remains a partial query projection, not a realisation and not a
semantic serialization format. It MUST NOT insert `before`, `overlaps`, or
covered-month values as positive career assertions.

## 14. Migration to ontology `5.0`

Migration constructs a new `5.0` candidate and validates it. It never mutates
or relabels an accepted `4` or `0.5` realisation.

| Source construct | Required migration treatment |
|---|---|
| Ontology `4` Context `start` and `end` | Create a `TemporalExtent` only when source evidence establishes canonical months and a valid end state; never invent a month from a year |
| Ontology `4` Context `status` | Drop; never translate free text into temporal continuation without dated evidence |
| Ontology `0.5` Context `temporal_extent` | Preserve when valid under `5.0` |
| `part_of`, `performs`, `occurs_in`, `takes_input`, `produces`, `applies`, `draws_on`, proposition relations, and `occurs_at` | Preserve identifiers where the assertion's meaning and endpoints are unchanged |
| compact `uses` with a `Technology` target | Replace with `uses_technology` |
| compact `uses` with an `Artifact` target | Replace with `uses_artifact` |
| compact `participates_in` | Preserve only when a nonempty role is supported; add the optional organization only from evidence |
| compact `associated_with(Context, Organization)` | Replace with `organization_association(Organization, Context)` only when a nonempty association role is supported |
| `exposed_to` and `learns` | Preserve their binary endpoints and required context qualifier |
| Proposition `context` property | Preserve as the sole locality authority |
| New Model 4.2 concepts and relations | Add only from source evidence; never infer them merely to make the target candidate complete |

Stable entity and relation assertion identifiers SHOULD be preserved when the
semantic assertion is unchanged. A split, reversed, or newly qualified
relation MAY require a new assertion identity according to the later migration
and serialization contract.

Missing evidence required by `5.0` produces a migration diagnostic. It MUST NOT
be replaced by a guessed role, date, endpoint, or assertion.

## 15. Deliberately deferred concerns

Ontology `5.0` does not define:

- assertion polarity, confidence, provenance, or assertion versioning;
- realisation transactions, branching, merge, or history;
- direct temporal extents on activities;
- relation-level temporal extents or participation periods;
- recurring or disconnected extents in one value;
- approximate, fuzzy, or probabilistic dates;
- a complete interval algebra;
- place hierarchies or spatial reasoning;
- `Maintains` or domain taxonomies for methods, subjects, or technologies;
- a canonical serialization, repository, or migration API;
- a public query-plan language or universal query-result class;
- ability, capability, recurring-pattern, narrative, or external-relevance
  claims.

These concerns require their own demonstrated cases and contracts. They MUST
NOT be added silently to an implementation claiming exact `5.0` conformance.

## 16. Conformance and acceptance

An implementation conforms to ontology `5.0` only if it:

1. exposes the exact ontology identity `caron.career-model` / `5.0`;
2. implements all 13 concept kinds and their exact property definitions;
3. implements all 31 relation kinds, endpoint unions, and qualifier rules;
4. enforces stable nonempty record identifiers and local structural closure;
5. enforces all activity and credential cardinalities;
6. enforces context and organization acyclicity;
7. enforces all `bears_on` role and contextual-locality constraints;
8. implements the complete month-level `TemporalExtent` value contract and
   transitive temporal consistency rules;
9. preserves every required non-inference in section 12;
10. rejects candidates declaring another exact ontology version;
11. keeps derived temporal and query results outside positive assertions;
12. passes representative valid, invalid, incomplete, and indeterminate
    scenarios for the adopted vocabulary.

Partial implementations MUST use an explicit development schema identifier and
MAY publish implementation-coverage records. They MUST NOT claim the accepted
`5.0` schema identifier.

At minimum, conformance tests MUST exercise:

- personal and collective performance without invalid attribution;
- participation with and without an organization qualifier;
- collective membership and organization association roles;
- Language in exposure, learning, activity use, and native-language facts;
- production versus modification and input versus use;
- one valid single-awarder and one valid joint-awarder credential;
- proposition locality and exact `bears_on` evidence across equal and nested
  contexts, plus invalid sibling and reversed-context cases;
- `Place` and `occurs_at` in a CV-oriented realisation;
- known, unknown, ongoing, nested, contradictory, and unconstrained temporal
  cases without wall-clock advancement or copied extents;
- explicit migration diagnostics for imprecise dates and missing required
  roles.

The package release implementing ontology `5.0` is assigned separately from
this specification. Until that implementation passes this gate, the current
executable authorities remain ontology versions `4` and `0.5` in `caron`
`0.1.0`.

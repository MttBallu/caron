---
kind: ontology_semantic_decision_record
status: m1b_accepted
date: 2026-09-21
ontology_family: caron.career-model
preserved_ontology_versions:
  - "4"
  - "0.5"
target_ontology_version: "5.0"
package_distribution: caron
current_package_version: "0.1.0"
implementation_package_version: unassigned
predecessor_review: career-ontology-m1a-reconciliation.md
next_gate: m1c_integrated_ontology_specification
---

# M1-B — Integrated Career Ontology Semantic Decisions

## 1. Purpose

This record closes the semantic choices raised by the
[M1-A reconciliation](career-ontology-m1a-reconciliation.md). It determines
the meaning and scope of the next integrated ontology specification. It does
not modify an existing executable schema or assign a new `caron` package
release.

The target is an exact new ontology schema:

```yaml
ontology:
  id: caron.career-model
  version: "5.0"

implementation_package:
  distribution: caron
  current_release: "0.1.0"
  implementation_release: unassigned
```

Ontology `5.0` will integrate the adopted Model 4.2 vocabulary, the accepted
month-level temporal semantics of ontology `0.5`, and the decisions below.

## 2. Independent identities and versions

The project has several version axes. They are neither aliases nor numbers to
compare across axes.

| Versioned concern | Current or target identifier | Meaning |
|---|---|---|
| Ontology family | `caron.career-model` | Stable identity shared by compatible lineage declarations |
| Compatibility ontology | `4` | Preserved first executable schema |
| Compact temporal ontology | `0.5` | Preserved exact schema adding accepted temporal semantics to the compact vocabulary |
| Integrated ontology | `5.0` | New semantic generation and target schema defined by M1-C |
| Python distribution | `caron` `0.1.0` currently | Software release containing one or more exact ontology schemas |
| Temporal contract | contract `0.2` | Version of the temporal design document, not an ontology or package version |
| Conceptual candidate | Model 4.2 | Historical conceptual revision, not an executable schema identifier |

The following rules are adopted:

1. An exact ontology version has immutable meaning once implemented and
   accepted. The integrated vocabulary therefore cannot reuse `0.5`.
2. A `caron` release may add support for one or several ontology versions,
   migrations, queries, or implementation changes.
3. An ontology revision does not mechanically determine the next package
   version. Package releases are assigned from software compatibility and
   delivery scope.
4. Specification-only work does not change the package version. The current
   package therefore remains `caron` `0.1.0` throughout M1-C.
5. Implementing ontology `5.0` requires a separate package-release decision.
   That decision must consider the complete implementation scope and backward
   compatibility; it is not assigned by this record.
6. A package may support several ontology versions simultaneously. Candidates
   and validated realisations always retain their exact ontology identity.
7. Contract, serialization, retrieval API, realisation, and interpretation
   versions remain separate whenever those contracts are introduced.

Ontology `5.0` resumes the conceptual model lineage after Model 4.2 and marks a
new integrated semantic generation. The legacy executable identifiers `4` and
`0.5` remain immutable even though their historical numbering conventions were
inconsistent. They are not renamed retroactively.

## 3. D1 — Target breadth

Ontology `5.0` adopts the complete accepted Model 4.2 semantic vocabulary,
rather than declaring the compact executable `0.5` subset to be the long-term
ontology.

This decision separates three claims:

- the **normative ontology** specifies the complete adopted vocabulary;
- **executable coverage** reports what a particular `caron` release actually
  implements;
- **deferred implementation** identifies adopted constructs that are not yet
  executable without changing their semantic status.

An implementation must not claim ontology `5.0` conformance until it implements
and validates the complete `5.0` schema. Partial work may use explicit
development identifiers or coverage records, but not the accepted `5.0`
version identifier.

## 4. D2 — Place

`Place` is adopted rather than provisional. The adopted connector is:

```text
OccursAt: Context → Place
```

The motivating use is faithful CV production: education, employment, projects,
and similar contexts may need an explicit reusable location. Adoption does not
introduce geographic containment, coordinates, distance, or spatial inference.
No current competency query depends on those richer semantics.

A CV-oriented realisation must exercise `Place` and `OccursAt` before executable
`5.0` is accepted.

## 5. D3 — Context status

The generic free-text `Context.status` property is not part of ontology `5.0`.

`TemporalExtent` is the sole ontology authority for known, unknown, or
observation-relative temporal continuation. A status value must not duplicate
or override its end state.

This decision does not mutate compatibility ontology `4`, where `status`
remains part of the exact historical schema. Compact temporal ontology `0.5`
already omits it. Migration to `5.0` drops the field rather than attempting to
convert it into temporal evidence.

If a future case requires states such as planned, paused, or abandoned, their
precise domain meaning must be established separately. They must not be
reintroduced as an unconstrained temporal proxy.

## 6. D4 — Proposition locality

Every `Proposition` retains exactly one required entity-reference property:

```text
Proposition.context → Context
```

Locality is constitutive and functional, so it is not duplicated as a relation
assertion. A query may traverse the reference and identify
`(proposition, "context")` as its witness. A renderer may display it as a
reference edge, but that edge remains a presentation projection.

Two context-local meanings normally require two Proposition entities even when
their textual content is identical. A separately identified relation would
become justified only if locality itself required multiple values,
qualification, provenance, or uncertainty.

## 7. D5 — BearsOn contextual validity

`BearsOn(outcome, aim)` retains its deliberately weak meaning: the outcome is
relevant to evaluating the aim. It does not classify success, failure,
support, contradiction, polarity, or completeness.

The relation is valid only when all of the following hold:

1. the source is a Proposition targeted by at least one of `ResultsIn`,
   `Establishes`, `Supports`, or `Contradicts`;
2. the target is a Proposition targeted by `AimsAt`;
3. source and target are distinct;
4. the source and target Proposition contexts are equal, or the source context
   is a transitive descendant of the target context through `PartOf`.

Context compatibility validates an explicit `BearsOn`; it never infers one.
An outcome in a broad context does not automatically bear on an aim in a
narrower context. Sibling and otherwise incomparable contexts are rejected
until a demonstrated case establishes a justified cross-context mechanism.

Exact CQ7 evidence continues to require an explicit `BearsOn` assertion. An
activity-mediated path remains only a candidate attribution.

## 8. D6 — Relation encoding

### 8.1 Uses relations

The compact executable `uses` relation is split into the Model 4.2 relations:

```text
UsesTechnology: Activity → Technology
UsesArtifact:   Activity → Artifact
```

Their executable identifiers will be `uses_technology` and `uses_artifact`.
Migration from compact `uses` is deterministic from the target entity kind.
Compatibility schemas retain their existing relation identifier.

### 8.2 Contextual and n-ary structures

Ontology `5.0` retains the identified-relation-plus-typed-qualifiers mechanism.
One relation assertion identity covers the complete fact; its roles must not be
decomposed into independent assertions that could drift apart.

| Conceptual structure | Binary backbone | Typed qualifiers |
|---|---|---|
| `Participation` | `Agent → Context` | required role; optional Organization |
| `CollectiveMembership` | `Person → Collective` | required Context; required role |
| `OrganizationAssociation` | `Organization → Context` | required role |
| `Exposure` | `Person → Learnable` | required Context |
| `Learning` | `Person → Learnable` | required Context |

Entity-reference qualifiers participate in reference closure and kind
validation. Role qualifiers use required nonempty text with relation-specific,
open vocabularies: examples guide authoring but do not constitute closed enums.
A renderer may reify the relation occurrence and show qualifier references as
additional legs. This does not introduce relation entities into the ontology.

A general role-based n-ary meta-model remains deferred until the current
encoding blocks an observed query, validation, cardinality, or provenance
requirement.

## 9. D7 — Cardinalities

The following cardinalities are accepted for ontology `5.0`:

| Subject | Relation and endpoint | Cardinality |
|---|---|---:|
| `Activity` | incoming `Performs` from `Agent` | `1..*` |
| `Activity` | outgoing `OccursIn` to its most-local `Context` | exactly `1` |
| `Credential` | outgoing `AwardedTo` to `Person` | exactly `1` |
| `Credential` | outgoing `AwardedBy` to `Organization` | `1..*` |
| `Credential` | outgoing `ObtainedThrough` to `Context` | `1..*` |
| `Credential` | outgoing `EvidencedBy` to `Artifact` | `0..*` |

The multiple-awarder rule supports jointly awarded qualifications. One
Credential represents one particular award to one Person, not a reusable
credential type.

Multiple performers may include Persons and Collectives. Ancestor contexts are
derived through `PartOf`; they do not violate the exactly-one most-local Context
rule. An activity genuinely spanning unrelated local contexts must be split or
placed in an explicit shared Context.

Coverage does not relax these local invariants. A selective realisation may
omit an unknown Credential, but an included Credential must identify its
recipient, at least one awarder, and at least one obtaining Context. Evidencing
documents remain optional.

## 10. Migration consequences

M1-C must specify an explicit migration to ontology `5.0`:

| Source construct | `5.0` treatment |
|---|---|
| ontology `4` Context `start`, `end`, and `status` | temporal fields migrate only with justified month-level evidence; `status` is dropped |
| ontology `0.5` `TemporalExtent` | preserved when valid under `5.0` |
| compact `uses` targeting Technology | becomes `uses_technology` |
| compact `uses` targeting Artifact | becomes `uses_artifact` |
| existing `Place` and `occurs_at` | retained as adopted semantics |
| existing Proposition `context` property | retained as the sole locality authority |
| newly adopted Model 4.2 constructs | added explicitly; never inferred from unrelated existing records |

No ontology `4` or `0.5` candidate may be silently relabelled as `5.0`.
Migration must construct and validate a new candidate while preserving stable
entity and relation identities wherever the semantic assertion is unchanged.

## 11. Routed outside M1-B

The following concerns are not ontology semantic decisions and do not block the
integrated specification:

- common query-result metadata and answer-specific result structures: M2A;
- public query-plan candidates and validation: M2A;
- assertion polarity, confidence, provenance, and assertion versioning: later
  assertion-layer work;
- serialization formats, codecs, repositories, and migrations as software
  APIs: storage milestone;
- CLI, authoring, and interactive workflows: application milestone;
- the next `caron` package release number: package release planning.

`GraphView` remains a structural query projection and does not become the
universal query-result type.

## 12. M1-B acceptance and next gate

M1-B is accepted because it resolves target breadth, Place, Context status,
Proposition locality, `BearsOn` contextual validity, relation encoding, and
provisional cardinalities while preserving independent version identities.

M1-C must now write the complete normative ontology `5.0` specification and its
lineage declaration. Executable changes begin only after that specification is
reviewed and accepted.

---
kind: implementation_design_note
status: implemented
scope: entity_and_relation_representation
architecture_contract: 0.2
---

# Entity and Relation Representation — Pseudocode

## 1. Recommendation

Represent concrete career information as immutable generic entity and relation records validated against an explicit ontology.

Do not initially define one Python class for each of `Person`, `Context`, `Activity`, `Technology`, `Method`, `Subject`, `Artifact`, `Proposition`, `Organization`, and `Place`.

Those are semantic concept identifiers owned by the ontology. Ten separate record classes would mostly repeat `id`, `label`, and generic property handling while making the Python class hierarchy a second, potentially inconsistent ontology.

The trade-off is intentional:

| Generic validated records | One class per concept |
|---|---|
| Ontology remains explicit and authoritative | Python classes partly define the ontology |
| Candidate input may contain reportable errors | Constructors tend to reject or normalize errors too early |
| Uniform relation and serialization boundary | More concept-specific boilerplate |
| Runtime validation provides semantic guarantees | More static narrowing before validation |
| New ontology concepts do not require a new class | Extensions require code changes |

If later implementation pressure reveals meaningful concept-specific behavior, typed views or dedicated classes can be introduced without changing the underlying assertion model.

## 2. Ontology definitions

The ontology defines which records are meaningful. Python-like pseudocode:

```python
type ConceptId = str
type RelationKind = str
type PropertyName = str
type QualifierName = str


class ValueKind(StrEnum):
    TEXT = "text"
    INTEGER = "integer"
    ENTITY_REFERENCE = "entity_reference"


@dataclass(frozen=True, slots=True)
class PropertyDefinition:
    name: PropertyName
    value_kind: ValueKind
    required: bool = False
    allowed_reference_kinds: frozenset[ConceptId] = frozenset()


@dataclass(frozen=True, slots=True)
class ConceptDefinition:
    id: ConceptId
    properties: tuple[PropertyDefinition, ...] = ()


@dataclass(frozen=True, slots=True)
class QualifierDefinition:
    name: QualifierName
    value_kind: ValueKind
    required: bool = False
    allowed_reference_kinds: frozenset[ConceptId] = frozenset()


@dataclass(frozen=True, slots=True)
class RelationDefinition:
    kind: RelationKind
    source_kinds: frozenset[ConceptId]
    target_kinds: frozenset[ConceptId]
    qualifiers: tuple[QualifierDefinition, ...] = ()


@dataclass(frozen=True, slots=True)
class OntologySchema:
    id: str
    version: str
    concepts: tuple[ConceptDefinition, ...]
    relations: tuple[RelationDefinition, ...]
    requirements: tuple[RelationRequirement, ...] = ()
```

`RelationRequirement` expresses the two established activity constraints without embedding them in validator control flow: at least one incoming `performs` assertion and exactly one outgoing `occurs_in` assertion.

## 3. Entity records

```python
type EntityId = str


@dataclass(frozen=True, slots=True)
class EntityRef:
    entity_id: EntityId


type PropertyValue = str | int | EntityRef


@dataclass(frozen=True, slots=True)
class Property:
    name: PropertyName
    value: PropertyValue


@dataclass(frozen=True, slots=True)
class Entity:
    id: EntityId
    kind: ConceptId
    properties: tuple[Property, ...] = ()
```

The record is structurally immutable but not automatically valid. For example, a candidate may contain an entity whose kind is unknown or whose required `label` property is missing. That must remain representable long enough to produce useful diagnostics.

Semantic validity belongs to the transition:

```text
RealisationCandidate --validate against OntologySchema--> ValidatedRealisation
```

## 4. Relation assertions

Relations remain separate from entities, both conceptually and in the package layout.

```python
type RelationId = str
type QualifierValue = str | int | EntityRef


@dataclass(frozen=True, slots=True)
class Qualifier:
    name: QualifierName
    value: QualifierValue


@dataclass(frozen=True, slots=True)
class RelationAssertion:
    id: RelationId
    kind: RelationKind
    source: EntityRef
    target: EntityRef
    qualifiers: tuple[Qualifier, ...] = ()
```

The ontology validates the relation kind, source and target concept kinds, required qualifiers, qualifier types, and referenced entities.

The first executable encoding treats the contextual structures as relations with qualifiers:

```yaml
participates_in:
  source: Person
  target: Context
  optional_qualifier:
    role: text

exposed_to:
  source: Person
  target:
    - Technology
    - Method
    - Subject
  required_qualifier:
    context: Context reference

learns:
  source: Person
  target:
    - Technology
    - Method
    - Subject
  required_qualifier:
    context: Context reference
```

This binary-relation-plus-qualifier encoding is a first-spine decision supported by the executable experiment. It is not a claim that all future contextual relations must use qualifiers.

## 5. Example records

```python
matteo = Entity(
    id="matteo",
    kind="Person",
    properties=(Property("label", "Matteo"),),
)

jax_geopro = Entity(
    id="jax_geopro",
    kind="Context",
    properties=(
        Property("label", "jax-geopro"),
        Property("start", 2026),
    ),
)

implement_ot_losses = Entity(
    id="implement_ot_losses",
    kind="Activity",
    properties=(Property("label", "Implement differentiable measure losses"),),
)

jax = Entity(
    id="jax",
    kind="Technology",
    properties=(Property("label", "JAX"),),
)
```

The activity's agency and context are represented by assertions rather than duplicated fields:

```python
performs = RelationAssertion(
    id="performs:implement_ot_losses",
    kind="performs",
    source=EntityRef("matteo"),
    target=EntityRef("implement_ot_losses"),
)

occurs_in = RelationAssertion(
    id="occurs_in:implement_ot_losses",
    kind="occurs_in",
    source=EntityRef("implement_ot_losses"),
    target=EntityRef("jax_geopro"),
)

uses_jax = RelationAssertion(
    id="uses:implement_ot_losses:jax",
    kind="uses",
    source=EntityRef("implement_ot_losses"),
    target=EntityRef("jax"),
)
```

This prevents `Activity` from becoming a container with a second relation system embedded in its fields.

## 6. Proposition locality

For the first spine, a proposition's local context is an entity-reference property:

```python
training_instability = Entity(
    id="training_instability",
    kind="Proposition",
    properties=(
        Property("label", "Training instability"),
        Property("content", "Initial U-Net training was unstable."),
        Property("context", EntityRef("dense_regression_ml_work")),
    ),
)
```

This means graph-view closure cannot stop at relation endpoints. If the proposition is selected, its referenced context must be included under the semantic-reference closure policy.

## 7. Candidates, coverage, and validated realisations

Coverage should be structured from the beginning rather than carried only as prose:

```python
class CoverageStatus(StrEnum):
    SELECTIVE = "selective"
    COMPLETE_WITHIN_SCOPE = "complete_within_scope"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Coverage:
    status: CoverageStatus
    scope: str


@dataclass(frozen=True, slots=True)
class RealisationCandidate:
    id: str
    ontology_id: str
    ontology_version: str
    entities: tuple[Entity, ...]
    relations: tuple[RelationAssertion, ...]
    coverage: Coverage


@dataclass(frozen=True, slots=True)
class ValidatedRealisation:
    id: str
    ontology: OntologySchema
    entities: tuple[Entity, ...]
    relations: tuple[RelationAssertion, ...]
    coverage: Coverage

    # Public reads; indexes remain private implementation details.
    def entity(self, entity_id: EntityId) -> Entity: ...

    def matching_relations(
        self,
        *,
        kind: RelationKind | None = None,
        source_id: EntityId | None = None,
        target_id: EntityId | None = None,
    ) -> tuple[RelationAssertion, ...]: ...
```

`ValidatedRealisation` is guarded by a private validation token and produced by the validator through a non-public factory.

No repository or protocol is required to establish the read boundary yet. The immutable class itself can provide the first public read contract.

## 8. Validation outcome

The implementation uses this non-exceptional validation boundary:

```python
@dataclass(frozen=True, slots=True)
class Accepted:
    realisation: ValidatedRealisation


@dataclass(frozen=True, slots=True)
class Rejected:
    diagnostics: tuple[Diagnostic, ...]


type ValidationResult = Accepted | Rejected


match validate_candidate(ontology, candidate):
    case Accepted(realisation):
        ...
    case Rejected(diagnostics):
        ...
```

This keeps invalid input representable and returns all discovered diagnostics without using exceptions for ordinary validation failure.

## 9. Deliberately deferred representation choices

```yaml
deferred:
  - richer domain-time value types
  - artifact modifies and maintains relations
  - dedicated typed entity views
  - persistent immutable maps or internal indexes
  - provenance and source-reference records
  - generic invariant language
  - serialization shapes
  - identifiers stronger than string aliases
```

These choices should be made when a concrete fixture or operation requires them.

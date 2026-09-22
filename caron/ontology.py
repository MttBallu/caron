"""Ontology schema definitions for the career model."""

from dataclasses import dataclass
from enum import StrEnum

type ConceptId = str
type RelationKind = str
type PropertyName = str
type QualifierName = str


class ValueKind(StrEnum):
    """Primitive value categories understood by the semantic validator."""

    TEXT = "text"
    INTEGER = "integer"
    ENTITY_REFERENCE = "entity_reference"
    YEAR_MONTH = "year_month"
    TEMPORAL_EXTENT = "temporal_extent"


class EndpointPosition(StrEnum):
    """A relation endpoint used by a realisation-level requirement."""

    SOURCE = "source"
    TARGET = "target"


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

    def property_definition(self, name: PropertyName) -> PropertyDefinition | None:
        return next((item for item in self.properties if item.name == name), None)


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

    def qualifier_definition(self, name: QualifierName) -> QualifierDefinition | None:
        return next((item for item in self.qualifiers if item.name == name), None)


@dataclass(frozen=True, slots=True)
class RelationRequirement:
    """Cardinality requirement for relations attached to a concept instance."""

    concept: ConceptId
    relation_kind: RelationKind
    endpoint: EndpointPosition
    minimum: int = 0
    maximum: int | None = None


@dataclass(frozen=True, slots=True)
class InvariantDefinition:
    """Inspectable declaration of a realisation-wide validity rule."""

    id: str


@dataclass(frozen=True, slots=True)
class OntologySchema:
    id: str
    version: str
    concepts: tuple[ConceptDefinition, ...]
    relations: tuple[RelationDefinition, ...]
    requirements: tuple[RelationRequirement, ...] = ()
    invariants: tuple[InvariantDefinition, ...] = ()

    def concept(self, concept_id: ConceptId) -> ConceptDefinition | None:
        return next((item for item in self.concepts if item.id == concept_id), None)

    def relation(self, kind: RelationKind) -> RelationDefinition | None:
        return next((item for item in self.relations if item.kind == kind), None)


PERSON = "Person"
CONTEXT = "Context"
ACTIVITY = "Activity"
TECHNOLOGY = "Technology"
METHOD = "Method"
SUBJECT = "Subject"
ARTIFACT = "Artifact"
PROPOSITION = "Proposition"
ORGANIZATION = "Organization"
PLACE = "Place"

ALL_CONCEPTS = frozenset(
    {
        PERSON,
        CONTEXT,
        ACTIVITY,
        TECHNOLOGY,
        METHOD,
        SUBJECT,
        ARTIFACT,
        PROPOSITION,
        ORGANIZATION,
        PLACE,
    }
)


def _labelled(
    concept_id: ConceptId, *properties: PropertyDefinition
) -> ConceptDefinition:
    return ConceptDefinition(
        id=concept_id,
        properties=(
            PropertyDefinition("label", ValueKind.TEXT, required=True),
            *properties,
        ),
    )


def _context_qualifier() -> QualifierDefinition:
    return QualifierDefinition(
        "context",
        ValueKind.ENTITY_REFERENCE,
        required=True,
        allowed_reference_kinds=frozenset({CONTEXT}),
    )


def model4_ontology() -> OntologySchema:
    """Return the explicit schema for the first executable career model."""

    concepts = (
        _labelled(PERSON),
        _labelled(
            CONTEXT,
            PropertyDefinition("start", ValueKind.INTEGER),
            PropertyDefinition("end", ValueKind.INTEGER),
            PropertyDefinition("status", ValueKind.TEXT),
        ),
        _labelled(ACTIVITY),
        _labelled(TECHNOLOGY),
        _labelled(METHOD),
        _labelled(SUBJECT),
        _labelled(ARTIFACT),
        _labelled(
            PROPOSITION,
            PropertyDefinition("content", ValueKind.TEXT, required=True),
            PropertyDefinition(
                "context",
                ValueKind.ENTITY_REFERENCE,
                required=True,
                allowed_reference_kinds=frozenset({CONTEXT}),
            ),
        ),
        _labelled(ORGANIZATION),
        _labelled(PLACE),
    )

    relations = (
        RelationDefinition("part_of", frozenset({CONTEXT}), frozenset({CONTEXT})),
        RelationDefinition(
            "participates_in",
            frozenset({PERSON}),
            frozenset({CONTEXT}),
            qualifiers=(QualifierDefinition("role", ValueKind.TEXT),),
        ),
        RelationDefinition("performs", frozenset({PERSON}), frozenset({ACTIVITY})),
        RelationDefinition("occurs_in", frozenset({ACTIVITY}), frozenset({CONTEXT})),
        RelationDefinition(
            "exposed_to",
            frozenset({PERSON}),
            frozenset({TECHNOLOGY, METHOD, SUBJECT}),
            qualifiers=(_context_qualifier(),),
        ),
        RelationDefinition(
            "learns",
            frozenset({PERSON}),
            frozenset({TECHNOLOGY, METHOD, SUBJECT}),
            qualifiers=(_context_qualifier(),),
        ),
        RelationDefinition(
            "uses", frozenset({ACTIVITY}), frozenset({TECHNOLOGY, ARTIFACT})
        ),
        RelationDefinition("takes_input", frozenset({ACTIVITY}), frozenset({ARTIFACT})),
        RelationDefinition("produces", frozenset({ACTIVITY}), frozenset({ARTIFACT})),
        RelationDefinition("applies", frozenset({ACTIVITY}), frozenset({METHOD})),
        RelationDefinition(
            "draws_on", frozenset({ACTIVITY}), frozenset({METHOD, SUBJECT})
        ),
        RelationDefinition("aims_at", frozenset({CONTEXT}), frozenset({PROPOSITION})),
        RelationDefinition(
            "results_in", frozenset({ACTIVITY}), frozenset({PROPOSITION})
        ),
        RelationDefinition(
            "establishes", frozenset({ACTIVITY}), frozenset({PROPOSITION})
        ),
        RelationDefinition("supports", frozenset({ACTIVITY}), frozenset({PROPOSITION})),
        RelationDefinition(
            "contradicts", frozenset({ACTIVITY}), frozenset({PROPOSITION})
        ),
        RelationDefinition(
            "motivates", frozenset({PROPOSITION}), frozenset({ACTIVITY, CONTEXT})
        ),
        RelationDefinition(
            "associated_with", frozenset({CONTEXT}), frozenset({ORGANIZATION})
        ),
        RelationDefinition("occurs_at", frozenset({CONTEXT}), frozenset({PLACE})),
    )

    requirements = (
        RelationRequirement(ACTIVITY, "performs", EndpointPosition.TARGET, minimum=1),
        RelationRequirement(
            ACTIVITY,
            "occurs_in",
            EndpointPosition.SOURCE,
            minimum=1,
            maximum=1,
        ),
    )

    return OntologySchema(
        id="caron.career-model",
        version="4",
        concepts=concepts,
        relations=relations,
        requirements=requirements,
    )


def model_v0_5_ontology() -> OntologySchema:
    """Return career model v0.5 with month-level context temporality."""

    predecessor = model4_ontology()
    concepts = tuple(
        _labelled(
            CONTEXT,
            PropertyDefinition("temporal_extent", ValueKind.TEMPORAL_EXTENT),
        )
        if concept.id == CONTEXT
        else concept
        for concept in predecessor.concepts
    )
    return OntologySchema(
        id=predecessor.id,
        version="0.5",
        concepts=concepts,
        relations=predecessor.relations,
        requirements=predecessor.requirements,
    )

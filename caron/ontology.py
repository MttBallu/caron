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
COLLECTIVE = "Collective"
CONTEXT = "Context"
ACTIVITY = "Activity"
TECHNOLOGY = "Technology"
METHOD = "Method"
SUBJECT = "Subject"
LANGUAGE = "Language"
ARTIFACT = "Artifact"
PROPOSITION = "Proposition"
ORGANIZATION = "Organization"
PLACE = "Place"
CREDENTIAL = "Credential"


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


def career_ontology_v5_0() -> OntologySchema:
    """Return the accepted Career Ontology 5.0 schema.

    The accepted specification sections 7–11 are the source of these
    declarations. Families are endpoint unions, never additional concepts.
    All declared invariant handlers are implemented and the complete section
    16.1 conformance gate has passed.
    """

    agent_kinds = frozenset({PERSON, COLLECTIVE})
    learnable_kinds = frozenset({TECHNOLOGY, METHOD, SUBJECT, LANGUAGE})
    intellectual_resource_kinds = frozenset({METHOD, SUBJECT})
    role = QualifierDefinition("role", ValueKind.TEXT, required=True)

    concepts = (
        _labelled(PERSON),
        _labelled(COLLECTIVE),
        _labelled(
            CONTEXT,
            PropertyDefinition("temporal_extent", ValueKind.TEMPORAL_EXTENT),
        ),
        _labelled(ACTIVITY),
        _labelled(TECHNOLOGY),
        _labelled(METHOD),
        _labelled(SUBJECT),
        _labelled(LANGUAGE),
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
        _labelled(
            CREDENTIAL,
            PropertyDefinition("awarded_in", ValueKind.YEAR_MONTH),
        ),
    )

    relations = (
        # Section 9.1: structure, agency, and social context.
        RelationDefinition("part_of", frozenset({CONTEXT}), frozenset({CONTEXT})),
        RelationDefinition(
            "suborganization_of",
            frozenset({ORGANIZATION}),
            frozenset({ORGANIZATION}),
        ),
        RelationDefinition("performs", agent_kinds, frozenset({ACTIVITY})),
        RelationDefinition("occurs_in", frozenset({ACTIVITY}), frozenset({CONTEXT})),
        RelationDefinition(
            "participates_in",
            agent_kinds,
            frozenset({CONTEXT}),
            qualifiers=(
                role,
                QualifierDefinition(
                    "organization",
                    ValueKind.ENTITY_REFERENCE,
                    allowed_reference_kinds=frozenset({ORGANIZATION}),
                ),
            ),
        ),
        RelationDefinition(
            "collective_membership",
            frozenset({PERSON}),
            frozenset({COLLECTIVE}),
            qualifiers=(_context_qualifier(), role),
        ),
        RelationDefinition(
            "organization_association",
            frozenset({ORGANIZATION}),
            frozenset({CONTEXT}),
            qualifiers=(role,),
        ),
        RelationDefinition("occurs_at", frozenset({CONTEXT}), frozenset({PLACE})),
        # Section 9.2: exposure, learning, and reusable resources.
        RelationDefinition(
            "exposed_to",
            frozenset({PERSON}),
            learnable_kinds,
            qualifiers=(_context_qualifier(),),
        ),
        RelationDefinition(
            "learns",
            frozenset({PERSON}),
            learnable_kinds,
            qualifiers=(_context_qualifier(),),
        ),
        RelationDefinition(
            "uses_technology", frozenset({ACTIVITY}), frozenset({TECHNOLOGY})
        ),
        RelationDefinition(
            "uses_artifact", frozenset({ACTIVITY}), frozenset({ARTIFACT})
        ),
        RelationDefinition(
            "uses_language", frozenset({ACTIVITY}), frozenset({LANGUAGE})
        ),
        RelationDefinition("applies", frozenset({ACTIVITY}), frozenset({METHOD})),
        RelationDefinition(
            "draws_on", frozenset({ACTIVITY}), intellectual_resource_kinds
        ),
        RelationDefinition(
            "native_language", frozenset({PERSON}), frozenset({LANGUAGE})
        ),
        # Section 9.3: independent artifact roles.
        RelationDefinition("takes_input", frozenset({ACTIVITY}), frozenset({ARTIFACT})),
        RelationDefinition("produces", frozenset({ACTIVITY}), frozenset({ARTIFACT})),
        RelationDefinition("modifies", frozenset({ACTIVITY}), frozenset({ARTIFACT})),
        # Section 9.4: particular credential awards, not reusable award types.
        RelationDefinition("awarded_to", frozenset({CREDENTIAL}), frozenset({PERSON})),
        RelationDefinition(
            "awarded_by", frozenset({CREDENTIAL}), frozenset({ORGANIZATION})
        ),
        RelationDefinition(
            "obtained_through", frozenset({CREDENTIAL}), frozenset({CONTEXT})
        ),
        RelationDefinition(
            "evidenced_by", frozenset({CREDENTIAL}), frozenset({ARTIFACT})
        ),
        # Section 9.5: intentional, outcome, and explanatory structure.
        RelationDefinition("aims_at", frozenset({CONTEXT}), frozenset({PROPOSITION})),
        RelationDefinition(
            "addresses", frozenset({ACTIVITY}), frozenset({PROPOSITION})
        ),
        RelationDefinition(
            "motivates", frozenset({PROPOSITION}), frozenset({ACTIVITY, CONTEXT})
        ),
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
            "bears_on", frozenset({PROPOSITION}), frozenset({PROPOSITION})
        ),
    )

    requirements = (
        RelationRequirement(ACTIVITY, "performs", EndpointPosition.TARGET, minimum=1),
        RelationRequirement(
            ACTIVITY, "occurs_in", EndpointPosition.SOURCE, minimum=1, maximum=1
        ),
        RelationRequirement(
            CREDENTIAL, "awarded_to", EndpointPosition.SOURCE, minimum=1, maximum=1
        ),
        RelationRequirement(
            CREDENTIAL, "awarded_by", EndpointPosition.SOURCE, minimum=1
        ),
        RelationRequirement(
            CREDENTIAL, "obtained_through", EndpointPosition.SOURCE, minimum=1
        ),
        RelationRequirement(CREDENTIAL, "evidenced_by", EndpointPosition.SOURCE),
    )

    return OntologySchema(
        id="caron.career-model",
        version="5.0",
        concepts=concepts,
        relations=relations,
        requirements=requirements,
        invariants=(
            InvariantDefinition("record_identifier_lexical"),
            InvariantDefinition("required_text_non_blank"),
            InvariantDefinition("semantic_relation_fact_unique"),
            InvariantDefinition("part_of_acyclic"),
            InvariantDefinition("suborganization_of_acyclic"),
            InvariantDefinition("aims_at_locality"),
            InvariantDefinition("bears_on_roles_and_locality"),
            InvariantDefinition("temporal_consistency"),
        ),
    )

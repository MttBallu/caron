"""Candidate and validated career-model realisations."""

from dataclasses import InitVar, dataclass
from enum import StrEnum
from typing import Self

from caron.entities import Entity, EntityId
from caron.ontology import ConceptId, OntologySchema, RelationKind
from caron.relations import RelationAssertion


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


_VALIDATION_TOKEN = object()


@dataclass(frozen=True, slots=True)
class ValidatedRealisation:
    """An immutable realisation constructible only through validation."""

    id: str
    ontology: OntologySchema
    entities: tuple[Entity, ...]
    relations: tuple[RelationAssertion, ...]
    coverage: Coverage
    _validation_token: InitVar[object] = None

    def __post_init__(self, _validation_token: object) -> None:
        if _validation_token is not _VALIDATION_TOKEN:
            raise TypeError(
                "ValidatedRealisation must be produced by validate_candidate()"
            )

    @classmethod
    def _from_candidate(
        cls,
        ontology: OntologySchema,
        candidate: RealisationCandidate,
    ) -> Self:
        return cls(
            id=candidate.id,
            ontology=ontology,
            entities=candidate.entities,
            relations=candidate.relations,
            coverage=candidate.coverage,
            _validation_token=_VALIDATION_TOKEN,
        )

    def entity(self, entity_id: EntityId) -> Entity | None:
        return next((item for item in self.entities if item.id == entity_id), None)

    def relation(self, relation_id: str) -> RelationAssertion | None:
        return next((item for item in self.relations if item.id == relation_id), None)

    def entities_of_kind(self, kind: ConceptId) -> tuple[Entity, ...]:
        return tuple(item for item in self.entities if item.kind == kind)

    def matching_relations(
        self,
        *,
        kind: RelationKind | None = None,
        source_id: EntityId | None = None,
        target_id: EntityId | None = None,
    ) -> tuple[RelationAssertion, ...]:
        return tuple(
            relation
            for relation in self.relations
            if (kind is None or relation.kind == kind)
            and (source_id is None or relation.source.entity_id == source_id)
            and (target_id is None or relation.target.entity_id == target_id)
        )

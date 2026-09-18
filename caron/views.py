"""Immutable, renderer-independent query result views."""

from dataclasses import dataclass

from caron.diagnostics import Diagnostic
from caron.entities import Entity, EntityRef
from caron.ontology import OntologySchema
from caron.realisations import Coverage
from caron.relations import RelationAssertion, RelationId


@dataclass(frozen=True, slots=True)
class QueryBinding:
    name: str
    entity: EntityRef


@dataclass(frozen=True, slots=True)
class QueryWitness:
    """Asserted records that justify one derived query result."""

    entities: tuple[EntityRef, ...]
    relations: tuple[RelationId, ...] = ()
    properties: tuple[tuple[EntityRef, str], ...] = ()


@dataclass(frozen=True, slots=True)
class GraphView[ResultT]:
    """An immutable semantic selection returned by a query."""

    query_name: str
    source_realisation_id: str
    ontology: OntologySchema
    entities: tuple[Entity, ...]
    relations: tuple[RelationAssertion, ...]
    bindings: tuple[QueryBinding, ...]
    results: tuple[ResultT, ...]
    coverage: Coverage
    diagnostics: tuple[Diagnostic, ...] = ()

    def __post_init__(self) -> None:
        entity_ids = {entity.id for entity in self.entities}
        if any(
            relation.source.entity_id not in entity_ids
            or relation.target.entity_id not in entity_ids
            for relation in self.relations
        ):
            raise ValueError("GraphView relations must retain both endpoint entities")
        if any(binding.entity.entity_id not in entity_ids for binding in self.bindings):
            raise ValueError("GraphView bindings must refer to selected entities")

    def entity(self, entity_id: str) -> Entity | None:
        return next((item for item in self.entities if item.id == entity_id), None)

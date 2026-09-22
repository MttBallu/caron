"""Immutable entity records used by career model realisations."""

from dataclasses import dataclass

from caron.ontology import ConceptId, PropertyName
from caron.temporal import TemporalExtent, YearMonth

type EntityId = str


@dataclass(frozen=True, slots=True)
class EntityRef:
    entity_id: EntityId


type PropertyValue = str | int | EntityRef | YearMonth | TemporalExtent


@dataclass(frozen=True, slots=True)
class Property:
    name: PropertyName
    value: PropertyValue


@dataclass(frozen=True, slots=True)
class Entity:
    id: EntityId
    kind: ConceptId
    properties: tuple[Property, ...] = ()

    def property(self, name: PropertyName) -> PropertyValue | None:
        item = next((item for item in self.properties if item.name == name), None)
        return None if item is None else item.value

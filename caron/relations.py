"""Immutable relation assertion records."""

from dataclasses import dataclass

from caron.entities import EntityRef, PropertyValue
from caron.ontology import QualifierName, RelationKind

type RelationId = str
type QualifierValue = PropertyValue


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

    def qualifier(self, name: QualifierName) -> QualifierValue | None:
        item = next((item for item in self.qualifiers if item.name == name), None)
        return None if item is None else item.value

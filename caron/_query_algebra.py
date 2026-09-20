"""Internal witness-carrying algebra for compositional graph queries.

This module preserves the accepted query-algebra experiment inside the
maintained source tree. Its plan objects are deliberately private: schema
validation and a stable public query-plan contract remain later work.
"""

from dataclasses import dataclass
from typing import assert_never

from caron.entities import EntityId, EntityRef, PropertyValue
from caron.realisations import ValidatedRealisation
from caron.relations import RelationId
from caron.views import GraphView, QueryWitness


@dataclass(frozen=True, slots=True)
class EntityValue:
    entity_id: EntityId


@dataclass(frozen=True, slots=True)
class RelationValue:
    relation_id: RelationId


type BoundValue = EntityValue | RelationValue | str | int | None


@dataclass(frozen=True, slots=True)
class Variable:
    name: str


@dataclass(frozen=True, slots=True)
class EntityConstant:
    entity_id: EntityId


type EntityTerm = Variable | EntityConstant


@dataclass(frozen=True, slots=True)
class QualifierPattern:
    name: str
    term: EntityTerm


@dataclass(frozen=True, slots=True)
class RelationPattern:
    kinds: frozenset[str]
    source: EntityTerm
    target: EntityTerm
    relation_variable: Variable | None = None
    kind_variable: Variable | None = None
    qualifiers: tuple[QualifierPattern, ...] = ()


@dataclass(frozen=True, slots=True)
class Join:
    operands: tuple["Plan", ...]


@dataclass(frozen=True, slots=True)
class LeftJoin:
    left: "Plan"
    right: "Plan"
    optional_variables: tuple[Variable, ...]


@dataclass(frozen=True, slots=True)
class Union:
    operands: tuple["Plan", ...]


@dataclass(frozen=True, slots=True)
class Extend:
    operand: "Plan"
    values: tuple[tuple[Variable, BoundValue], ...]


@dataclass(frozen=True, slots=True)
class LookupProperty:
    operand: "Plan"
    entity: Variable
    property_name: str
    output: Variable
    allow_missing: bool = False


@dataclass(frozen=True, slots=True)
class Project:
    operand: "Plan"
    variables: tuple[Variable, ...]


@dataclass(frozen=True, slots=True)
class OrderBy:
    operand: "Plan"
    variables: tuple[Variable, ...]


type Plan = (
    RelationPattern
    | Join
    | LeftJoin
    | Union
    | Extend
    | LookupProperty
    | Project
    | OrderBy
)


@dataclass(frozen=True, slots=True)
class AlgebraRow:
    bindings: tuple[tuple[str, BoundValue], ...]
    witness: QueryWitness

    def value(self, variable: Variable) -> BoundValue:
        for name, value in self.bindings:
            if name == variable.name:
                return value
        raise KeyError(variable.name)

    def as_dict(self) -> dict[str, BoundValue]:
        return dict(self.bindings)


@dataclass(frozen=True, slots=True)
class AlgebraRelation:
    rows: tuple[AlgebraRow, ...]


type AnswerValue = str | int | None


@dataclass(frozen=True, slots=True)
class BindingRow:
    values: tuple[AnswerValue, ...]


@dataclass(frozen=True, slots=True)
class BindingTable:
    columns: tuple[str, ...]
    rows: tuple[BindingRow, ...]
    ordered_by: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class GraphPath:
    node_ids: tuple[EntityId, ...]
    relation_ids: tuple[RelationId, ...]


@dataclass(frozen=True, slots=True)
class PathSet:
    paths: tuple[GraphPath, ...]


def _ordered_bindings(
    bindings: dict[str, BoundValue],
) -> tuple[tuple[str, BoundValue], ...]:
    return tuple(sorted(bindings.items()))


def _combine_witnesses(left: QueryWitness, right: QueryWitness) -> QueryWitness:
    return QueryWitness(
        entities=tuple(dict.fromkeys((*left.entities, *right.entities))),
        relations=tuple(dict.fromkeys((*left.relations, *right.relations))),
        properties=tuple(dict.fromkeys((*left.properties, *right.properties))),
    )


def _bind_entity_term(
    term: EntityTerm,
    entity_id: EntityId,
    bindings: dict[str, BoundValue],
) -> bool:
    match term:
        case EntityConstant(expected_id):
            return expected_id == entity_id
        case Variable(name):
            value = EntityValue(entity_id)
            if name in bindings and bindings[name] != value:
                return False
            bindings[name] = value
            return True


def _relation_pattern(
    realisation: ValidatedRealisation,
    pattern: RelationPattern,
) -> AlgebraRelation:
    rows: list[AlgebraRow] = []
    for relation in realisation.relations:
        if relation.kind not in pattern.kinds:
            continue

        source_id = relation.source.entity_id
        target_id = relation.target.entity_id
        bindings: dict[str, BoundValue] = {}
        if not _bind_entity_term(pattern.source, source_id, bindings):
            continue
        if not _bind_entity_term(pattern.target, target_id, bindings):
            continue

        referenced_entities = {source_id, target_id}
        qualifier_match = True
        for qualifier_pattern in pattern.qualifiers:
            qualifier_value = relation.qualifier(qualifier_pattern.name)
            if not isinstance(qualifier_value, EntityRef) or not _bind_entity_term(
                qualifier_pattern.term,
                qualifier_value.entity_id,
                bindings,
            ):
                qualifier_match = False
                break
            referenced_entities.add(qualifier_value.entity_id)
        if not qualifier_match:
            continue

        if pattern.relation_variable is not None:
            bindings[pattern.relation_variable.name] = RelationValue(relation.id)
        if pattern.kind_variable is not None:
            bindings[pattern.kind_variable.name] = relation.kind

        rows.append(
            AlgebraRow(
                bindings=_ordered_bindings(bindings),
                witness=QueryWitness(
                    entities=tuple(
                        EntityRef(entity_id)
                        for entity_id in sorted(referenced_entities)
                    ),
                    relations=(relation.id,),
                ),
            )
        )
    return AlgebraRelation(tuple(rows))


def _merge_rows(left: AlgebraRow, right: AlgebraRow) -> AlgebraRow | None:
    bindings = left.as_dict()
    for name, value in right.bindings:
        if name in bindings and bindings[name] != value:
            return None
        bindings[name] = value
    return AlgebraRow(
        bindings=_ordered_bindings(bindings),
        witness=_combine_witnesses(left.witness, right.witness),
    )


def _join(relations: tuple[AlgebraRelation, ...]) -> AlgebraRelation:
    rows: tuple[AlgebraRow, ...] = (AlgebraRow((), QueryWitness(())),)
    for relation in relations:
        joined: list[AlgebraRow] = []
        for left in rows:
            for right in relation.rows:
                merged = _merge_rows(left, right)
                if merged is not None:
                    joined.append(merged)
        rows = tuple(joined)
    return AlgebraRelation(rows)


def _left_join(
    left: AlgebraRelation,
    right: AlgebraRelation,
    optional_variables: tuple[Variable, ...],
) -> AlgebraRelation:
    rows: list[AlgebraRow] = []
    for left_row in left.rows:
        matches = tuple(
            merged
            for right_row in right.rows
            if (merged := _merge_rows(left_row, right_row)) is not None
        )
        if matches:
            rows.extend(matches)
            continue
        bindings = left_row.as_dict()
        for variable in optional_variables:
            bindings.setdefault(variable.name, None)
        rows.append(AlgebraRow(_ordered_bindings(bindings), left_row.witness))
    return AlgebraRelation(tuple(rows))


def _extend(
    relation: AlgebraRelation,
    values: tuple[tuple[Variable, BoundValue], ...],
) -> AlgebraRelation:
    rows: list[AlgebraRow] = []
    for row in relation.rows:
        bindings = row.as_dict()
        compatible = True
        for variable, value in values:
            if variable.name in bindings and bindings[variable.name] != value:
                compatible = False
                break
            bindings[variable.name] = value
        if compatible:
            rows.append(AlgebraRow(_ordered_bindings(bindings), row.witness))
    return AlgebraRelation(tuple(rows))


def _property_value(value: PropertyValue) -> BoundValue:
    if isinstance(value, EntityRef):
        return EntityValue(value.entity_id)
    if isinstance(value, str) or isinstance(value, int) and not isinstance(value, bool):
        return value
    raise TypeError("the internal algebra can only bind scalar or entity properties")


def _lookup_property(
    realisation: ValidatedRealisation,
    relation: AlgebraRelation,
    *,
    entity_variable: Variable,
    property_name: str,
    output: Variable,
    allow_missing: bool,
) -> AlgebraRelation:
    rows: list[AlgebraRow] = []
    for row in relation.rows:
        entity_value = row.value(entity_variable)
        if not isinstance(entity_value, EntityValue):
            continue
        entity = realisation.entity(entity_value.entity_id)
        if entity is None:
            raise AssertionError("a validated binding refers to a missing entity")
        property_value = entity.property(property_name)
        if property_value is None:
            if allow_missing:
                rows.extend(_extend(AlgebraRelation((row,)), ((output, None),)).rows)
            continue
        extended = _extend(
            AlgebraRelation((row,)),
            ((output, _property_value(property_value)),),
        )
        property_witness = QueryWitness(
            entities=(EntityRef(entity.id),),
            properties=((EntityRef(entity.id), property_name),),
        )
        rows.extend(
            AlgebraRow(
                bindings=extended_row.bindings,
                witness=_combine_witnesses(extended_row.witness, property_witness),
            )
            for extended_row in extended.rows
        )
    return AlgebraRelation(tuple(rows))


def _project(
    relation: AlgebraRelation,
    variables: tuple[Variable, ...],
) -> AlgebraRelation:
    return AlgebraRelation(
        tuple(
            AlgebraRow(
                bindings=tuple(
                    (variable.name, row.value(variable)) for variable in variables
                ),
                witness=row.witness,
            )
            for row in relation.rows
        )
    )


def _sortable_value(value: BoundValue) -> tuple[int, int, str | int]:
    match value:
        case None:
            return (1, 0, "")
        case EntityValue(entity_id):
            return (0, 0, entity_id)
        case RelationValue(relation_id):
            return (0, 1, relation_id)
        case int():
            return (0, 2, value)
        case str():
            return (0, 3, value)


def _order_by(
    relation: AlgebraRelation,
    variables: tuple[Variable, ...],
) -> AlgebraRelation:
    return AlgebraRelation(
        tuple(
            sorted(
                relation.rows,
                key=lambda row: tuple(
                    _sortable_value(row.value(variable)) for variable in variables
                ),
            )
        )
    )


def evaluate_plan(
    realisation: ValidatedRealisation,
    plan: Plan,
) -> AlgebraRelation:
    """Evaluate one unchecked internal plan against a validated realisation."""

    match plan:
        case RelationPattern():
            return _relation_pattern(realisation, plan)
        case Join(operands):
            return _join(
                tuple(evaluate_plan(realisation, operand) for operand in operands)
            )
        case LeftJoin(left, right, optional_variables):
            return _left_join(
                evaluate_plan(realisation, left),
                evaluate_plan(realisation, right),
                optional_variables,
            )
        case Union(operands):
            return AlgebraRelation(
                tuple(
                    row
                    for operand in operands
                    for row in evaluate_plan(realisation, operand).rows
                )
            )
        case Extend(operand, values):
            return _extend(evaluate_plan(realisation, operand), values)
        case LookupProperty(operand, entity, property_name, output, allow_missing):
            return _lookup_property(
                realisation,
                evaluate_plan(realisation, operand),
                entity_variable=entity,
                property_name=property_name,
                output=output,
                allow_missing=allow_missing,
            )
        case Project(operand, variables):
            return _project(evaluate_plan(realisation, operand), variables)
        case OrderBy(operand, variables):
            return _order_by(evaluate_plan(realisation, operand), variables)
        case _ as unreachable:
            assert_never(unreachable)


def _answer_value(value: BoundValue) -> AnswerValue:
    match value:
        case EntityValue(entity_id):
            return entity_id
        case RelationValue(relation_id):
            return relation_id
        case None | str() | int():
            return value


def binding_table(
    relation: AlgebraRelation,
    *,
    variables: tuple[Variable, ...],
    ordered_by: tuple[Variable, ...] = (),
) -> BindingTable:
    return BindingTable(
        columns=tuple(variable.name for variable in variables),
        rows=tuple(
            BindingRow(
                tuple(_answer_value(row.value(variable)) for variable in variables)
            )
            for row in relation.rows
        ),
        ordered_by=tuple(variable.name for variable in ordered_by),
    )


def path_set(
    relation: AlgebraRelation,
    *,
    node_variables: tuple[Variable, ...],
    relation_variables: tuple[Variable, ...],
) -> PathSet:
    paths: list[GraphPath] = []
    for row in relation.rows:
        node_values = tuple(row.value(variable) for variable in node_variables)
        relation_values = tuple(row.value(variable) for variable in relation_variables)
        node_ids: list[EntityId] = []
        for value in node_values:
            if not isinstance(value, EntityValue):
                raise TypeError("path node variables must contain entity values")
            node_ids.append(value.entity_id)
        relation_ids: list[RelationId] = []
        for value in relation_values:
            if not isinstance(value, RelationValue):
                raise TypeError("path relation variables must contain relation values")
            relation_ids.append(value.relation_id)
        paths.append(
            GraphPath(
                node_ids=tuple(node_ids),
                relation_ids=tuple(relation_ids),
            )
        )
    return PathSet(tuple(paths))


def _reference_closed_entity_ids(
    realisation: ValidatedRealisation,
    relation: AlgebraRelation,
) -> set[EntityId]:
    entity_ids = {
        reference.entity_id
        for row in relation.rows
        for reference in row.witness.entities
    }
    relation_ids = {
        relation_id for row in relation.rows for relation_id in row.witness.relations
    }
    selected_relations = tuple(
        item for item in realisation.relations if item.id in relation_ids
    )

    for item in selected_relations:
        entity_ids.update((item.source.entity_id, item.target.entity_id))
        entity_ids.update(
            qualifier.value.entity_id
            for qualifier in item.qualifiers
            if isinstance(qualifier.value, EntityRef)
        )

    changed = True
    while changed:
        changed = False
        for entity_id in tuple(entity_ids):
            entity = realisation.entity(entity_id)
            if entity is None:
                raise AssertionError("a validated witness refers to a missing entity")
            for prop in entity.properties:
                if (
                    isinstance(prop.value, EntityRef)
                    and prop.value.entity_id not in entity_ids
                ):
                    entity_ids.add(prop.value.entity_id)
                    changed = True
    return entity_ids


def graph_view_from_relation(
    realisation: ValidatedRealisation,
    *,
    query_name: str,
    relation: AlgebraRelation,
) -> GraphView[AlgebraRow]:
    """Build a reference-closed view from the witnesses of surviving rows."""

    relation_ids = {
        relation_id for row in relation.rows for relation_id in row.witness.relations
    }
    entity_ids = _reference_closed_entity_ids(realisation, relation)
    return GraphView(
        query_name=query_name,
        source_realisation_id=realisation.id,
        ontology=realisation.ontology,
        entities=tuple(
            entity for entity in realisation.entities if entity.id in entity_ids
        ),
        relations=tuple(
            item for item in realisation.relations if item.id in relation_ids
        ),
        bindings=(),
        results=relation.rows,
        coverage=realisation.coverage,
    )

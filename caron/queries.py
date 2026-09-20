"""Small typed temporal queries over validated career realisations."""

from dataclasses import dataclass
from enum import StrEnum

from caron.entities import Entity, EntityId, EntityRef
from caron.ontology import ACTIVITY, CONTEXT
from caron.realisations import ValidatedRealisation
from caron.temporal import (
    KnownEnd,
    OngoingAsOf,
    TemporalExtent,
    TemporalWindow,
    UnknownEnd,
    YearMonth,
)
from caron.views import GraphView, QueryBinding, QueryWitness


class TemporalClassification(StrEnum):
    ENTAILED = "entailed"
    POSSIBLE = "possible"
    EXCLUDED = "excluded"
    UNKNOWN = "unknown"


class TemporalMatchMode(StrEnum):
    DEFINITE = "definite"
    POSSIBLE = "possible"


class CoveredMonthKind(StrEnum):
    EXACT = "exact"
    EXACT_AS_OF = "exact_as_of"
    BOUNDED = "bounded"
    INDETERMINATE = "indeterminate"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class TemporalPredicateResult:
    predicate: str
    left: EntityRef
    right: EntityRef
    classification: TemporalClassification
    witness: QueryWitness


@dataclass(frozen=True, slots=True)
class CoveredMonthResult:
    context: EntityRef
    kind: CoveredMonthKind
    minimum: int | None
    maximum: int | None
    as_of: YearMonth | None
    witness: QueryWitness


@dataclass(frozen=True, slots=True)
class TemporalMatch:
    entity: EntityRef
    classification: TemporalClassification
    witness: QueryWitness


@dataclass(frozen=True, slots=True)
class _TemporalConstraint:
    start_minimum: YearMonth | None
    start_maximum: YearMonth | None
    end_minimum: YearMonth | None
    end_maximum: YearMonth | None
    witness: QueryWitness

    @property
    def has_evidence(self) -> bool:
        return any(
            value is not None
            for value in (
                self.start_minimum,
                self.start_maximum,
                self.end_minimum,
                self.end_maximum,
            )
        )


def select_whole_realisation(
    realisation: ValidatedRealisation,
) -> GraphView[object]:
    """Return every asserted record in one immutable query view.

    Coverage remains explicit: this selects the whole accepted realisation,
    not a complete account of the person's career.
    """

    return GraphView(
        query_name="whole_realisation",
        source_realisation_id=realisation.id,
        ontology=realisation.ontology,
        entities=realisation.entities,
        relations=realisation.relations,
        bindings=(),
        results=(),
        coverage=realisation.coverage,
    )


def covered_months(
    realisation: ValidatedRealisation,
    context_id: EntityId,
) -> CoveredMonthResult:
    """Derive an exact, bounded, indeterminate, or unknown month count."""

    context = _required_entity(realisation, context_id, CONTEXT)
    extent = _extent(context)
    constraint = _context_constraint(realisation, context)

    if extent is not None:
        match extent.end:
            case KnownEnd(month):
                count = _inclusive_month_count(extent.start, month)
                return CoveredMonthResult(
                    EntityRef(context.id),
                    CoveredMonthKind.EXACT,
                    count,
                    count,
                    None,
                    constraint.witness,
                )
            case OngoingAsOf(month):
                count = _inclusive_month_count(extent.start, month)
                return CoveredMonthResult(
                    EntityRef(context.id),
                    CoveredMonthKind.EXACT_AS_OF,
                    count,
                    count,
                    month,
                    constraint.witness,
                )
            case UnknownEnd():
                if constraint.end_maximum is not None:
                    maximum = _inclusive_month_count(
                        extent.start, constraint.end_maximum
                    )
                    return CoveredMonthResult(
                        EntityRef(context.id),
                        CoveredMonthKind.BOUNDED,
                        1,
                        maximum,
                        None,
                        constraint.witness,
                    )
                return CoveredMonthResult(
                    EntityRef(context.id),
                    CoveredMonthKind.INDETERMINATE,
                    1,
                    None,
                    None,
                    constraint.witness,
                )

    if constraint.start_minimum is not None and constraint.end_maximum is not None:
        maximum = _inclusive_month_count(
            constraint.start_minimum, constraint.end_maximum
        )
        return CoveredMonthResult(
            EntityRef(context.id),
            CoveredMonthKind.BOUNDED,
            1,
            maximum,
            None,
            constraint.witness,
        )
    if constraint.has_evidence:
        return CoveredMonthResult(
            EntityRef(context.id),
            CoveredMonthKind.INDETERMINATE,
            1,
            None,
            None,
            constraint.witness,
        )
    return CoveredMonthResult(
        EntityRef(context.id),
        CoveredMonthKind.UNKNOWN,
        None,
        None,
        None,
        constraint.witness,
    )


def before(
    realisation: ValidatedRealisation,
    left_id: EntityId,
    right_id: EntityId,
) -> TemporalPredicateResult:
    """Classify whether one context or activity is strictly before another."""

    left = _required_temporal_entity(realisation, left_id)
    right = _required_temporal_entity(realisation, right_id)
    left_constraint = _constraint(realisation, left)
    right_constraint = _constraint(realisation, right)
    witness = _merge_witnesses(left_constraint.witness, right_constraint.witness)

    if not left_constraint.has_evidence or not right_constraint.has_evidence:
        classification = TemporalClassification.UNKNOWN
    elif (
        left_constraint.end_maximum is not None
        and right_constraint.start_minimum is not None
        and left_constraint.end_maximum < right_constraint.start_minimum
    ):
        classification = TemporalClassification.ENTAILED
    elif (
        left_constraint.end_minimum is not None
        and right_constraint.start_maximum is not None
        and left_constraint.end_minimum >= right_constraint.start_maximum
    ):
        classification = TemporalClassification.EXCLUDED
    else:
        classification = TemporalClassification.POSSIBLE

    return TemporalPredicateResult(
        "before",
        EntityRef(left.id),
        EntityRef(right.id),
        classification,
        witness,
    )


def overlaps(
    realisation: ValidatedRealisation,
    left_id: EntityId,
    right_id: EntityId,
) -> TemporalPredicateResult:
    """Classify whether two context or activity occurrences overlap."""

    left = _required_temporal_entity(realisation, left_id)
    right = _required_temporal_entity(realisation, right_id)
    left_constraint = _constraint(realisation, left)
    right_constraint = _constraint(realisation, right)
    witness = _merge_witnesses(left_constraint.witness, right_constraint.witness)

    if not left_constraint.has_evidence or not right_constraint.has_evidence:
        classification = TemporalClassification.UNKNOWN
    elif (
        left_constraint.end_maximum is not None
        and right_constraint.start_minimum is not None
        and left_constraint.end_maximum < right_constraint.start_minimum
    ) or (
        right_constraint.end_maximum is not None
        and left_constraint.start_minimum is not None
        and right_constraint.end_maximum < left_constraint.start_minimum
    ):
        classification = TemporalClassification.EXCLUDED
    elif (
        left_constraint.end_minimum is not None
        and right_constraint.start_maximum is not None
        and left_constraint.end_minimum >= right_constraint.start_maximum
        and right_constraint.end_minimum is not None
        and left_constraint.start_maximum is not None
        and right_constraint.end_minimum >= left_constraint.start_maximum
    ):
        classification = TemporalClassification.ENTAILED
    else:
        classification = TemporalClassification.POSSIBLE

    return TemporalPredicateResult(
        "overlaps",
        EntityRef(left.id),
        EntityRef(right.id),
        classification,
        witness,
    )


def select_activities_in_window(
    realisation: ValidatedRealisation,
    window: TemporalWindow,
    *,
    mode: TemporalMatchMode = TemporalMatchMode.DEFINITE,
    include_unknown: bool = False,
) -> GraphView[TemporalMatch]:
    """Select activities using context-derived temporal constraints."""

    matches = tuple(
        _activity_window_match(realisation, activity, window)
        for activity in realisation.entities_of_kind(ACTIVITY)
    )
    selected = tuple(
        match
        for match in matches
        if _include_match(match.classification, mode, include_unknown)
    )
    selected_entity_ids = {
        reference.entity_id
        for match in selected
        for reference in match.witness.entities
    }
    selected_relation_ids = {
        relation_id for match in selected for relation_id in match.witness.relations
    }
    selected_relations = tuple(
        relation
        for relation in realisation.relations
        if relation.id in selected_relation_ids
    )
    for relation in selected_relations:
        selected_entity_ids.add(relation.source.entity_id)
        selected_entity_ids.add(relation.target.entity_id)
    selected_entities = tuple(
        entity for entity in realisation.entities if entity.id in selected_entity_ids
    )
    bindings = tuple(QueryBinding("activity", match.entity) for match in selected)
    return GraphView(
        query_name="activities_in_temporal_window",
        source_realisation_id=realisation.id,
        ontology=realisation.ontology,
        entities=selected_entities,
        relations=selected_relations,
        bindings=bindings,
        results=selected,
        coverage=realisation.coverage,
    )


def _activity_window_match(
    realisation: ValidatedRealisation,
    activity: Entity,
    window: TemporalWindow,
) -> TemporalMatch:
    constraint = _activity_constraint(realisation, activity)
    if not constraint.has_evidence:
        classification = TemporalClassification.UNKNOWN
    elif (
        constraint.end_maximum is not None and constraint.end_maximum < window.start
    ) or (
        constraint.start_minimum is not None and constraint.start_minimum > window.end
    ):
        classification = TemporalClassification.EXCLUDED
    elif (
        constraint.start_minimum is not None
        and constraint.end_maximum is not None
        and window.start <= constraint.start_minimum
        and constraint.end_maximum <= window.end
    ):
        classification = TemporalClassification.ENTAILED
    else:
        classification = TemporalClassification.POSSIBLE
    return TemporalMatch(EntityRef(activity.id), classification, constraint.witness)


def _include_match(
    classification: TemporalClassification,
    mode: TemporalMatchMode,
    include_unknown: bool,
) -> bool:
    if classification is TemporalClassification.ENTAILED:
        return True
    if (
        mode is TemporalMatchMode.POSSIBLE
        and classification is TemporalClassification.POSSIBLE
    ):
        return True
    return include_unknown and classification is TemporalClassification.UNKNOWN


def _constraint(
    realisation: ValidatedRealisation,
    entity: Entity,
) -> _TemporalConstraint:
    if entity.kind == CONTEXT:
        return _context_constraint(realisation, entity)
    if entity.kind == ACTIVITY:
        return _activity_constraint(realisation, entity)
    raise ValueError("temporal queries accept only Context or Activity entities")


def _context_constraint(
    realisation: ValidatedRealisation,
    context: Entity,
) -> _TemporalConstraint:
    extent = _extent(context)
    ancestors = _dated_ancestors(realisation, context.id)
    witness = QueryWitness(
        entities=_unique_refs(
            (EntityRef(context.id),)
            + tuple(EntityRef(item.id) for item, _ in ancestors)
        ),
        relations=_unique_strings(
            tuple(
                relation_id
                for _, relation_path in ancestors
                for relation_id in relation_path
            )
        ),
        properties=tuple(
            (EntityRef(entity.id), "temporal_extent")
            for entity in (context, *(item for item, _ in ancestors))
            if _extent(entity) is not None
        ),
    )
    ancestor_extents = tuple(
        item_extent
        for item, _ in ancestors
        if (item_extent := _extent(item)) is not None
    )
    ancestor_start = max(
        (item.start for item in ancestor_extents),
        default=None,
    )
    ancestor_end = min(
        (item.end.month for item in ancestor_extents if isinstance(item.end, KnownEnd)),
        default=None,
    )

    if extent is None:
        return _TemporalConstraint(
            ancestor_start,
            ancestor_end,
            ancestor_start,
            ancestor_end,
            witness,
        )

    match extent.end:
        case KnownEnd(month):
            return _TemporalConstraint(
                extent.start,
                extent.start,
                month,
                month,
                witness,
            )
        case OngoingAsOf(month):
            return _TemporalConstraint(
                extent.start,
                extent.start,
                month,
                ancestor_end,
                witness,
            )
        case UnknownEnd():
            return _TemporalConstraint(
                extent.start,
                extent.start,
                extent.start,
                ancestor_end,
                witness,
            )


def _activity_constraint(
    realisation: ValidatedRealisation,
    activity: Entity,
) -> _TemporalConstraint:
    occurs_in = realisation.matching_relations(kind="occurs_in", source_id=activity.id)
    if not occurs_in:
        return _TemporalConstraint(
            None,
            None,
            None,
            None,
            QueryWitness((EntityRef(activity.id),)),
        )
    relation = occurs_in[0]
    context = realisation.entity(relation.target.entity_id)
    if context is None:
        raise AssertionError("validated occurs_in relation has a missing context")
    context_constraint = _context_constraint(realisation, context)
    return _TemporalConstraint(
        context_constraint.start_minimum,
        context_constraint.end_maximum,
        context_constraint.start_minimum,
        context_constraint.end_maximum,
        _merge_witnesses(
            QueryWitness(
                (EntityRef(activity.id), EntityRef(context.id)),
                (relation.id,),
            ),
            context_constraint.witness,
        ),
    )


def _dated_ancestors(
    realisation: ValidatedRealisation,
    context_id: EntityId,
) -> tuple[tuple[Entity, tuple[str, ...]], ...]:
    parent_edges: dict[str, list[tuple[str, str]]] = {}
    for relation in realisation.matching_relations(kind="part_of"):
        parent_edges.setdefault(relation.source.entity_id, []).append(
            (relation.target.entity_id, relation.id)
        )

    discovered: list[tuple[Entity, tuple[str, ...]]] = []
    pending: list[tuple[str, tuple[str, ...]]] = [(context_id, ())]
    visited = {context_id}
    while pending:
        current_id, path = pending.pop()
        for parent_id, relation_id in parent_edges.get(current_id, []):
            if parent_id in visited:
                continue
            visited.add(parent_id)
            parent = realisation.entity(parent_id)
            if parent is None:
                raise AssertionError("validated part_of relation has a missing parent")
            parent_path = (*path, relation_id)
            discovered.append((parent, parent_path))
            pending.append((parent_id, parent_path))
    return tuple(discovered)


def _required_temporal_entity(
    realisation: ValidatedRealisation,
    entity_id: EntityId,
) -> Entity:
    entity = realisation.entity(entity_id)
    if entity is None:
        raise KeyError(entity_id)
    if entity.kind not in {CONTEXT, ACTIVITY}:
        raise ValueError("temporal queries accept only Context or Activity entities")
    return entity


def _required_entity(
    realisation: ValidatedRealisation,
    entity_id: EntityId,
    expected_kind: str,
) -> Entity:
    entity = realisation.entity(entity_id)
    if entity is None:
        raise KeyError(entity_id)
    if entity.kind != expected_kind:
        raise ValueError(f"entity must be a {expected_kind}")
    return entity


def _extent(entity: Entity) -> TemporalExtent | None:
    value = entity.property("temporal_extent")
    return value if isinstance(value, TemporalExtent) else None


def _inclusive_month_count(start: YearMonth, end: YearMonth) -> int:
    return end.month_index - start.month_index + 1


def _merge_witnesses(*witnesses: QueryWitness) -> QueryWitness:
    return QueryWitness(
        entities=_unique_refs(
            tuple(reference for witness in witnesses for reference in witness.entities)
        ),
        relations=_unique_strings(
            tuple(relation for witness in witnesses for relation in witness.relations)
        ),
        properties=tuple(
            dict.fromkeys(
                property_reference
                for witness in witnesses
                for property_reference in witness.properties
            )
        ),
    )


def _unique_refs(values: tuple[EntityRef, ...]) -> tuple[EntityRef, ...]:
    return tuple(dict.fromkeys(values))


def _unique_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))

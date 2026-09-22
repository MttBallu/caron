"""Realisation-wide invariant implementations for Career Ontology 5.0."""

from collections.abc import Hashable

from caron._invariants import register_invariant
from caron.diagnostics import Diagnostic, DiagnosticLayer
from caron.entities import Entity, EntityRef, PropertyValue
from caron.ontology import CONTEXT, OntologySchema
from caron.realisations import RealisationCandidate
from caron.relations import RelationAssertion
from caron.temporal import KnownEnd, OngoingAsOf, TemporalExtent, UnknownEnd, YearMonth

type SemanticRelationKey = tuple[
    str,
    str,
    str,
    tuple[tuple[str, Hashable], ...],
]

_ACTIVITY_OUTCOMES = frozenset({"results_in", "establishes", "supports", "contradicts"})


def semantic_relation_key(relation: RelationAssertion) -> SemanticRelationKey:
    """Return the typed semantic identity of one relation fact."""

    qualifiers = tuple(
        sorted(
            (
                (qualifier.name, _typed_value_key(qualifier.value))
                for qualifier in relation.qualifiers
            ),
            key=lambda item: item[0],
        )
    )
    return (
        relation.kind,
        relation.source.entity_id,
        relation.target.entity_id,
        qualifiers,
    )


def _typed_value_key(value: PropertyValue) -> Hashable:
    if isinstance(value, str):
        return ("text", value)
    if isinstance(value, bool):
        # Boolean values cannot pass local integer validation. Retaining an
        # explicit tag keeps this utility total and prevents Python's 1 == True.
        return ("invalid_boolean", value)
    if isinstance(value, int):
        return ("integer", value)
    if isinstance(value, EntityRef):
        return ("entity_reference", value.entity_id)
    if isinstance(value, YearMonth):
        return ("year_month", value.year, value.month)
    if isinstance(value, TemporalExtent):
        match value.end:
            case KnownEnd(month):
                end: Hashable = ("known", month.year, month.month)
            case OngoingAsOf(month):
                end = ("ongoing_as_of", month.year, month.month)
            case UnknownEnd():
                end = ("unknown",)
        return ("temporal_extent", value.start.year, value.start.month, end)
    raise TypeError(f"Unsupported relation qualifier value: {value!r}")


@register_invariant("semantic_relation_fact_unique")
def _semantic_relation_fact_unique(
    ontology: OntologySchema, candidate: RealisationCandidate
) -> tuple[Diagnostic, ...]:
    del ontology
    by_key: dict[SemanticRelationKey, list[RelationAssertion]] = {}
    for relation in candidate.relations:
        by_key.setdefault(semantic_relation_key(relation), []).append(relation)

    duplicate_groups = sorted(
        (
            tuple(sorted(group, key=lambda relation: relation.id))
            for group in by_key.values()
            if len(group) > 1
        ),
        key=lambda group: tuple(relation.id for relation in group),
    )
    diagnostics: list[Diagnostic] = []
    for group in duplicate_groups:
        canonical = group[0]
        for duplicate in group[1:]:
            diagnostics.append(
                Diagnostic(
                    code="realisation.duplicate_relation_fact",
                    layer=DiagnosticLayer.REALISATION,
                    message=(
                        f"Relation {duplicate.id!r} duplicates the semantic fact "
                        f"identified by relation {canonical.id!r}."
                    ),
                    record_id=duplicate.id,
                )
            )
    return tuple(diagnostics)


@register_invariant("part_of_acyclic")
def _part_of_acyclic(
    ontology: OntologySchema, candidate: RealisationCandidate
) -> tuple[Diagnostic, ...]:
    del ontology
    return _cycle_diagnostics(candidate.relations, "part_of")


@register_invariant("suborganization_of_acyclic")
def _suborganization_of_acyclic(
    ontology: OntologySchema, candidate: RealisationCandidate
) -> tuple[Diagnostic, ...]:
    del ontology
    return _cycle_diagnostics(candidate.relations, "suborganization_of")


def _cycle_diagnostics(
    relations: tuple[RelationAssertion, ...], relation_kind: str
) -> tuple[Diagnostic, ...]:
    selected = tuple(
        sorted(
            (relation for relation in relations if relation.kind == relation_kind),
            key=lambda relation: relation.id,
        )
    )
    adjacency: dict[str, set[str]] = {}
    for relation in selected:
        adjacency.setdefault(relation.source.entity_id, set()).add(
            relation.target.entity_id
        )

    code = f"realisation.{relation_kind}_cycle"
    diagnostics: list[Diagnostic] = []
    for relation in selected:
        source_id = relation.source.entity_id
        target_id = relation.target.entity_id
        if source_id != target_id and not _reaches(target_id, source_id, adjacency):
            continue
        diagnostics.append(
            Diagnostic(
                code=code,
                layer=DiagnosticLayer.REALISATION,
                message=(
                    f"Relation {relation.id!r} participates in a cycle in the "
                    f"{relation_kind!r} graph."
                ),
                record_id=relation.id,
                field=relation_kind,
            )
        )
    return tuple(diagnostics)


def _reaches(source_id: str, target_id: str, adjacency: dict[str, set[str]]) -> bool:
    pending = [source_id]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == target_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(sorted(adjacency.get(current, ()), reverse=True))
    return False


@register_invariant("aims_at_locality")
def _aims_at_locality(
    ontology: OntologySchema, candidate: RealisationCandidate
) -> tuple[Diagnostic, ...]:
    del ontology
    entity_by_id = {entity.id: entity for entity in candidate.entities}
    diagnostics: list[Diagnostic] = []
    for relation in sorted(candidate.relations, key=lambda item: item.id):
        if relation.kind != "aims_at":
            continue
        proposition = entity_by_id[relation.target.entity_id]
        context = proposition.property("context")
        if not isinstance(context, EntityRef):
            continue
        if context.entity_id != relation.source.entity_id:
            diagnostics.append(
                Diagnostic(
                    code="realisation.aims_at_context_mismatch",
                    layer=DiagnosticLayer.REALISATION,
                    message=(
                        f"Proposition {proposition.id!r} is local to Context "
                        f"{context.entity_id!r}, not {relation.source.entity_id!r}."
                    ),
                    record_id=relation.id,
                    field="target",
                )
            )
    return tuple(diagnostics)


@register_invariant("bears_on_roles_and_locality")
def _bears_on_roles_and_locality(
    ontology: OntologySchema, candidate: RealisationCandidate
) -> tuple[Diagnostic, ...]:
    del ontology
    entity_by_id = {entity.id: entity for entity in candidate.entities}
    outcome_propositions = frozenset(
        relation.target.entity_id
        for relation in candidate.relations
        if relation.kind in _ACTIVITY_OUTCOMES
    )
    aim_propositions = frozenset(
        relation.target.entity_id
        for relation in candidate.relations
        if relation.kind == "aims_at"
    )
    context_adjacency = _relation_adjacency(candidate.relations, "part_of")

    diagnostics: list[Diagnostic] = []
    for relation in sorted(candidate.relations, key=lambda item: item.id):
        if relation.kind != "bears_on":
            continue
        source_id = relation.source.entity_id
        target_id = relation.target.entity_id
        if source_id not in outcome_propositions:
            diagnostics.append(
                _bears_on_diagnostic(
                    relation,
                    "realisation.bears_on_source_not_outcome",
                    "source",
                    "The source Proposition is not an explicit Activity outcome.",
                )
            )
        if target_id not in aim_propositions:
            diagnostics.append(
                _bears_on_diagnostic(
                    relation,
                    "realisation.bears_on_target_not_aim",
                    "target",
                    "The target Proposition is not an explicit Context aim.",
                )
            )
        if source_id == target_id:
            diagnostics.append(
                _bears_on_diagnostic(
                    relation,
                    "realisation.bears_on_self_reference",
                    "target",
                    "A bears_on assertion must connect distinct Propositions.",
                )
            )

        source_context = _proposition_context(entity_by_id[source_id])
        target_context = _proposition_context(entity_by_id[target_id])
        if (
            source_context is not None
            and target_context is not None
            and source_context != target_context
            and not _reaches(source_context, target_context, context_adjacency)
        ):
            diagnostics.append(
                _bears_on_diagnostic(
                    relation,
                    "realisation.bears_on_incompatible_context",
                    "target",
                    (
                        f"Source Context {source_context!r} is neither equal to nor "
                        f"nested within target Context {target_context!r}."
                    ),
                )
            )
    return tuple(diagnostics)


def _bears_on_diagnostic(
    relation: RelationAssertion, code: str, field: str, message: str
) -> Diagnostic:
    return Diagnostic(
        code=code,
        layer=DiagnosticLayer.REALISATION,
        message=message,
        record_id=relation.id,
        field=field,
    )


def _proposition_context(proposition: Entity) -> str | None:
    context = proposition.property("context")
    return context.entity_id if isinstance(context, EntityRef) else None


def _relation_adjacency(
    relations: tuple[RelationAssertion, ...], relation_kind: str
) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {}
    for relation in relations:
        if relation.kind == relation_kind:
            adjacency.setdefault(relation.source.entity_id, set()).add(
                relation.target.entity_id
            )
    return adjacency


@register_invariant("temporal_consistency")
def _temporal_consistency(
    ontology: OntologySchema, candidate: RealisationCandidate
) -> tuple[Diagnostic, ...]:
    del ontology
    return temporal_consistency_diagnostics(candidate.entities, candidate.relations)


def temporal_consistency_diagnostics(
    entities: tuple[Entity, ...],
    relations: tuple[RelationAssertion, ...],
) -> tuple[Diagnostic, ...]:
    """Reject Context occurrences that cannot fit in all of their ancestors.

    Activity has no intrinsic temporal property in 5.0. Its single ``occurs_in``
    relation therefore constrains its nonempty occurrence to the target Context
    without introducing a copied or independently stored extent.
    """

    context_by_id = {entity.id: entity for entity in entities if entity.kind == CONTEXT}
    parent_edges: dict[str, list[tuple[str, str]]] = {}
    for relation in relations:
        if relation.kind != "part_of":
            continue
        if (
            relation.source.entity_id not in context_by_id
            or relation.target.entity_id not in context_by_id
        ):
            continue
        parent_edges.setdefault(relation.source.entity_id, []).append(
            (relation.target.entity_id, relation.id)
        )
    for edges in parent_edges.values():
        edges.sort()

    diagnostics: list[Diagnostic] = []
    for child in sorted(context_by_id.values(), key=lambda entity: entity.id):
        ancestors = _ancestor_paths(child.id, parent_edges)
        dated_ancestors = tuple(
            (ancestor_id, relation_path, ancestor_extent)
            for ancestor_id, relation_path in ancestors
            if isinstance(
                ancestor_extent := context_by_id[ancestor_id].property(
                    "temporal_extent"
                ),
                TemporalExtent,
            )
        )
        lower_bound = max(
            (extent.start for _, _, extent in dated_ancestors), default=None
        )
        upper_bound = min(
            (
                extent.end.month
                for _, _, extent in dated_ancestors
                if isinstance(extent.end, KnownEnd)
            ),
            default=None,
        )
        if (
            lower_bound is not None
            and upper_bound is not None
            and lower_bound > upper_bound
        ):
            diagnostics.append(
                Diagnostic(
                    code="realisation.temporal_containment_impossible",
                    layer=DiagnosticLayer.REALISATION,
                    message=(
                        f"Dated ancestors of Context {child.id!r} have no common "
                        "month in which its nonempty occurrence can fit."
                    ),
                    record_id=child.id,
                    field="temporal_extent",
                )
            )
            continue

        child_extent = child.property("temporal_extent")
        if not isinstance(child_extent, TemporalExtent):
            continue
        for ancestor_id, relation_path, ancestor_extent in dated_ancestors:
            if _can_be_contained(child_extent, ancestor_extent):
                continue
            diagnostics.append(
                Diagnostic(
                    code="realisation.temporal_containment_impossible",
                    layer=DiagnosticLayer.REALISATION,
                    message=(
                        f"Context {child.id!r} cannot occur within dated ancestor "
                        f"{ancestor_id!r} along relations {relation_path!r}."
                    ),
                    record_id=child.id,
                    field="temporal_extent",
                )
            )
    return tuple(diagnostics)


def _ancestor_paths(
    child_id: str,
    parent_edges: dict[str, list[tuple[str, str]]],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    discovered: list[tuple[str, tuple[str, ...]]] = []
    pending: list[tuple[str, tuple[str, ...]]] = [(child_id, ())]
    visited = {child_id}
    while pending:
        current_id, path = pending.pop()
        for parent_id, relation_id in reversed(parent_edges.get(current_id, [])):
            if parent_id in visited:
                continue
            visited.add(parent_id)
            parent_path = (*path, relation_id)
            discovered.append((parent_id, parent_path))
            pending.append((parent_id, parent_path))
    return tuple(sorted(discovered))


def _can_be_contained(child: TemporalExtent, parent: TemporalExtent) -> bool:
    if child.start < parent.start:
        return False
    if not isinstance(parent.end, KnownEnd):
        return True
    match child.end:
        case KnownEnd(month) | OngoingAsOf(month):
            child_minimum_end = month
        case UnknownEnd():
            child_minimum_end = child.start
    return child_minimum_end <= parent.end.month

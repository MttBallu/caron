"""Private, draft M2-A result assembly for a validated Neo4j projection."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, Self

from caron.adapters.neo4j_projection import ProjectionError
from caron.adapters.neo4j_reconstruction import ReconstructedSnapshot, _extract
from caron.adapters.neo4j_retrieval import _RESOURCE_KINDS, RetrievalRows, _read
from caron.entities import Entity, EntityRef
from caron.ontology import career_ontology_v5_0
from caron.realisations import Coverage, ValidatedRealisation
from caron.relations import RelationAssertion
from caron.views import GraphView, QueryBinding


@dataclass(frozen=True, slots=True)
class Request:
    person_id: str
    target_id: str


@dataclass(frozen=True, slots=True)
class RequestDiagnostic:
    code: str
    entity_id: str


@dataclass(frozen=True, slots=True)
class LearningMatch:
    person: EntityRef
    target: EntityRef
    context: EntityRef
    learns: str


@dataclass(frozen=True, slots=True)
class ActivityResourceMatch:
    person: EntityRef
    activity: EntityRef
    target: EntityRef
    local_context: EntityRef
    resource_kind: str
    performs: str
    occurs_in: str
    resource_relation: str


type Match = LearningMatch | ActivityResourceMatch


@dataclass(frozen=True, slots=True)
class AssembledResult:
    request: Request
    source_realisation_id: str
    source_state_id: str | None
    ontology_id: str
    ontology_version: str
    coverage: Coverage
    matches: tuple[Match, ...]
    view: GraphView[Match] | None
    diagnostics: tuple[RequestDiagnostic, ...] = ()


def _request_diagnostics(
    source: ValidatedRealisation, request: Request
) -> tuple[RequestDiagnostic, ...]:
    ontology = career_ontology_v5_0()
    if (source.ontology.id, source.ontology.version) != (
        ontology.id,
        ontology.version,
    ):
        return (RequestDiagnostic("query.unsupported_ontology", source.ontology.id),)
    person = source.entity(request.person_id)
    target = source.entity(request.target_id)
    errors = []
    if person is None:
        errors.append(RequestDiagnostic("query.unknown_person", request.person_id))
    elif person.kind != "Person":
        errors.append(RequestDiagnostic("query.invalid_person_kind", request.person_id))
    if target is None:
        errors.append(RequestDiagnostic("query.unknown_target", request.target_id))
    elif target.kind not in {"Technology", "Language", "Method", "Subject"}:
        errors.append(RequestDiagnostic("query.invalid_target_kind", request.target_id))
    return tuple(errors)


def _support(
    source: ValidatedRealisation,
    relation_id: str,
    kind: str,
    source_id: str,
    target_id: str,
) -> RelationAssertion:
    relation = source.relation(relation_id)
    if (
        relation is None
        or relation.kind != kind
        or relation.source.entity_id != source_id
        or relation.target.entity_id != target_id
    ):
        raise ProjectionError(
            f"Match support {relation_id!r} disagrees with its source"
        )
    return relation


def assemble_result(
    snapshot: ReconstructedSnapshot,
    request: Request,
    rows: RetrievalRows | None,
) -> AssembledResult:
    """Assemble selected source records without creating inferred assertions."""
    source = snapshot.validated
    diagnostics = _request_diagnostics(source, request)
    base = (
        request,
        source.id,
        snapshot.source_state_id,
        source.ontology.id,
        source.ontology.version,
        source.coverage,
    )
    if diagnostics:
        return AssembledResult(*base, (), None, diagnostics)
    if rows is None:
        raise ProjectionError("Missing retrieval rows for a valid request")
    if (
        rows.realisation_id != source.id
        or (rows.ontology_id, rows.ontology_version)
        != (source.ontology.id, source.ontology.version)
        or rows.source_state_id != snapshot.source_state_id
        or rows.coverage != source.coverage
    ):
        raise ProjectionError("Retrieval and reconstructed snapshot disagree")

    matches: list[Match] = []
    selected_relations: dict[str, RelationAssertion] = {}
    selected_entities: dict[str, Entity] = {}

    def select_entity(entity_id: str) -> None:
        entity = source.entity(entity_id)
        if entity is None:
            raise ProjectionError(f"Match refers to missing entity {entity_id!r}")
        selected_entities[entity_id] = entity

    def select_relation(relation: RelationAssertion) -> None:
        selected_relations[relation.id] = relation
        select_entity(relation.source.entity_id)
        select_entity(relation.target.entity_id)
        for qualifier in relation.qualifiers:
            if isinstance(qualifier.value, EntityRef):
                select_entity(qualifier.value.entity_id)

    for row in rows.learning:
        if (row.person_id, row.target_id) != (request.person_id, request.target_id):
            raise ProjectionError("Learning match changed request bindings")
        relation = _support(
            source, row.learns_id, "learns", row.person_id, row.target_id
        )
        if relation.qualifier("context") != EntityRef(row.context_id):
            raise ProjectionError("Learning match context disagrees with support")
        select_relation(relation)
        matches.append(
            LearningMatch(
                EntityRef(row.person_id),
                EntityRef(row.target_id),
                EntityRef(row.context_id),
                row.learns_id,
            )
        )
    for activity_row in rows.activity:
        if (activity_row.person_id, activity_row.target_id) != (
            request.person_id,
            request.target_id,
        ):
            raise ProjectionError("Activity match changed request bindings")
        target = source.entity(request.target_id)
        assert target is not None  # request validated above
        if activity_row.resource_kind not in _RESOURCE_KINDS[target.kind]:
            raise ProjectionError("Activity match has an unlicensed resource kind")
        for relation_id, kind, start, end in (
            (
                activity_row.performs_id,
                "performs",
                activity_row.person_id,
                activity_row.activity_id,
            ),
            (
                activity_row.occurs_in_id,
                "occurs_in",
                activity_row.activity_id,
                activity_row.context_id,
            ),
            (
                activity_row.resource_relation_id,
                activity_row.resource_kind,
                activity_row.activity_id,
                activity_row.target_id,
            ),
        ):
            select_relation(_support(source, relation_id, kind, start, end))
        matches.append(
            ActivityResourceMatch(
                EntityRef(activity_row.person_id),
                EntityRef(activity_row.activity_id),
                EntityRef(activity_row.target_id),
                EntityRef(activity_row.context_id),
                activity_row.resource_kind,
                activity_row.performs_id,
                activity_row.occurs_in_id,
                activity_row.resource_relation_id,
            )
        )
    if len(set(matches)) != len(matches):
        raise ProjectionError("Duplicate complete matches in retrieval rows")
    # Entity properties can also refer to entities outside the selected relations.
    pending = list(selected_entities.values())
    while pending:
        entity = pending.pop()
        for prop in entity.properties:
            if (
                isinstance(prop.value, EntityRef)
                and prop.value.entity_id not in selected_entities
            ):
                select_entity(prop.value.entity_id)
                pending.append(selected_entities[prop.value.entity_id])

    selected = tuple(matches)
    view = GraphView(
        query_name="ReusableEntityMatches",
        source_realisation_id=source.id,
        ontology=source.ontology,
        entities=tuple(sorted(selected_entities.values(), key=lambda item: item.id)),
        relations=tuple(sorted(selected_relations.values(), key=lambda item: item.id)),
        bindings=(
            (
                QueryBinding("person", EntityRef(request.person_id)),
                QueryBinding("target", EntityRef(request.target_id)),
            )
            if selected
            else ()
        ),
        results=selected,
        coverage=source.coverage,
    )
    return AssembledResult(*base, selected, view)


class _Rows(Protocol):
    def data(self) -> list[dict[str, object]]: ...


class _ReadTransaction(Protocol):
    def run(self, query: str, **parameters: object) -> _Rows: ...


class _ReadSession(Protocol):
    def __enter__(self) -> Self: ...
    def __exit__(self, *args: object) -> object: ...
    def execute_read(
        self, work: Callable[[_ReadTransaction], AssembledResult]
    ) -> AssembledResult: ...


class _ReadDriver(Protocol):
    def session(self, *, database: str) -> _ReadSession: ...


def evaluate_projected_matches(
    driver: _ReadDriver,
    *,
    request: Request,
    expected_realisation_id: str,
    expected_source_state_id: str | None = None,
    database: str = "neo4j",
) -> AssembledResult:
    """Read, verify and evaluate one committed snapshot in one read transaction."""

    def evaluate(tx: _ReadTransaction) -> AssembledResult:
        # The two private readers use the same read transaction and never
        # assemble records from different committed snapshots.
        snapshot = _extract(tx)
        if snapshot.validated.id != expected_realisation_id or (
            expected_source_state_id is not None
            and snapshot.source_state_id != expected_source_state_id
        ):
            raise ProjectionError(
                "Projected snapshot does not match the requested source"
            )
        if _request_diagnostics(snapshot.validated, request):
            return assemble_result(snapshot, request, None)
        rows = _read(
            tx,
            request.person_id,
            request.target_id,
            expected_realisation_id,
            expected_source_state_id,
        )
        return assemble_result(snapshot, request, rows)

    with driver.session(database=database) as session:
        return session.execute_read(evaluate)

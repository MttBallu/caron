"""Private, draft M2-A result assembly for a validated Neo4j projection."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, Self

from caron._m2a import (
    _RESOURCE_KINDS,
    ActivityResourceMatch,
    LearningMatch,
    Match,
    MatchesAccepted,
    MatchesRejected,
    Request,
    RequestDiagnostic,
    build_view,
    request_diagnostics,
)
from caron.adapters.neo4j_projection import ProjectionError
from caron.adapters.neo4j_reconstruction import ReconstructedSnapshot, _extract
from caron.adapters.neo4j_retrieval import RetrievalRows, _read
from caron.entities import EntityRef
from caron.realisations import Coverage, ValidatedRealisation
from caron.relations import RelationAssertion
from caron.views import GraphView


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

    def semantic_outcome(self) -> MatchesAccepted | MatchesRejected:
        """Discard projection metadata and expose the draft semantic outcome."""
        identity = (
            self.request,
            self.source_realisation_id,
            self.ontology_id,
            self.ontology_version,
        )
        if self.diagnostics:
            return MatchesRejected(*identity, self.diagnostics)
        if self.view is None:
            raise ProjectionError("Successful retrieval has no graph view")
        return MatchesAccepted(*identity, self.coverage, self.matches, self.view)


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
    diagnostics = request_diagnostics(source, request)
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
    for row in rows.learning:
        if (row.person_id, row.target_id) != (request.person_id, request.target_id):
            raise ProjectionError("Learning match changed request bindings")
        relation = _support(
            source, row.learns_id, "learns", row.person_id, row.target_id
        )
        if relation.qualifier("context") != EntityRef(row.context_id):
            raise ProjectionError("Learning match context disagrees with support")
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
            _support(source, relation_id, kind, start, end)
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
    selected = tuple(matches)
    view = build_view(source, request, selected)
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
        if request_diagnostics(snapshot.validated, request):
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

"""Private M2-A structural retrieval against one committed projection snapshot.

The returned rows are only the two physical query branches. Public request
diagnostics, typed match variants, and GraphView assembly belong to step 6.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Protocol, Self

from caron.adapters.neo4j_projection import PROFILE_VERSION, ProjectionError
from caron.ontology import career_ontology_v5_0
from caron.realisations import Coverage, CoverageStatus

_RESOURCE_KINDS = {
    "Technology": ("uses_technology",),
    "Language": ("uses_language",),
    "Method": ("applies", "draws_on"),
    "Subject": ("draws_on",),
}

_LEARNING = """CYPHER 25
MATCH (person:CaronEntity:Person {id: $person_id})
      <-[:CARON_SOURCE]-(learning:CaronRelation {kind: 'learns'})
      -[:CARON_TARGET]->(target:CaronEntity {id: $target_id})
MATCH (learning)-[:CARON_Q_CONTEXT]->(context:CaronEntity:Context)
RETURN person.id AS person_id, target.id AS target_id,
       context.id AS context_id, learning.id AS learns_id
"""

_ACTIVITY = """CYPHER 25
MATCH (person:CaronEntity:Person {id: $person_id})
      -[performed:CARON_DIRECT {kind: 'performs'}]->(activity:CaronEntity:Activity)
MATCH (activity)-[located:CARON_DIRECT {kind: 'occurs_in'}]
      ->(context:CaronEntity:Context)
MATCH (activity)-[resource:CARON_DIRECT]->(target:CaronEntity {id: $target_id})
WHERE resource.kind IN $resource_kinds
RETURN person.id AS person_id, activity.id AS activity_id,
       target.id AS target_id, context.id AS context_id,
       resource.kind AS resource_kind, performed.id AS performs_id,
       located.id AS occurs_in_id, resource.id AS resource_relation_id
"""


class _Rows(Protocol):
    def data(self) -> list[dict[str, object]]: ...


class _ReadTransaction(Protocol):
    def run(self, query: str, **parameters: object) -> _Rows: ...


class _ReadSession(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(self, *args: object) -> object: ...

    def execute_read(
        self, work: Callable[[_ReadTransaction], RetrievalRows]
    ) -> RetrievalRows: ...


class _ReadDriver(Protocol):
    def session(self, *, database: str) -> _ReadSession: ...


@dataclass(frozen=True, slots=True)
class LearningRow:
    person_id: str
    target_id: str
    context_id: str
    learns_id: str


@dataclass(frozen=True, slots=True)
class ActivityRow:
    person_id: str
    target_id: str
    activity_id: str
    context_id: str
    resource_kind: str
    performs_id: str
    occurs_in_id: str
    resource_relation_id: str


@dataclass(frozen=True, slots=True)
class RetrievalRows:
    realisation_id: str
    ontology_id: str
    ontology_version: str
    source_state_id: str | None
    coverage: Coverage
    learning: tuple[LearningRow, ...]
    activity: tuple[ActivityRow, ...]


def _string_fields(
    row: Mapping[str, object], expected: set[str], where: str
) -> dict[str, str]:
    if set(row) != expected or any(
        not isinstance(value, str) for value in row.values()
    ):
        raise ProjectionError(f"Unexpected fields or values in {where}")
    return {key: value for key, value in row.items() if isinstance(value, str)}


def _read(
    tx: _ReadTransaction,
    person_id: str,
    target_id: str,
    expected_realisation_id: str,
    expected_source_state_id: str | None,
) -> RetrievalRows:
    marker_rows = tx.run(
        "CYPHER 25 MATCH (m:CaronProjection) RETURN properties(m) AS marker"
    ).data()
    if len(marker_rows) != 1:
        raise ProjectionError("Expected exactly one projected snapshot marker")
    raw_marker = marker_rows[0].get("marker")
    if not isinstance(raw_marker, Mapping):
        raise ProjectionError("Invalid projection marker properties")
    marker = _string_fields(
        raw_marker,
        {
            "marker",
            "profile_version",
            "ontology_id",
            "ontology_version",
            "realisation_id",
            "coverage_status",
            "coverage_scope",
        }
        | ({"source_state_id"} if "source_state_id" in raw_marker else set()),
        "snapshot marker",
    )
    ontology = career_ontology_v5_0()
    if (
        marker["marker"] != "active"
        or marker["profile_version"] != PROFILE_VERSION
        or (marker["ontology_id"], marker["ontology_version"])
        != (ontology.id, ontology.version)
        or marker["realisation_id"] != expected_realisation_id
        or (
            expected_source_state_id is not None
            and marker.get("source_state_id") != expected_source_state_id
        )
    ):
        raise ProjectionError("Projected snapshot does not match the requested source")
    try:
        coverage = Coverage(
            CoverageStatus(marker["coverage_status"]), marker["coverage_scope"]
        )
    except ValueError as error:
        raise ProjectionError("Projected snapshot has invalid coverage") from error

    endpoints = tx.run(
        "CYPHER 25 MATCH (e:CaronEntity) "
        "WHERE e.id IN [$person_id, $target_id] "
        "RETURN e.id AS id, labels(e) AS labels",
        person_id=person_id,
        target_id=target_id,
    ).data()
    kinds: dict[str, str] = {}
    for row in endpoints:
        entity_id = row.get("id")
        labels = row.get("labels")
        if (
            not isinstance(entity_id, str)
            or not isinstance(labels, list)
            or len(labels) != 2
            or "CaronEntity" not in labels
            or not all(isinstance(label, str) for label in labels)
            or entity_id in kinds
        ):
            raise ProjectionError("Malformed or duplicate requested entity")
        kinds[entity_id] = next(label for label in labels if label != "CaronEntity")
    if kinds.get(person_id) != "Person":
        raise ProjectionError("Requested person is absent or is not a Person")
    target_kind = kinds.get(target_id)
    if target_kind not in _RESOURCE_KINDS:
        raise ProjectionError("Requested target is absent or is not Learnable")

    params = {"person_id": person_id, "target_id": target_id}
    learning = []
    for row in tx.run(_LEARNING, **params).data():
        fields = _string_fields(
            row, {"person_id", "target_id", "context_id", "learns_id"}, "learning match"
        )
        if (fields["person_id"], fields["target_id"]) != (person_id, target_id):
            raise ProjectionError("Learning row changed the requested binding")
        learning.append(LearningRow(**fields))

    activities = []
    for row in tx.run(
        _ACTIVITY, **params, resource_kinds=list(_RESOURCE_KINDS[target_kind])
    ).data():
        fields = _string_fields(
            row,
            {
                "person_id",
                "target_id",
                "activity_id",
                "context_id",
                "resource_kind",
                "performs_id",
                "occurs_in_id",
                "resource_relation_id",
            },
            "activity match",
        )
        if (fields["person_id"], fields["target_id"]) != (
            person_id,
            target_id,
        ) or fields["resource_kind"] not in _RESOURCE_KINDS[target_kind]:
            raise ProjectionError("Activity row changed the requested binding or kind")
        activities.append(ActivityRow(**fields))

    return RetrievalRows(
        marker["realisation_id"],
        marker["ontology_id"],
        marker["ontology_version"],
        marker.get("source_state_id"),
        coverage,
        tuple(sorted(learning, key=lambda row: (row.context_id, row.learns_id))),
        tuple(
            sorted(
                activities,
                key=lambda row: (
                    row.activity_id,
                    row.context_id,
                    row.resource_kind,
                    row.performs_id,
                    row.occurs_in_id,
                    row.resource_relation_id,
                ),
            )
        ),
    )


def retrieve_match_rows(
    driver: _ReadDriver,
    *,
    person_id: str,
    target_id: str,
    expected_realisation_id: str,
    expected_source_state_id: str | None = None,
    database: str = "neo4j",
) -> RetrievalRows:
    """Select raw, support-labelled rows from one matched, committed snapshot."""
    with driver.session(database=database) as session:
        return session.execute_read(
            lambda tx: _read(
                tx,
                person_id,
                target_id,
                expected_realisation_id,
                expected_source_state_id,
            )
        )

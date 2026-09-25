"""Strict inverse of the experimental Neo4j projection profile 0.1."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, Self

from caron.adapters.neo4j_projection import (
    _CONCEPTS,
    _KINDS,
    _QUALIFIED,
    PROFILE_VERSION,
    ProjectionError,
)
from caron.entities import Entity, EntityRef, Property
from caron.ontology import career_ontology_v5_0
from caron.realisations import (
    Coverage,
    CoverageStatus,
    RealisationCandidate,
    ValidatedRealisation,
)
from caron.relations import Qualifier, RelationAssertion
from caron.temporal import TemporalExtent, YearMonth
from caron.validation import Accepted, Rejected, validate_candidate

_METADATA = frozenset(
    {
        "marker",
        "profile_version",
        "ontology_id",
        "ontology_version",
        "realisation_id",
        "coverage_status",
        "coverage_scope",
    }
)
_LINKS = frozenset(
    {
        "CARON_SOURCE",
        "CARON_TARGET",
        "CARON_Q_CONTEXT",
        "CARON_Q_ORGANIZATION",
        "CARON_P_CONTEXT",
    }
)


class _Rows(Protocol):
    def data(self) -> list[dict[str, object]]: ...


class _ReadTransaction(Protocol):
    def run(self, query: str) -> _Rows: ...


class _ReadSession(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(self, *args: object) -> object: ...

    def execute_read(
        self, work: Callable[[_ReadTransaction], ReconstructedSnapshot]
    ) -> ReconstructedSnapshot: ...


class _ReadDriver(Protocol):
    def session(self, *, database: str) -> _ReadSession: ...


@dataclass(frozen=True, slots=True)
class ReconstructedSnapshot:
    candidate: RealisationCandidate
    validated: ValidatedRealisation
    source_state_id: str | None


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise ProjectionError(f"Stored {field} must be a string")
    return value


def _fields(
    value: object, required: set[str], optional: set[str], where: str
) -> dict[str, str]:
    if (
        not isinstance(value, Mapping)
        or set(value) - (required | optional)
        or required - set(value)
    ):
        raise ProjectionError(f"Unexpected or missing fields on {where}")
    return {
        _text(key, where): _text(item, f"{where}.{key}") for key, item in value.items()
    }


def _month(value: str, field: str) -> YearMonth:
    try:
        return YearMonth.parse(value)
    except ValueError as error:
        raise ProjectionError(f"Invalid stored month in {field}: {value!r}") from error


def _entity_properties(
    kind: str,
    values: dict[str, str],
    outgoing: list[tuple[str, str, dict[str, str]]],
    nodes: dict[str, tuple[str, dict[str, str]]],
) -> tuple[Property, ...]:
    entity_id = values["id"]
    properties = [Property("label", values["label"])]
    by_type: dict[str, list[str]] = defaultdict(list)
    for link_type, target, link_properties in outgoing:
        if link_type != "CARON_P_CONTEXT" or link_properties:
            raise ProjectionError(f"Unexpected outgoing link from entity {entity_id!r}")
        if nodes[target][0] != "Context":
            raise ProjectionError(
                f"Proposition context link points outside Context: {entity_id!r}"
            )
        by_type[link_type].append(nodes[target][1]["id"])
    if kind == "Proposition":
        if len(by_type["CARON_P_CONTEXT"]) != 1:
            raise ProjectionError(
                f"Proposition {entity_id!r} needs exactly one Context link"
            )
        properties.extend(
            (
                Property("content", values["content"]),
                Property("context", EntityRef(by_type["CARON_P_CONTEXT"][0])),
            )
        )
    elif by_type:
        raise ProjectionError(
            f"Non-Proposition entity {entity_id!r} has a property link"
        )

    if kind == "Credential" and "awarded_in_month" in values:
        properties.append(
            Property("awarded_in", _month(values["awarded_in_month"], entity_id))
        )
    if kind == "Context" and "temporal_start" in values:
        start = values["temporal_start"]
        end_kind = values["temporal_end_kind"]
        try:
            if end_kind == "unknown" and "temporal_end_month" not in values:
                extent = TemporalExtent.unknown_end(start)
            elif end_kind == "known" and "temporal_end_month" in values:
                extent = TemporalExtent.closed(start, values["temporal_end_month"])
            elif end_kind == "ongoing_as_of" and "temporal_end_month" in values:
                extent = TemporalExtent.ongoing(
                    start, as_of=values["temporal_end_month"]
                )
            else:
                raise ProjectionError(f"Incomplete temporal slots on {entity_id!r}")
        except ValueError as error:
            raise ProjectionError(f"Invalid temporal slots on {entity_id!r}") from error
        properties.append(Property("temporal_extent", extent))
    return tuple(properties)


def _decode_snapshot(
    node_rows: Sequence[Mapping[str, object]], link_rows: Sequence[Mapping[str, object]]
) -> ReconstructedSnapshot:
    """Decode raw storage rows; reject unexpected records before ontology validation."""
    nodes: dict[str, tuple[str, dict[str, str]]] = {}
    markers: list[dict[str, str]] = []
    for row in node_rows:
        storage_id = _text(row.get("storage_id"), "node storage ID")
        labels = row.get("labels")
        if not isinstance(labels, list) or any(
            not isinstance(label, str) for label in labels
        ):
            raise ProjectionError("Invalid node labels")
        label_set = set(labels)
        if len(label_set) != len(labels) or storage_id in nodes:
            raise ProjectionError("Duplicate node identity or label")
        if label_set == {"CaronProjection"}:
            values = _fields(
                row.get("properties"),
                set(_METADATA),
                {"source_state_id"},
                "projection marker",
            )
            markers.append(values)
            nodes[storage_id] = ("CaronProjection", values)
        elif label_set == {"CaronRelation"}:
            values = _fields(
                row.get("properties"), {"id", "kind"}, {"q_role"}, "relation node"
            )
            if values["kind"] not in _QUALIFIED:
                raise ProjectionError(
                    f"Relation node has an unqualified kind: {values['kind']!r}"
                )
            nodes[storage_id] = ("CaronRelation", values)
        elif len(label_set) == 2 and "CaronEntity" in label_set:
            kind = next(iter(label_set - {"CaronEntity"}))
            if kind not in _CONCEPTS:
                raise ProjectionError(f"Unknown entity concept label: {kind!r}")
            required = {"id", "label"} | (
                {"content"} if kind == "Proposition" else set()
            )
            optional = ({"awarded_in_month"} if kind == "Credential" else set()) | (
                {"temporal_start", "temporal_end_kind", "temporal_end_month"}
                if kind == "Context"
                else set()
            )
            values = _fields(
                row.get("properties"), required, optional, f"{kind} entity"
            )
            if (
                kind == "Context"
                and ({"temporal_start", "temporal_end_kind"} & values.keys())
                and not {"temporal_start", "temporal_end_kind"} <= values.keys()
            ):
                raise ProjectionError(f"Incomplete temporal slots on {values['id']!r}")
            if (
                kind == "Context"
                and "temporal_start" not in values
                and "temporal_end_month" in values
            ):
                raise ProjectionError(f"Orphan temporal end on {values['id']!r}")
            nodes[storage_id] = (kind, values)
        else:
            raise ProjectionError(f"Unexpected storage labels: {sorted(label_set)!r}")

    if len(markers) != 1:
        raise ProjectionError("Expected exactly one projection marker")
    marker = markers[0]
    ontology = career_ontology_v5_0()
    if (
        marker["marker"],
        marker["profile_version"],
        marker["ontology_id"],
        marker["ontology_version"],
    ) != ("active", PROFILE_VERSION, ontology.id, ontology.version):
        raise ProjectionError("Projection marker has a different profile or ontology")

    outgoing: dict[str, list[tuple[str, str, dict[str, str]]]] = defaultdict(list)
    direct: list[RelationAssertion] = []
    for row in link_rows:
        source = _text(row.get("source"), "link source")
        target = _text(row.get("target"), "link target")
        link_type = _text(row.get("type"), "link type")
        if source not in nodes or target not in nodes:
            raise ProjectionError("Link endpoint is absent from snapshot")
        if link_type == "CARON_DIRECT":
            values = _fields(
                row.get("properties"), {"id", "kind"}, {"q_role"}, "direct assertion"
            )
            kind = values["kind"]
            if kind not in _KINDS or kind in _QUALIFIED:
                raise ProjectionError(f"Unexpected direct assertion kind: {kind!r}")
            if ("q_role" in values) != (kind == "organization_association"):
                raise ProjectionError(f"Invalid scalar qualifier on {values['id']!r}")
            if nodes[source][0] not in _CONCEPTS or nodes[target][0] not in _CONCEPTS:
                raise ProjectionError("Direct assertion must link two entities")
            direct.append(
                RelationAssertion(
                    values["id"],
                    kind,
                    EntityRef(nodes[source][1]["id"]),
                    EntityRef(nodes[target][1]["id"]),
                    (Qualifier("role", values["q_role"]),)
                    if "q_role" in values
                    else (),
                )
            )
        elif link_type in _LINKS:
            values = _fields(row.get("properties"), set(), set(), "encoding link")
            if nodes[target][0] not in _CONCEPTS:
                raise ProjectionError("Encoding link must target an entity")
            outgoing[source].append((link_type, target, values))
        else:
            raise ProjectionError(f"Unexpected relationship type {link_type!r}")

    entities: list[Entity] = []
    qualified: list[RelationAssertion] = []
    for storage_id, (kind, values) in nodes.items():
        links = outgoing[storage_id]
        if kind in _CONCEPTS:
            entities.append(
                Entity(
                    values["id"], kind, _entity_properties(kind, values, links, nodes)
                )
            )
        elif kind == "CaronRelation":
            by_type: dict[str, list[str]] = defaultdict(list)
            for link_type, target, link_properties in links:
                if link_type not in _LINKS - {"CARON_P_CONTEXT"} or link_properties:
                    raise ProjectionError(
                        f"Unexpected link on relation {values['id']!r}"
                    )
                target_kind = nodes[target][0]
                if link_type == "CARON_Q_CONTEXT" and target_kind != "Context":
                    raise ProjectionError(
                        "Context qualifier points to the wrong concept"
                    )
                if (
                    link_type == "CARON_Q_ORGANIZATION"
                    and target_kind != "Organization"
                ):
                    raise ProjectionError(
                        "Organization qualifier points to the wrong concept"
                    )
                by_type[link_type].append(nodes[target][1]["id"])
            relation_kind = values["kind"]
            expected = {"CARON_SOURCE", "CARON_TARGET"}
            if relation_kind in {"collective_membership", "exposed_to", "learns"}:
                expected.add("CARON_Q_CONTEXT")
            if relation_kind == "participates_in" and "CARON_Q_ORGANIZATION" in by_type:
                expected.add("CARON_Q_ORGANIZATION")
            if set(by_type) != expected or any(
                len(by_type[key]) != 1 for key in expected
            ):
                raise ProjectionError(
                    f"Missing, repeated, or unexpected links on {values['id']!r}"
                )
            if ("q_role" in values) != (
                relation_kind in {"participates_in", "collective_membership"}
            ):
                raise ProjectionError(f"Invalid scalar qualifier on {values['id']!r}")
            qualifiers = (
                [Qualifier("role", values["q_role"])] if "q_role" in values else []
            )
            for link_type, name in (
                ("CARON_Q_CONTEXT", "context"),
                ("CARON_Q_ORGANIZATION", "organization"),
            ):
                if link_type in by_type:
                    qualifiers.append(Qualifier(name, EntityRef(by_type[link_type][0])))
            qualified.append(
                RelationAssertion(
                    values["id"],
                    relation_kind,
                    EntityRef(by_type["CARON_SOURCE"][0]),
                    EntityRef(by_type["CARON_TARGET"][0]),
                    tuple(qualifiers),
                )
            )
        elif links:
            raise ProjectionError("Projection marker has outgoing links")

    all_ids = [item.id for item in entities] + [
        item.id for item in (*direct, *qualified)
    ]
    if len(all_ids) != len(set(all_ids)):
        raise ProjectionError("Duplicate domain ID across projected records")
    try:
        coverage = Coverage(
            CoverageStatus(marker["coverage_status"]), marker["coverage_scope"]
        )
    except ValueError as error:
        raise ProjectionError("Unknown stored coverage status") from error
    candidate = RealisationCandidate(
        marker["realisation_id"],
        ontology.id,
        ontology.version,
        tuple(sorted(entities, key=lambda item: item.id)),
        tuple(sorted((*direct, *qualified), key=lambda item: item.id)),
        coverage,
    )
    checked = validate_candidate(ontology, candidate)
    if isinstance(checked, Rejected):
        details = ", ".join(
            f"{item.code} ({item.record_id})" for item in checked.diagnostics
        )
        raise ProjectionError(f"Stored snapshot fails ontology validation: {details}")
    assert isinstance(checked, Accepted)
    return ReconstructedSnapshot(
        candidate, checked.realisation, marker.get("source_state_id")
    )


def _extract(tx: _ReadTransaction) -> ReconstructedSnapshot:
    nodes = tx.run(
        "CYPHER 25 MATCH (n) RETURN elementId(n) AS storage_id, "
        "labels(n) AS labels, properties(n) AS properties"
    ).data()
    links = tx.run(
        "CYPHER 25 MATCH (a)-[r]->(b) RETURN elementId(a) AS source, "
        "elementId(b) AS target, type(r) AS type, properties(r) AS properties"
    ).data()
    return _decode_snapshot(nodes, links)


def extract_snapshot(
    driver: _ReadDriver, *, database: str = "neo4j"
) -> ReconstructedSnapshot:
    """Read one consistent snapshot, decode profile 0.1, and revalidate ontology 5.0."""
    with driver.session(database=database) as session:
        return session.execute_read(_extract)

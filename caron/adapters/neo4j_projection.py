"""Experimental, whole-snapshot Neo4j projection for Career Ontology 5.0.

The ontology validator is the only admission boundary. Storage nodes and
encoding links created here are not new career entities or assertions.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, Self

from caron.entities import Entity, EntityRef
from caron.ontology import career_ontology_v5_0
from caron.realisations import ValidatedRealisation
from caron.relations import RelationAssertion
from caron.temporal import KnownEnd, OngoingAsOf, TemporalExtent, UnknownEnd, YearMonth

PROFILE_VERSION = "0.1"
_QUALIFIED = frozenset(
    {"participates_in", "collective_membership", "exposed_to", "learns"}
)
_CONCEPTS = frozenset(concept.id for concept in career_ontology_v5_0().concepts)
_KINDS = frozenset(relation.kind for relation in career_ontology_v5_0().relations)
_UNIQUENESS_CONSTRAINTS = (
    "CREATE CONSTRAINT caron_entity_id_unique IF NOT EXISTS "
    "FOR (n:CaronEntity) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT caron_relation_id_unique IF NOT EXISTS "
    "FOR (n:CaronRelation) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT caron_direct_id_unique IF NOT EXISTS "
    "FOR ()-[r:CARON_DIRECT]-() REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT caron_projection_marker_unique IF NOT EXISTS "
    "FOR (n:CaronProjection) REQUIRE n.marker IS UNIQUE",
)


class ProjectionError(ValueError):
    """The source, current database, or written projection violates this profile."""


class _Result(Protocol):
    def single(self) -> Mapping[str, object] | None: ...

    def consume(self) -> object: ...


class _Transaction(Protocol):
    def run(self, query: str, **parameters: object) -> _Result: ...


class _Session(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(self, *args: object) -> object: ...

    def execute_write(
        self, work: Callable[[_Transaction], ProjectionCounts]
    ) -> ProjectionCounts: ...

    def run(self, query: str) -> _Result: ...


class _Driver(Protocol):
    def session(self, *, database: str) -> _Session: ...


@dataclass(frozen=True, slots=True)
class ProjectionCounts:
    nodes: int
    relationships: int


@dataclass(frozen=True, slots=True)
class _EntityRow:
    kind: str
    properties: dict[str, str]
    context_id: str | None


@dataclass(frozen=True, slots=True)
class _RelationRow:
    properties: dict[str, str]
    source: str
    target: str
    context_id: str | None = None
    organization_id: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectionPlan:
    """Prepared, profile-specific rows; no database or driver objects."""

    entities: tuple[_EntityRow, ...]
    direct: tuple[_RelationRow, ...]
    qualified: tuple[_RelationRow, ...]
    metadata: dict[str, str]

    @property
    def counts(self) -> ProjectionCounts:
        qualifier_links = sum(
            (row.context_id is not None) + (row.organization_id is not None)
            for row in self.qualified
        )
        property_links = sum(row.context_id is not None for row in self.entities)
        return ProjectionCounts(
            nodes=len(self.entities) + len(self.qualified) + 1,
            relationships=(
                len(self.direct)
                + 2 * len(self.qualified)
                + qualifier_links
                + property_links
            ),
        )


def _entity_row(entity: Entity) -> _EntityRow:
    if entity.kind not in _CONCEPTS:
        raise ProjectionError(f"Unknown concept {entity.kind!r}")
    properties = {"id": entity.id}
    context_id: str | None = None
    for prop in entity.properties:
        value = prop.value
        if prop.name in {"label", "content"} and isinstance(value, str):
            properties[prop.name] = value
        elif (
            prop.name == "context"
            and entity.kind == "Proposition"
            and isinstance(value, EntityRef)
        ):
            context_id = value.entity_id
        elif (
            prop.name == "awarded_in"
            and entity.kind == "Credential"
            and isinstance(value, YearMonth)
        ):
            properties["awarded_in_month"] = str(value)
        elif (
            prop.name == "temporal_extent"
            and entity.kind == "Context"
            and isinstance(value, TemporalExtent)
        ):
            properties["temporal_start"] = str(value.start)
            match value.end:
                case KnownEnd(month):
                    properties["temporal_end_kind"] = "known"
                    properties["temporal_end_month"] = str(month)
                case UnknownEnd():
                    properties["temporal_end_kind"] = "unknown"
                case OngoingAsOf(month):
                    properties["temporal_end_kind"] = "ongoing_as_of"
                    properties["temporal_end_month"] = str(month)
        else:
            raise ProjectionError(f"Unmapped property {entity.kind}.{prop.name}")
    return _EntityRow(entity.kind, properties, context_id)


def _relation_row(relation: RelationAssertion) -> _RelationRow:
    if relation.kind not in _KINDS:
        raise ProjectionError(f"Unknown relation kind {relation.kind!r}")
    properties = {"id": relation.id, "kind": relation.kind}
    context_id: str | None = None
    organization_id: str | None = None
    for qualifier in relation.qualifiers:
        if (
            qualifier.name == "role"
            and relation.kind
            in {"participates_in", "collective_membership", "organization_association"}
            and isinstance(qualifier.value, str)
        ):
            properties["q_role"] = qualifier.value
        elif (
            qualifier.name == "context"
            and relation.kind in {"collective_membership", "exposed_to", "learns"}
            and isinstance(qualifier.value, EntityRef)
        ):
            context_id = qualifier.value.entity_id
        elif (
            qualifier.name == "organization"
            and relation.kind == "participates_in"
            and isinstance(qualifier.value, EntityRef)
        ):
            organization_id = qualifier.value.entity_id
        else:
            raise ProjectionError(
                f"Unmapped qualifier {relation.kind}.{qualifier.name}"
            )
    return _RelationRow(
        properties,
        relation.source.entity_id,
        relation.target.entity_id,
        context_id,
        organization_id,
    )


def prepare_snapshot(
    realisation: ValidatedRealisation, *, source_state_id: str | None = None
) -> ProjectionPlan:
    """Fail closed for any ontology other than the exact accepted 5.0 schema."""
    if not isinstance(realisation, ValidatedRealisation):
        raise TypeError("Projection requires a ValidatedRealisation")
    if realisation.ontology != career_ontology_v5_0():
        raise ProjectionError(
            "Projection profile 0.1 requires exact Career Ontology 5.0"
        )
    metadata = {
        "marker": "active",
        "profile_version": PROFILE_VERSION,
        "ontology_id": realisation.ontology.id,
        "ontology_version": realisation.ontology.version,
        "realisation_id": realisation.id,
        "coverage_status": realisation.coverage.status.value,
        "coverage_scope": realisation.coverage.scope,
    }
    if source_state_id is not None:
        metadata["source_state_id"] = source_state_id
    entities = tuple(_entity_row(item) for item in realisation.entities)
    rows = tuple(_relation_row(item) for item in realisation.relations)
    return ProjectionPlan(
        entities,
        tuple(row for row in rows if row.properties["kind"] not in _QUALIFIED),
        tuple(row for row in rows if row.properties["kind"] in _QUALIFIED),
        metadata,
    )


def _one(tx: _Transaction, query: str, **parameters: object) -> Mapping[str, object]:
    result = tx.run(query, **parameters).single()
    if result is None:
        raise ProjectionError("Neo4j returned no summary for a projection operation")
    return result


def _insert(tx: _Transaction, query: str, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        return
    result = _one(tx, query, rows=rows)
    if result["created"] != len(rows):
        raise ProjectionError("A projection reference did not resolve exactly once")


def _write_snapshot(tx: _Transaction, plan: ProjectionPlan) -> ProjectionCounts:
    existing = _one(
        tx,
        "MATCH (n) RETURN count(n) AS nodes, "
        "count(CASE WHEN n:CaronProjection AND n.marker = 'active' "
        "THEN 1 END) AS markers, "
        "count(CASE WHEN n:CaronProjection OR n:CaronEntity OR n:CaronRelation "
        "THEN 1 END) AS owned",
    )
    if existing["nodes"] != 0:
        if existing["markers"] != 1 or existing["owned"] != existing["nodes"]:
            raise ProjectionError("Database is not an isolated Caron projection")
        marker = _one(
            tx,
            "MATCH (m:CaronProjection {marker: 'active'}) "
            "RETURN m.profile_version AS profile, m.ontology_id AS ontology_id, "
            "m.ontology_version AS ontology_version",
        )
        if (
            marker["profile"] != PROFILE_VERSION
            or marker["ontology_id"] != plan.metadata["ontology_id"]
            or marker["ontology_version"] != plan.metadata["ontology_version"]
        ):
            raise ProjectionError(
                "Existing projection has a different profile or ontology"
            )
        _one(tx, "MATCH (n) DETACH DELETE n RETURN count(n) AS deleted")

    for kind in sorted(_CONCEPTS):
        rows = [row.properties for row in plan.entities if row.kind == kind]
        # Only closed ontology labels enter the query text. Values remain parameters.
        _insert(
            tx,
            f"UNWIND $rows AS row CREATE (e:CaronEntity:{kind}) "
            "SET e = row RETURN count(e) AS created",
            rows,
        )
    _insert(
        tx,
        "UNWIND $rows AS row "
        "MATCH (s:CaronEntity {id: row.source}) "
        "MATCH (t:CaronEntity {id: row.target}) "
        "CREATE (s)-[r:CARON_DIRECT]->(t) SET r = row.properties "
        "RETURN count(r) AS created",
        [
            {"source": row.source, "target": row.target, "properties": row.properties}
            for row in plan.direct
        ],
    )
    _insert(
        tx,
        "UNWIND $rows AS row CREATE (r:CaronRelation) "
        "SET r = row RETURN count(r) AS created",
        [row.properties for row in plan.qualified],
    )
    _insert(
        tx,
        "UNWIND $rows AS row "
        "MATCH (r:CaronRelation {id: row.id}) "
        "MATCH (s:CaronEntity {id: row.source}) "
        "MATCH (t:CaronEntity {id: row.target}) "
        "CREATE (r)-[:CARON_SOURCE]->(s), (r)-[:CARON_TARGET]->(t) "
        "RETURN count(r) AS created",
        [
            {"id": row.properties["id"], "source": row.source, "target": row.target}
            for row in plan.qualified
        ],
    )
    for field, link_type in (
        ("context_id", "CARON_Q_CONTEXT"),
        ("organization_id", "CARON_Q_ORGANIZATION"),
    ):
        rows = [
            {"id": row.properties["id"], "ref": ref}
            for row in plan.qualified
            if (ref := getattr(row, field)) is not None
        ]
        _insert(
            tx,
            "UNWIND $rows AS row "
            "MATCH (r:CaronRelation {id: row.id}) "
            "MATCH (q:CaronEntity {id: row.ref}) "
            f"CREATE (r)-[link:{link_type}]->(q) "
            "RETURN count(link) AS created",
            rows,
        )
    _insert(
        tx,
        "UNWIND $rows AS row "
        "MATCH (p:CaronEntity:Proposition {id: row.id}) "
        "MATCH (c:CaronEntity:Context {id: row.ref}) "
        "CREATE (p)-[link:CARON_P_CONTEXT]->(c) "
        "RETURN count(link) AS created",
        [
            {"id": row.properties["id"], "ref": row.context_id}
            for row in plan.entities
            if row.context_id is not None
        ],
    )
    _one(
        tx,
        "CREATE (m:CaronProjection) SET m = $metadata RETURN m.marker AS marker",
        metadata=plan.metadata,
    )
    nodes = _one(tx, "MATCH (n) RETURN count(n) AS count")["count"]
    links = _one(tx, "MATCH ()-[r]->() RETURN count(r) AS count")["count"]
    if nodes != plan.counts.nodes or links != plan.counts.relationships:
        raise ProjectionError(
            "Written snapshot does not have the expected physical counts"
        )
    return plan.counts


def project_snapshot(
    driver: _Driver,
    realisation: ValidatedRealisation,
    *,
    database: str = "neo4j",
    source_state_id: str | None = None,
) -> ProjectionCounts:
    """Replace one isolated snapshot in one managed write transaction.

    A failure rolls back the replacement; a previous committed snapshot remains.
    The caller owns the driver and the isolated test database.
    """
    plan = prepare_snapshot(realisation, source_state_id=source_state_id)
    with driver.session(database=database) as session:
        return session.execute_write(lambda tx: _write_snapshot(tx, plan))


def install_projection_constraints(driver: _Driver, *, database: str = "neo4j") -> None:
    """Install the four Community uniqueness guards before loading snapshots.

    Schema setup is separate from the atomic data replacement. It does not
    guarantee existence, endpoint kinds, qualifier requirements, or global
    assertion-ID uniqueness across the two physical assertion shapes.
    """
    with driver.session(database=database) as session:
        for statement in _UNIQUENESS_CONSTRAINTS:
            session.run(statement).consume()

"""Inverse-profile probes with distinct source and stored representations."""

from pathlib import Path
from typing import TypedDict

import pytest

from caron import (
    Accepted,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    RelationAssertion,
    TemporalExtent,
    ValidatedRealisation,
    career_ontology_v5_0,
    validate_candidate,
)
from caron.adapters.neo4j_projection import (
    ProjectionError,
    ProjectionPlan,
    prepare_snapshot,
)
from caron.adapters.neo4j_reconstruction import _decode_snapshot
from caron.yaml_reader import LoadAccepted, load_realisation_yaml

FIXTURE = Path(__file__).parents[1] / "fixtures/geant4-learning-and-activity-v0.1.yaml"
CAREER = Path(__file__).parents[2] / "caron/data/career-across-contexts-v0.1.yaml"


class _NodeRow(TypedDict):
    storage_id: str
    labels: list[str]
    properties: dict[str, str]


class _LinkRow(TypedDict):
    source: str
    target: str
    type: str
    properties: dict[str, str]


def _load(path: Path) -> LoadAccepted:
    loaded = load_realisation_yaml(path, ontology=career_ontology_v5_0())
    assert isinstance(loaded, LoadAccepted)
    return loaded


def _storage_rows(
    plan: ProjectionPlan,
) -> tuple[list[_NodeRow], list[_LinkRow]]:
    """Independent storage rows for decoder tests; the live gate reads real Cypher."""
    nodes: list[_NodeRow] = []
    links: list[_LinkRow] = []
    storage_ids: dict[str, str] = {}

    def node(labels: list[str], properties: dict[str, str]) -> str:
        storage_id = f"storage:{len(nodes)}"
        nodes.append(
            {"storage_id": storage_id, "labels": labels, "properties": properties}
        )
        return storage_id

    def link(
        source: str, target: str, kind: str, properties: dict[str, str] | None = None
    ) -> None:
        links.append(
            {
                "source": source,
                "target": target,
                "type": kind,
                "properties": properties if properties is not None else {},
            }
        )

    for entity in plan.entities:
        storage_ids[entity.properties["id"]] = node(
            ["CaronEntity", entity.kind], dict(entity.properties)
        )
    for relation in plan.direct:
        link(
            storage_ids[relation.source],
            storage_ids[relation.target],
            "CARON_DIRECT",
            dict(relation.properties),
        )
    for relation in plan.qualified:
        source = node(["CaronRelation"], dict(relation.properties))
        link(source, storage_ids[relation.source], "CARON_SOURCE")
        link(source, storage_ids[relation.target], "CARON_TARGET")
        if relation.context_id is not None:
            link(source, storage_ids[relation.context_id], "CARON_Q_CONTEXT")
        if relation.organization_id is not None:
            link(source, storage_ids[relation.organization_id], "CARON_Q_ORGANIZATION")
    for entity in plan.entities:
        if entity.context_id is not None:
            link(
                storage_ids[entity.properties["id"]],
                storage_ids[entity.context_id],
                "CARON_P_CONTEXT",
            )
    node(["CaronProjection"], dict(plan.metadata))
    return nodes, links


def _semantic_records(
    realisation: ValidatedRealisation,
) -> tuple[dict[str, object], dict[str, object]]:
    entities: dict[str, object] = {
        item.id: (item.kind, dict((p.name, p.value) for p in item.properties))
        for item in realisation.entities
    }
    relations: dict[str, object] = {
        item.id: (
            item.kind,
            item.source,
            item.target,
            dict((q.name, q.value) for q in item.qualifiers),
        )
        for item in realisation.relations
    }
    return entities, relations


@pytest.mark.parametrize("path", [FIXTURE, CAREER])
def test_inverse_profile_reconstructs_validated_records_and_metadata(
    path: Path,
) -> None:
    loaded = _load(path)
    plan = prepare_snapshot(loaded.realisation, source_state_id=loaded.source_state_id)
    nodes, links = _storage_rows(plan)
    reconstructed = _decode_snapshot(nodes, links)
    assert reconstructed.source_state_id == loaded.source_state_id
    assert reconstructed.validated.id == loaded.realisation.id
    assert reconstructed.validated.coverage == loaded.realisation.coverage
    assert _semantic_records(reconstructed.validated) == _semantic_records(
        loaded.realisation
    )


def test_unknown_and_ongoing_end_are_distinct_from_absent_extent() -> None:
    original = _load(FIXTURE).realisation
    candidate = RealisationCandidate(
        original.id,
        original.ontology.id,
        original.ontology.version,
        (
            *original.entities,
            Entity(
                "context:unknown",
                "Context",
                (
                    Property("label", "Unknown"),
                    Property("temporal_extent", TemporalExtent.unknown_end("2023-01")),
                ),
            ),
            Entity(
                "context:ongoing",
                "Context",
                (
                    Property("label", "Ongoing"),
                    Property(
                        "temporal_extent",
                        TemporalExtent.ongoing("2023-01", as_of="2026-09"),
                    ),
                ),
            ),
            Entity("context:undated", "Context", (Property("label", "Undated"),)),
        ),
        original.relations,
        original.coverage,
    )
    checked = validate_candidate(original.ontology, candidate)
    assert isinstance(checked, Accepted)
    nodes, links = _storage_rows(prepare_snapshot(checked.realisation))
    extracted = _decode_snapshot(nodes, links)
    assert _semantic_records(extracted.validated) == _semantic_records(
        checked.realisation
    )


def test_collective_membership_and_exposure_preserve_context_links() -> None:
    original = _load(FIXTURE).realisation
    candidate = RealisationCandidate(
        original.id,
        original.ontology.id,
        original.ontology.version,
        (
            *original.entities,
            Entity("collective:team", "Collective", (Property("label", "Team"),)),
            Entity("method:analysis", "Method", (Property("label", "Analysis"),)),
        ),
        (
            *original.relations,
            RelationAssertion(
                "relation:membership",
                "collective_membership",
                EntityRef("person:matteo"),
                EntityRef("collective:team"),
                (
                    Qualifier("context", EntityRef("context:msc")),
                    Qualifier("role", "member"),
                ),
            ),
            RelationAssertion(
                "relation:exposure",
                "exposed_to",
                EntityRef("person:matteo"),
                EntityRef("method:analysis"),
                (Qualifier("context", EntityRef("context:msc")),),
            ),
        ),
        original.coverage,
    )
    checked = validate_candidate(original.ontology, candidate)
    assert isinstance(checked, Accepted), checked
    nodes, links = _storage_rows(prepare_snapshot(checked.realisation))
    restored = _decode_snapshot(nodes, links)
    assert _semantic_records(restored.validated) == _semantic_records(
        checked.realisation
    )


def test_missing_or_repeated_relation_endpoint_and_cross_shape_id_are_rejected() -> (
    None
):
    nodes, links = _storage_rows(prepare_snapshot(_load(FIXTURE).realisation))
    source_links = [link for link in links if link["type"] == "CARON_SOURCE"]
    assert len(source_links) == 1
    with pytest.raises(ProjectionError, match="Missing, repeated, or unexpected links"):
        _decode_snapshot(nodes, [link for link in links if link is not source_links[0]])
    with pytest.raises(ProjectionError, match="Missing, repeated, or unexpected links"):
        _decode_snapshot(nodes, [*links, dict(source_links[0])])
    direct = next(link for link in links if link["type"] == "CARON_DIRECT")
    corrupted = [dict(link) for link in links]
    direct_copy = next(link for link in corrupted if link["type"] == "CARON_DIRECT")
    direct_copy["properties"] = {**direct["properties"], "id": "relation:learns-geant4"}
    with pytest.raises(ProjectionError, match="Duplicate domain ID"):
        _decode_snapshot(nodes, corrupted)


def test_invalid_storage_slots_and_ontology_violation_are_rejected() -> None:
    nodes, links = _storage_rows(prepare_snapshot(_load(FIXTURE).realisation))
    context = next(
        row
        for row in nodes
        if row["labels"] == ["CaronEntity", "Context"]
        and "temporal_start" in row["properties"]
    )
    corrupt_nodes = [dict(row) for row in nodes]
    corrupted = next(
        row for row in corrupt_nodes if row["storage_id"] == context["storage_id"]
    )
    corrupted["properties"] = {
        "id": "context:phd",
        "label": "PhD",
        "temporal_end_kind": "known",
    }
    with pytest.raises(ProjectionError, match="Incomplete temporal slots"):
        _decode_snapshot(corrupt_nodes, links)
    changed_links = [link.copy() for link in links]
    performs = next(
        link
        for link in changed_links
        if link["type"] == "CARON_DIRECT" and link["properties"]["kind"] == "performs"
    )
    performs["target"] = context["storage_id"]
    with pytest.raises(ProjectionError, match="fails ontology validation"):
        _decode_snapshot(nodes, changed_links)

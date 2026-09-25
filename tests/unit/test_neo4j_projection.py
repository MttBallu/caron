"""The projection plan is checked against pinned, accepted source fixtures."""

from pathlib import Path

import pytest

from caron import Entity, Property, TemporalExtent, career_ontology_v5_0
from caron.adapters.neo4j_projection import (
    ProjectionError,
    _entity_row,
    prepare_snapshot,
    project_snapshot,
)
from caron.yaml_reader import LoadAccepted, load_realisation_yaml

GEANT4 = Path(__file__).parents[1] / "fixtures/geant4-learning-and-activity-v0.1.yaml"
CAREER = Path(__file__).parents[2] / "caron/data/career-across-contexts-v0.1.yaml"


def _load(path: Path) -> LoadAccepted:
    result = load_realisation_yaml(path, ontology=career_ontology_v5_0())
    assert isinstance(result, LoadAccepted), result
    return result


def test_geant4_profile_preserves_ids_and_learning_qualifier() -> None:
    loaded = _load(GEANT4)
    plan = prepare_snapshot(loaded.realisation, source_state_id=loaded.source_state_id)
    assert (plan.counts.nodes, plan.counts.relationships) == (7, 6)
    assert len(plan.entities) == 5 and len(plan.direct) == 3
    assert plan.qualified[0].properties == {
        "id": "relation:learns-geant4",
        "kind": "learns",
    }
    assert plan.qualified[0].context_id == "context:msc"
    assert plan.metadata["source_state_id"] == loaded.source_state_id
    assert {row.properties["id"] for row in plan.entities} == {
        entity.id for entity in loaded.realisation.entities
    }
    assert {row.properties["id"] for row in (*plan.direct, *plan.qualified)} == {
        relation.id for relation in loaded.realisation.relations
    }


def test_whole_career_profile_preserves_optional_refs_and_values() -> None:
    plan = prepare_snapshot(_load(CAREER).realisation)
    assert (plan.counts.nodes, plan.counts.relationships) == (77, 113)
    participates = [
        row for row in plan.qualified if row.properties["kind"] == "participates_in"
    ]
    assert len(participates) == 6
    assert sum(row.organization_id is not None for row in participates) == 5
    assert sum(row.context_id is not None for row in plan.entities) == 3
    assert sum("temporal_start" in row.properties for row in plan.entities) == 8
    assert sum("awarded_in_month" in row.properties for row in plan.entities) == 1
    assert "source_state_id" not in plan.metadata


def test_temporal_alternatives_keep_explicit_end_kind() -> None:
    base = (Property("label", "Test context"),)
    unknown = _entity_row(
        Entity(
            "c1",
            "Context",
            (*base, Property("temporal_extent", TemporalExtent.unknown_end("2020-01"))),
        )
    )
    ongoing = _entity_row(
        Entity(
            "c2",
            "Context",
            (
                *base,
                Property(
                    "temporal_extent",
                    TemporalExtent.ongoing("2020-01", as_of="2026-09"),
                ),
            ),
        )
    )
    assert unknown.properties["temporal_end_kind"] == "unknown"
    assert "temporal_end_month" not in unknown.properties
    assert ongoing.properties["temporal_end_kind"] == "ongoing_as_of"
    assert ongoing.properties["temporal_end_month"] == "2026-09"


class _FakeResult:
    def __init__(self, row: dict[str, object]):
        self.row = row

    def single(self) -> dict[str, object]:
        return self.row


class _FakeTransaction:
    def __init__(self, driver: "_FakeDriver") -> None:
        self.driver = driver

    def run(self, query: str, **parameters: object) -> _FakeResult:
        self.driver.queries.append(query)
        if "AS nodes," in query:
            return _FakeResult(
                {
                    "nodes": self.driver.saved_nodes,
                    "markers": int(self.driver.saved_nodes > 0),
                    "owned": self.driver.saved_nodes,
                }
            )
        if "AS profile," in query:
            return _FakeResult(
                {
                    "profile": "0.1",
                    "ontology_id": "caron.career-model",
                    "ontology_version": "5.0",
                }
            )
        if "AS deleted" in query:
            return _FakeResult({"deleted": self.driver.saved_nodes})
        if "AS created" in query:
            rows = parameters["rows"]
            assert isinstance(rows, list)
            self.driver.staged_rows.extend(rows)
            created = (
                0 if self.driver.fail_on and self.driver.fail_on in query else len(rows)
            )
            return _FakeResult({"created": created})
        if "AS marker" in query:
            return _FakeResult({"marker": "active"})
        if "MATCH (n) RETURN count(n) AS count" in query:
            return _FakeResult({"count": self.driver.expected_nodes})
        if "MATCH ()-[r]->() RETURN count(r) AS count" in query:
            return _FakeResult({"count": self.driver.expected_links})
        raise AssertionError(f"Unexpected query: {query}")


class _FakeSession:
    def __init__(self, driver: "_FakeDriver") -> None:
        self.driver = driver

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def execute_write(self, work: object) -> object:
        assert callable(work)
        self.driver.staged_rows = []
        result = work(_FakeTransaction(self.driver))
        self.driver.commits += 1
        self.driver.saved_nodes = self.driver.expected_nodes
        return result


class _FakeDriver:
    def __init__(self, nodes: int, links: int) -> None:
        self.expected_nodes = nodes
        self.expected_links = links
        self.saved_nodes = 0
        self.commits = 0
        self.fail_on: str | None = None
        self.staged_rows: list[object] = []
        self.queries: list[str] = []

    def session(self, *, database: str) -> _FakeSession:
        assert database == "neo4j"
        return _FakeSession(self)


def test_failed_replacement_keeps_previous_snapshot() -> None:
    graph = _load(GEANT4).realisation
    counts = prepare_snapshot(graph).counts
    driver = _FakeDriver(counts.nodes, counts.relationships)
    assert project_snapshot(driver, graph) == counts  # type: ignore[arg-type]
    assert driver.commits == 1 and driver.saved_nodes == 7
    assert driver.queries and all(
        query.startswith("CYPHER 25 ") for query in driver.queries
    )
    assert project_snapshot(driver, graph) == counts  # type: ignore[arg-type]
    assert any("DETACH DELETE" in query for query in driver.queries)
    driver.fail_on = "CARON_Q_CONTEXT"
    with pytest.raises(ProjectionError, match="reference did not resolve"):
        project_snapshot(driver, graph)  # type: ignore[arg-type]
    assert driver.commits == 2 and driver.saved_nodes == 7

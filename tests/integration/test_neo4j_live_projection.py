"""Run with a dedicated Neo4j Community 2026.09.0 test database.

Set CARON_NEO4J_EXPERIMENT_URI, USER, PASSWORD, and optionally DATABASE.
Set CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 to opt in to replacement of an
existing Caron projection in that database.
"""

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from caron import career_ontology_v5_0
from caron.adapters.neo4j_projection import (
    _write_snapshot,
    install_projection_constraints,
    prepare_snapshot,
    project_snapshot,
)
from caron.adapters.neo4j_reconstruction import extract_snapshot
from caron.yaml_reader import LoadAccepted, load_realisation_yaml

ROOT = Path(__file__).parents[2]
GEANT4 = ROOT / "tests/fixtures/geant4-learning-and-activity-v0.1.yaml"
CAREER = ROOT / "caron/data/career-across-contexts-v0.1.yaml"


@pytest.fixture
def connection() -> Iterator[tuple[Any, str]]:
    uri = os.environ.get("CARON_NEO4J_EXPERIMENT_URI")
    if uri is None:
        pytest.skip("Set CARON_NEO4J_EXPERIMENT_URI for the live projection gate")
    if os.environ.get("CARON_NEO4J_EXPERIMENT_ALLOW_WRITE") != "1":
        pytest.skip("Set CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 for snapshot replacement")
    neo4j = pytest.importorskip("neo4j")
    database = os.environ.get("CARON_NEO4J_EXPERIMENT_DATABASE", "neo4j")
    with neo4j.GraphDatabase.driver(
        uri,
        auth=(
            os.environ["CARON_NEO4J_EXPERIMENT_USER"],
            os.environ["CARON_NEO4J_EXPERIMENT_PASSWORD"],
        ),
    ) as driver:
        driver.verify_connectivity()
        yield driver, database


def _load(path: Path) -> LoadAccepted:
    result = load_realisation_yaml(path, ontology=career_ontology_v5_0())
    assert isinstance(result, LoadAccepted), result
    return result


def _stored_ids(driver: Any, database: str) -> tuple[set[str], set[str]]:
    with driver.session(database=database) as session:
        entities = session.run(
            "MATCH (n:CaronEntity) RETURN collect(n.id) AS ids"
        ).single()
        direct = session.run(
            "MATCH ()-[r:CARON_DIRECT]->() RETURN collect(r.id) AS ids"
        ).single()
        qualified = session.run(
            "MATCH (n:CaronRelation) RETURN collect(n.id) AS ids"
        ).single()
        assert entities is not None and direct is not None and qualified is not None
        return set(entities["ids"]), set(direct["ids"]) | set(qualified["ids"])


def test_live_projection_counts_ids_and_transaction_rollback(
    connection: tuple[Any, str],
) -> None:
    driver, database = connection
    with driver.session(database=database) as session:
        component = session.run(
            "CALL dbms.components() YIELD name, versions, edition "
            "WHERE name = 'Neo4j Kernel' "
            "RETURN versions[0] AS version, edition"
        ).single()
        assert component is not None
        assert component["version"] == "2026.09.0"
        assert component["edition"].lower() == "community"
        cypher = session.run("CYPHER 25 RETURN 25 AS version").single()
        assert cypher is not None
        assert cypher["version"] == 25
        print(
            {
                "server": dict(component),
                "cypher": "25 (explicit)",
                "driver": pytest.importorskip("neo4j").__version__,
            }
        )
    install_projection_constraints(driver, database=database)

    for path, expected in ((GEANT4, (7, 6)), (CAREER, (77, 113))):
        loaded = _load(path)
        print({"fixture": path.name, "source_state_id": loaded.source_state_id})
        counts = project_snapshot(
            driver,
            loaded.realisation,
            database=database,
            source_state_id=loaded.source_state_id,
        )
        assert (counts.nodes, counts.relationships) == expected
        with driver.session(database=database) as session:
            node_count = session.run("MATCH (n) RETURN count(n) AS count").single()
            link_count = session.run(
                "MATCH ()-[r]->() RETURN count(r) AS count"
            ).single()
            metadata = session.run(
                "MATCH (m:CaronProjection {marker: 'active'}) "
                "RETURN m.source_state_id AS source_state_id"
            ).single()
            assert node_count is not None and link_count is not None
            assert metadata is not None
            assert (node_count["count"], link_count["count"]) == expected
            assert metadata["source_state_id"] == loaded.source_state_id
        assert _stored_ids(driver, database) == (
            {item.id for item in loaded.realisation.entities},
            {item.id for item in loaded.realisation.relations},
        )
        extracted = extract_snapshot(driver, database=database)
        assert extracted.source_state_id == loaded.source_state_id
        assert extracted.candidate.id == loaded.realisation.id
        assert extracted.candidate.coverage == loaded.realisation.coverage
        source_entities = {item.id: item for item in loaded.realisation.entities}
        restored_entities = {item.id: item for item in extracted.validated.entities}
        assert source_entities.keys() == restored_entities.keys()
        for entity_id, source in source_entities.items():
            restored = restored_entities[entity_id]
            assert restored.kind == source.kind
            assert {p.name: p.value for p in restored.properties} == {
                p.name: p.value for p in source.properties
            }
        source_relations = {item.id: item for item in loaded.realisation.relations}
        restored_relations = {item.id: item for item in extracted.validated.relations}
        assert source_relations.keys() == restored_relations.keys()
        for relation_id, source_relation in source_relations.items():
            restored_relation = restored_relations[relation_id]
            assert (
                restored_relation.kind,
                restored_relation.source,
                restored_relation.target,
            ) == (
                source_relation.kind,
                source_relation.source,
                source_relation.target,
            )
            assert {q.name: q.value for q in restored_relation.qualifiers} == {
                q.name: q.value for q in source_relation.qualifiers
            }

    original_ids = _stored_ids(driver, database)
    original_snapshot = extract_snapshot(driver, database=database)
    plan = prepare_snapshot(_load(GEANT4).realisation)

    class FaultAfterDeletion:
        def __init__(self, tx: Any) -> None:
            self.tx = tx

        def run(self, query: str, **parameters: object) -> Any:
            if "CARON_Q_CONTEXT" in query:
                raise RuntimeError("Injected failure during snapshot replacement")
            return self.tx.run(query, **parameters)

    with (
        driver.session(database=database) as session,
        pytest.raises(RuntimeError, match="Injected failure"),
    ):
        session.execute_write(lambda tx: _write_snapshot(FaultAfterDeletion(tx), plan))
    assert _stored_ids(driver, database) == original_ids
    assert extract_snapshot(driver, database=database) == original_snapshot

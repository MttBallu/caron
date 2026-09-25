"""Run with a dedicated Neo4j Community 2026.09.0 test database.

Set CARON_NEO4J_EXPERIMENT_URI, USER, PASSWORD, and optionally DATABASE.
The test replaces the database's prior Caron projection in a transaction.
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
from caron.yaml_reader import LoadAccepted, load_realisation_yaml

ROOT = Path(__file__).parents[2]
GEANT4 = ROOT / "tests/fixtures/geant4-learning-and-activity-v0.1.yaml"
CAREER = ROOT / "caron/data/career-across-contexts-v0.1.yaml"


@pytest.fixture
def connection() -> Iterator[tuple[Any, str]]:
    uri = os.environ.get("CARON_NEO4J_EXPERIMENT_URI")
    if uri is None:
        pytest.skip("Set CARON_NEO4J_EXPERIMENT_URI for the live projection gate")
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
            "CALL dbms.components() YIELD versions, edition "
            "RETURN versions[0] AS version, edition"
        ).single()
        assert component is not None
        assert component["version"] == "2026.09.0"
        assert component["edition"].lower() == "community"
        setting = session.run(
            "SHOW SETTINGS YIELD name, value "
            "WHERE name = 'db.query.default_language' RETURN value"
        ).single()
        assert setting is not None
        assert setting["value"] == "CYPHER_25"
        print(
            {
                "server": dict(component),
                "cypher_default": setting["value"],
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

    original_ids = _stored_ids(driver, database)
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

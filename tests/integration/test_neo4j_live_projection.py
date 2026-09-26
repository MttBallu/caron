"""Run with a dedicated Neo4j Community 2026.09.0 test database.

Set CARON_NEO4J_EXPERIMENT_URI, USER, PASSWORD, and optionally DATABASE.
Set CARON_NEO4J_EXPERIMENT_ALLOW_WRITE=1 to opt in to replacement of an
existing Caron projection in that database.
"""

import os
from collections.abc import Iterator
from pathlib import Path
from time import perf_counter
from typing import Any

import pytest

from caron import (
    Accepted,
    EntityRef,
    career_ontology_v5_0,
    validate_candidate,
)
from caron._m2a import (
    ActivityResourceMatch,
    LearningMatch,
    MatchesAccepted,
    MatchesRejected,
    Request,
    evaluate_matches,
)
from caron.adapters.neo4j_projection import (
    _write_snapshot,
    install_projection_constraints,
    prepare_snapshot,
    project_snapshot,
)
from caron.adapters.neo4j_reconstruction import extract_snapshot
from caron.adapters.neo4j_results import evaluate_projected_matches
from caron.yaml_reader import LoadAccepted, load_realisation_yaml
from tests.fixtures.neo4j_career import PERSON, PROBES, source_matches, source_view_ids
from tests.fixtures.neo4j_m2a import CASES, Case
from tests.fixtures.v5 import labelled, v5_candidate

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
                    "driver": neo4j.__version__,
                }
            )
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


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_live_m2a_case(connection: tuple[Any, str], case: Case) -> None:
    driver, database = connection
    install_projection_constraints(driver, database=database)
    checked = validate_candidate(
        career_ontology_v5_0(),
        v5_candidate(
            case.entities,
            case.relations,
            candidate_id=f"fixture:{case.id}",
            scope="fixture_career",
        ),
    )
    assert isinstance(checked, Accepted), checked
    try:
        project_snapshot(driver, checked.realisation, database=database)
        result = evaluate_projected_matches(
            driver,
            request=Request("p", "x"),
            expected_realisation_id=checked.realisation.id,
            database=database,
        )
        assert result.diagnostics == ()
        assert result.request == Request("p", "x")
        assert result.source_realisation_id == checked.realisation.id
        assert result.coverage == checked.realisation.coverage
        assert len(result.matches) == len(case.expected)
        assert set(result.matches) == set(case.expected)
        assert result.view is not None
        assert result.view.results == result.matches
        reference = evaluate_matches(checked.realisation, Request("p", "x"))
        semantic = result.semantic_outcome()
        assert isinstance(reference, MatchesAccepted)
        assert isinstance(semantic, MatchesAccepted)
        assert set(semantic.matches) == set(reference.matches)
        assert semantic.view.entities == reference.view.entities
        assert semantic.view.relations == reference.view.relations
        assert result.view.coverage == checked.realisation.coverage
        assert {item.id for item in result.view.entities} == case.view_entities
        assert {item.id for item in result.view.relations} == case.view_relations
        source_entities = {item.id: item for item in checked.realisation.entities}
        source_relations = {item.id: item for item in checked.realisation.relations}
        for entity in result.view.entities:
            assert entity == source_entities[entity.id]
        for relation in result.view.relations:
            assert relation == source_relations[relation.id]
    finally:
        career = _load(CAREER)
        project_snapshot(
            driver,
            career.realisation,
            database=database,
            source_state_id=career.source_state_id,
        )


@pytest.mark.parametrize(
    ("person_id", "target_id", "code"),
    [
        ("missing", "x", "query.unknown_person"),
        ("x", "x", "query.invalid_person_kind"),
        ("p", "missing", "query.unknown_target"),
        ("p", "p", "query.invalid_target_kind"),
        ("p", "artifact", "query.invalid_target_kind"),
    ],
)
def test_live_m2a_request_diagnostic(
    connection: tuple[Any, str],
    person_id: str,
    target_id: str,
    code: str,
) -> None:
    driver, database = connection
    case = next(item for item in CASES if item.id == "C08_empty_selective_realisation")
    checked = validate_candidate(
        career_ontology_v5_0(),
        v5_candidate(
            (*case.entities, labelled("artifact", "Artifact")),
            case.relations,
            candidate_id="fixture:C08",
            scope="fixture_career",
        ),
    )
    assert isinstance(checked, Accepted), checked
    install_projection_constraints(driver, database=database)
    try:
        project_snapshot(driver, checked.realisation, database=database)
        result = evaluate_projected_matches(
            driver,
            request=Request(person_id, target_id),
            expected_realisation_id=checked.realisation.id,
            database=database,
        )
        assert result.matches == () and result.view is None
        assert tuple(item.code for item in result.diagnostics) == (code,)
        assert result.coverage == checked.realisation.coverage
        assert result.request == Request(person_id, target_id)
        reference = evaluate_matches(
            checked.realisation, Request(person_id, target_id)
        )
        assert isinstance(reference, MatchesRejected)
        assert result.semantic_outcome() == reference
    finally:
        career = _load(CAREER)
        project_snapshot(
            driver,
            career.realisation,
            database=database,
            source_state_id=career.source_state_id,
        )


def test_live_whole_career_m2a_queries(connection: tuple[Any, str]) -> None:
    driver, database = connection
    loaded = _load(CAREER)
    source = loaded.realisation
    install_projection_constraints(driver, database=database)
    start = perf_counter()
    counts = project_snapshot(
        driver, source, database=database, source_state_id=loaded.source_state_id
    )
    load_seconds = perf_counter() - start
    assert (counts.nodes, counts.relationships) == (77, 113)
    start = perf_counter()
    reconstructed = extract_snapshot(driver, database=database)
    reconstruction_seconds = perf_counter() - start
    assert reconstructed.source_state_id == loaded.source_state_id
    assert reconstructed.candidate.id == source.id
    assert reconstructed.validated.coverage == source.coverage
    assert {
        item.id: (item.kind, {p.name: p.value for p in item.properties})
        for item in reconstructed.validated.entities
    } == {
        item.id: (item.kind, {p.name: p.value for p in item.properties})
        for item in source.entities
    }
    assert {
        item.id: (
            item.kind,
            item.source,
            item.target,
            {q.name: q.value for q in item.qualifiers},
        )
        for item in reconstructed.validated.relations
    } == {
        item.id: (
            item.kind,
            item.source,
            item.target,
            {q.name: q.value for q in item.qualifiers},
        )
        for item in source.relations
    }

    for probe in PROBES:
        start = perf_counter()
        result = evaluate_projected_matches(
            driver,
            request=Request(PERSON, probe.target_id),
            expected_realisation_id=source.id,
            expected_source_state_id=loaded.source_state_id,
            database=database,
        )
        query_seconds = perf_counter() - start
        expected = source_matches(source, probe.target_id)
        assert result.diagnostics == ()
        assert result.request == Request(PERSON, probe.target_id)
        assert result.source_realisation_id == source.id
        assert result.source_state_id == loaded.source_state_id
        assert result.coverage == source.coverage
        assert len(result.matches) == len(expected)
        assert set(result.matches) == set(expected)
        assert {
            item.learns for item in result.matches if isinstance(item, LearningMatch)
        } == probe.learning_ids
        assert {
            item.resource_relation
            for item in result.matches
            if isinstance(item, ActivityResourceMatch)
        } == probe.resource_ids
        assert result.view is not None
        assert result.view.results == result.matches
        reference = evaluate_matches(source, Request(PERSON, probe.target_id))
        semantic = result.semantic_outcome()
        assert isinstance(reference, MatchesAccepted)
        assert isinstance(semantic, MatchesAccepted)
        assert set(semantic.matches) == set(reference.matches)
        assert semantic.view.entities == reference.view.entities
        assert semantic.view.relations == reference.view.relations
        assert result.view.source_realisation_id == source.id
        assert result.view.coverage == source.coverage
        expected_entity_ids, relation_ids = source_view_ids(source, expected)
        assert {item.id for item in result.view.relations} == relation_ids
        for item in result.view.relations:
            original = source.relation(item.id)
            assert original is not None
            assert (item.kind, item.source, item.target) == (
                original.kind,
                original.source,
                original.target,
            )
            assert {q.name: q.value for q in item.qualifiers} == {
                q.name: q.value for q in original.qualifiers
            }
        entity_ids = {item.id for item in result.view.entities}
        assert entity_ids == expected_entity_ids
        assert tuple(binding.name for binding in result.view.bindings) == (
            "person",
            "target",
        )
        for relation in result.view.relations:
            assert relation.source.entity_id in entity_ids
            assert relation.target.entity_id in entity_ids
            assert all(
                qualifier.value.entity_id in entity_ids
                for qualifier in relation.qualifiers
                if isinstance(qualifier.value, EntityRef)
            )
        for entity in result.view.entities:
            original_entity = source.entity(entity.id)
            assert original_entity is not None
            assert entity.kind == original_entity.kind
            assert {p.name: p.value for p in entity.properties} == {
                p.name: p.value for p in original_entity.properties
            }
            assert all(
                prop.value.entity_id in entity_ids
                for prop in entity.properties
                if isinstance(prop.value, EntityRef)
            )
        print(
            {
                "target": probe.target_id,
                "matches": len(result.matches),
                "view_entities": len(result.view.entities),
                "view_relations": len(result.view.relations),
                "query_seconds": round(query_seconds, 6),
            }
        )
    print(
        {
            "fixture": CAREER.name,
            "source_state_id": loaded.source_state_id,
            "load_seconds": round(load_seconds, 6),
            "reconstruction_seconds": round(reconstruction_seconds, 6),
        }
    )


def test_live_projection_counts_ids_and_transaction_rollback(
    connection: tuple[Any, str],
) -> None:
    driver, database = connection
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

"""Private retrieval rows preserve named supports and input parameters."""

from collections.abc import Callable

import pytest

from caron import Coverage, CoverageStatus
from caron.adapters.neo4j_projection import ProjectionError
from caron.adapters.neo4j_retrieval import (
    ActivityRow,
    LearningRow,
    RetrievalRows,
    retrieve_match_rows,
)


class _Result:
    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = rows

    def data(self) -> list[dict[str, object]]:
        return self.rows


class _Driver:
    def __init__(self, target_kind: str = "Method") -> None:
        self.target_kind = target_kind
        self.marker: dict[str, str] = {
            "marker": "active",
            "profile_version": "0.1",
            "ontology_id": "caron.career-model",
            "ontology_version": "5.0",
            "realisation_id": "fixture:example",
            "coverage_status": "selective",
            "coverage_scope": "Some facts",
            "source_state_id": "hash:example",
        }
        self.learning: list[dict[str, object]] = []
        self.activities: list[dict[str, object]] = []
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.reads = 0

    def session(self, *, database: str) -> "_Driver":
        assert database == "neo4j"
        return self

    def __enter__(self) -> "_Driver":
        return self

    def __exit__(self, *args: object) -> None:
        pass

    def execute_read(self, work: Callable[["_Driver"], RetrievalRows]) -> RetrievalRows:
        self.reads += 1
        return work(self)

    def run(self, query: str, **parameters: object) -> _Result:
        assert query.startswith("CYPHER 25")
        self.calls.append((query, parameters))
        if "properties(m) AS marker" in query:
            return _Result([{"marker": self.marker}])
        if "labels(e) AS labels" in query:
            return _Result(
                [
                    {
                        "id": parameters["person_id"],
                        "labels": ["CaronEntity", "Person"],
                    },
                    {
                        "id": parameters["target_id"],
                        "labels": ["CaronEntity", self.target_kind],
                    },
                ]
            )
        if "learning.id AS learns_id" in query:
            return _Result(self.learning)
        if "resource.id AS resource_relation_id" in query:
            return _Result(self.activities)
        raise AssertionError(f"Unexpected Cypher statement: {query}")


def test_distinct_activity_supports_keep_roles_and_target_kind_filter() -> None:
    driver = _Driver()
    driver.learning = [
        {
            "person_id": "person:sample",
            "target_id": "method:x",
            "context_id": "context:c",
            "learns_id": "l1",
        }
    ]
    driver.activities = [
        {
            "person_id": "person:sample",
            "target_id": "method:x",
            "activity_id": "activity:a",
            "context_id": "context:c",
            "resource_kind": kind,
            "performs_id": "p1",
            "occurs_in_id": "o1",
            "resource_relation_id": rid,
        }
        for kind, rid in (("draws_on", "m2"), ("applies", "m1"))
    ]
    rows = retrieve_match_rows(
        driver,
        person_id="person:sample",
        target_id="method:x",
        expected_realisation_id="fixture:example",
        expected_source_state_id="hash:example",
    )
    assert driver.reads == 1
    assert rows.coverage == Coverage(CoverageStatus.SELECTIVE, "Some facts")
    assert rows.source_state_id == "hash:example"
    assert rows.learning == (
        LearningRow("person:sample", "method:x", "context:c", "l1"),
    )
    assert rows.activity == (
        ActivityRow(
            "person:sample",
            "method:x",
            "activity:a",
            "context:c",
            "applies",
            "p1",
            "o1",
            "m1",
        ),
        ActivityRow(
            "person:sample",
            "method:x",
            "activity:a",
            "context:c",
            "draws_on",
            "p1",
            "o1",
            "m2",
        ),
    )
    assert all(
        "person:sample" not in query and "method:x" not in query
        for query, _ in driver.calls
    )
    assert all(
        "$person_id" in query and "$target_id" in query for query, _ in driver.calls[1:]
    )
    assert driver.calls[-1][1]["resource_kinds"] == ["applies", "draws_on"]


def test_snapshot_mismatch_and_invalid_resource_kind_rejected() -> None:
    driver = _Driver("Technology")
    with pytest.raises(ProjectionError, match="does not match"):
        retrieve_match_rows(
            driver, person_id="p", target_id="x", expected_realisation_id="other"
        )
    assert len(driver.calls) == 1
    driver.calls.clear()
    with pytest.raises(ProjectionError, match="does not match"):
        retrieve_match_rows(
            driver,
            person_id="p",
            target_id="x",
            expected_realisation_id="fixture:example",
            expected_source_state_id="other-hash",
        )
    assert len(driver.calls) == 1
    driver.calls.clear()
    driver.activities = [
        {
            "person_id": "p",
            "target_id": "x",
            "activity_id": "a",
            "context_id": "c",
            "resource_kind": "draws_on",
            "performs_id": "p1",
            "occurs_in_id": "o1",
            "resource_relation_id": "u1",
        }
    ]
    with pytest.raises(ProjectionError, match="requested binding or kind"):
        retrieve_match_rows(
            driver,
            person_id="p",
            target_id="x",
            expected_realisation_id="fixture:example",
        )

"""Conformance of the draft M2-A reference evaluator to independent cases."""

from dataclasses import replace
from pathlib import Path

import pytest

from caron import Accepted, career_ontology_v5_0, validate_candidate
from caron._m2a import (
    MatchesAccepted,
    MatchesRejected,
    Request,
    evaluate_matches,
)
from caron.yaml_reader import LoadAccepted, load_realisation_yaml
from tests.fixtures.neo4j_career import (
    PERSON,
    PROBES,
    CareerProbe,
    source_matches,
    source_view_ids,
)
from tests.fixtures.neo4j_m2a import CASES, Case
from tests.fixtures.v5 import v5_candidate

CAREER = Path(__file__).parents[2] / "caron/data/career-across-contexts-v0.1.yaml"


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_frozen_case_matches_and_selected_records(case: Case) -> None:
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
    source = checked.realisation
    result = evaluate_matches(source, Request("p", "x"))
    assert isinstance(result, MatchesAccepted)
    assert result.request == Request("p", "x")
    assert result.source_realisation_id == source.id
    assert (result.ontology_id, result.ontology_version) == (
        source.ontology.id,
        source.ontology.version,
    )
    assert result.coverage == source.coverage
    assert len(result.matches) == len(case.expected)
    assert set(result.matches) == set(case.expected)
    assert result.view.results == result.matches
    assert {entity.id for entity in result.view.entities} == case.view_entities
    assert {relation.id for relation in result.view.relations} == case.view_relations
    assert result.view.coverage == source.coverage


@pytest.mark.parametrize("probe", PROBES, ids=lambda probe: probe.target_id)
def test_whole_career_against_independent_source_expectations(
    probe: CareerProbe,
) -> None:
    loaded = load_realisation_yaml(CAREER, ontology=career_ontology_v5_0())
    assert isinstance(loaded, LoadAccepted), loaded
    source = loaded.realisation
    result = evaluate_matches(source, Request(PERSON, probe.target_id))
    assert isinstance(result, MatchesAccepted)
    assert set(result.matches) == set(source_matches(source, probe.target_id))
    entities, relations = source_view_ids(source, result.matches)
    assert {entity.id for entity in result.view.entities} == entities
    assert {relation.id for relation in result.view.relations} == relations


def test_empty_success_is_distinct_from_rejected_request() -> None:
    checked = validate_candidate(
        career_ontology_v5_0(),
        v5_candidate(CASES[8].entities, candidate_id="fixture:empty"),
    )
    assert isinstance(checked, Accepted)
    source = checked.realisation
    empty = evaluate_matches(source, Request("p", "x"))
    assert isinstance(empty, MatchesAccepted)
    assert empty.matches == ()
    assert empty.view.entities == () and empty.view.relations == ()
    assert empty.coverage == source.coverage

    for request, code in (
        (Request("missing", "x"), "query.unknown_person"),
        (Request("x", "x"), "query.invalid_person_kind"),
        (Request("p", "missing"), "query.unknown_target"),
        (Request("p", "p"), "query.invalid_target_kind"),
    ):
        rejected = evaluate_matches(source, request)
        assert isinstance(rejected, MatchesRejected)
        assert rejected.request == request
        assert tuple(diagnostic.code for diagnostic in rejected.diagnostics) == (code,)


def test_same_identity_with_changed_schema_is_rejected() -> None:
    accepted_schema = career_ontology_v5_0()
    changed = replace(accepted_schema, relations=accepted_schema.relations[:-1])
    checked = validate_candidate(
        changed, v5_candidate(CASES[8].entities, candidate_id="fixture:impostor")
    )
    assert isinstance(checked, Accepted)
    result = evaluate_matches(checked.realisation, Request("p", "x"))
    assert isinstance(result, MatchesRejected)
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        "query.unsupported_ontology",
    )

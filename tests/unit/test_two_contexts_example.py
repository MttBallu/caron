"""Behavioral checks for the Python cross-context example."""

from caron import Accepted, EntityRef, validate_candidate
from caron.ontology import career_ontology_v5_0
from examples.two_contexts import build_candidate


def test_cross_context_candidate_is_valid() -> None:
    assert isinstance(
        validate_candidate(career_ontology_v5_0(), build_candidate()),
        Accepted,
    )


def test_contexts_organize_their_own_activities() -> None:
    candidate = build_candidate()
    activity_contexts = {
        relation.source.entity_id: relation.target.entity_id
        for relation in candidate.relations
        if relation.kind == "occurs_in"
    }

    assert activity_contexts == {
        "activity:analyse-alice-data": "context:msc-alice-analysis",
        "activity:build-training-dataset": "context:phd-synthetic-data",
    }


def test_python_connects_alice_analysis_and_synthetic_data_work() -> None:
    candidate = build_candidate()
    python_uses = {
        relation.source.entity_id
        for relation in candidate.relations
        if relation.kind == "uses_technology"
        and relation.target == EntityRef("technology:python")
    }

    assert python_uses == {
        "activity:analyse-alice-data",
        "activity:build-training-dataset",
    }
    assert all("transfer" not in relation.kind for relation in candidate.relations)


def test_each_activity_has_input_output_and_domain_evidence() -> None:
    candidate = build_candidate()
    activity_ids = {
        entity.id for entity in candidate.entities if entity.kind == "Activity"
    }
    required_relation_kinds = {
        "uses_technology",
        "draws_on",
        "takes_input",
        "produces",
    }

    for activity_id in activity_ids:
        actual_relation_kinds = {
            relation.kind
            for relation in candidate.relations
            if relation.source == EntityRef(activity_id)
        }
        assert required_relation_kinds <= actual_relation_kinds

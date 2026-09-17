"""Behavioral checks for the example spanning two contexts."""

from caron import Accepted, EntityRef, model4_ontology, validate_candidate
from examples.two_contexts import build_candidate


def test_two_context_candidate_is_valid() -> None:
    assert isinstance(
        validate_candidate(model4_ontology(), build_candidate()), Accepted
    )


def test_both_contextualized_activities_share_one_python_entity() -> None:
    candidate = build_candidate()
    python_entities = tuple(
        entity for entity in candidate.entities if entity.id == "technology:python"
    )
    python_uses = tuple(
        relation
        for relation in candidate.relations
        if relation.kind == "uses" and relation.target == EntityRef("technology:python")
    )
    activity_contexts = {
        relation.source.entity_id: relation.target.entity_id
        for relation in candidate.relations
        if relation.kind == "occurs_in"
    }

    assert len(python_entities) == 1
    assert {relation.source.entity_id for relation in python_uses} == {
        "activity:analyse-spectra",
        "activity:build-data-pipeline",
    }
    assert {
        activity_contexts[relation.source.entity_id] for relation in python_uses
    } == {
        "context:phd",
        "context:data-project",
    }

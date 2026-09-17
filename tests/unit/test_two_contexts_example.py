"""Behavioral checks for the cross-context development example."""

from caron import Accepted, EntityRef, model4_ontology, validate_candidate
from examples.two_contexts import build_candidate


def test_cross_context_candidate_is_valid() -> None:
    assert isinstance(
        validate_candidate(model4_ontology(), build_candidate()), Accepted
    )


def test_contexts_organize_their_own_activities() -> None:
    candidate = build_candidate()
    activity_contexts = {
        relation.source.entity_id: relation.target.entity_id
        for relation in candidate.relations
        if relation.kind == "occurs_in"
    }

    assert activity_contexts == {
        "activity:evaluate-ot-formulation": "context:phd-optimal-transport",
        "activity:design-discrete-measure-abstraction": "context:jax-geopro",
        "activity:implement-ot-losses": "context:jax-geopro",
    }


def test_reusable_entities_connect_the_contexts_without_transfer_edges() -> None:
    candidate = build_candidate()
    activity_contexts = {
        relation.source.entity_id: relation.target.entity_id
        for relation in candidate.relations
        if relation.kind == "occurs_in"
    }

    def contexts_using(kind: str, target_id: str) -> set[str]:
        return {
            activity_contexts[relation.source.entity_id]
            for relation in candidate.relations
            if relation.kind == kind and relation.target == EntityRef(target_id)
        }

    expected_contexts = {
        "context:phd-optimal-transport",
        "context:jax-geopro",
    }
    assert contexts_using("uses", "technology:python") == expected_contexts
    assert contexts_using("applies", "method:optimal-transport") == expected_contexts
    assert contexts_using("draws_on", "subject:discrete-measures") == expected_contexts
    assert all("transfer" not in relation.kind for relation in candidate.relations)


def test_every_activity_has_concrete_semantic_evidence() -> None:
    candidate = build_candidate()
    activity_ids = {
        entity.id for entity in candidate.entities if entity.kind == "Activity"
    }
    evidence_relations = {"uses", "applies", "draws_on", "produces", "supports"}
    evidence_by_activity = {
        activity_id: {
            relation.kind
            for relation in candidate.relations
            if relation.source == EntityRef(activity_id)
            and relation.kind in evidence_relations
        }
        for activity_id in activity_ids
    }

    assert all(
        {"uses", "produces"} <= relation_kinds
        for relation_kinds in evidence_by_activity.values()
    )

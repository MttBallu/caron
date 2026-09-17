"""Generative checks of semantic validation invariants."""

from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from caron import (
    ACTIVITY,
    ARTIFACT,
    CONTEXT,
    METHOD,
    ORGANIZATION,
    PERSON,
    PLACE,
    PROPOSITION,
    SUBJECT,
    TECHNOLOGY,
    Accepted,
    EntityRef,
    Rejected,
    RelationAssertion,
    model4_ontology,
    validate_candidate,
)
from tests.fixtures.minimal import labelled, minimal_candidate

CONCEPT_KINDS = (
    PERSON,
    CONTEXT,
    ACTIVITY,
    TECHNOLOGY,
    METHOD,
    SUBJECT,
    ARTIFACT,
    PROPOSITION,
    ORGANIZATION,
    PLACE,
)


@given(
    st.text(min_size=1).filter(
        lambda value: value not in {"person:ada", "activity:build"}
    )
)
def test_dangling_relation_endpoint_is_never_accepted(missing_id: str) -> None:
    candidate = minimal_candidate()
    malformed = replace(candidate.relations[0], source=EntityRef(missing_id))

    result = validate_candidate(
        model4_ontology(),
        replace(candidate, relations=(malformed, candidate.relations[1])),
    )

    assert isinstance(result, Rejected)
    assert "record.dangling_endpoint" in {item.code for item in result.diagnostics}


@given(st.sampled_from(CONCEPT_KINDS), st.sampled_from(CONCEPT_KINDS))
def test_performs_only_accepts_person_to_activity(
    source_kind: str, target_kind: str
) -> None:
    candidate = minimal_candidate()
    source = labelled("source", source_kind)
    target = labelled("target", target_kind)
    performs = RelationAssertion(
        "relation:generated-performs",
        "performs",
        EntityRef(source.id),
        EntityRef(target.id),
    )
    generated = replace(
        candidate,
        entities=candidate.entities + (source, target),
        relations=candidate.relations + (performs,),
    )

    result = validate_candidate(model4_ontology(), generated)

    if isinstance(result, Accepted):
        assert source_kind == PERSON
        assert target_kind == ACTIVITY
    elif source_kind != PERSON or target_kind != ACTIVITY:
        assert "record.invalid_endpoint_kind" in {
            item.code for item in result.diagnostics
        }


@given(st.permutations((0, 1, 2)), st.permutations((0, 1)))
def test_validation_is_independent_of_record_order(
    entity_order: list[int], relation_order: list[int]
) -> None:
    candidate = minimal_candidate()
    reordered = replace(
        candidate,
        entities=tuple(candidate.entities[index] for index in entity_order),
        relations=tuple(candidate.relations[index] for index in relation_order),
    )

    original_result = validate_candidate(model4_ontology(), candidate)
    reordered_result = validate_candidate(model4_ontology(), reordered)

    assert isinstance(original_result, Accepted)
    assert isinstance(reordered_result, Accepted)
    assert frozenset(reordered_result.realisation.entities) == frozenset(
        original_result.realisation.entities
    )
    assert frozenset(reordered_result.realisation.relations) == frozenset(
        original_result.realisation.relations
    )

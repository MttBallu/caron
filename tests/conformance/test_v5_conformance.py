"""Representative valid, invalid, and non-inference scenarios for 5.0."""

from dataclasses import replace

import pytest

from caron import (
    ARTIFACT,
    COLLECTIVE,
    CONTEXT,
    LANGUAGE,
    METHOD,
    PERSON,
    PLACE,
    SUBJECT,
    TECHNOLOGY,
    Accepted,
    Entity,
    EntityRef,
    Property,
    Qualifier,
    RealisationCandidate,
    Rejected,
    RelationAssertion,
    TemporalExtent,
    YearMonth,
    validate_candidate,
)
from caron.ontology import career_ontology_v5_0
from tests.fixtures.v5 import (
    activity_candidate,
    assertion,
    credential_candidate,
    labelled,
    minimal_v5_candidate,
    proposition,
    rich_v5_candidate,
    v5_candidate,
)

EXPECTED_CONCEPT_KINDS = frozenset(
    {
        "Person",
        "Collective",
        "Context",
        "Activity",
        "Technology",
        "Method",
        "Subject",
        "Language",
        "Artifact",
        "Proposition",
        "Organization",
        "Place",
        "Credential",
    }
)
EXPECTED_RELATION_KINDS = frozenset(
    {
        "part_of",
        "suborganization_of",
        "performs",
        "occurs_in",
        "participates_in",
        "collective_membership",
        "organization_association",
        "occurs_at",
        "exposed_to",
        "learns",
        "uses_technology",
        "uses_artifact",
        "uses_language",
        "applies",
        "draws_on",
        "native_language",
        "takes_input",
        "produces",
        "modifies",
        "awarded_to",
        "awarded_by",
        "obtained_through",
        "evidenced_by",
        "aims_at",
        "addresses",
        "motivates",
        "results_in",
        "establishes",
        "supports",
        "contradicts",
        "bears_on",
    }
)


def _validate(candidate: RealisationCandidate) -> Accepted | Rejected:
    return validate_candidate(career_ontology_v5_0(), candidate)


def _accept(candidate: RealisationCandidate) -> Accepted:
    result = _validate(candidate)
    assert isinstance(result, Accepted)
    return result


def _codes(result: Rejected) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def _with_minimal_evidence(
    *entities: Entity,
    relations: tuple[RelationAssertion, ...],
) -> RealisationCandidate:
    candidate = minimal_v5_candidate()
    return replace(
        candidate,
        entities=(*candidate.entities, *entities),
        relations=(*candidate.relations, *relations),
    )


def test_minimal_v5_candidate_is_valid() -> None:
    candidate = minimal_v5_candidate()
    result = _accept(candidate)

    assert result.realisation.entities == candidate.entities
    assert result.realisation.relations == candidate.relations


def test_rich_candidate_covers_and_validates_the_complete_vocabulary() -> None:
    candidate = rich_v5_candidate()

    assert {entity.kind for entity in candidate.entities} == EXPECTED_CONCEPT_KINDS
    assert {
        relation.kind for relation in candidate.relations
    } == EXPECTED_RELATION_KINDS
    result = _accept(candidate)
    assert result.realisation.entities == candidate.entities
    assert result.realisation.relations == candidate.relations


@pytest.mark.parametrize(
    "performer_kinds",
    ((PERSON,), (COLLECTIVE,), (PERSON, COLLECTIVE)),
    ids=("personal", "collective", "multiple"),
)
def test_personal_collective_and_multiple_performance(
    performer_kinds: tuple[str, ...],
) -> None:
    candidate = activity_candidate(performer_kinds)
    result = _accept(candidate)
    performers = tuple(
        relation.source.entity_id
        for relation in result.realisation.relations
        if relation.kind == "performs"
    )

    assert performers == tuple(entity.id for entity in candidate.entities[:-2])


def test_participation_membership_and_organization_roles() -> None:
    result = _accept(rich_v5_candidate())
    participations = tuple(
        relation
        for relation in result.realisation.relations
        if relation.kind == "participates_in"
    )

    assert len(participations) == 2
    assert {
        relation.qualifier("organization") is None for relation in participations
    } == {
        True,
        False,
    }
    assert all(
        isinstance(relation.qualifier("role"), str) for relation in participations
    )
    assert {relation.kind for relation in result.realisation.relations} >= {
        "collective_membership",
        "organization_association",
    }


def test_language_has_independent_exposure_learning_use_and_native_facts() -> None:
    result = _accept(rich_v5_candidate())
    language_id = "language:english"
    kinds = {
        relation.kind
        for relation in result.realisation.relations
        if relation.target.entity_id == language_id
    }

    assert kinds == {"exposed_to", "learns", "uses_language", "native_language"}


@pytest.mark.parametrize("present_kind", ("applies", "draws_on"))
def test_applies_and_draws_on_are_independently_valid(present_kind: str) -> None:
    method = labelled("method:focused", METHOD)
    relation = assertion(
        f"relation:{present_kind}",
        present_kind,
        "activity:minimal",
        method.id,
    )
    result = _accept(_with_minimal_evidence(method, relations=(relation,)))
    kinds = {item.kind for item in result.realisation.relations}

    assert present_kind in kinds
    assert ({"applies", "draws_on"} - {present_kind}).isdisjoint(kinds)


@pytest.mark.parametrize(
    "present_kind", ("uses_artifact", "takes_input", "produces", "modifies")
)
def test_artifact_roles_are_independently_valid(present_kind: str) -> None:
    artifact = labelled("artifact:focused", ARTIFACT)
    relation = assertion(
        f"relation:{present_kind}",
        present_kind,
        "activity:minimal",
        artifact.id,
    )
    result = _accept(_with_minimal_evidence(artifact, relations=(relation,)))
    artifact_relations = tuple(
        item
        for item in result.realisation.relations
        if item.target.entity_id == artifact.id
    )

    assert [item.kind for item in artifact_relations] == [present_kind]


@pytest.mark.parametrize(
    ("awarder_count", "awarded_in"),
    ((1, None), (2, YearMonth(2025, 10))),
    ids=("single-awarder-unknown-month", "joint-awarder-known-month"),
)
def test_single_and_joint_awards_with_absent_and_known_months(
    awarder_count: int, awarded_in: YearMonth | None
) -> None:
    candidate = credential_candidate(awarder_count=awarder_count, awarded_in=awarded_in)
    result = _accept(candidate)
    credential = result.realisation.entity("credential:focused")

    assert credential is not None
    assert credential.property("awarded_in") == awarded_in
    assert (
        sum(relation.kind == "awarded_by" for relation in result.realisation.relations)
        == awarder_count
    )
    assert not any(
        relation.kind == "evidenced_by" for relation in result.realisation.relations
    )


def test_obtaining_context_does_not_supply_an_award_month() -> None:
    candidate = credential_candidate()
    context = next(entity for entity in candidate.entities if entity.kind == CONTEXT)
    dated_context = replace(
        context,
        properties=(
            *context.properties,
            Property("temporal_extent", TemporalExtent.closed("2020-01", "2022-12")),
        ),
    )
    candidate = replace(
        candidate,
        entities=tuple(
            dated_context if entity.id == context.id else entity
            for entity in candidate.entities
        ),
    )

    result = _accept(candidate)
    credential = result.realisation.entity("credential:focused")
    assert credential is not None
    assert credential.property("awarded_in") is None


def test_place_and_occurs_at_are_present_in_cv_graph() -> None:
    result = _accept(rich_v5_candidate())
    place = result.realisation.entity("place:saclay")

    assert place is not None and place.kind == PLACE
    assert any(
        relation.kind == "occurs_at" and relation.target.entity_id == place.id
        for relation in result.realisation.relations
    )


@pytest.mark.parametrize(
    "fault",
    (
        "activity_without_performer",
        "activity_without_context",
        "activity_with_two_contexts",
        "credential_without_recipient",
        "credential_with_two_recipients",
        "credential_without_awarder",
        "credential_without_obtaining_context",
    ),
)
def test_every_bounded_activity_and_credential_cardinality_failure(
    fault: str,
) -> None:
    if fault.startswith("activity"):
        candidate = minimal_v5_candidate()
        relations = candidate.relations
        entities = candidate.entities
        if fault == "activity_without_performer":
            relations = tuple(item for item in relations if item.kind != "performs")
        elif fault == "activity_without_context":
            relations = tuple(item for item in relations if item.kind != "occurs_in")
        else:
            other = labelled("context:second", CONTEXT)
            entities = (*entities, other)
            relations = (
                *relations,
                assertion(
                    "relation:second-occurs",
                    "occurs_in",
                    "activity:minimal",
                    other.id,
                ),
            )
    else:
        candidate = credential_candidate()
        relations = candidate.relations
        entities = candidate.entities
        if fault == "credential_without_recipient":
            relations = tuple(item for item in relations if item.kind != "awarded_to")
        elif fault == "credential_with_two_recipients":
            other = labelled("person:second-recipient", PERSON)
            entities = (*entities, other)
            relations = (
                *relations,
                assertion(
                    "relation:second-recipient",
                    "awarded_to",
                    "credential:focused",
                    other.id,
                ),
            )
        elif fault == "credential_without_awarder":
            relations = tuple(item for item in relations if item.kind != "awarded_by")
        else:
            relations = tuple(
                item for item in relations if item.kind != "obtained_through"
            )

    result = _validate(replace(candidate, entities=entities, relations=relations))
    assert isinstance(result, Rejected)
    expected_code = (
        "realisation.relation_requirement_above_maximum"
        if fault in {"activity_with_two_contexts", "credential_with_two_recipients"}
        else "realisation.relation_requirement_below_minimum"
    )
    assert expected_code in _codes(result)


def test_participation_does_not_create_performance_or_addresses() -> None:
    person = labelled("person:participant", PERSON)
    context = labelled("context:participation", CONTEXT)
    participation = assertion(
        "relation:participation",
        "participates_in",
        person.id,
        context.id,
        Qualifier("role", "Participant"),
    )
    result = _accept(v5_candidate((person, context), (participation,)))

    assert result.realisation.relations == (participation,)
    assert {item.kind for item in result.realisation.relations}.isdisjoint(
        {"performs", "addresses"}
    )


def test_collective_performance_does_not_create_personal_performance() -> None:
    result = _accept(activity_candidate((COLLECTIVE,)))
    performs = tuple(
        relation
        for relation in result.realisation.relations
        if relation.kind == "performs"
    )

    assert len(performs) == 1
    performer = result.realisation.entity(performs[0].source.entity_id)
    assert performer is not None and performer.kind == COLLECTIVE
    assert not result.realisation.entities_of_kind(PERSON)


def test_exposure_does_not_create_learning() -> None:
    person = labelled("person:learner", PERSON)
    context = labelled("context:learning", CONTEXT)
    technology = labelled("technology:tool", TECHNOLOGY)
    exposure = assertion(
        "relation:exposure",
        "exposed_to",
        person.id,
        technology.id,
        Qualifier("context", EntityRef(context.id)),
    )
    result = _accept(v5_candidate((person, context, technology), (exposure,)))

    assert result.realisation.relations == (exposure,)
    assert not any(item.kind == "learns" for item in result.realisation.relations)


@pytest.mark.parametrize("resource_kind", (TECHNOLOGY, METHOD, SUBJECT, LANGUAGE))
def test_learning_does_not_create_exposure_or_activity_use(
    resource_kind: str,
) -> None:
    person = labelled("person:learner", PERSON)
    context = labelled("context:learning", CONTEXT)
    resource = labelled("resource:target", resource_kind)
    learning = assertion(
        "relation:learning",
        "learns",
        person.id,
        resource.id,
        Qualifier("context", EntityRef(context.id)),
    )
    result = _accept(v5_candidate((person, context, resource), (learning,)))

    assert result.realisation.relations == (learning,)


@pytest.mark.parametrize(
    ("resource_kind", "use_kind"),
    (
        (TECHNOLOGY, "uses_technology"),
        (METHOD, "applies"),
        (SUBJECT, "draws_on"),
        (LANGUAGE, "uses_language"),
    ),
)
def test_activity_resource_use_does_not_create_person_to_resource_fact(
    resource_kind: str, use_kind: str
) -> None:
    resource = labelled("resource:used", resource_kind)
    use = assertion("relation:resource-use", use_kind, "activity:minimal", resource.id)
    result = _accept(_with_minimal_evidence(resource, relations=(use,)))

    assert not any(
        relation.source.entity_id == "person:minimal"
        and relation.target.entity_id == resource.id
        for relation in result.realisation.relations
    )


def test_language_learning_does_not_create_native_language() -> None:
    person = labelled("person:learner", PERSON)
    context = labelled("context:language", CONTEXT)
    language = labelled("language:target", LANGUAGE)
    learning = assertion(
        "relation:learn-language",
        "learns",
        person.id,
        language.id,
        Qualifier("context", EntityRef(context.id)),
    )
    result = _accept(v5_candidate((person, context, language), (learning,)))

    assert result.realisation.relations == (learning,)
    assert not any(
        item.kind == "native_language" for item in result.realisation.relations
    )


def test_support_does_not_create_establishment() -> None:
    proposition_entity = proposition(
        "proposition:supported",
        "context:minimal",
        "A supported but not established claim.",
    )
    support = assertion(
        "relation:support",
        "supports",
        "activity:minimal",
        proposition_entity.id,
    )
    result = _accept(_with_minimal_evidence(proposition_entity, relations=(support,)))

    assert support in result.realisation.relations
    assert not any(item.kind == "establishes" for item in result.realisation.relations)


def test_outcome_and_aim_paths_do_not_create_bears_on() -> None:
    aim = proposition("proposition:aim", "context:minimal", "A local purpose.")
    outcome = proposition(
        "proposition:outcome", "context:minimal", "An explicit result."
    )
    relations = (
        assertion("relation:aim", "aims_at", "context:minimal", aim.id),
        assertion("relation:outcome", "results_in", "activity:minimal", outcome.id),
    )
    result = _accept(_with_minimal_evidence(aim, outcome, relations=relations))

    assert not any(item.kind == "bears_on" for item in result.realisation.relations)


def test_temporal_containment_does_not_copy_extents() -> None:
    parent = labelled(
        "context:parent",
        CONTEXT,
        None,
        Property("temporal_extent", TemporalExtent.closed("2020-01", "2024-12")),
    )
    child = labelled("context:child", CONTEXT)
    nesting = assertion("relation:nesting", "part_of", child.id, parent.id)
    result = _accept(v5_candidate((child, parent), (nesting,)))
    accepted_child = result.realisation.entity(child.id)

    assert accepted_child is not None
    assert accepted_child.property("temporal_extent") is None


def test_validation_preserves_the_complete_positive_relation_set_exactly() -> None:
    candidate = rich_v5_candidate()
    before = repr(candidate)
    result = _accept(candidate)

    assert result.realisation.relations == candidate.relations
    assert repr(candidate) == before

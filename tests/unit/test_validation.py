"""Deterministic examples for the realisation validation boundary."""

from dataclasses import FrozenInstanceError, replace

import pytest

from caron import (
    CONTEXT,
    METHOD,
    PERSON,
    Accepted,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    OntologySchema,
    Property,
    PropertyDefinition,
    Qualifier,
    RealisationCandidate,
    Rejected,
    RelationAssertion,
    ValidatedRealisation,
    ValueKind,
    YearMonth,
    model4_ontology,
    validate_candidate,
)
from tests.fixtures.minimal import labelled, minimal_candidate


def diagnostic_codes(result: Rejected) -> set[str]:
    return {item.code for item in result.diagnostics}


def test_valid_candidate_becomes_immutable_realisation() -> None:
    result = validate_candidate(model4_ontology(), minimal_candidate())

    assert isinstance(result, Accepted)
    assert result.realisation.entity("person:ada") is not None
    assert len(result.realisation.matching_relations(kind="occurs_in")) == 1
    with pytest.raises(FrozenInstanceError):
        result.realisation.id = "changed"  # type: ignore[misc]


def test_validated_realisation_cannot_be_constructed_directly() -> None:
    candidate = minimal_candidate()

    with pytest.raises(TypeError, match="validate_candidate"):
        ValidatedRealisation(
            id=candidate.id,
            ontology=model4_ontology(),
            entities=candidate.entities,
            relations=candidate.relations,
            coverage=candidate.coverage,
        )


def test_unknown_concept_is_rejected() -> None:
    candidate = minimal_candidate()
    unknown = Entity("unknown:1", "Unknown", (Property("label", "Unknown"),))

    result = validate_candidate(
        model4_ontology(), replace(candidate, entities=candidate.entities + (unknown,))
    )

    assert isinstance(result, Rejected)
    assert "record.unknown_concept" in diagnostic_codes(result)


def test_invalid_relation_endpoint_kind_is_rejected() -> None:
    candidate = minimal_candidate()
    malformed = replace(
        candidate.relations[0],
        source=EntityRef("context:lab"),
    )

    result = validate_candidate(
        model4_ontology(),
        replace(candidate, relations=(malformed, candidate.relations[1])),
    )

    assert isinstance(result, Rejected)
    assert "record.invalid_endpoint_kind" in diagnostic_codes(result)


@pytest.mark.parametrize("missing_kind", ["performs", "occurs_in"])
def test_activity_relation_requirements_are_enforced(missing_kind: str) -> None:
    candidate = minimal_candidate()
    relations = tuple(item for item in candidate.relations if item.kind != missing_kind)

    result = validate_candidate(
        model4_ontology(), replace(candidate, relations=relations)
    )

    assert isinstance(result, Rejected)
    assert "realisation.relation_requirement_below_minimum" in diagnostic_codes(result)


def test_contextual_relation_requires_context_qualifier() -> None:
    candidate = minimal_candidate()
    method = labelled("method:interview", METHOD, "Interviewing")
    learns = RelationAssertion(
        id="relation:learns",
        kind="learns",
        source=EntityRef("person:ada"),
        target=EntityRef(method.id),
    )

    result = validate_candidate(
        model4_ontology(),
        replace(
            candidate,
            entities=candidate.entities + (method,),
            relations=candidate.relations + (learns,),
        ),
    )

    assert isinstance(result, Rejected)
    assert "record.missing_required_qualifier" in diagnostic_codes(result)


def test_contextual_relation_accepts_context_reference() -> None:
    candidate = minimal_candidate()
    method = labelled("method:interview", METHOD, "Interviewing")
    learns = RelationAssertion(
        id="relation:learns",
        kind="learns",
        source=EntityRef("person:ada"),
        target=EntityRef(method.id),
        qualifiers=(Qualifier("context", EntityRef("context:lab")),),
    )

    result = validate_candidate(
        model4_ontology(),
        replace(
            candidate,
            entities=candidate.entities + (method,),
            relations=candidate.relations + (learns,),
        ),
    )

    assert isinstance(result, Accepted)


def test_reference_qualifier_rejects_wrong_concept_kind() -> None:
    candidate = minimal_candidate()
    method = labelled("method:interview", METHOD, "Interviewing")
    learns = RelationAssertion(
        id="relation:learns",
        kind="learns",
        source=EntityRef("person:ada"),
        target=EntityRef(method.id),
        qualifiers=(Qualifier("context", EntityRef("person:ada")),),
    )

    result = validate_candidate(
        model4_ontology(),
        replace(
            candidate,
            entities=candidate.entities + (method,),
            relations=candidate.relations + (learns,),
        ),
    )

    assert isinstance(result, Rejected)
    assert "record.invalid_reference_kind" in diagnostic_codes(result)


def test_integer_property_rejects_boolean_runtime_value() -> None:
    ontology = model4_ontology()
    person = labelled("person:ada", PERSON, "Ada")
    context = Entity(
        "context:lab",
        CONTEXT,
        (Property("label", "Research lab"), Property("start", True)),
    )
    candidate = RealisationCandidate(
        id="realisation:boolean",
        ontology_id=ontology.id,
        ontology_version=ontology.version,
        entities=(person, context),
        relations=(),
        coverage=Coverage(CoverageStatus.SELECTIVE, "Runtime type test"),
    )

    result = validate_candidate(ontology, candidate)

    assert isinstance(result, Rejected)
    assert "record.invalid_value_kind" in diagnostic_codes(result)


def _ontology_with_year_month_person_property() -> OntologySchema:
    ontology = model4_ontology()
    person = ontology.concept(PERSON)
    assert person is not None
    extended_person = replace(
        person,
        properties=person.properties
        + (PropertyDefinition("award_month", ValueKind.YEAR_MONTH),),
    )
    return replace(
        ontology,
        concepts=tuple(
            extended_person if concept.id == PERSON else concept
            for concept in ontology.concepts
        ),
    )


def test_year_month_property_accepts_year_month_value() -> None:
    candidate = minimal_candidate()
    person = candidate.entities[0]
    dated_person = replace(
        person,
        properties=person.properties
        + (Property("award_month", YearMonth.parse("2025-10")),),
    )

    result = validate_candidate(
        _ontology_with_year_month_person_property(),
        replace(candidate, entities=(dated_person, *candidate.entities[1:])),
    )

    assert isinstance(result, Accepted)


def test_year_month_property_rejects_raw_string() -> None:
    candidate = minimal_candidate()
    person = candidate.entities[0]
    dated_person = replace(
        person,
        properties=person.properties + (Property("award_month", "2025-10"),),
    )

    result = validate_candidate(
        _ontology_with_year_month_person_property(),
        replace(candidate, entities=(dated_person, *candidate.entities[1:])),
    )

    assert isinstance(result, Rejected)
    assert "record.invalid_value_kind" in diagnostic_codes(result)

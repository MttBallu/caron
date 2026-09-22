"""Generative conformance checks for the complete 5.0 validator."""

from dataclasses import replace

from hypothesis import assume, given
from hypothesis import strategies as st

from caron import (
    CONTEXT,
    PROPOSITION,
    Accepted,
    Entity,
    EntityRef,
    KnownEnd,
    Property,
    Qualifier,
    RealisationCandidate,
    Rejected,
    TemporalExtent,
    ValueKind,
    YearMonth,
    validate_candidate,
)
from caron.ontology import RelationDefinition, career_ontology_v5_0
from tests.fixtures.v5 import (
    assertion,
    credential_candidate,
    labelled,
    minimal_v5_candidate,
    proposition,
    v5_candidate,
)

SCHEMA = career_ontology_v5_0()
CONCEPT_KINDS = tuple(concept.id for concept in SCHEMA.concepts)
RELATION_KINDS = tuple(relation.kind for relation in SCHEMA.relations)


def _validate(candidate: RealisationCandidate) -> Accepted | Rejected:
    return validate_candidate(SCHEMA, candidate)


def _month(index: int) -> YearMonth:
    year_index, month_index = divmod(index, 12)
    return YearMonth(year_index + 1, month_index + 1)


@given(st.permutations((0, 1, 2)), st.permutations((0, 1)))
def test_validation_is_independent_of_v5_record_order(
    entity_order: list[int], relation_order: list[int]
) -> None:
    candidate = minimal_v5_candidate()
    reordered = replace(
        candidate,
        entities=tuple(candidate.entities[index] for index in entity_order),
        relations=tuple(candidate.relations[index] for index in relation_order),
    )

    result = _validate(reordered)
    assert isinstance(result, Accepted)
    assert result.realisation.entities == reordered.entities
    assert result.realisation.relations == reordered.relations


@given(st.permutations((0, 1)), st.permutations((0, 1)))
def test_equivalent_qualifier_map_orders_remain_one_semantic_fact(
    first_order: list[int], second_order: list[int]
) -> None:
    person = labelled("person", "Person")
    context = labelled("context", CONTEXT)
    organization = labelled("organization", "Organization")
    qualifiers = (
        Qualifier("role", "Contributor"),
        Qualifier("organization", EntityRef(organization.id)),
    )
    first = assertion(
        "first",
        "participates_in",
        person.id,
        context.id,
        *(qualifiers[index] for index in first_order),
    )
    second = assertion(
        "second",
        "participates_in",
        person.id,
        context.id,
        *(qualifiers[index] for index in second_order),
    )

    result = _validate(v5_candidate((person, context, organization), (first, second)))
    assert isinstance(result, Rejected)
    assert [item.code for item in result.diagnostics] == [
        "realisation.duplicate_relation_fact"
    ]


def _endpoint_entity(entity_id: str, kind: str, context_id: str) -> Entity:
    if kind == PROPOSITION:
        return proposition(entity_id, context_id, f"Content for {entity_id}")
    return labelled(entity_id, kind)


def _required_qualifiers(
    definition: RelationDefinition, context_id: str
) -> tuple[Qualifier, ...]:
    qualifiers: list[Qualifier] = []
    for qualifier in definition.qualifiers:
        if not qualifier.required:
            continue
        if qualifier.value_kind is ValueKind.TEXT:
            value: str | EntityRef = "Generated role"
        else:
            value = EntityRef(context_id)
        qualifiers.append(Qualifier(qualifier.name, value))
    return tuple(qualifiers)


@given(
    st.sampled_from(RELATION_KINDS),
    st.sampled_from(CONCEPT_KINDS),
    st.sampled_from(CONCEPT_KINDS),
)
def test_generated_endpoint_families_match_the_schema(
    relation_kind: str, source_kind: str, target_kind: str
) -> None:
    definition = SCHEMA.relation(relation_kind)
    assert definition is not None
    context = labelled("support:context", CONTEXT)
    source = _endpoint_entity("generated:source", source_kind, context.id)
    target = _endpoint_entity("generated:target", target_kind, context.id)
    relation = assertion(
        "generated:relation",
        relation_kind,
        source.id,
        target.id,
        *_required_qualifiers(definition, context.id),
    )

    result = _validate(v5_candidate((context, source, target), (relation,)))
    codes = (
        set()
        if isinstance(result, Accepted)
        else {item.code for item in result.diagnostics}
    )
    endpoints_are_valid = (
        source_kind in definition.source_kinds
        and target_kind in definition.target_kinds
    )
    assert ("record.invalid_endpoint_kind" not in codes) is endpoints_are_valid


@given(
    year=st.integers(min_value=1, max_value=9999),
    month=st.integers(min_value=1, max_value=12),
)
def test_generated_credential_year_month_round_trips(year: int, month: int) -> None:
    award_month = YearMonth(year, month)
    candidate = credential_candidate(awarded_in=award_month)

    result = _validate(candidate)
    assert isinstance(result, Accepted)
    credential = result.realisation.entity("credential:focused")
    assert credential is not None
    assert credential.property("awarded_in") == YearMonth.parse(str(award_month))


@given(
    parent_start=st.integers(min_value=0, max_value=119_940),
    parent_length=st.integers(min_value=0, max_value=24),
    child_start_offset=st.integers(min_value=0, max_value=24),
    child_length=st.integers(min_value=0, max_value=24),
)
def test_generated_temporal_containment_accepts_nested_extents(
    parent_start: int,
    parent_length: int,
    child_start_offset: int,
    child_length: int,
) -> None:
    assume(child_start_offset <= parent_length)
    parent_end = parent_start + parent_length
    child_start = parent_start + child_start_offset
    child_end = min(parent_end, child_start + child_length)
    parent = labelled(
        "parent",
        CONTEXT,
        None,
        Property(
            "temporal_extent",
            TemporalExtent(_month(parent_start), KnownEnd(_month(parent_end))),
        ),
    )
    child = labelled(
        "child",
        CONTEXT,
        None,
        Property(
            "temporal_extent",
            TemporalExtent(_month(child_start), KnownEnd(_month(child_end))),
        ),
    )
    nesting = assertion("nested", "part_of", child.id, parent.id)

    assert isinstance(_validate(v5_candidate((child, parent), (nesting,))), Accepted)


@given(
    parent_start=st.integers(min_value=0, max_value=119_940),
    parent_length=st.integers(min_value=0, max_value=12),
    gap=st.integers(min_value=1, max_value=12),
)
def test_generated_temporal_containment_rejects_impossible_extents(
    parent_start: int, parent_length: int, gap: int
) -> None:
    parent_end = parent_start + parent_length
    child_month = parent_end + gap
    parent = labelled(
        "parent",
        CONTEXT,
        None,
        Property(
            "temporal_extent",
            TemporalExtent(_month(parent_start), KnownEnd(_month(parent_end))),
        ),
    )
    child = labelled(
        "child",
        CONTEXT,
        None,
        Property(
            "temporal_extent",
            TemporalExtent(_month(child_month), KnownEnd(_month(child_month))),
        ),
    )
    nesting = assertion("nested", "part_of", child.id, parent.id)

    result = _validate(v5_candidate((child, parent), (nesting,)))
    assert isinstance(result, Rejected)
    assert "realisation.temporal_containment_impossible" in {
        item.code for item in result.diagnostics
    }

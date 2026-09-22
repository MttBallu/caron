"""Focused tests for the realisation-wide Career Ontology 5.0 rules."""

from dataclasses import replace

import pytest

from caron import (
    Accepted,
    Coverage,
    CoverageStatus,
    Entity,
    EntityRef,
    KnownEnd,
    OngoingAsOf,
    Property,
    Qualifier,
    RealisationCandidate,
    Rejected,
    RelationAssertion,
    TemporalExtent,
    UnknownEnd,
    YearMonth,
    validate_candidate,
)
from caron._career_v5_invariants import semantic_relation_key
from caron.ontology import career_ontology_v5_0


def _entity(
    identifier: str,
    kind: str,
    *,
    context: str | None = None,
    extent: TemporalExtent | None = None,
) -> Entity:
    properties: tuple[Property, ...] = (Property("label", identifier),)
    if context is not None:
        properties += (
            Property("content", f"Content of {identifier}"),
            Property("context", EntityRef(context)),
        )
    if extent is not None:
        properties += (Property("temporal_extent", extent),)
    return Entity(identifier, kind, properties)


def _relation(
    identifier: str,
    kind: str,
    source: str,
    target: str,
    qualifiers: tuple[Qualifier, ...] = (),
) -> RelationAssertion:
    return RelationAssertion(
        identifier, kind, EntityRef(source), EntityRef(target), qualifiers
    )


def _candidate(
    entities: tuple[Entity, ...],
    relations: tuple[RelationAssertion, ...] = (),
) -> RealisationCandidate:
    return RealisationCandidate(
        id="phase-4-test",
        ontology_id="caron.career-model",
        ontology_version="5.0",
        entities=entities,
        relations=relations,
        coverage=Coverage(CoverageStatus.SELECTIVE, "Phase 4 focused fixture"),
    )


def _result(candidate: RealisationCandidate) -> Accepted | Rejected:
    return validate_candidate(career_ontology_v5_0(), candidate)


def _codes(result: Rejected) -> list[str]:
    return [diagnostic.code for diagnostic in result.diagnostics]


def _assert_rejected(candidate: RealisationCandidate, code: str) -> Rejected:
    result = _result(candidate)
    assert isinstance(result, Rejected)
    assert code in _codes(result)
    return result


def _activity_graph(
    context_id: str = "context",
) -> tuple[tuple[Entity, ...], tuple[RelationAssertion, ...]]:
    entities = (
        _entity("person", "Person"),
        _entity(context_id, "Context"),
        _entity("activity", "Activity"),
    )
    relations = (
        _relation("performs", "performs", "person", "activity"),
        _relation("occurs", "occurs_in", "activity", context_id),
    )
    return entities, relations


def _bears_on_graph(
    source_context: str,
    target_context: str,
    *,
    part_of: tuple[RelationAssertion, ...] = (),
    outcome_kind: str = "results_in",
    include_outcome: bool = True,
    include_aim: bool = True,
) -> tuple[tuple[Entity, ...], tuple[RelationAssertion, ...]]:
    context_ids = tuple(dict.fromkeys((source_context, target_context)))
    activity_entities, activity_relations = _activity_graph(source_context)
    entities = (
        activity_entities[0],
        *(_entity(identifier, "Context") for identifier in context_ids),
        activity_entities[2],
        _entity("source-proposition", "Proposition", context=source_context),
        _entity("target-proposition", "Proposition", context=target_context),
    )
    relations = (*activity_relations, *part_of)
    if include_outcome:
        relations += (
            _relation("outcome", outcome_kind, "activity", "source-proposition"),
        )
    if include_aim:
        relations += (
            _relation("aim", "aims_at", target_context, "target-proposition"),
        )
    relations += (
        _relation("bears", "bears_on", "source-proposition", "target-proposition"),
    )
    return entities, relations


def test_semantic_key_excludes_record_id_and_qualifier_order() -> None:
    first = _relation(
        "first",
        "participates_in",
        "person",
        "context",
        (
            Qualifier("role", "Contributor"),
            Qualifier("organization", EntityRef("organization")),
        ),
    )
    second = replace(first, id="second", qualifiers=tuple(reversed(first.qualifiers)))

    assert semantic_relation_key(first) == semantic_relation_key(second)


def test_semantic_key_preserves_typed_qualifier_values() -> None:
    text = _relation(
        "text", "participates_in", "person", "context", (Qualifier("role", "1"),)
    )
    integer = replace(text, id="integer", qualifiers=(Qualifier("role", 1),))
    reference = replace(
        text, id="reference", qualifiers=(Qualifier("role", EntityRef("1")),)
    )

    assert (
        len(
            {
                semantic_relation_key(text),
                semantic_relation_key(integer),
                semantic_relation_key(reference),
            }
        )
        == 3
    )


def test_duplicate_plain_relation_fact_is_rejected() -> None:
    entities = (_entity("child", "Context"), _entity("parent", "Context"))
    relation = _relation("first", "part_of", "child", "parent")
    result = _assert_rejected(
        _candidate(entities, (relation, replace(relation, id="second"))),
        "realisation.duplicate_relation_fact",
    )

    duplicate = next(
        item
        for item in result.diagnostics
        if item.code == "realisation.duplicate_relation_fact"
    )
    assert duplicate.record_id == "second"
    assert "first" in duplicate.message


def test_qualifier_order_does_not_create_a_second_fact() -> None:
    entities = (
        _entity("person", "Person"),
        _entity("context", "Context"),
        _entity("organization", "Organization"),
    )
    relation = _relation(
        "first",
        "participates_in",
        "person",
        "context",
        (
            Qualifier("role", "Contributor"),
            Qualifier("organization", EntityRef("organization")),
        ),
    )
    duplicate = replace(
        relation, id="second", qualifiers=tuple(reversed(relation.qualifiers))
    )

    _assert_rejected(
        _candidate(entities, (relation, duplicate)),
        "realisation.duplicate_relation_fact",
    )


def test_distinct_qualifier_mappings_are_distinct_facts() -> None:
    entities = (_entity("person", "Person"), _entity("context", "Context"))
    first = _relation(
        "first",
        "participates_in",
        "person",
        "context",
        (Qualifier("role", "Contributor"),),
    )
    second = replace(first, id="second", qualifiers=(Qualifier("role", "Lead"),))

    assert isinstance(_result(_candidate(entities, (first, second))), Accepted)


def test_cardinality_counts_duplicate_records_as_one_fact() -> None:
    entities, relations = _activity_graph()
    duplicate = replace(relations[1], id="duplicate-occurs")

    result = _assert_rejected(
        _candidate(entities, (*relations, duplicate)),
        "realisation.duplicate_relation_fact",
    )
    assert "realisation.relation_requirement_above_maximum" not in _codes(result)


def test_cardinality_counts_distinct_facts() -> None:
    entities, relations = _activity_graph()
    entities += (_entity("other-context", "Context"),)
    other = _relation("other-occurs", "occurs_in", "activity", "other-context")

    result = _assert_rejected(
        _candidate(entities, (*relations, other)),
        "realisation.relation_requirement_above_maximum",
    )
    assert "realisation.duplicate_relation_fact" not in _codes(result)


@pytest.mark.parametrize("distinct_recipient", (False, True))
def test_credential_cardinality_counts_semantic_facts(
    distinct_recipient: bool,
) -> None:
    entities = (
        _entity("credential", "Credential"),
        _entity("person", "Person"),
        _entity("other-person", "Person"),
        _entity("organization", "Organization"),
        _entity("context", "Context"),
    )
    required = (
        _relation("awarded-to", "awarded_to", "credential", "person"),
        _relation("awarded-by", "awarded_by", "credential", "organization"),
        _relation("obtained", "obtained_through", "credential", "context"),
    )
    extra = replace(
        required[0],
        id="extra-awarded-to",
        target=EntityRef("other-person" if distinct_recipient else "person"),
    )

    result = _result(_candidate(entities, (*required, extra)))

    assert isinstance(result, Rejected)
    if distinct_recipient:
        assert "realisation.relation_requirement_above_maximum" in _codes(result)
        assert "realisation.duplicate_relation_fact" not in _codes(result)
    else:
        assert "realisation.duplicate_relation_fact" in _codes(result)
        assert "realisation.relation_requirement_above_maximum" not in _codes(result)


@pytest.mark.parametrize(
    ("kind", "concept", "code"),
    (
        ("part_of", "Context", "realisation.part_of_cycle"),
        (
            "suborganization_of",
            "Organization",
            "realisation.suborganization_of_cycle",
        ),
    ),
)
def test_structural_self_loops_are_rejected(kind: str, concept: str, code: str) -> None:
    entity = _entity("node", concept)
    _assert_rejected(
        _candidate((entity,), (_relation("loop", kind, "node", "node"),)), code
    )


@pytest.mark.parametrize(
    ("kind", "concept", "code"),
    (
        ("part_of", "Context", "realisation.part_of_cycle"),
        (
            "suborganization_of",
            "Organization",
            "realisation.suborganization_of_cycle",
        ),
    ),
)
def test_long_structural_cycles_are_rejected_deterministically(
    kind: str, concept: str, code: str
) -> None:
    entities = tuple(_entity(identifier, concept) for identifier in ("a", "b", "c"))
    relations = (
        _relation("edge-2", kind, "b", "c"),
        _relation("edge-3", kind, "c", "a"),
        _relation("edge-1", kind, "a", "b"),
    )

    forward = _assert_rejected(_candidate(entities, relations), code)
    reverse = _assert_rejected(
        _candidate(tuple(reversed(entities)), tuple(reversed(relations))), code
    )

    forward_cycles = tuple(item for item in forward.diagnostics if item.code == code)
    reverse_cycles = tuple(item for item in reverse.diagnostics if item.code == code)
    assert forward_cycles == reverse_cycles
    assert [item.record_id for item in forward_cycles] == ["edge-1", "edge-2", "edge-3"]


@pytest.mark.parametrize(
    "concept,kind", (("Context", "part_of"), ("Organization", "suborganization_of"))
)
def test_multiple_parent_dags_are_valid(concept: str, kind: str) -> None:
    entities = tuple(
        _entity(identifier, concept)
        for identifier in ("child", "left", "right", "root")
    )
    relations = (
        _relation("child-left", kind, "child", "left"),
        _relation("child-right", kind, "child", "right"),
        _relation("left-root", kind, "left", "root"),
        _relation("right-root", kind, "right", "root"),
    )

    assert isinstance(_result(_candidate(entities, relations)), Accepted)


def test_aim_must_match_proposition_context() -> None:
    entities = (
        _entity("local", "Context"),
        _entity("other", "Context"),
        _entity("aim", "Proposition", context="local"),
    )
    relation = _relation("aims", "aims_at", "other", "aim")

    _assert_rejected(
        _candidate(entities, (relation,)),
        "realisation.aims_at_context_mismatch",
    )


def test_same_context_aim_and_duplicate_content_across_contexts_are_valid() -> None:
    entities = (
        _entity("left", "Context"),
        _entity("right", "Context"),
        _entity("left-aim", "Proposition", context="left"),
        _entity("right-aim", "Proposition", context="right"),
    )
    left = entities[2]
    right = replace(
        entities[3],
        properties=(
            entities[3].properties[0],
            left.properties[1],
            entities[3].properties[2],
        ),
    )
    candidate = _candidate(
        (*entities[:3], right),
        (
            _relation("left-purpose", "aims_at", "left", "left-aim"),
            _relation("right-purpose", "aims_at", "right", "right-aim"),
        ),
    )

    assert isinstance(_result(candidate), Accepted)


@pytest.mark.parametrize(
    "outcome_kind", ("results_in", "establishes", "supports", "contradicts")
)
def test_bears_on_accepts_each_explicit_outcome_role(outcome_kind: str) -> None:
    entities, relations = _bears_on_graph(
        "context", "context", outcome_kind=outcome_kind
    )
    assert isinstance(_result(_candidate(entities, relations)), Accepted)


def test_bears_on_requires_explicit_source_outcome() -> None:
    entities, relations = _bears_on_graph("context", "context", include_outcome=False)
    _assert_rejected(
        _candidate(entities, relations),
        "realisation.bears_on_source_not_outcome",
    )


def test_bears_on_requires_explicit_target_aim() -> None:
    entities, relations = _bears_on_graph("context", "context", include_aim=False)
    _assert_rejected(
        _candidate(entities, relations),
        "realisation.bears_on_target_not_aim",
    )


def test_bears_on_rejects_self_reference() -> None:
    entities, relations = _activity_graph()
    proposition = _entity("proposition", "Proposition", context="context")
    relations += (
        _relation("outcome", "results_in", "activity", "proposition"),
        _relation("aim", "aims_at", "context", "proposition"),
        _relation("bears", "bears_on", "proposition", "proposition"),
    )
    _assert_rejected(
        _candidate((*entities, proposition), relations),
        "realisation.bears_on_self_reference",
    )


def test_bears_on_accepts_nested_source_context() -> None:
    nesting = (_relation("nested", "part_of", "source-context", "target-context"),)
    entities, relations = _bears_on_graph(
        "source-context", "target-context", part_of=nesting
    )
    assert isinstance(_result(_candidate(entities, relations)), Accepted)


@pytest.mark.parametrize("case", ("siblings", "reversed"))
def test_bears_on_rejects_incompatible_context_direction(case: str) -> None:
    nesting: tuple[RelationAssertion, ...]
    if case == "siblings":
        nesting = (
            _relation("source-parent", "part_of", "source-context", "parent"),
            _relation("target-parent", "part_of", "target-context", "parent"),
        )
        entities, relations = _bears_on_graph(
            "source-context", "target-context", part_of=nesting
        )
        entities += (_entity("parent", "Context"),)
    else:
        nesting = (
            _relation("target-source", "part_of", "target-context", "source-context"),
        )
        entities, relations = _bears_on_graph(
            "source-context", "target-context", part_of=nesting
        )

    _assert_rejected(
        _candidate(entities, relations),
        "realisation.bears_on_incompatible_context",
    )


def test_roles_do_not_infer_bears_on() -> None:
    entities, relations = _bears_on_graph("context", "context")
    candidate = _candidate(
        entities,
        tuple(relation for relation in relations if relation.kind != "bears_on"),
    )

    result = _result(candidate)
    assert isinstance(result, Accepted)
    assert all(relation.kind != "bears_on" for relation in result.realisation.relations)


def test_activity_outcome_may_cross_contexts_without_changing_locality() -> None:
    activity_entities, activity_relations = _activity_graph("activity-context")
    proposition = _entity("proposition", "Proposition", context="proposition-context")
    candidate = _candidate(
        (
            *activity_entities,
            _entity("proposition-context", "Context"),
            proposition,
        ),
        (
            *activity_relations,
            _relation("outcome", "results_in", "activity", "proposition"),
        ),
    )

    result = _result(candidate)
    assert isinstance(result, Accepted)
    assert result.realisation.entity("proposition") == proposition


def _temporal_context(
    identifier: str, start: str, end: str | None, *, ongoing: bool = False
) -> Entity:
    if end is None:
        extent = TemporalExtent(YearMonth.parse(start), UnknownEnd())
    elif ongoing:
        extent = TemporalExtent(
            YearMonth.parse(start), OngoingAsOf(YearMonth.parse(end))
        )
    else:
        extent = TemporalExtent(YearMonth.parse(start), KnownEnd(YearMonth.parse(end)))
    return _entity(identifier, "Context", extent=extent)


@pytest.mark.parametrize(
    ("child", "parent"),
    (
        (
            _temporal_context("child", "2023-01", "2023-12"),
            _temporal_context("parent", "2022-01", "2024-12"),
        ),
        (
            _temporal_context("child", "2023-01", None),
            _temporal_context("parent", "2022-01", "2024-12"),
        ),
        (
            _temporal_context("child", "2023-01", "2024-01", ongoing=True),
            _temporal_context("parent", "2022-01", None),
        ),
        (
            _temporal_context("child", "2023-01", "2024-01", ongoing=True),
            _temporal_context("parent", "2022-01", "2025-01", ongoing=True),
        ),
    ),
)
def test_known_unknown_and_ongoing_nested_extents_are_valid(
    child: Entity, parent: Entity
) -> None:
    candidate = _candidate(
        (child, parent), (_relation("nested", "part_of", "child", "parent"),)
    )
    before = repr(candidate)
    result = _result(candidate)

    assert isinstance(result, Accepted)
    assert repr(candidate) == before
    assert result.realisation.entity("child") == child
    assert result.realisation.entity("parent") == parent


@pytest.mark.parametrize(
    ("child", "parent"),
    (
        (
            _temporal_context("child", "2021-12", "2022-06"),
            _temporal_context("parent", "2022-01", "2024-12"),
        ),
        (
            _temporal_context("child", "2023-01", "2025-01", ongoing=True),
            _temporal_context("parent", "2022-01", "2024-12"),
        ),
    ),
)
def test_incompatible_nested_extents_are_rejected(
    child: Entity, parent: Entity
) -> None:
    _assert_rejected(
        _candidate(
            (child, parent), (_relation("nested", "part_of", "child", "parent"),)
        ),
        "realisation.temporal_containment_impossible",
    )


def test_transitive_temporal_containment_is_enforced() -> None:
    entities = (
        _temporal_context("child", "2025-01", "2025-02"),
        _entity("middle", "Context"),
        _temporal_context("parent", "2022-01", "2024-12"),
    )
    relations = (
        _relation("child-middle", "part_of", "child", "middle"),
        _relation("middle-parent", "part_of", "middle", "parent"),
    )
    _assert_rejected(
        _candidate(entities, relations),
        "realisation.temporal_containment_impossible",
    )


def test_undated_context_requires_nonempty_multi_parent_intersection() -> None:
    entities = (
        _entity("child", "Context"),
        _temporal_context("early", "2020-01", "2020-12"),
        _temporal_context("late", "2022-01", "2022-12"),
    )
    relations = (
        _relation("child-early", "part_of", "child", "early"),
        _relation("child-late", "part_of", "child", "late"),
    )
    _assert_rejected(
        _candidate(entities, relations),
        "realisation.temporal_containment_impossible",
    )


def test_undated_context_accepts_overlapping_multiple_parents() -> None:
    child = _entity("child", "Context")
    entities = (
        child,
        _temporal_context("left", "2020-01", "2021-06"),
        _temporal_context("right", "2021-01", "2022-12"),
    )
    relations = (
        _relation("child-left", "part_of", "child", "left"),
        _relation("child-right", "part_of", "child", "right"),
    )

    result = _result(_candidate(entities, relations))
    assert isinstance(result, Accepted)
    assert result.realisation.entity("child") == child


def test_incomplete_temporal_information_is_valid_and_not_copied() -> None:
    activity_entities, activity_relations = _activity_graph("child")
    entities = (
        activity_entities[0],
        _entity("child", "Context"),
        _temporal_context("parent", "2022-01", None),
        activity_entities[2],
    )
    relations = (
        *activity_relations,
        _relation("child-parent", "part_of", "child", "parent"),
    )
    result = _result(_candidate(entities, relations))

    assert isinstance(result, Accepted)
    assert result.realisation.entity("child").property("temporal_extent") is None  # type: ignore[union-attr]
    assert result.realisation.entity("activity").property("temporal_extent") is None  # type: ignore[union-attr]


def test_activity_occurrence_inherits_context_constraints_without_an_extent() -> None:
    activity_entities, activity_relations = _activity_graph("child")
    entities = (
        activity_entities[0],
        _temporal_context("child", "2025-01", "2025-02"),
        _temporal_context("parent", "2022-01", "2024-12"),
        activity_entities[2],
    )
    relations = (
        *activity_relations,
        _relation("child-parent", "part_of", "child", "parent"),
    )
    _assert_rejected(
        _candidate(entities, relations),
        "realisation.temporal_containment_impossible",
    )

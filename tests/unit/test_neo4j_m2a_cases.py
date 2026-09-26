"""Validate frozen cases and compare their overlap with the private algebra."""

import pytest

from caron import Accepted, career_ontology_v5_0, validate_candidate
from caron._query_algebra import (
    EntityConstant,
    EntityValue,
    Join,
    QualifierPattern,
    RelationPattern,
    RelationValue,
    Variable,
    evaluate_plan,
)
from caron.adapters.neo4j_results import ActivityResourceMatch, LearningMatch, Match
from caron.entities import EntityRef
from tests.fixtures.neo4j_m2a import CASES, Case
from tests.fixtures.v5 import v5_candidate


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_frozen_case_is_accepted_and_private_algebra_agrees(case: Case) -> None:
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
    context = Variable("context")
    activity = Variable("activity")
    learning_id = Variable("learning_id")
    performs_id = Variable("performs_id")
    occurs_id = Variable("occurs_id")
    resource_id = Variable("resource_id")
    resource_kind = Variable("resource_kind")
    learning = evaluate_plan(
        source,
        RelationPattern(
            frozenset({"learns"}),
            EntityConstant("p"),
            EntityConstant("x"),
            relation_variable=learning_id,
            qualifiers=(QualifierPattern("context", context),),
        ),
    )
    kinds = {
        "Technology": frozenset({"uses_technology"}),
        "Language": frozenset({"uses_language"}),
        "Method": frozenset({"applies", "draws_on"}),
        "Subject": frozenset({"draws_on"}),
    }[source.entity("x").kind]  # type: ignore[union-attr]
    practical = evaluate_plan(
        source,
        Join(
            (
                RelationPattern(
                    frozenset({"performs"}),
                    EntityConstant("p"),
                    activity,
                    relation_variable=performs_id,
                ),
                RelationPattern(
                    frozenset({"occurs_in"}),
                    activity,
                    context,
                    relation_variable=occurs_id,
                ),
                RelationPattern(
                    kinds,
                    activity,
                    EntityConstant("x"),
                    relation_variable=resource_id,
                    kind_variable=resource_kind,
                ),
            )
        ),
    )
    actual: list[Match] = []
    for row in learning.rows:
        context_value = row.value(context)
        assertion_value = row.value(learning_id)
        assert isinstance(context_value, EntityValue)
        assert isinstance(assertion_value, RelationValue)
        assert row.witness.relations == (assertion_value.relation_id,)
        actual.append(
            LearningMatch(
                EntityRef("p"),
                EntityRef("x"),
                EntityRef(context_value.entity_id),
                assertion_value.relation_id,
            )
        )
    for row in practical.rows:
        activity_value = row.value(activity)
        context_value = row.value(context)
        kind_value = row.value(resource_kind)
        p_value = row.value(performs_id)
        o_value = row.value(occurs_id)
        u_value = row.value(resource_id)
        assert isinstance(activity_value, EntityValue)
        assert isinstance(context_value, EntityValue)
        assert isinstance(kind_value, str)
        assert isinstance(p_value, RelationValue)
        assert isinstance(o_value, RelationValue)
        assert isinstance(u_value, RelationValue)
        assert set(row.witness.relations) == {
            p_value.relation_id,
            o_value.relation_id,
            u_value.relation_id,
        }
        actual.append(
            ActivityResourceMatch(
                EntityRef("p"),
                EntityRef(activity_value.entity_id),
                EntityRef("x"),
                EntityRef(context_value.entity_id),
                kind_value,
                p_value.relation_id,
                o_value.relation_id,
                u_value.relation_id,
            )
        )
    assert len(actual) == len(case.expected)
    assert set(actual) == set(case.expected)

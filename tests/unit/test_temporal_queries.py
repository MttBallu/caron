"""Deterministic tests for the first temporal query slice."""

from dataclasses import FrozenInstanceError, replace

import pytest

from caron import (
    ACTIVITY,
    CONTEXT,
    Accepted,
    CoveredMonthKind,
    EntityRef,
    Property,
    RelationAssertion,
    TemporalClassification,
    TemporalExtent,
    TemporalMatchMode,
    TemporalWindow,
    ValidatedRealisation,
    before,
    covered_months,
    overlaps,
    select_activities_in_window,
    validate_candidate,
)
from caron.ontology import career_ontology_v5_0
from tests.fixtures.temporal_v5 import temporal_v5_candidate
from tests.fixtures.v5 import labelled


def _realisation() -> ValidatedRealisation:
    result = validate_candidate(career_ontology_v5_0(), temporal_v5_candidate())
    assert isinstance(result, Accepted)
    return result.realisation


@pytest.mark.parametrize(
    ("context_id", "kind", "minimum", "maximum"),
    [
        ("context:alice-project", CoveredMonthKind.EXACT, 4, 4),
        ("context:phd", CoveredMonthKind.EXACT, 37, 37),
        ("context:synthetic-data-work", CoveredMonthKind.BOUNDED, 1, 37),
        ("context:jax-geopro", CoveredMonthKind.EXACT_AS_OF, 6, 6),
    ],
)
def test_covered_month_results_preserve_epistemic_kind(
    context_id: str,
    kind: CoveredMonthKind,
    minimum: int,
    maximum: int,
) -> None:
    result = covered_months(_realisation(), context_id)

    assert result.kind is kind
    assert result.minimum == minimum
    assert result.maximum == maximum


def test_ongoing_count_is_tied_to_recorded_observation() -> None:
    result = covered_months(_realisation(), "context:jax-geopro")

    assert str(result.as_of) == "2026-09"


def test_synthetic_count_retains_part_of_witness() -> None:
    result = covered_months(_realisation(), "context:synthetic-data-work")

    assert result.witness.relations == ("relation:synthetic-part-of-phd",)
    assert (
        EntityRef("context:phd"),
        "temporal_extent",
    ) in result.witness.properties


def test_direct_temporal_witness_names_only_asserted_property() -> None:
    result = covered_months(_realisation(), "context:alice-project")

    assert result.witness.entities == (EntityRef("context:alice-project"),)
    assert result.witness.relations == ()
    assert result.witness.properties == (
        (EntityRef("context:alice-project"), "temporal_extent"),
    )


def test_context_and_activity_order_are_entailed_through_composition() -> None:
    realisation = _realisation()

    context_order = before(
        realisation,
        "context:alice-project",
        "context:synthetic-data-work",
    )
    activity_order = before(
        realisation,
        "activity:analyse-alice-data",
        "activity:build-synthetic-dataset",
    )

    assert context_order.classification is TemporalClassification.ENTAILED
    assert activity_order.classification is TemporalClassification.ENTAILED
    assert "relation:synthetic-part-of-phd" in activity_order.witness.relations
    assert "relation:alice-activity-occurs-in" in activity_order.witness.relations
    assert "relation:synthetic-activity-occurs-in" in activity_order.witness.relations


def test_python_activity_order_extends_to_jax_geopro() -> None:
    result = before(
        _realisation(),
        "activity:build-synthetic-dataset",
        "activity:implement-discrete-measure-losses",
    )

    assert result.classification is TemporalClassification.ENTAILED


def test_overlap_distinguishes_disjoint_and_contained_contexts() -> None:
    realisation = _realisation()

    disjoint = overlaps(realisation, "context:alice-project", "context:phd")
    contained = overlaps(
        realisation,
        "context:synthetic-data-work",
        "context:phd",
    )

    assert disjoint.classification is TemporalClassification.EXCLUDED
    assert contained.classification is TemporalClassification.ENTAILED


def test_definite_window_selects_only_entailed_activity() -> None:
    view = select_activities_in_window(
        _realisation(),
        TemporalWindow.closed("2021-11", "2022-02"),
    )

    assert tuple(binding.entity.entity_id for binding in view.bindings) == (
        "activity:analyse-alice-data",
    )
    assert {relation.kind for relation in view.relations} == {"occurs_in"}
    assert view.ontology.version == "5.0"


def test_possible_window_returns_partial_context_matches() -> None:
    view = select_activities_in_window(
        _realisation(),
        TemporalWindow.closed("2022-01", "2022-12"),
        mode=TemporalMatchMode.POSSIBLE,
    )

    assert {binding.entity.entity_id for binding in view.bindings} == {
        "activity:analyse-alice-data",
        "activity:build-synthetic-dataset",
    }
    assert {result.classification for result in view.results} == {
        TemporalClassification.POSSIBLE
    }


def test_parent_window_entails_nested_activity_match() -> None:
    view = select_activities_in_window(
        _realisation(),
        TemporalWindow.closed("2022-10", "2025-10"),
    )

    assert tuple(binding.entity.entity_id for binding in view.bindings) == (
        "activity:build-synthetic-dataset",
    )
    assert {relation.id for relation in view.relations} == {
        "relation:synthetic-activity-occurs-in",
        "relation:synthetic-part-of-phd",
    }
    assert all(relation.kind != "before" for relation in view.relations)


def test_temporal_graph_view_only_projects_asserted_records() -> None:
    realisation = _realisation()
    view = select_activities_in_window(
        realisation,
        TemporalWindow.closed("2022-10", "2025-10"),
    )

    assert set(view.relations) <= set(realisation.relations)
    assert set(view.entities) <= set(realisation.entities)
    assert {relation.kind for relation in view.relations} == {
        "occurs_in",
        "part_of",
    }
    assert {relation.kind for relation in view.relations}.isdisjoint(
        {"before", "overlaps"}
    )
    activity = view.entity("activity:build-synthetic-dataset")
    assert activity is not None
    assert activity.property("temporal_extent") is None


def test_ongoing_observation_does_not_cap_activity_time() -> None:
    window = TemporalWindow.closed("2026-04", "2026-09")

    definite = select_activities_in_window(_realisation(), window)
    possible = select_activities_in_window(
        _realisation(),
        window,
        mode=TemporalMatchMode.POSSIBLE,
    )

    assert "activity:implement-discrete-measure-losses" not in {
        binding.entity.entity_id for binding in definite.bindings
    }
    jax_match = next(
        result
        for result in possible.results
        if result.entity == EntityRef("activity:implement-discrete-measure-losses")
    )
    assert jax_match.classification is TemporalClassification.POSSIBLE


def test_unconstrained_activity_is_unknown_and_excluded_by_default() -> None:
    candidate = temporal_v5_candidate()
    context = labelled("context:undated", CONTEXT, "Undated work")
    activity = labelled("activity:undated", ACTIVITY, "Undated activity")
    performs = RelationAssertion(
        "relation:performs-undated",
        "performs",
        EntityRef("person:matteo"),
        EntityRef(activity.id),
    )
    occurs_in = RelationAssertion(
        "relation:undated-occurs-in",
        "occurs_in",
        EntityRef(activity.id),
        EntityRef(context.id),
    )
    extended = replace(
        candidate,
        entities=candidate.entities + (context, activity),
        relations=candidate.relations + (performs, occurs_in),
    )
    validated = validate_candidate(career_ontology_v5_0(), extended)
    assert isinstance(validated, Accepted)

    default_view = select_activities_in_window(
        validated.realisation,
        TemporalWindow.closed("2022-01", "2022-12"),
        mode=TemporalMatchMode.POSSIBLE,
    )
    diagnostic_view = select_activities_in_window(
        validated.realisation,
        TemporalWindow.closed("2022-01", "2022-12"),
        include_unknown=True,
    )

    assert "activity:undated" not in {
        binding.entity.entity_id for binding in default_view.bindings
    }
    unknown = next(
        result
        for result in diagnostic_view.results
        if result.entity == EntityRef("activity:undated")
    )
    assert unknown.classification is TemporalClassification.UNKNOWN


def test_graph_view_is_immutable() -> None:
    view = select_activities_in_window(
        _realisation(),
        TemporalWindow.closed("2021-11", "2022-02"),
    )

    with pytest.raises(FrozenInstanceError):
        view.query_name = "changed"  # type: ignore[misc]


def test_unknown_end_count_is_indeterminate() -> None:
    candidate = temporal_v5_candidate()
    context = labelled("context:open", CONTEXT, "Open-ended work")
    context = replace(
        context,
        properties=context.properties
        + (
            Property(
                "temporal_extent",
                TemporalExtent.unknown_end("2024-01"),
            ),
        ),
    )
    validated = validate_candidate(
        career_ontology_v5_0(),
        replace(candidate, entities=candidate.entities + (context,)),
    )
    assert isinstance(validated, Accepted)

    result = covered_months(validated.realisation, context.id)

    assert result.kind is CoveredMonthKind.INDETERMINATE
    assert result.minimum == 1
    assert result.maximum is None

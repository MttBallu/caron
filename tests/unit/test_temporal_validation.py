"""Deterministic tests for ontology 5.0 temporal validation."""

from dataclasses import replace

from caron import (
    CONTEXT,
    Accepted,
    Entity,
    EntityRef,
    KnownEnd,
    Property,
    Rejected,
    RelationAssertion,
    TemporalExtent,
    YearMonth,
    validate_candidate,
    validate_ontology,
)
from caron.ontology import career_ontology_v5_0
from examples.temporal_queries import build_candidate as temporal_candidate


def _codes(result: Rejected) -> set[str]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def test_v5_schema_has_the_temporal_extent_property() -> None:
    ontology = career_ontology_v5_0()
    context = ontology.concept(CONTEXT)

    assert validate_ontology(ontology) == ()
    assert ontology.version == "5.0"
    assert context is not None
    assert context.property_definition("start") is None
    assert context.property_definition("temporal_extent") is not None


def test_reference_temporal_candidate_is_valid() -> None:
    assert isinstance(
        validate_candidate(career_ontology_v5_0(), temporal_candidate()),
        Accepted,
    )


def test_known_end_before_start_is_rejected() -> None:
    candidate = temporal_candidate()
    alice = candidate.entities[1]
    invalid_extent = TemporalExtent(
        YearMonth.parse("2022-02"),
        KnownEnd(YearMonth.parse("2021-11")),
    )
    invalid_alice = replace(
        alice,
        properties=(
            Property("label", "ALICE data-analysis project"),
            Property("temporal_extent", invalid_extent),
        ),
    )

    result = validate_candidate(
        career_ontology_v5_0(),
        replace(
            candidate,
            entities=(candidate.entities[0], invalid_alice, *candidate.entities[2:]),
        ),
    )

    assert isinstance(result, Rejected)
    assert "record.invalid_temporal_extent" in _codes(result)


def test_child_extent_outside_parent_is_rejected() -> None:
    candidate = temporal_candidate()
    synthetic = candidate.entities[3]
    invalid_synthetic = replace(
        synthetic,
        properties=synthetic.properties
        + (
            Property(
                "temporal_extent",
                TemporalExtent.closed("2025-11", "2026-01"),
            ),
        ),
    )
    result = validate_candidate(
        career_ontology_v5_0(),
        replace(
            candidate,
            entities=(
                *candidate.entities[:3],
                invalid_synthetic,
                *candidate.entities[4:],
            ),
        ),
    )

    assert isinstance(result, Rejected)
    assert "realisation.temporal_containment_impossible" in _codes(result)


def test_transitive_ancestor_containment_is_enforced() -> None:
    candidate = temporal_candidate()
    nested = Entity(
        "context:nested",
        CONTEXT,
        (
            Property("label", "Nested context"),
            Property("temporal_extent", TemporalExtent.closed("2026-01", "2026-02")),
        ),
    )
    relation = RelationAssertion(
        "relation:nested-part-of-synthetic",
        "part_of",
        EntityRef(nested.id),
        EntityRef("context:synthetic-data-work"),
    )
    result = validate_candidate(
        career_ontology_v5_0(),
        replace(
            candidate,
            entities=candidate.entities + (nested,),
            relations=candidate.relations + (relation,),
        ),
    )

    assert isinstance(result, Rejected)
    assert "realisation.temporal_containment_impossible" in _codes(result)


def test_undated_child_cannot_fit_inside_disjoint_parents() -> None:
    candidate = temporal_candidate()
    later_parent = Entity(
        "context:later-parent",
        CONTEXT,
        (
            Property("label", "Later parent"),
            Property("temporal_extent", TemporalExtent.closed("2027-01", "2027-02")),
        ),
    )
    second_parent = RelationAssertion(
        "relation:synthetic-part-of-later",
        "part_of",
        EntityRef("context:synthetic-data-work"),
        EntityRef(later_parent.id),
    )
    result = validate_candidate(
        career_ontology_v5_0(),
        replace(
            candidate,
            entities=candidate.entities + (later_parent,),
            relations=candidate.relations + (second_parent,),
        ),
    )

    assert isinstance(result, Rejected)
    assert "realisation.temporal_containment_impossible" in _codes(result)


def test_temporal_extent_property_rejects_a_raw_string() -> None:
    candidate = temporal_candidate()
    context = Entity(
        "context:raw-date",
        CONTEXT,
        (Property("label", "Raw date"), Property("temporal_extent", "2022-01")),
    )
    result = validate_candidate(
        career_ontology_v5_0(),
        replace(candidate, entities=candidate.entities + (context,)),
    )

    assert isinstance(result, Rejected)
    assert "record.invalid_value_kind" in _codes(result)


def test_legacy_candidate_version_is_not_silently_validated_as_v5() -> None:
    candidate = temporal_candidate()
    mismatched = replace(candidate, ontology_version="0.5")

    result = validate_candidate(career_ontology_v5_0(), mismatched)

    assert isinstance(result, Rejected)
    assert "realisation.ontology_version_mismatch" in _codes(result)

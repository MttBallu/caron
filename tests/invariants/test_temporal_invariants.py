"""Generative checks for month-level temporal invariants."""

from dataclasses import replace

from hypothesis import given
from hypothesis import strategies as st

from caron import (
    Accepted,
    CoveredMonthKind,
    KnownEnd,
    Property,
    Rejected,
    TemporalExtent,
    YearMonth,
    covered_months,
    validate_candidate,
)
from caron.ontology import career_ontology_v5_0
from tests.fixtures.temporal_v5 import temporal_v5_candidate


def _from_month_index(index: int) -> YearMonth:
    year_index, month_index = divmod(index, 12)
    return YearMonth(year_index + 1, month_index + 1)


@given(
    year=st.integers(min_value=1, max_value=9999),
    month=st.integers(min_value=1, max_value=12),
)
def test_year_month_canonical_round_trip(year: int, month: int) -> None:
    value = YearMonth(year, month)

    assert YearMonth.parse(str(value)) == value


@given(
    start_index=st.integers(min_value=0, max_value=119_976),
    length=st.integers(min_value=1, max_value=12),
)
def test_exact_covered_month_count_is_inclusive_and_positive(
    start_index: int,
    length: int,
) -> None:
    candidate = temporal_v5_candidate()
    alice = candidate.entities[1]
    start = _from_month_index(start_index)
    end = _from_month_index(start_index + length - 1)
    generated_alice = replace(
        alice,
        properties=(
            Property("label", "Generated context"),
            Property("temporal_extent", TemporalExtent(start, KnownEnd(end))),
        ),
    )
    generated = replace(
        candidate,
        entities=(candidate.entities[0], generated_alice, *candidate.entities[2:]),
    )
    result = validate_candidate(career_ontology_v5_0(), generated)
    assert isinstance(result, Accepted)

    count = covered_months(result.realisation, generated_alice.id)

    assert count.kind is CoveredMonthKind.EXACT
    assert count.minimum == length
    assert count.maximum == length


@given(
    start_index=st.integers(
        min_value=YearMonth(2022, 10).month_index,
        max_value=YearMonth(2025, 10).month_index,
    ),
    end_index=st.integers(
        min_value=YearMonth(2022, 10).month_index,
        max_value=YearMonth(2025, 10).month_index,
    ),
)
def test_every_closed_child_inside_parent_is_accepted(
    start_index: int,
    end_index: int,
) -> None:
    start_index, end_index = sorted((start_index, end_index))
    candidate = temporal_v5_candidate()
    synthetic = candidate.entities[3]
    generated_synthetic = replace(
        synthetic,
        properties=synthetic.properties
        + (
            Property(
                "temporal_extent",
                TemporalExtent(
                    _from_month_index(start_index),
                    KnownEnd(_from_month_index(end_index)),
                ),
            ),
        ),
    )
    generated = replace(
        candidate,
        entities=(
            *candidate.entities[:3],
            generated_synthetic,
            *candidate.entities[4:],
        ),
    )

    assert isinstance(validate_candidate(career_ontology_v5_0(), generated), Accepted)


@given(offset=st.integers(min_value=1, max_value=120))
def test_child_starting_after_parent_is_never_accepted(offset: int) -> None:
    candidate = temporal_v5_candidate()
    synthetic = candidate.entities[3]
    start = _from_month_index(YearMonth(2025, 10).month_index + offset)
    generated_synthetic = replace(
        synthetic,
        properties=synthetic.properties
        + (
            Property(
                "temporal_extent",
                TemporalExtent(start, KnownEnd(start)),
            ),
        ),
    )
    generated = replace(
        candidate,
        entities=(
            *candidate.entities[:3],
            generated_synthetic,
            *candidate.entities[4:],
        ),
    )

    result = validate_candidate(career_ontology_v5_0(), generated)

    assert isinstance(result, Rejected)
    assert "realisation.temporal_containment_impossible" in {
        diagnostic.code for diagnostic in result.diagnostics
    }

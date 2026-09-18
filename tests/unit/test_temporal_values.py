"""Deterministic tests for month-level temporal values."""

from dataclasses import FrozenInstanceError

import pytest

from caron import KnownEnd, TemporalExtent, TemporalWindow, YearMonth


@pytest.mark.parametrize("value", ["2022", "2022-1", "2022-13", "22-01"])
def test_year_month_rejects_noncanonical_values(value: str) -> None:
    with pytest.raises(ValueError, match="YYYY-MM"):
        YearMonth.parse(value)


def test_year_month_round_trips_and_orders_chronologically() -> None:
    november = YearMonth.parse("2021-11")
    february = YearMonth.parse("2022-02")

    assert str(november) == "2021-11"
    assert november < february
    assert february.month_index - november.month_index == 3


def test_temporal_values_are_immutable() -> None:
    extent = TemporalExtent.closed("2021-11", "2022-02")

    with pytest.raises(FrozenInstanceError):
        extent.start = YearMonth.parse("2021-12")  # type: ignore[misc]


def test_window_rejects_reversed_boundaries() -> None:
    with pytest.raises(ValueError, match="end"):
        TemporalWindow.closed("2022-02", "2021-11")


def test_closed_extent_uses_a_known_end_variant() -> None:
    extent = TemporalExtent.closed("2021-11", "2022-02")

    assert extent.start == YearMonth(2021, 11)
    assert extent.end == KnownEnd(YearMonth(2022, 2))

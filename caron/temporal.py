"""Immutable month-level temporal values for career model v0.5."""

from dataclasses import dataclass
from re import fullmatch


@dataclass(frozen=True, slots=True, order=True)
class YearMonth:
    """One calendar month in canonical ``YYYY-MM`` form."""

    year: int
    month: int

    def __post_init__(self) -> None:
        if isinstance(self.year, bool) or not isinstance(self.year, int):
            raise TypeError("year must be an integer")
        if isinstance(self.month, bool) or not isinstance(self.month, int):
            raise TypeError("month must be an integer")
        if not 1 <= self.year <= 9999:
            raise ValueError("year must be between 1 and 9999")
        if not 1 <= self.month <= 12:
            raise ValueError("month must be between 1 and 12")

    @classmethod
    def parse(cls, value: str) -> "YearMonth":
        """Parse a canonical four-digit year and two-digit month."""

        if fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", value) is None:
            raise ValueError("YearMonth must use canonical YYYY-MM form")
        year, month = value.split("-")
        return cls(int(year), int(month))

    @property
    def month_index(self) -> int:
        """Return an ordinal suitable for differences and ordering."""

        return (self.year - 1) * 12 + self.month - 1

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


@dataclass(frozen=True, slots=True)
class KnownEnd:
    month: YearMonth

    def __post_init__(self) -> None:
        if not isinstance(self.month, YearMonth):
            raise TypeError("known end must contain a YearMonth")


@dataclass(frozen=True, slots=True)
class UnknownEnd:
    """An end for which neither a month nor continuing status is known."""


@dataclass(frozen=True, slots=True)
class OngoingAsOf:
    month: YearMonth

    def __post_init__(self) -> None:
        if not isinstance(self.month, YearMonth):
            raise TypeError("ongoing observation must contain a YearMonth")


type TemporalEnd = KnownEnd | UnknownEnd | OngoingAsOf


@dataclass(frozen=True, slots=True)
class TemporalExtent:
    """A context's connected calendar envelope at month resolution."""

    start: YearMonth
    end: TemporalEnd

    def __post_init__(self) -> None:
        if not isinstance(self.start, YearMonth):
            raise TypeError("temporal extent start must be a YearMonth")
        if not isinstance(self.end, KnownEnd | UnknownEnd | OngoingAsOf):
            raise TypeError("temporal extent must contain a valid end state")

    @classmethod
    def closed(cls, start: str, end: str) -> "TemporalExtent":
        return cls(YearMonth.parse(start), KnownEnd(YearMonth.parse(end)))

    @classmethod
    def unknown_end(cls, start: str) -> "TemporalExtent":
        return cls(YearMonth.parse(start), UnknownEnd())

    @classmethod
    def ongoing(cls, start: str, *, as_of: str) -> "TemporalExtent":
        return cls(YearMonth.parse(start), OngoingAsOf(YearMonth.parse(as_of)))

    @property
    def observed_end(self) -> YearMonth | None:
        """Return the known end or recorded observation month, when present."""

        match self.end:
            case KnownEnd(month) | OngoingAsOf(month):
                return month
            case UnknownEnd():
                return None


@dataclass(frozen=True, slots=True)
class TemporalWindow:
    """An inclusive month-level query window."""

    start: YearMonth
    end: YearMonth

    def __post_init__(self) -> None:
        if not isinstance(self.start, YearMonth) or not isinstance(self.end, YearMonth):
            raise TypeError("temporal window boundaries must be YearMonth values")
        if self.end < self.start:
            raise ValueError("temporal window end must not be before its start")

    @classmethod
    def closed(cls, start: str, end: str) -> "TemporalWindow":
        return cls(YearMonth.parse(start), YearMonth.parse(end))

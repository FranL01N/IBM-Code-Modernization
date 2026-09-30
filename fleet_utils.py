"""Small fleet-report helpers retained for compatibility."""

from collections.abc import Iterable, Sequence
from typing import TypeVar

MILES_PER_KM = 0.621371

T = TypeVar("T")


def km_to_miles(km: int | float) -> float:
    """Convert kilometers to miles."""
    return km * MILES_PER_KM


def format_number(value: int | float) -> str:
    """Format a number with one decimal place."""
    return f"{value:.1f}"


def format_percent(value: int | float) -> str:
    """Format a percentage as a whole number."""
    return f"{value:.0f}%"


def mean(values: Iterable[int | float]) -> float:
    """Return the arithmetic mean, or zero for an empty iterable."""
    values_list = list(values)
    return sum(values_list) / len(values_list) if values_list else 0.0


def is_due(pct: int | float, threshold: int | float) -> bool:
    """Return whether a wear percentage has reached its threshold."""
    return pct >= threshold


def parse_service_date(text: str) -> tuple[int, int, int] | None:
    """Parse a DD.MM.YYYY service date into a year-month-day tuple."""
    parts = text.split(".")
    if len(parts) != 3:
        return None

    day, month, year = (int(part) for part in parts)
    return year, month, day


def chunk_list(items: Sequence[T], size: int) -> list[list[T]]:
    """Split a sequence into chunks of the requested size."""
    return [list(items[index:index + size]) for index in range(0, len(items), size)]

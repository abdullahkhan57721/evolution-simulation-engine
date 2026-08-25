"""Domain-neutral linkage and transmission-association models.

Linkage describes how nearby transmissible components tend to remain associated
when descendant state is assembled. Biology realizes this with loci on
chromosomes, but the same abstraction can describe any ordered heritable
components whose joint transmission depends on proximity.
"""

from __future__ import annotations

import math
import random
from typing import Protocol

import attrs

from evo_engine.validation import validators


class LinkageComponent(Protocol):
    """Describe one addressable component within an ordered linkage system."""

    @property
    def name(self) -> str:
        """Return the component identifier."""
        ...

    @property
    def linkage_group(self) -> str:
        """Return the linkage-group identifier containing the component."""
        ...

    @property
    def linkage_position(self) -> int:
        """Return the nonnegative coordinate within the linkage group."""
        ...


class LinkageMap(Protocol):
    """Provide relative breakpoint intensity across a linkage group."""

    def breakpoint_weight(
        self,
        *,
        linkage_group: str,
        position: int,
    ) -> float:
        """Return relative breakage intensity after ``position``.

        A larger value makes transmission breakpoints more likely at this
        coordinate. A value of zero makes that coordinate fully linked for
        models that use this map.

        Args:
            linkage_group: Linkage group being transmitted.
            position: Integer coordinate immediately before a possible break.

        Returns:
            Finite nonnegative relative breakpoint weight.
        """
        ...


def _validate_rate(value: object, *, name: str) -> float:
    """Return a finite nonnegative linkage rate."""
    rate = float(validators.validate_number(value, name=name))
    if not math.isfinite(rate):
        raise ValueError(f"{name} must be finite.")
    if rate < 0:
        raise ValueError(f"{name} must be non-negative.")
    return rate


@attrs.frozen(slots=True, kw_only=True)
class RecombinationInterval:
    """Override breakpoint intensity on one half-open linkage interval.

    ``relative_rate`` acts like local permeability to linkage breakage. Values
    below one make components across the interval more tightly linked; zero
    prevents a breakpoint there; values above one create recombination
    hotspots.

    Attributes:
        linkage_group: Group whose transmission map is modified.
        start: First integer breakpoint coordinate included in the interval.
        end: First integer breakpoint coordinate excluded from the interval.
        relative_rate: Nonnegative local breakpoint-rate multiplier.
    """

    linkage_group: str
    start: int
    end: int
    relative_rate: int | float = 1.0

    def __attrs_post_init__(self) -> None:
        """Validate interval coordinates and local rate."""
        validators.validate_str(self.linkage_group, name="linkage_group")
        if not self.linkage_group.strip():
            raise ValueError("linkage_group must not be empty or whitespace-only.")
        validators.validate_int_ge(self.start, bound=0, name="start")
        validators.validate_int_ge(self.end, bound=0, name="end")
        if self.end <= self.start:
            raise ValueError("end must be greater than start.")
        _validate_rate(self.relative_rate, name="relative_rate")


@attrs.frozen(slots=True, kw_only=True)
class UniformLinkageMap:
    """Use one uniform breakpoint intensity everywhere.

    Attributes:
        relative_rate: Nonnegative breakpoint-rate multiplier.
    """

    relative_rate: int | float = 1.0

    def __attrs_post_init__(self) -> None:
        """Validate uniform linkage rate."""
        _validate_rate(self.relative_rate, name="relative_rate")

    def breakpoint_weight(
        self,
        *,
        linkage_group: str,
        position: int,
    ) -> float:
        """Return the configured uniform breakpoint weight."""
        validators.validate_str(linkage_group, name="linkage_group")
        validators.validate_int_ge(position, bound=0, name="position")
        return float(self.relative_rate)


@attrs.frozen(slots=True, kw_only=True)
class PiecewiseLinkageMap:
    """Use local breakpoint-rate modifiers across linkage groups.

    Intervals on the same linkage group may not overlap. Coordinates not
    covered by an interval use ``default_rate``.

    Attributes:
        intervals: Explicit local rate intervals.
        default_rate: Rate used outside explicit intervals.
    """

    intervals: tuple[RecombinationInterval, ...] = ()
    default_rate: int | float = 1.0

    def __attrs_post_init__(self) -> None:
        """Validate intervals and reject ambiguous overlapping ranges."""
        validators.validate_tuple(self.intervals, name="intervals")
        _validate_rate(self.default_rate, name="default_rate")
        by_group: dict[str, list[RecombinationInterval]] = {}
        for index, interval in enumerate(self.intervals):
            if not isinstance(interval, RecombinationInterval):
                raise TypeError(
                    f"intervals[{index}] must be a RecombinationInterval."
                )
            by_group.setdefault(interval.linkage_group, []).append(interval)

        for linkage_group, intervals in by_group.items():
            ordered = sorted(intervals, key=lambda item: item.start)
            for previous, current in zip(ordered, ordered[1:], strict=False):
                if current.start < previous.end:
                    raise ValueError(
                        "intervals on the same linkage group must not overlap; "
                        f"overlap found in {linkage_group!r}."
                    )

    def breakpoint_weight(
        self,
        *,
        linkage_group: str,
        position: int,
    ) -> float:
        """Return the local breakpoint weight at a coordinate."""
        validators.validate_str(linkage_group, name="linkage_group")
        validators.validate_int_ge(position, bound=0, name="position")
        for interval in self.intervals:
            if (
                interval.linkage_group == linkage_group
                and interval.start <= position < interval.end
            ):
                return float(interval.relative_rate)
        return float(self.default_rate)


def sample_linkage_breakpoint(
    linkage_map: LinkageMap,
    *,
    linkage_group: str,
    first_position: int,
    last_position: int,
    rng: random.Random,
) -> int | None:
    """Sample a breakpoint using distance and local linkage intensity.

    Every integer coordinate from ``first_position`` through the coordinate
    immediately before ``last_position`` is a possible breakpoint. Therefore a
    larger physical coordinate gap naturally provides more opportunities for
    separation, while the linkage map can make particular regions stickier or
    more recombinogenic.

    Args:
        linkage_map: Map providing relative breakpoint weights.
        linkage_group: Linkage group being transmitted.
        first_position: Lowest component coordinate.
        last_position: Highest component coordinate.
        rng: Simulation random-number generator.

    Returns:
        Sampled integer breakpoint, or ``None`` when every possible breakpoint
        has zero weight.

    Raises:
        TypeError: If linkage_map, linkage_group, or rng is invalid.
        ValueError: If coordinates are invalid or a map returns an invalid
            weight.
    """
    try:
        breakpoint_weight = linkage_map.breakpoint_weight
    except AttributeError as error:
        raise TypeError(
            "linkage_map must provide a callable breakpoint_weight method."
        ) from error
    if not callable(breakpoint_weight):
        raise TypeError(
            "linkage_map must provide a callable breakpoint_weight method."
        )

    validators.validate_str(linkage_group, name="linkage_group")
    validators.validate_int_ge(first_position, bound=0, name="first_position")
    validators.validate_int_ge(last_position, bound=0, name="last_position")
    if last_position <= first_position:
        raise ValueError("last_position must be greater than first_position.")
    if not isinstance(rng, random.Random):
        raise TypeError("rng must be an instance of random.Random.")

    weighted_positions: list[tuple[int, float]] = []
    total_weight = 0.0
    for position in range(first_position, last_position):
        weight = _validate_rate(
            linkage_map.breakpoint_weight(
                linkage_group=linkage_group,
                position=position,
            ),
            name="linkage_map breakpoint weight",
        )
        if weight == 0:
            continue
        total_weight += weight
        weighted_positions.append((position, weight))

    if not weighted_positions:
        return None

    target = rng.random() * total_weight
    cumulative = 0.0
    for position, weight in weighted_positions:
        cumulative += weight
        if target < cumulative:
            return position

    return weighted_positions[-1][0]

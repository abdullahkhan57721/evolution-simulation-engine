"""Population-level observers for evolutionary simulations."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

import attrs

from evo_engine.observation.records import (
    IntegerSummary,
    IntegerTraitSummary,
    PopulationObservation,
)
from evo_engine.validation import attrs_validators, validators
from evo_engine.world import Organism, WorldState


@attrs.define(slots=True, kw_only=True)
class PopulationRecorder:
    """Record population and selected genetic-trait state over time.

    The recorder is intentionally read-only with respect to ``WorldState``. It
    stores immutable ``PopulationObservation`` values and therefore does not
    retain references to mutable organisms or world collections.

    Attributes:
        trait_names: Integer genetic-phenotype traits to summarize.
        every_n_steps: Positive observation interval. A value of 1 records every
            committed step.
        include_step_zero: Whether to record the pre-step baseline at step zero.
    """

    trait_names: tuple[str, ...] = attrs.field(
        factory=tuple,
    )
    every_n_steps: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    include_step_zero: bool = attrs.field(
        default=True,
        validator=attrs_validators.validate_bool,
    )
    _observations: list[PopulationObservation] = attrs.field(
        factory=list,
        init=False,
        repr=False,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured trait names."""
        validators.validate_tuple(
            self.trait_names,
            name="trait_names",
        )

        seen: set[str] = set()
        for index, trait_name in enumerate(self.trait_names):
            validated_name = validators.validate_str(
                trait_name,
                name=f"trait_names[{index}]",
            )
            if not validated_name.strip():
                raise ValueError(
                    f"trait_names[{index}] must not be empty or whitespace-only."
                )
            if validated_name in seen:
                raise ValueError(
                    f"trait_names must not contain duplicates; received "
                    f"{validated_name!r}."
                )
            seen.add(validated_name)

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic phenotype traits required by this recorder."""
        return frozenset(self.trait_names)

    @property
    def observations(self) -> tuple[PopulationObservation, ...]:
        """Return recorded observations as an immutable tuple."""
        return tuple(self._observations)

    @property
    def latest(self) -> PopulationObservation | None:
        """Return the latest observation, if one has been recorded."""
        if not self._observations:
            return None
        return self._observations[-1]

    def should_observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> bool:
        """Return whether the current committed state should be recorded.

        Args:
            world_state: Current committed world state.
            step_index: Current completed simulation-step index.

        Returns:
            ``True`` when the state falls on the configured interval and has not
            already been recorded.
        """
        _validate_observation_inputs(
            world_state,
            step_index=step_index,
        )

        if self._observations and self._observations[-1].step_index == step_index:
            return False

        if step_index == 0 and not self.include_step_zero:
            return False

        return step_index % self.every_n_steps == 0

    def observe(
        self,
        world_state: WorldState,
        *,
        step_index: int,
    ) -> None:
        """Record one immutable population observation.

        Args:
            world_state: Current committed world state.
            step_index: Current completed simulation-step index.

        Raises:
            ValueError: If observations are supplied out of chronological order.
            KeyError: If a configured trait is absent from an organism's genetic
                phenotype.
            TypeError: If a configured trait is not expressed as an integer.
        """
        _validate_observation_inputs(
            world_state,
            step_index=step_index,
        )

        if self._observations and step_index <= self._observations[-1].step_index:
            raise ValueError(
                "PopulationRecorder observations must have strictly increasing "
                "step_index values."
            )

        organisms = tuple(world_state.organisms.values())
        self._observations.append(
            PopulationObservation(
                step_index=step_index,
                population_size=len(organisms),
                carcass_count=len(world_state.carcasses),
                total_resources=sum(world_state.resources.values()),
                age=_summarize_integers(organism.age for organism in organisms),
                energy=_summarize_integers(organism.energy for organism in organisms),
                body_mass=_summarize_integers(
                    organism.body_mass for organism in organisms
                ),
                traits=tuple(
                    _summarize_trait(
                        trait_name,
                        organisms,
                    )
                    for trait_name in self.trait_names
                ),
            )
        )

    def clear(self) -> None:
        """Remove all recorded observations."""
        self._observations.clear()


def _validate_observation_inputs(
    world_state: WorldState,
    *,
    step_index: int,
) -> None:
    if not isinstance(world_state, WorldState):
        raise TypeError("world_state must be an instance of WorldState.")

    validators.validate_int_ge(
        step_index,
        bound=0,
        name="step_index",
    )


def _summarize_integers(values: Iterable[int]) -> IntegerSummary:
    values_tuple = tuple(values)
    for index, value in enumerate(values_tuple):
        validators.validate_int(
            value,
            name=f"values[{index}]",
        )

    if not values_tuple:
        return IntegerSummary(
            count=0,
            total=0,
        )

    total = sum(values_tuple)
    return IntegerSummary(
        count=len(values_tuple),
        total=total,
        mean=total / len(values_tuple),
        minimum=min(values_tuple),
        maximum=max(values_tuple),
    )


def _summarize_trait(
    trait_name: str,
    organisms: tuple[Organism, ...],
) -> IntegerTraitSummary:
    values = tuple(
        organism.genetic_phenotype.int_value(trait_name) for organism in organisms
    )
    counts = Counter(values)

    return IntegerTraitSummary(
        trait_name=trait_name,
        summary=_summarize_integers(values),
        value_counts=tuple(sorted(counts.items())),
    )

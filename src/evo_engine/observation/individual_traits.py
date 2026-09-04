"""Record selected per-organism genetic-phenotype traits from committed state."""

from __future__ import annotations

from collections.abc import Sequence

import attrs

from evo_engine.validation import attrs_validators, validators
from evo_engine.world import WorldState


@attrs.frozen(slots=True, kw_only=True)
class IndividualGeneticTraitSnapshot:
    """Record selected genetic-phenotype values for one active organism.

    ``trait_values`` follows the configured trait-name order carried by the
    enclosing :class:`IndividualGeneticTraitObservation`. The record contains
    immutable scalar values only and retains no organism, genome, phenotype, or
    world references.

    Attributes:
        organism_id: Permanent world-managed organism ID.
        trait_values: Integer genetic-phenotype values in configured trait order.
    """

    organism_id: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    trait_values: tuple[int, ...] = attrs.field(factory=tuple)

    def __attrs_post_init__(self) -> None:
        """Validate the immutable integer trait-value tuple."""
        validators.validate_tuple(self.trait_values, name="trait_values")
        for index, value in enumerate(self.trait_values):
            validators.validate_int(value, name=f"trait_values[{index}]")


@attrs.frozen(slots=True, kw_only=True)
class IndividualGeneticTraitObservation:
    """Record selected per-organism genetic-phenotype traits for one state.

    Attributes:
        step_index: Completed simulation-state index represented by the record.
        trait_names: Configured genetic-phenotype trait names in stable order.
        individuals: Active-organism snapshots ordered by permanent organism ID.
    """

    step_index: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    trait_names: tuple[str, ...] = attrs.field(factory=tuple)
    individuals: tuple[IndividualGeneticTraitSnapshot, ...] = attrs.field(
        factory=tuple,
    )

    def __attrs_post_init__(self) -> None:
        """Validate trait names, individual ordering, and value widths."""
        _validate_trait_names(self.trait_names)
        validators.validate_tuple(self.individuals, name="individuals")

        organism_ids: list[int] = []
        for index, individual in enumerate(self.individuals):
            if not isinstance(individual, IndividualGeneticTraitSnapshot):
                raise TypeError(
                    "individuals["
                    f"{index}] must be an IndividualGeneticTraitSnapshot; "
                    f"received {individual!r}."
                )
            if len(individual.trait_values) != len(self.trait_names):
                raise ValueError(
                    f"individuals[{index}].trait_values must contain exactly "
                    f"{len(self.trait_names)} values; received "
                    f"{len(individual.trait_values)}."
                )
            organism_ids.append(individual.organism_id)

        _validate_unique_sorted(organism_ids, name="organism IDs")

    def snapshot(self, organism_id: int) -> IndividualGeneticTraitSnapshot:
        """Return the selected genetic-trait snapshot for one organism.

        Args:
            organism_id: Permanent organism ID to retrieve.

        Returns:
            Matching immutable individual snapshot.

        Raises:
            KeyError: If the organism is absent from this committed state.
        """
        validated_id = validators.validate_int_ge(
            organism_id,
            bound=0,
            name="organism_id",
        )
        for individual in self.individuals:
            if individual.organism_id == validated_id:
                return individual
        raise KeyError(f"No individual trait record for organism {validated_id}.")

    def trait_value(self, organism_id: int, trait_name: str) -> int:
        """Return one recorded genetic-phenotype value for an organism.

        Args:
            organism_id: Permanent organism ID to retrieve.
            trait_name: Configured trait name to retrieve.

        Returns:
            Recorded integer genetic-phenotype value.

        Raises:
            KeyError: If the organism or trait name is absent from this record.
        """
        validated_name = validators.validate_str(trait_name, name="trait_name")
        if not validated_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")
        try:
            trait_index = self.trait_names.index(validated_name)
        except ValueError as error:
            raise KeyError(
                f"No individual genetic trait recorded for {validated_name!r}."
            ) from error
        return self.snapshot(organism_id).trait_values[trait_index]


@attrs.define(slots=True, kw_only=True)
class IndividualGeneticTraitRecorder:
    """Record selected integer genetic-phenotype values for active organisms.

    The recorder is opt-in and stores only explicitly configured trait values.
    It observes authoritative committed ``WorldState`` values and never retains
    live organism, genome, phenotype, or world references.

    Attributes:
        trait_names: Integer genetic-phenotype traits to record per organism.
        every_n_steps: Positive committed-state observation interval.
        include_step_zero: Whether to record the pre-step founder baseline.
    """

    trait_names: tuple[str, ...] = attrs.field(factory=tuple)
    every_n_steps: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    include_step_zero: bool = attrs.field(
        default=True,
        validator=attrs_validators.validate_bool,
    )
    _observations: list[IndividualGeneticTraitObservation] = attrs.field(
        factory=list,
        init=False,
        repr=False,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured trait names."""
        _validate_trait_names(self.trait_names)

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic-phenotype traits required by this recorder."""
        return frozenset(self.trait_names)

    @property
    def observations(self) -> tuple[IndividualGeneticTraitObservation, ...]:
        """Return recorded observations as an immutable tuple."""
        return tuple(self._observations)

    @property
    def latest(self) -> IndividualGeneticTraitObservation | None:
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
        """Return whether the current committed state should be recorded."""
        _validate_observation_inputs(world_state, step_index=step_index)
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
        """Record selected traits from one authoritative committed world state.

        Args:
            world_state: Current authoritative committed biological world.
            step_index: Current completed simulation-state index.

        Raises:
            ValueError: If observations are supplied out of chronological order.
            KeyError: If a configured trait is absent from an organism phenotype.
            TypeError: If a configured trait is not expressed as an integer.
        """
        _validate_observation_inputs(world_state, step_index=step_index)
        if self._observations and step_index <= self._observations[-1].step_index:
            raise ValueError(
                "IndividualGeneticTraitRecorder observations must have strictly "
                "increasing step_index values."
            )

        self._observations.append(
            IndividualGeneticTraitObservation(
                step_index=step_index,
                trait_names=self.trait_names,
                individuals=tuple(
                    IndividualGeneticTraitSnapshot(
                        organism_id=organism_id,
                        trait_values=tuple(
                            organism.genetic_phenotype.int_value(trait_name)
                            for trait_name in self.trait_names
                        ),
                    )
                    for organism_id, organism in sorted(world_state.organisms.items())
                ),
            )
        )

    def clear(self) -> None:
        """Remove all recorded observations."""
        self._observations.clear()


def _validate_trait_names(trait_names: object) -> tuple[str, ...]:
    validated = validators.validate_tuple(trait_names, name="trait_names")
    seen: set[str] = set()
    for index, trait_name in enumerate(validated):
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
                f"trait_names must not contain duplicates; received {validated_name!r}."
            )
        seen.add(validated_name)
    return validated


def _validate_observation_inputs(
    world_state: WorldState,
    *,
    step_index: int,
) -> None:
    if not isinstance(world_state, WorldState):
        raise TypeError("world_state must be an instance of WorldState.")
    validators.validate_int_ge(step_index, bound=0, name="step_index")


def _validate_unique_sorted(values: Sequence[int], *, name: str) -> None:
    if tuple(values) != tuple(sorted(values)):
        raise ValueError(f"{name} must be in deterministic increasing order.")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique.")

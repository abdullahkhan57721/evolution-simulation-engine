"""Record allele and genotype composition of evolving populations."""

from __future__ import annotations

from collections.abc import Iterable

import attrs

from evo_engine.validation import attrs_validators, validators
from evo_engine.world import Organism, WorldState


@attrs.frozen(slots=True, kw_only=True)
class AlleleFrequency:
    """Observed frequency of one allele value at a locus.

    Attributes:
        value: Raw inherited allele value.
        count: Number of observed allele copies carrying the value.
        frequency: Fraction of all observed allele copies carrying the value.
    """

    value: object
    count: int = attrs.field(validator=attrs_validators.validate_int_ge(1))
    frequency: float = attrs.field(
        validator=attrs_validators.validate_float_in_range(0.0, 1.0),
    )


@attrs.frozen(slots=True, kw_only=True)
class GenotypeFrequency:
    """Observed frequency of one unphased genotype at a locus.

    Alleles are canonically ordered for observation, so diploid ``(A, B)`` and
    ``(B, A)`` contribute to the same unphased genotype.

    Attributes:
        allele_values: Canonically ordered allele values comprising the genotype.
        count: Number of organisms carrying the genotype.
        frequency: Fraction of observed organisms carrying the genotype.
    """

    allele_values: tuple[object, ...]
    count: int = attrs.field(validator=attrs_validators.validate_int_ge(1))
    frequency: float = attrs.field(
        validator=attrs_validators.validate_float_in_range(0.0, 1.0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate genotype structure."""
        validators.validate_tuple(self.allele_values, name="allele_values")
        if not self.allele_values:
            raise ValueError("allele_values must not be empty.")


@attrs.frozen(slots=True, kw_only=True)
class LocusComposition:
    """Allele and genotype composition observed at one locus.

    Attributes:
        locus_name: Observed locus name.
        organism_count: Number of organisms represented in genotype frequencies.
        allele_copy_count: Total observed allele copies at the locus.
        alleles: Allele frequencies in deterministic value order.
        genotypes: Unphased genotype frequencies in deterministic order.
    """

    locus_name: str
    organism_count: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    allele_copy_count: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    alleles: tuple[AlleleFrequency, ...] = attrs.field(factory=tuple)
    genotypes: tuple[GenotypeFrequency, ...] = attrs.field(factory=tuple)

    def __attrs_post_init__(self) -> None:
        """Validate composition invariants."""
        _validate_nonempty_name(self.locus_name, name="locus_name")
        validators.validate_tuple(self.alleles, name="alleles")
        validators.validate_tuple(self.genotypes, name="genotypes")
        if sum(item.count for item in self.alleles) != self.allele_copy_count:
            raise ValueError("Allele counts must sum to allele_copy_count.")
        if sum(item.count for item in self.genotypes) != self.organism_count:
            raise ValueError("Genotype counts must sum to organism_count.")

    def allele_frequency(self, value: object) -> float:
        """Return the observed frequency of an allele value, or zero if absent.

        Args:
            value: Allele value to query.

        Returns:
            Observed allele-copy frequency.
        """
        for allele in self.alleles:
            if allele.value == value:
                return allele.frequency
        return 0.0


@attrs.frozen(slots=True, kw_only=True)
class GeneticCompositionObservation:
    """Immutable raw-genetic population observation for one committed state.

    Attributes:
        step_index: Committed simulation state index.
        population_size: Number of active organisms.
        loci: Per-locus allele and genotype compositions.
    """

    step_index: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    population_size: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    loci: tuple[LocusComposition, ...]

    def __attrs_post_init__(self) -> None:
        """Validate locus uniqueness."""
        validators.validate_tuple(self.loci, name="loci")
        names = tuple(locus.locus_name for locus in self.loci)
        if len(names) != len(set(names)):
            raise ValueError("loci must have unique locus names.")
        if any(locus.organism_count != self.population_size for locus in self.loci):
            raise ValueError("Each locus organism_count must equal population_size.")

    def locus(self, locus_name: str) -> LocusComposition:
        """Return composition for a named locus.

        Args:
            locus_name: Locus to retrieve.

        Returns:
            Matching locus composition.

        Raises:
            KeyError: If the locus was not recorded.
        """
        validated_name = _validate_nonempty_name(locus_name, name="locus_name")
        for locus in self.loci:
            if locus.locus_name == validated_name:
                return locus
        raise KeyError(f"No genetic composition recorded for locus {validated_name!r}.")


@attrs.define(slots=True, kw_only=True)
class GeneticCompositionRecorder:
    """Record raw allele and unphased genotype frequencies over time.

    Unlike ``PopulationRecorder`` trait summaries, this recorder reads the
    inherited ``Genome`` directly. Hidden genetic variation therefore remains
    observable even when dominance or other expression rules map distinct
    genotypes to the same phenotype.

    Attributes:
        locus_names: Loci to observe from every active organism genome.
        every_n_steps: Positive committed-state observation interval.
        include_step_zero: Whether to record the pre-step baseline.
    """

    locus_names: tuple[str, ...]
    every_n_steps: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    include_step_zero: bool = attrs.field(
        default=True,
        validator=attrs_validators.validate_bool,
    )
    _observations: list[GeneticCompositionObservation] = attrs.field(
        factory=list,
        init=False,
        repr=False,
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured locus names."""
        _validate_unique_names(self.locus_names, name="locus_names")

    @property
    def observations(self) -> tuple[GeneticCompositionObservation, ...]:
        """Return recorded genetic-composition observations."""
        return tuple(self._observations)

    @property
    def latest(self) -> GeneticCompositionObservation | None:
        """Return the latest genetic-composition observation, if any."""
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
        """Record one immutable raw-genetic population observation.

        Args:
            world_state: Current committed world state.
            step_index: Current committed simulation-state index.

        Raises:
            ValueError: If observations are supplied out of chronological order.
            KeyError: If an active organism lacks a configured locus.
        """
        _validate_observation_inputs(world_state, step_index=step_index)
        if self._observations and step_index <= self._observations[-1].step_index:
            raise ValueError(
                "GeneticCompositionRecorder observations must have strictly "
                "increasing step_index values."
            )

        organisms = tuple(world_state.organisms.values())
        self._observations.append(
            GeneticCompositionObservation(
                step_index=step_index,
                population_size=len(organisms),
                loci=tuple(
                    _summarize_locus(locus_name, organisms)
                    for locus_name in self.locus_names
                ),
            )
        )

    def clear(self) -> None:
        """Remove all recorded genetic-composition observations."""
        self._observations.clear()


def _summarize_locus(
    locus_name: str,
    organisms: tuple[Organism, ...],
) -> LocusComposition:
    genotypes = tuple(
        _canonical_genotype(
            tuple(allele.value for allele in organism.genome.alleles_at(locus_name))
        )
        for organism in organisms
    )
    allele_values = tuple(value for genotype in genotypes for value in genotype)
    allele_counts = _count_equal_values(allele_values)
    genotype_counts = _count_equal_values(genotypes)
    allele_total = len(allele_values)
    organism_total = len(organisms)

    return LocusComposition(
        locus_name=locus_name,
        organism_count=organism_total,
        allele_copy_count=allele_total,
        alleles=tuple(
            AlleleFrequency(
                value=value,
                count=count,
                frequency=count / allele_total,
            )
            for value, count in allele_counts
        ),
        genotypes=tuple(
            GenotypeFrequency(
                allele_values=genotype,
                count=count,
                frequency=count / organism_total,
            )
            for genotype, count in genotype_counts
        ),
    ) if organisms else LocusComposition(
        locus_name=locus_name,
        organism_count=0,
        allele_copy_count=0,
    )


def _canonical_genotype(values: tuple[object, ...]) -> tuple[object, ...]:
    if not values:
        raise ValueError("A genome locus must contain at least one allele copy.")
    return tuple(sorted(values, key=_value_sort_key))


def _count_equal_values(values: Iterable[object]) -> tuple[tuple[object, int], ...]:
    counted: list[list[object]] = []
    for value in values:
        for item in counted:
            if item[0] == value:
                item[1] = int(item[1]) + 1
                break
        else:
            counted.append([value, 1])
    return tuple(
        (item[0], int(item[1]))
        for item in sorted(counted, key=lambda item: _value_sort_key(item[0]))
    )


def _value_sort_key(value: object) -> tuple[str, str, str]:
    value_type = type(value)
    return value_type.__module__, value_type.__qualname__, repr(value)


def _validate_unique_names(values: tuple[str, ...], *, name: str) -> None:
    validators.validate_tuple(values, name=name)
    seen: set[str] = set()
    for index, value in enumerate(values):
        validated = _validate_nonempty_name(value, name=f"{name}[{index}]")
        if validated in seen:
            raise ValueError(f"{name} must not contain duplicate {validated!r}.")
        seen.add(validated)


def _validate_nonempty_name(value: object, *, name: str) -> str:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")
    return validated


def _validate_observation_inputs(
    world_state: WorldState,
    *,
    step_index: int,
) -> None:
    if not isinstance(world_state, WorldState):
        raise TypeError("world_state must be an instance of WorldState.")
    validators.validate_int_ge(step_index, bound=0, name="step_index")

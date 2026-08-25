"""Immutable records produced by simulation observers."""

from __future__ import annotations

import attrs

from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class IntegerSummary:
    """Summarize a finite collection of integer values.

    Attributes:
        count: Number of summarized values.
        total: Exact integer sum of all values.
        mean: Arithmetic mean, or ``None`` when count is zero.
        minimum: Smallest value, or ``None`` when count is zero.
        maximum: Largest value, or ``None`` when count is zero.
    """

    count: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    total: int = attrs.field(
        validator=attrs_validators.validate_int,
    )
    mean: float | None = None
    minimum: int | None = None
    maximum: int | None = None

    def __attrs_post_init__(self) -> None:
        """Validate empty and nonempty summary invariants."""
        if self.count == 0:
            if self.total != 0:
                raise ValueError("An empty IntegerSummary must have total=0.")
            if any(
                value is not None for value in (self.mean, self.minimum, self.maximum)
            ):
                raise ValueError(
                    "An empty IntegerSummary must have mean, minimum, and maximum set "
                    "to None."
                )
            return

        if self.mean is None or self.minimum is None or self.maximum is None:
            raise ValueError(
                "A nonempty IntegerSummary requires mean, minimum, and maximum."
            )

        validators.validate_float(
            self.mean,
            name="mean",
        )
        validators.validate_int(
            self.minimum,
            name="minimum",
        )
        validators.validate_int(
            self.maximum,
            name="maximum",
        )

        if self.minimum > self.maximum:
            raise ValueError("minimum must be less than or equal to maximum.")

        if not self.minimum <= self.mean <= self.maximum:
            raise ValueError("mean must lie between minimum and maximum.")


@attrs.frozen(slots=True, kw_only=True)
class CategoryCounts:
    """Record deterministic counts for string-valued population categories.

    Category counts are stored in strictly increasing lexicographic order so
    snapshots, equality comparisons, JSON output, and tabular exports remain
    deterministic regardless of the order in which organisms were encountered.

    Attributes:
        value_counts: Ordered ``(category, count)`` pairs. Categories are
            nonempty strings and counts are positive integers.
    """

    value_counts: tuple[tuple[str, int], ...] = attrs.field(factory=tuple)

    def __attrs_post_init__(self) -> None:
        """Validate category labels, counts, and deterministic ordering."""
        validators.validate_tuple(self.value_counts, name="value_counts")
        previous_value: str | None = None

        for index, entry in enumerate(self.value_counts):
            if type(entry) is not tuple:
                raise TypeError(
                    f"value_counts[{index}] must be a tuple; received {entry!r}."
                )
            if len(entry) != 2:
                raise ValueError(
                    f"value_counts[{index}] must contain exactly two items."
                )

            value = validators.validate_str(
                entry[0],
                name=f"value_counts[{index}][0]",
            )
            if not value.strip():
                raise ValueError(
                    f"value_counts[{index}][0] must not be empty or whitespace-only."
                )
            validators.validate_int_gt(
                entry[1],
                bound=0,
                name=f"value_counts[{index}][1]",
            )

            if previous_value is not None and value <= previous_value:
                raise ValueError(
                    "value_counts categories must be unique and strictly increasing."
                )
            previous_value = value

    @property
    def total_count(self) -> int:
        """Return the total number of categorized observations."""
        return sum(count for _, count in self.value_counts)

    def count_for(self, value: str) -> int:
        """Return the number of observations in one category.

        Args:
            value: Category label to look up.

        Returns:
            Number of observations in the category, or zero when absent.
        """
        validated_value = validators.validate_str(value, name="value")
        for observed_value, count in self.value_counts:
            if observed_value == validated_value:
                return count
        return 0

    def frequency_for(self, value: str) -> float | None:
        """Return one category's population frequency.

        Args:
            value: Category label to look up.

        Returns:
            Category count divided by total count, or ``None`` for an empty
            categorical population.
        """
        if self.total_count == 0:
            validators.validate_str(value, name="value")
            return None
        return self.count_for(value) / self.total_count


@attrs.frozen(slots=True, kw_only=True)
class IntegerTraitSummary:
    """Summarize one integer genetic-phenotype trait across a population.

    Attributes:
        trait_name: Genetic phenotype trait being summarized.
        summary: Numerical summary across active organisms.
        value_counts: Ordered ``(value, count)`` pairs for the population.
    """

    trait_name: str = attrs.field(
        validator=attrs_validators.validate_str,
    )
    summary: IntegerSummary = attrs.field(
        validator=attrs.validators.instance_of(IntegerSummary),
    )
    value_counts: tuple[tuple[int, int], ...] = attrs.field(
        factory=tuple,
    )

    def __attrs_post_init__(self) -> None:
        """Validate trait-name and distribution invariants."""
        if not self.trait_name.strip():
            raise ValueError("trait_name must not be empty or whitespace-only.")

        validators.validate_tuple(
            self.value_counts,
            name="value_counts",
        )

        previous_value: int | None = None
        total_count = 0

        for index, entry in enumerate(self.value_counts):
            if type(entry) is not tuple:
                raise TypeError(
                    f"value_counts[{index}] must be a tuple; received {entry!r}."
                )
            if len(entry) != 2:
                raise ValueError(
                    f"value_counts[{index}] must contain exactly two items."
                )

            value = validators.validate_int(
                entry[0],
                name=f"value_counts[{index}][0]",
            )
            count = validators.validate_int_gt(
                entry[1],
                bound=0,
                name=f"value_counts[{index}][1]",
            )

            if previous_value is not None and value <= previous_value:
                raise ValueError(
                    "value_counts values must be unique and strictly increasing."
                )

            previous_value = value
            total_count += count

        if total_count != self.summary.count:
            raise ValueError(
                "value_counts counts must sum to summary.count; "
                f"received {total_count} and {self.summary.count}."
            )

    def count_for(self, value: int) -> int:
        """Return the number of organisms with one trait value.

        Args:
            value: Integer trait value to look up.

        Returns:
            Number of active organisms with the value.
        """
        validators.validate_int(
            value,
            name="value",
        )

        for observed_value, count in self.value_counts:
            if observed_value == value:
                return count

        return 0


@attrs.frozen(slots=True, kw_only=True)
class PopulationObservation:
    """Record population, ecosystem, reproductive, and genetic-trait state.

    Attributes:
        step_index: Completed simulation-step index represented by the record.
        population_size: Number of active organisms.
        carcass_count: Number of carcasses currently in the world.
        total_resources: Total environmental resource units in the world.
        age: Age summary across active organisms.
        energy: Energy summary across active organisms.
        body_mass: Current body-mass summary across active organisms.
        mating_type_counts: Counts of active organisms by mating-type label.
        traits: Selected integer genetic-phenotype trait summaries.
    """

    step_index: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    population_size: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    carcass_count: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    total_resources: int = attrs.field(
        validator=attrs_validators.validate_int_ge(0),
    )
    age: IntegerSummary = attrs.field(
        validator=attrs.validators.instance_of(IntegerSummary),
    )
    energy: IntegerSummary = attrs.field(
        validator=attrs.validators.instance_of(IntegerSummary),
    )
    body_mass: IntegerSummary = attrs.field(
        validator=attrs.validators.instance_of(IntegerSummary),
    )
    mating_type_counts: CategoryCounts = attrs.field(
        validator=attrs.validators.instance_of(CategoryCounts),
    )
    traits: tuple[IntegerTraitSummary, ...] = attrs.field(
        factory=tuple,
    )

    def __attrs_post_init__(self) -> None:
        """Validate population-size, category, and trait-summary consistency."""
        for name, summary in (
            ("age", self.age),
            ("energy", self.energy),
            ("body_mass", self.body_mass),
        ):
            if summary.count != self.population_size:
                raise ValueError(
                    f"{name}.count must equal population_size; received "
                    f"{summary.count} and {self.population_size}."
                )

        if self.mating_type_counts.total_count != self.population_size:
            raise ValueError(
                "mating_type_counts.total_count must equal population_size; received "
                f"{self.mating_type_counts.total_count} and {self.population_size}."
            )

        seen_trait_names: set[str] = set()
        for index, trait_summary in enumerate(self.traits):
            if not isinstance(trait_summary, IntegerTraitSummary):
                raise TypeError(
                    f"traits[{index}] must be an IntegerTraitSummary; "
                    f"received {trait_summary!r}."
                )
            if trait_summary.trait_name in seen_trait_names:
                raise ValueError(
                    "traits must not contain duplicate trait names; received "
                    f"{trait_summary.trait_name!r}."
                )
            if trait_summary.summary.count != self.population_size:
                raise ValueError(
                    f"Trait {trait_summary.trait_name!r} count must equal "
                    "population_size."
                )
            seen_trait_names.add(trait_summary.trait_name)

    def trait(self, trait_name: str) -> IntegerTraitSummary:
        """Return one recorded trait summary by name.

        Args:
            trait_name: Trait name to look up.

        Returns:
            Matching integer trait summary.

        Raises:
            KeyError: If the observation does not contain the trait.
        """
        validators.validate_str(
            trait_name,
            name="trait_name",
        )

        for trait_summary in self.traits:
            if trait_summary.trait_name == trait_name:
                return trait_summary

        raise KeyError(f"Observation has no recorded trait named {trait_name!r}.")

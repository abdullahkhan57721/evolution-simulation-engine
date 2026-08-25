"""Represent organisms in the simulated world."""

from __future__ import annotations

import random

import attrs

from evo_engine.development.models import (
    DeterministicDevelopment,
    DevelopmentModel,
    realize_developmental_profile,
)
from evo_engine.development.profile import DevelopmentalProfile
from evo_engine.genetics.builtin_traits import ADULT_BODY_MASS
from evo_engine.genetics.genetic_architecture import GeneticArchitecture
from evo_engine.genetics.genetic_phenotype import GeneticPhenotype
from evo_engine.genetics.genome import Genome
from evo_engine.validation import attrs_validators, validators


@attrs.define(slots=True, kw_only=True)
class Organism:
    """Represent an organism's mutable, genetic, and expressed state.

    Genetic state, genetic phenotype, developmental targets, and mating type are
    fixed for the lifetime of an organism. Mutable state such as age, energy,
    current body mass, and position may change during simulation.

    ``body_mass`` represents current physical mass. A heritable
    ``adult_body_mass`` genetic phenotype defines a genetic expectation, while
    the developmental profile can realize an individual-specific adult target.
    Those concepts are intentionally separate so a Growth process can change
    current mass without changing the organism's genome or genetic phenotype.

    ``mating_type`` is reproductive identity rather than a built-in genetic
    trait. Simulations may derive or assign it through reproduction policies,
    including sex-determination systems, environmental assignment, or arbitrary
    multi-type compatibility systems.

    Attributes:
        age: Organism age in simulation timesteps.
        energy: Current organism energy.
        body_mass: Current positive physical mass/biomass.
        genome: Inherited genetic state.
        genetic_phenotype: Genetic trait values expressed from the genome.
        developmental_profile: Individual developmental targets realized from
            the genetic phenotype.
        mating_type: Immutable reproductive mating-type label.
        x: Horizontal world coordinate.
        y: Vertical world coordinate.
    """

    _id: int | None = attrs.field(
        default=None,
        init=False,
        repr=False,
    )
    age: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )
    energy: int = attrs.field(
        default=100,
        validator=attrs_validators.validate_int_ge(0),
    )
    body_mass: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    genome: Genome = attrs.field(
        validator=attrs.validators.instance_of(Genome),
        on_setattr=attrs.setters.frozen,
    )
    genetic_phenotype: GeneticPhenotype = attrs.field(
        validator=attrs.validators.instance_of(GeneticPhenotype),
        on_setattr=attrs.setters.frozen,
    )
    developmental_profile: DevelopmentalProfile = attrs.field(
        validator=attrs.validators.instance_of(DevelopmentalProfile),
        on_setattr=attrs.setters.frozen,
    )
    mating_type: str = attrs.field(
        default="default",
        validator=attrs_validators.validate_str,
        on_setattr=attrs.setters.frozen,
    )
    x: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )
    y: int = attrs.field(
        default=0,
        validator=attrs_validators.validate_int_ge(0),
    )

    def __attrs_post_init__(self) -> None:
        """Validate immutable genetic/developmental cross-field invariants."""
        self.developmental_profile.validate_against(self.genetic_phenotype)
        if not self.mating_type.strip():
            raise ValueError("mating_type must not be empty or whitespace-only.")

    def __deepcopy__(self, memo: dict[int, object]) -> Organism:
        """Return a deep copy while sharing immutable genetic state."""
        # Genome and genetic phenotype are frozen value objects, so sharing them
        # is cheaper and just as safe as recursively copying them each timestep.
        copied = type(self)(
            age=self.age,
            energy=self.energy,
            body_mass=self.body_mass,
            genome=self.genome,
            genetic_phenotype=self.genetic_phenotype,
            developmental_profile=self.developmental_profile,
            mating_type=self.mating_type,
            x=self.x,
            y=self.y,
        )
        copied._id = self._id
        memo[id(self)] = copied
        return copied

    @classmethod
    def from_genome(
        cls,
        *,
        genetic_architecture: GeneticArchitecture,
        genome: Genome,
        age: int = 0,
        energy: int = 100,
        body_mass: int | None = None,
        development_model: DevelopmentModel | None = None,
        rng: random.Random | None = None,
        mating_type: str = "default",
        x: int = 0,
        y: int = 0,
    ) -> Organism:
        """Create an organism and express its genetic phenotype from its genome.

        When ``body_mass`` is omitted and the genetic phenotype defines the
        canonical ``adult_body_mass`` trait, current mass initially matches that
        target. This preserves fixed-size behavior until a developmental model
        is configured. Genomes without that trait default to one mass unit.

        Args:
            genetic_architecture: Shared architecture used to validate and
                express the genome.
            genome: Inherited genetic state.
            age: Initial organism age in simulation timesteps.
            energy: Initial organism energy.
            body_mass: Optional initial current physical mass. If omitted,
                the realized adult-body-mass target is used when available,
                otherwise one.
            development_model: Optional model used to realize individual
                developmental targets. Defaults to deterministic development.
            rng: Random-number generator used by development_model. Required
                when a development_model is explicitly supplied.
            mating_type: Immutable reproductive mating-type label.
            x: Initial horizontal world coordinate.
            y: Initial vertical world coordinate.

        Returns:
            Organism with a genetic phenotype consistent with its genome.
        """
        if not isinstance(genetic_architecture, GeneticArchitecture):
            raise TypeError(
                "genetic_architecture must be an instance of GeneticArchitecture."
            )

        genetic_phenotype = genetic_architecture.express(genome)

        if development_model is None:
            development_model = DeterministicDevelopment()
            development_rng = random.Random(0)
        else:
            if rng is None:
                raise ValueError("rng is required when development_model is supplied.")
            if not isinstance(rng, random.Random):
                raise TypeError("rng must be an instance of random.Random.")
            development_rng = rng

        developmental_profile = realize_developmental_profile(
            development_model,
            genetic_phenotype,
            rng=development_rng,
        )

        if body_mass is None:
            if ADULT_BODY_MASS in developmental_profile:
                body_mass = developmental_profile.int_value(ADULT_BODY_MASS)
            else:
                body_mass = 1

        validators.validate_int_ge(
            body_mass,
            bound=1,
            name="body_mass",
        )

        return cls(
            age=age,
            energy=energy,
            body_mass=body_mass,
            genome=genome,
            genetic_phenotype=genetic_phenotype,
            developmental_profile=developmental_profile,
            mating_type=mating_type,
            x=x,
            y=y,
        )

    @property
    def id(self) -> int:
        """Return the organism's permanent world ID.

        Returns:
            Assigned organism ID.

        Raises:
            RuntimeError: If the organism has not been assigned an ID.
        """
        if self._id is None:
            raise RuntimeError("Organism has not been assigned an ID.")
        return self._id

    def _assign_id(self, organism_id: int) -> None:
        """Assign the organism's permanent ID."""
        if self._id is not None:
            raise RuntimeError("Organism already has an assigned ID.")

        validators.validate_int_ge(
            organism_id,
            0,
            "organism_id",
        )

        self._id = organism_id

    def age_step(self) -> None:
        """Increase the organism's age by one timestep."""
        self.age += 1

    def change_energy(self, delta: int) -> None:
        """Change the organism's energy by a signed amount.

        Energy is clamped to zero if the loss exceeds the organism's current
        energy.

        Args:
            delta: Signed amount by which to change the organism's energy.

        Raises:
            TypeError: If delta is not an integer.
        """
        validators.validate_int(
            value=delta,
            name="delta",
        )

        new_energy = self.energy + delta
        if new_energy < 0:
            new_energy = 0

        self.energy = new_energy
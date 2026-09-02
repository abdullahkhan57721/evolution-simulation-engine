"""Biological offspring production from already-propagated genetic state."""

from __future__ import annotations

import random

import attrs

from evo_engine.development.context import DevelopmentLocation
from evo_engine.development.models import (
    DeterministicDevelopment,
    DevelopmentModel,
    realize_developmental_profile,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics import GENETIC_ARCHITECTURE
from evo_engine.genetics.genome import Genome
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.production import EntityProductionModel
from evo_engine.reproduction.birth_mass import (
    AdultBodyMassAtBirth,
    OffspringBodyMassModel,
)
from evo_engine.reproduction.mating_types import (
    FixedMatingType,
    OffspringMatingTypeModel,
    determine_offspring_mating_type,
)
from evo_engine.reproduction.placement import (
    OffspringPlacement,
    RandomProductionSourceLocation,
)
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


@attrs.frozen(slots=True, kw_only=True)
class OffspringProductionContext:
    """Provide simulation state and committed newborn energy to production."""

    simulation_state: SimulationState = attrs.field(
        validator=attrs.validators.instance_of(SimulationState),
    )
    initial_energy: int = attrs.field(
        validator=attrs_validators.validate_int_ge(1),
    )


@attrs.frozen(slots=True, kw_only=True)
class BiologicalOffspringProduction(
    EntityProductionModel[Genome, Organism, OffspringProductionContext, Organism]
):
    """Produce a newborn organism from an already-propagated genome."""

    development_model: DevelopmentModel = attrs.field(factory=DeterministicDevelopment)
    offspring_placement: OffspringPlacement = attrs.field(
        factory=RandomProductionSourceLocation
    )
    offspring_body_mass_model: OffspringBodyMassModel = attrs.field(
        factory=AdultBodyMassAtBirth
    )
    offspring_mating_type_model: OffspringMatingTypeModel = attrs.field(
        factory=lambda: FixedMatingType(mating_type="default"),
    )

    def __attrs_post_init__(self) -> None:
        """Validate configured biological production policies."""
        required_methods = (
            (self.development_model, "develop", "development_model"),
            (self.offspring_placement, "choose_location", "offspring_placement"),
            (
                self.offspring_body_mass_model,
                "determine_body_mass",
                "offspring_body_mass_model",
            ),
            (
                self.offspring_mating_type_model,
                "determine_mating_type",
                "offspring_mating_type_model",
            ),
        )
        for policy, method_name, policy_name in required_methods:
            if not callable(getattr(policy, method_name, None)):
                raise TypeError(
                    f"{policy_name} must provide a callable {method_name} method."
                )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic traits required by configured production policies."""
        return collect_required_traits(
            self.development_model,
            self.offspring_placement,
            self.offspring_body_mass_model,
            self.offspring_mating_type_model,
        )

    def produce(
        self,
        state: Genome,
        *,
        source_entities: tuple[Organism, ...],
        context: OffspringProductionContext,
        rng: random.Random,
    ) -> Organism:
        """Produce a fully materialized newborn from a propagated genome."""
        if not isinstance(state, Genome):
            raise TypeError("state must be an instance of Genome.")
        if type(source_entities) is not tuple:
            raise TypeError("source_entities must be a tuple.")
        if not isinstance(rng, random.Random):
            raise TypeError("rng must be an instance of random.Random.")

        for index, source in enumerate(source_entities):
            if not isinstance(source, Organism):
                raise TypeError(
                    f"source_entities[{index}] must be an instance of Organism."
                )

        simulation_state = context.simulation_state
        architecture = simulation_state.context.require(GENETIC_ARCHITECTURE)
        architecture.validate_genome(state)
        genetic_phenotype = architecture.express(state)

        x, y = self.offspring_placement.choose_location(
            source_entities,
            simulation_state=simulation_state,
            rng=rng,
        )
        developmental_profile = realize_developmental_profile(
            self.development_model,
            genetic_phenotype,
            rng=rng,
            simulation_state=simulation_state,
            location=DevelopmentLocation(x=x, y=y),
        )
        body_mass = self.offspring_body_mass_model.determine_body_mass(
            developmental_profile,
            source_entities,
            simulation_state=simulation_state,
        )
        validators.validate_int_ge(
            body_mass,
            bound=1,
            name="offspring initial body mass",
        )
        mating_type = determine_offspring_mating_type(
            self.offspring_mating_type_model,
            source_entities,
            offspring_genome=state,
            offspring_genetic_phenotype=genetic_phenotype,
            offspring_developmental_profile=developmental_profile,
            simulation_state=simulation_state,
            rng=rng,
        )
        return Organism(
            age=0,
            energy=context.initial_energy,
            body_mass=body_mass,
            genome=state,
            genetic_phenotype=genetic_phenotype,
            developmental_profile=developmental_profile,
            mating_type=mating_type,
            x=x,
            y=y,
        )

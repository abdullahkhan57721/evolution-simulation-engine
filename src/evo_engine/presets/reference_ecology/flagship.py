"""Compose the reference ecology into the v0.1 flagship evolution demo."""

from __future__ import annotations

from collections.abc import Iterable

import attrs

from evo_engine.engine import Observer, Simulation
from evo_engine.genetics import (
    GENETIC_ARCHITECTURE,
    MAX_INTAKE_RATE,
    GeneticArchitecture,
)
from evo_engine.presets.reference_ecology.builders import ReferenceEcology
from evo_engine.presets.reference_ecology.config import ReferenceEcologyConfig
from evo_engine.presets.reference_ecology.genetics import (
    build_balanced_reference_trait_world,
)
from evo_engine.presets.reference_ecology.observable import build_reference_ecology
from evo_engine.telemetry import TelemetryObserver
from evo_engine.validation import validators
from evo_engine.world import WorldState

FLAGSHIP_MAX_INTAKE_SEED = 41
FLAGSHIP_MAX_INTAKE_ROBUSTNESS_SEEDS = (11, 23, 37, 41, 59, 73, 89, 101)
FLAGSHIP_LOW_MAX_INTAKE_RATE = 2
FLAGSHIP_HIGH_MAX_INTAKE_RATE = 8


@attrs.frozen(slots=True, kw_only=True)
class FlagshipMaxIntakeSpecification:
    """Describe the standing-variation setup for the flagship demonstration.

    The embedded reference configuration supplies the ordinary ecological and
    life-history mechanisms. ``low_max_intake_rate`` and
    ``high_max_intake_rate`` describe the two deliberately heterogeneous founder
    genomes layered onto that reference baseline.

    This is an illustrative integration scenario, not a calibrated ecological
    model.
    """

    reference_config: ReferenceEcologyConfig = attrs.field(
        validator=attrs.validators.instance_of(ReferenceEcologyConfig)
    )
    low_max_intake_rate: int = FLAGSHIP_LOW_MAX_INTAKE_RATE
    high_max_intake_rate: int = FLAGSHIP_HIGH_MAX_INTAKE_RATE

    def __attrs_post_init__(self) -> None:
        """Validate the founder-variation contract."""
        validators.validate_int_ge(
            self.low_max_intake_rate,
            bound=0,
            name="low_max_intake_rate",
        )
        validators.validate_int_ge(
            self.high_max_intake_rate,
            bound=0,
            name="high_max_intake_rate",
        )
        if self.low_max_intake_rate >= self.high_max_intake_rate:
            raise ValueError(
                "low_max_intake_rate must be less than high_max_intake_rate."
            )
        if self.reference_config.initial_population % 4 != 0:
            raise ValueError(
                "flagship founder population must be divisible by 4 so intake "
                "variants remain balanced across reference mating types."
            )


def build_flagship_max_intake_specification(
    *,
    seed: int = FLAGSHIP_MAX_INTAKE_SEED,
    max_steps: int = 40,
) -> FlagshipMaxIntakeSpecification:
    """Build the evidence-backed canonical flagship specification.

    Args:
        seed: Simulation seed. Defaults to the canonical cinematic seed.
        max_steps: Number of simulation steps. Defaults to the measured 40-step
            demonstration window.

    Returns:
        Immutable specification containing the reference configuration and the
        two founder intake-capacity variants.
    """
    baseline = ReferenceEcologyConfig()
    reference_config = attrs.evolve(
        baseline,
        initial_population=20,
        initial_energy=30,
        max_steps=max_steps,
        seed=seed,
        mutation_probability_ppm=0,
        resource_generation_amount=6,
        resource_deposits_per_step=32,
        mating_radius=1,
        traits=attrs.evolve(
            baseline.traits,
            attack_strength=0,
            defense=1,
        ),
    )
    return FlagshipMaxIntakeSpecification(reference_config=reference_config)


def build_flagship_max_intake_world(
    genetic_architecture: GeneticArchitecture,
    specification: FlagshipMaxIntakeSpecification,
) -> WorldState:
    """Build balanced low- and high-intake homozygous reference founders.

    Founder placement and mating-type assignment retain the deterministic
    reference conventions. The four-position intake pattern gives each of the
    two alternating reference mating types equal representation of both intake
    variants, avoiding a founder genotype/mating-type confound.

    Args:
        genetic_architecture: Reference genetic architecture shared by founders.
        specification: Flagship standing-variation specification.

    Returns:
        World containing a balanced heterogeneous founder population.
    """
    if not isinstance(genetic_architecture, GeneticArchitecture):
        raise TypeError("genetic_architecture must be a GeneticArchitecture.")
    if not isinstance(specification, FlagshipMaxIntakeSpecification):
        raise TypeError("specification must be a FlagshipMaxIntakeSpecification.")

    return build_balanced_reference_trait_world(
        genetic_architecture,
        trait_name=MAX_INTAKE_RATE,
        variant_values=(
            specification.low_max_intake_rate,
            specification.high_max_intake_rate,
        ),
        config=specification.reference_config,
    )


def build_flagship_max_intake_ecology(
    specification: FlagshipMaxIntakeSpecification | None = None,
    *,
    additional_observers: Iterable[Observer] = (),
    additional_telemetry_observers: Iterable[TelemetryObserver] = (),
) -> ReferenceEcology:
    """Build the flagship demo by replacing only reference founder state.

    The reference ecology continues to own lifecycle processes, behavior,
    genetics, observation, and telemetry. This composer deliberately changes
    only the initial founder genomes and the evidence-backed numerical
    configuration, then reuses the reference simulation context and engine.

    Args:
        specification: Optional explicit flagship specification. Defaults to the
            canonical seed-41, 40-step scenario.
        additional_observers: Extra committed-state observers to attach.
        additional_telemetry_observers: Extra committed-telemetry observers to
            attach.

    Returns:
        Reference ecology bundle initialized with balanced standing variation.
    """
    resolved = specification or build_flagship_max_intake_specification()
    if not isinstance(resolved, FlagshipMaxIntakeSpecification):
        raise TypeError(
            "specification must be a FlagshipMaxIntakeSpecification or None."
        )

    ecology = build_reference_ecology(
        resolved.reference_config,
        additional_observers=additional_observers,
        additional_telemetry_observers=additional_telemetry_observers,
    )
    genetic_architecture = ecology.simulation.context.require(GENETIC_ARCHITECTURE)
    flagship_world = build_flagship_max_intake_world(
        genetic_architecture,
        resolved,
    )
    flagship_simulation = Simulation(
        initial_domain_state=flagship_world,
        seed=resolved.reference_config.seed,
        context=ecology.simulation.context,
    )
    return attrs.evolve(ecology, simulation=flagship_simulation)

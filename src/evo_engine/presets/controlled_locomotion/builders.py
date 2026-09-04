"""Builders for the deliberately minimal controlled locomotion composition."""

from __future__ import annotations

import math
import random
from collections.abc import Iterable

from evo_engine.behavior import (
    ENERGY_ACQUISITION,
    FixedMovementIntent,
    FixedSensoryAccuracy,
    FixedSensoryRange,
    NearestResourceTarget,
    UnrestrictedBehavior,
)
from evo_engine.biology import BiologicalSimulationSpec
from evo_engine.characteristics import GeneticPhenotypeCharacteristics
from evo_engine.energetics import PowerLawLocomotionCost, SpendToZero
from evo_engine.engine import (
    MaxSteps,
    Observer,
    Process,
    SequentialStepCoordinator,
    StageCoordinator,
)
from evo_engine.feeding import FullAssimilation
from evo_engine.genetics import ClonalInheritance
from evo_engine.observation import EventRecorder
from evo_engine.presets.controlled_locomotion.config import ControlledLocomotionConfig
from evo_engine.presets.controlled_locomotion.genetics import (
    build_controlled_locomotion_genetic_architecture,
    build_controlled_locomotion_world,
)
from evo_engine.processes import Movement, Reproduction, ResourceConsumption, Starvation
from evo_engine.reproduction import (
    FixedBodyMassAtBirth,
    FixedEnergyInvestment,
    MinimumEnergyEligibility,
    SingleParent,
)
from evo_engine.resolvers import AcceptAll
from evo_engine.resolvers.resource_allocation import RandomOrder
from evo_engine.spatial.boundary_conditions import Clamped
from evo_engine.telemetry import TelemetryObserver


class _StationaryFallbackMovement:
    """Stay in place when no resource target exists."""

    def choose_displacement(
        self,
        *,
        rng: random.Random,
        max_speed: int,
    ) -> tuple[int, int]:
        """Return zero displacement without consuming RNG state."""
        return (0, 0)


def build_controlled_locomotion_spec(
    config: ControlledLocomotionConfig | None = None,
    *,
    observers: Iterable[Observer] = (),
    telemetry_observers: Iterable[TelemetryObserver] = (),
) -> BiologicalSimulationSpec:
    """Build the complete minimal clonal locomotion simulation specification.

    The lifecycle contains only target-directed movement, local resource
    consumption, one-parent clonal reproduction, and starvation cleanup. It has
    no mate search, predation, metabolism, growth, aging, resource generation,
    or capacity-maintenance cost. ``max_speed`` is therefore the only inherited
    variable and locomotion-use expenditure is the only movement-specific cost.

    Args:
        config: Controlled E2 configuration. Defaults to canonical values.
        observers: State observers attached to committed states.
        telemetry_observers: Event observers attached to committed steps.

    Returns:
        Dependency-validatable biological simulation specification.
    """
    resolved = ControlledLocomotionConfig() if config is None else config
    if not isinstance(resolved, ControlledLocomotionConfig):
        raise TypeError("config must be a ControlledLocomotionConfig or None.")

    architecture = build_controlled_locomotion_genetic_architecture()
    world = build_controlled_locomotion_world(architecture, resolved)

    movement_stage = _accept_all_stage(
        Movement(
            movement_pattern=_StationaryFallbackMovement(),
            boundary_condition=Clamped(),
            locomotion_cost_model=PowerLawLocomotionCost(
                coefficient=resolved.locomotion_cost_coefficient,
                mass_exponent=0,
                distance_exponent=resolved.locomotion_distance_exponent,
            ),
            max_speed_source=GeneticPhenotypeCharacteristics(),
            energy_expenditure_policy=SpendToZero(),
            movement_intent_model=FixedMovementIntent(
                behavioral_purpose=ENERGY_ACQUISITION,
            ),
            movement_target_model=NearestResourceTarget(
                sensory_range_model=FixedSensoryRange(
                    radius=_full_world_sensory_radius(resolved),
                ),
                sensory_accuracy_model=FixedSensoryAccuracy(accuracy_percent=100),
            ),
        )
    )
    feeding_stage = StageCoordinator(
        processes=(
            ResourceConsumption(
                requested_amount=resolved.resource_request_amount,
                assimilation_model=FullAssimilation(),
            ),
        ),
        resolver=RandomOrder(),
    )
    reproduction_stage = _accept_all_stage(
        Reproduction(
            eligibility=MinimumEnergyEligibility(
                minimum_energy=resolved.reproduction_minimum_energy,
            ),
            reproductive_group_selection=SingleParent(),
            inheritance_model=ClonalInheritance(),
            reproductive_energy_investment=FixedEnergyInvestment(
                amount=resolved.reproduction_energy_investment,
            ),
            energy_expenditure_policy=SpendToZero(),
            offspring_body_mass_model=FixedBodyMassAtBirth(
                body_mass=resolved.body_mass,
            ),
        )
    )
    starvation_stage = _accept_all_stage(Starvation())

    return BiologicalSimulationSpec(
        initial_world_state=world,
        genetic_architecture=architecture,
        step_coordinator=SequentialStepCoordinator(
            stages=(
                movement_stage,
                feeding_stage,
                reproduction_stage,
                starvation_stage,
            )
        ),
        stopping_condition=MaxSteps(max_steps=resolved.max_steps),
        seed=resolved.seed,
        behavior_selection_model=UnrestrictedBehavior(),
        observers=tuple(observers),
        telemetry_observers=tuple(telemetry_observers),
    )


def build_controlled_locomotion_event_recorder_spec(
    config: ControlledLocomotionConfig | None = None,
) -> tuple[BiologicalSimulationSpec, EventRecorder]:
    """Build a controlled locomotion spec with authoritative event recording.

    Args:
        config: Controlled E2 configuration. Defaults to canonical values.

    Returns:
        Simulation specification and its attached event recorder.
    """
    recorder = EventRecorder()
    return (
        build_controlled_locomotion_spec(
            config,
            telemetry_observers=(recorder,),
        ),
        recorder,
    )


def _accept_all_stage(*processes: Process) -> StageCoordinator:
    return StageCoordinator(
        processes=processes,
        resolver=AcceptAll(),
    )


def _full_world_sensory_radius(config: ControlledLocomotionConfig) -> int:
    return math.ceil(math.hypot(config.width - 1, config.height - 1))

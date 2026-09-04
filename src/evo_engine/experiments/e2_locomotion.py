"""Focused mechanics assays for the controlled E2 locomotion composition."""

from __future__ import annotations

import attrs

from evo_engine.experiments.locomotion import (
    AppliedMovementMeasurement,
    measure_applied_movement,
)
from evo_engine.observation import EventRecorder
from evo_engine.presets.controlled_locomotion import (
    CONTROLLED_MAX_SPEED_MAXIMUM,
    ControlledLocomotionConfig,
    ControlledLocomotionFounder,
    ControlledResourceDeposit,
    build_controlled_locomotion_spec,
)
from evo_engine.processes import Movement
from evo_engine.validation import attrs_validators, validators


@attrs.frozen(slots=True, kw_only=True)
class LocomotionMechanicsCase:
    """Define one deterministic target-directed mechanics assay.

    Attributes:
        max_speed: Inherited maximum movement capacity.
        target_dx: Horizontal target offset from the founder.
        target_dy: Vertical target offset from the founder.
        seed: Simulation seed retained for reproducibility even though the
            single-organism canonical assay consumes no stochastic target or
            movement draw.
    """

    max_speed: int = attrs.field(
        validator=attrs_validators.validate_int_in_range(
            0,
            CONTROLLED_MAX_SPEED_MAXIMUM,
        ),
    )
    target_dx: int = attrs.field(validator=attrs_validators.validate_int)
    target_dy: int = attrs.field(validator=attrs_validators.validate_int)
    seed: int = attrs.field(default=17, validator=attrs_validators.validate_int)

    def __attrs_post_init__(self) -> None:
        """Require a target distinct from the founder coordinate."""
        if self.target_dx == 0 and self.target_dy == 0:
            raise ValueError("target offset must be nonzero for a mechanics case.")


@attrs.frozen(slots=True, kw_only=True)
class LocomotionMechanicsOutcome:
    """Store one mechanics case and its evidence-derived movement measurement.

    Attributes:
        case: Predeclared mechanics case.
        attempted_dx: Horizontal displacement recorded by the applied event.
        attempted_dy: Vertical displacement recorded by the applied event.
        target_x: In-bounds resource target x coordinate.
        target_y: In-bounds resource target y coordinate.
        target_reached: Whether the committed endpoint equals the target.
        measurement: E1 measurement derived from authoritative applied evidence.
    """

    case: LocomotionMechanicsCase
    attempted_dx: int
    attempted_dy: int
    target_x: int
    target_y: int
    target_reached: bool
    measurement: AppliedMovementMeasurement

    def __attrs_post_init__(self) -> None:
        """Validate typed mechanics evidence."""
        if not isinstance(self.case, LocomotionMechanicsCase):
            raise TypeError("case must be a LocomotionMechanicsCase.")
        validators.validate_int(self.attempted_dx, name="attempted_dx")
        validators.validate_int(self.attempted_dy, name="attempted_dy")
        validators.validate_int_ge(self.target_x, bound=0, name="target_x")
        validators.validate_int_ge(self.target_y, bound=0, name="target_y")
        validators.validate_bool(self.target_reached, name="target_reached")
        if not isinstance(self.measurement, AppliedMovementMeasurement):
            raise TypeError("measurement must be an AppliedMovementMeasurement.")


def run_locomotion_mechanics_case(
    case: LocomotionMechanicsCase,
) -> LocomotionMechanicsOutcome:
    """Run one deterministic target-directed E2 mechanics case.

    The founder is padded away from every world edge, the target is guaranteed
    in bounds, reproduction is disabled by an unreachable energy threshold, and
    one committed step is recorded. The returned displacement and cost are then
    derived through E1's authoritative applied-movement measurement path.

    Args:
        case: Predeclared capacity and target-bearing case.

    Returns:
        Applied-event mechanics outcome for the single founder.
    """
    if not isinstance(case, LocomotionMechanicsCase):
        raise TypeError("case must be a LocomotionMechanicsCase.")

    padding = case.max_speed + 2
    start_x = padding - min(0, case.target_dx)
    start_y = padding - min(0, case.target_dy)
    target_x = start_x + case.target_dx
    target_y = start_y + case.target_dy
    width = max(start_x, target_x) + padding + 1
    height = max(start_y, target_y) + padding + 1
    config = ControlledLocomotionConfig(
        width=width,
        height=height,
        max_steps=1,
        seed=case.seed,
        founders=(
            ControlledLocomotionFounder(
                max_speed=case.max_speed,
                x=start_x,
                y=start_y,
            ),
        ),
        resource_deposits=(
            ControlledResourceDeposit(x=target_x, y=target_y, amount=100),
        ),
        reproduction_minimum_energy=10_000,
    )
    recorder = EventRecorder()
    spec = build_controlled_locomotion_spec(
        config,
        telemetry_observers=(recorder,),
    )
    compiled = spec.compile()
    compiled.engine.run(compiled.simulation)

    applied = next(
        event for event in recorder.events if isinstance(event.event, Movement.Event)
    )
    event = applied.event
    measurement = measure_applied_movement(applied)
    organism = compiled.simulation.state.domain_state.organisms[event.organism_id]
    return LocomotionMechanicsOutcome(
        case=case,
        attempted_dx=event.dx,
        attempted_dy=event.dy,
        target_x=target_x,
        target_y=target_y,
        target_reached=(organism.x, organism.y) == (target_x, target_y),
        measurement=measurement,
    )


def run_locomotion_bearing_assay(
    *,
    max_speed: int,
    target_offsets: tuple[tuple[int, int], ...],
    seed: int = 17,
) -> tuple[LocomotionMechanicsOutcome, ...]:
    """Run the same locomotor capacity against several target bearings.

    Args:
        max_speed: Shared inherited movement capacity.
        target_offsets: Nonzero target vectors defining bearings and distances.
        seed: Shared simulation seed for reproducibility.

    Returns:
        Mechanics outcomes in caller-supplied bearing order.
    """
    validators.validate_tuple(target_offsets, name="target_offsets")
    if not target_offsets:
        raise ValueError("target_offsets must contain at least one bearing.")
    outcomes: list[LocomotionMechanicsOutcome] = []
    for index, offset in enumerate(target_offsets):
        if type(offset) is not tuple or len(offset) != 2:
            raise TypeError(f"target_offsets[{index}] must be a two-integer tuple.")
        dx, dy = offset
        outcomes.append(
            run_locomotion_mechanics_case(
                LocomotionMechanicsCase(
                    max_speed=max_speed,
                    target_dx=dx,
                    target_dy=dy,
                    seed=seed,
                )
            )
        )
    return tuple(outcomes)

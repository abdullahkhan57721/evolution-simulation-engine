"""Configuration values for the controlled clonal locomotion experiments."""

from __future__ import annotations

import attrs

from evo_engine.validation import attrs_validators, validators

CONTROLLED_MAX_SPEED_MAXIMUM = 20


@attrs.frozen(slots=True, kw_only=True)
class ControlledLocomotionFounder:
    """Define one deterministic founder in the controlled locomotion system.

    Attributes:
        max_speed: Inherited maximum Euclidean movement capacity per timestep.
        x: Initial horizontal world coordinate.
        y: Initial vertical world coordinate.
    """

    max_speed: int = attrs.field(
        validator=attrs_validators.validate_int_in_range(
            0,
            CONTROLLED_MAX_SPEED_MAXIMUM,
        ),
    )
    x: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    y: int = attrs.field(validator=attrs_validators.validate_int_ge(0))


@attrs.frozen(slots=True, kw_only=True)
class ControlledResourceDeposit:
    """Define one deterministic initial resource deposit.

    Attributes:
        x: Horizontal world coordinate.
        y: Vertical world coordinate.
        amount: Positive initial resource units at the coordinate.
    """

    x: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    y: int = attrs.field(validator=attrs_validators.validate_int_ge(0))
    amount: int = attrs.field(validator=attrs_validators.validate_int_gt(0))


@attrs.frozen(slots=True, kw_only=True)
class ControlledLocomotionConfig:
    """Configure the deliberately minimal E2 locomotion composition.

    Only ``max_speed`` is inherited. Body mass, sensing, feeding, and
    reproduction parameters are simulation-wide constants so they cannot create
    nonfocal genetic variation. Resources and founders are supplied explicitly
    to keep initialization deterministic and scientifically inspectable.

    Attributes:
        width: World width in grid cells.
        height: World height in grid cells.
        max_steps: Fixed simulation horizon in timesteps.
        seed: Simulation RNG seed.
        founders: Ordered deterministic founder definitions.
        resource_deposits: Deterministic initial resource deposits.
        initial_energy: Shared founder energy.
        body_mass: Shared current body mass for founders and offspring.
        locomotion_cost_coefficient: Fixed locomotion-use cost coefficient.
        locomotion_distance_exponent: Power applied to attempted travel distance.
        resource_request_amount: Fixed resource demand per feeding attempt.
        reproduction_minimum_energy: Fixed energy threshold for clonal reproduction.
        reproduction_energy_investment: Fixed energy invested in each clone.
    """

    width: int = attrs.field(
        default=31,
        validator=attrs_validators.validate_int_ge(1),
    )
    height: int = attrs.field(
        default=31,
        validator=attrs_validators.validate_int_ge(1),
    )
    max_steps: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    seed: int = attrs.field(default=42, validator=attrs_validators.validate_int)
    founders: tuple[ControlledLocomotionFounder, ...] = attrs.field(
        factory=lambda: (ControlledLocomotionFounder(max_speed=1, x=15, y=15),),
        validator=attrs.validators.instance_of(tuple),
    )
    resource_deposits: tuple[ControlledResourceDeposit, ...] = attrs.field(
        factory=lambda: (ControlledResourceDeposit(x=25, y=15, amount=100),),
        validator=attrs.validators.instance_of(tuple),
    )
    initial_energy: int = attrs.field(
        default=100,
        validator=attrs_validators.validate_int_ge(1),
    )
    body_mass: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(1),
    )
    locomotion_cost_coefficient: int = attrs.field(
        default=1,
        validator=attrs_validators.validate_int_ge(0),
    )
    locomotion_distance_exponent: int = attrs.field(
        default=2,
        validator=attrs_validators.validate_int_ge(1),
    )
    resource_request_amount: int = attrs.field(
        default=20,
        validator=attrs_validators.validate_int_ge(1),
    )
    reproduction_minimum_energy: int = attrs.field(
        default=120,
        validator=attrs_validators.validate_int_ge(1),
    )
    reproduction_energy_investment: int = attrs.field(
        default=20,
        validator=attrs_validators.validate_int_ge(1),
    )

    def __attrs_post_init__(self) -> None:
        """Validate deterministic population and resource geometry."""
        validators.validate_tuple(self.founders, name="founders")
        if not self.founders:
            raise ValueError("founders must contain at least one founder.")
        for index, founder in enumerate(self.founders):
            if not isinstance(founder, ControlledLocomotionFounder):
                raise TypeError(
                    f"founders[{index}] must be a ControlledLocomotionFounder."
                )
            self._validate_coordinate(founder.x, founder.y, name=f"founders[{index}]")

        validators.validate_tuple(
            self.resource_deposits,
            name="resource_deposits",
        )
        if not self.resource_deposits:
            raise ValueError("resource_deposits must contain at least one deposit.")

        seen_coordinates: set[tuple[int, int]] = set()
        for index, deposit in enumerate(self.resource_deposits):
            if not isinstance(deposit, ControlledResourceDeposit):
                raise TypeError(
                    f"resource_deposits[{index}] must be a ControlledResourceDeposit."
                )
            self._validate_coordinate(
                deposit.x,
                deposit.y,
                name=f"resource_deposits[{index}]",
            )
            coordinate = (deposit.x, deposit.y)
            if coordinate in seen_coordinates:
                raise ValueError(
                    "resource_deposits must not contain duplicate coordinates."
                )
            seen_coordinates.add(coordinate)

    def _validate_coordinate(self, x: int, y: int, *, name: str) -> None:
        if x >= self.width or y >= self.height:
            raise ValueError(
                f"{name} coordinate ({x}, {y}) must lie inside "
                f"the {self.width}x{self.height} world."
            )

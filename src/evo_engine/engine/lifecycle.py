"""Factories for common ordered simulation lifecycles."""

from __future__ import annotations

from evo_engine.engine.stage_coordinator import StageCoordinator
from evo_engine.engine.step_coordinator import SequentialStepCoordinator


def build_standard_lifecycle(
    *,
    starvation_stage: StageCoordinator,
    maximum_age_mortality_stage: StageCoordinator,
    metabolism_stage: StageCoordinator,
    aging_stage: StageCoordinator,
    environment_stage: StageCoordinator | None = None,
    movement_stage: StageCoordinator | None = None,
    predation_stage: StageCoordinator | None = None,
    resource_consumption_stage: StageCoordinator | None = None,
    growth_stage: StageCoordinator | None = None,
    reproduction_stage: StageCoordinator | None = None,
) -> SequentialStepCoordinator:
    """Build the engine's standard ecological lifecycle.

    The lifecycle establishes a recommended ordering without embedding that
    ordering in any individual process. Optional ecological stages are omitted
    when not supplied.

    Mortality uses checkpoints. Starvation is checked at entry, after mandatory
    metabolism, and after reproduction or other late voluntary expenditures.
    Maximum-age mortality is checked at entry and again immediately after Aging
    increments age.

    Aging marks completion of the timestep before reproduction occurs at the
    end-of-step boundary. This keeps newborns at age zero during their birth
    step while making age equal completed timesteps lived. An organism with
    maximum age 5 is removed when its age becomes 5, before reproduction at
    that boundary and before it could begin a sixth timestep.

    Args:
        starvation_stage: Stage removing zero-energy organisms.
        maximum_age_mortality_stage: Stage removing organisms at maximum age.
        metabolism_stage: Mandatory maintenance-energy stage.
        aging_stage: Stage incrementing age after somatic/ecological activity.
        environment_stage: Optional resource generation/decomposition stage.
        movement_stage: Optional movement stage.
        predation_stage: Optional predation stage.
        resource_consumption_stage: Optional environmental feeding stage.
        growth_stage: Optional somatic-growth stage.
        reproduction_stage: Optional end-of-step reproduction stage.

    Returns:
        Sequential coordinator implementing the standard lifecycle.
    """
    ordered_stages: tuple[StageCoordinator | None, ...] = (
        starvation_stage,
        maximum_age_mortality_stage,
        metabolism_stage,
        starvation_stage,
        environment_stage,
        movement_stage,
        predation_stage,
        resource_consumption_stage,
        growth_stage,
        aging_stage,
        maximum_age_mortality_stage,
        reproduction_stage,
        starvation_stage,
    )

    return SequentialStepCoordinator(
        stages=tuple(stage for stage in ordered_stages if stage is not None),
    )

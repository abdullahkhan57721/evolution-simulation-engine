"""Biological lifecycle composition built from domain-neutral coordinators."""

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
    """Build the standard biological/ecological lifecycle.

    This ordering is a biological composition policy, not simulation-kernel
    infrastructure. The domain-neutral engine only executes the resulting
    sequence of stages.

    Args:
        starvation_stage: Stage removing zero-energy organisms.
        maximum_age_mortality_stage: Stage removing organisms at maximum age.
        metabolism_stage: Mandatory maintenance-energy stage.
        aging_stage: Stage incrementing organism age.
        environment_stage: Optional resource/decomposition stage.
        movement_stage: Optional movement stage.
        predation_stage: Optional predation stage.
        resource_consumption_stage: Optional feeding stage.
        growth_stage: Optional somatic-growth stage.
        reproduction_stage: Optional reproduction stage.

    Returns:
        Sequential coordinator implementing the standard biological lifecycle.
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

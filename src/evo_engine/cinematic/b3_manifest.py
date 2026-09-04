"""Reproducibility metadata for the concrete B3 flagship cinematic director."""

from __future__ import annotations

import attrs

from evo_engine.cinematic.api import AnimationQuality
from evo_engine.cinematic.b3_director import (
    B3_DIRECTOR_MODE,
    B3_FLAGSHIP_SCENARIO_LABEL,
    B3_REPRESENTATIVE_SEED,
    B3FlagshipDirectorPlan,
)
from evo_engine.presets.reference_ecology.b3_flagship import B3_PRIMARY_STEP


@attrs.frozen(slots=True, kw_only=True)
class B3FlagshipRenderManifest:
    """Identify stable scientific/director inputs for one B3 flagship render."""

    scenario_label: str
    director_mode: str
    representative_seed: int
    first_step: int
    last_step: int
    primary_step: int
    focal_trait_name: str
    focal_label: str
    focal_lower_bound: int
    focal_upper_bound: int
    low_speed_organism_id: int
    low_speed_completed_step: int
    high_speed_organism_id: int
    high_speed_completed_step: int
    confirmation_seed_count: int
    confirmation_seeds: str
    includes_radius2_sensitivity: bool
    renderer_name: str
    renderer_version: str | None
    quality: AnimationQuality

    def to_dict(self) -> dict[str, str | int | bool | None]:
        """Return deterministic JSON-ready scalar metadata."""
        return {
            "scenario_label": self.scenario_label,
            "director_mode": self.director_mode,
            "representative_seed": self.representative_seed,
            "first_step": self.first_step,
            "last_step": self.last_step,
            "primary_step": self.primary_step,
            "focal_trait_name": self.focal_trait_name,
            "focal_label": self.focal_label,
            "focal_lower_bound": self.focal_lower_bound,
            "focal_upper_bound": self.focal_upper_bound,
            "low_speed_organism_id": self.low_speed_organism_id,
            "low_speed_completed_step": self.low_speed_completed_step,
            "high_speed_organism_id": self.high_speed_organism_id,
            "high_speed_completed_step": self.high_speed_completed_step,
            "confirmation_seed_count": self.confirmation_seed_count,
            "confirmation_seeds": self.confirmation_seeds,
            "includes_radius2_sensitivity": self.includes_radius2_sensitivity,
            "renderer_name": self.renderer_name,
            "renderer_version": self.renderer_version,
            "quality": self.quality,
        }


def build_b3_flagship_render_manifest(
    plan: B3FlagshipDirectorPlan,
    *,
    renderer_version: str | None,
    quality: AnimationQuality,
) -> B3FlagshipRenderManifest:
    """Build stable reproducibility metadata from one prepared B3 director plan."""
    if not isinstance(plan, B3FlagshipDirectorPlan):
        raise TypeError("plan must be a B3FlagshipDirectorPlan.")
    if quality not in ("low", "medium", "high"):
        raise ValueError("quality must be 'low', 'medium', or 'high'.")
    low_focus, high_focus = plan.representative_focus
    first_step = plan.control.timeline.frames[0].step_index
    last_step = plan.control.timeline.frames[-1].step_index
    seeds = tuple(point.seed for point in plan.confirmation_points)
    return B3FlagshipRenderManifest(
        scenario_label=B3_FLAGSHIP_SCENARIO_LABEL,
        director_mode=B3_DIRECTOR_MODE,
        representative_seed=B3_REPRESENTATIVE_SEED,
        first_step=first_step,
        last_step=last_step,
        primary_step=B3_PRIMARY_STEP,
        focal_trait_name=plan.focal_encoding.trait_name,
        focal_label=plan.focal_encoding.label,
        focal_lower_bound=plan.focal_encoding.lower_bound,
        focal_upper_bound=plan.focal_encoding.upper_bound,
        low_speed_organism_id=low_focus.episode.organism_id,
        low_speed_completed_step=low_focus.episode.completed_step_index,
        high_speed_organism_id=high_focus.episode.organism_id,
        high_speed_completed_step=high_focus.episode.completed_step_index,
        confirmation_seed_count=len(seeds),
        confirmation_seeds=",".join(str(seed) for seed in seeds),
        includes_radius2_sensitivity=plan.broad_patch_step30_mean is not None,
        renderer_name="manim",
        renderer_version=renderer_version,
        quality=quality,
    )


__all__ = ["B3FlagshipRenderManifest", "build_b3_flagship_render_manifest"]

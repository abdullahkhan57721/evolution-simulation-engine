"""Reproducibility metadata for deterministic cinematic presentation."""

from __future__ import annotations

from typing import Literal

import attrs

from evo_engine.cinematic.timeline import PortfolioAnimationTimeline
from evo_engine.validation import attrs_validators, validators

CinematicQuality = Literal["low", "medium", "high"]


@attrs.frozen(slots=True, kw_only=True)
class CinematicRenderManifest:
    """Record stable inputs needed to identify one cinematic presentation.

    The manifest contains scalar/string metadata only. It never stores output
    paths, simulation owners, mutable world state, recorders, or renderer objects.

    Attributes:
        scenario_label: Optional stable scenario/configuration label.
        seed: Optional deterministic simulation seed.
        first_step: First committed scientific step included, if any.
        last_step: Last committed scientific step included, if any.
        population_trait_name: Population-level trait highlighted by the replay.
        focal_trait_name: Optional per-organism focal scientific trait.
        focal_label: Optional human-readable focal legend label.
        focal_lower_bound: Optional lower bound of the shared focal scale.
        focal_upper_bound: Optional upper bound of the shared focal scale.
        director_mode: Cinematic composition mode; V3 I1 provides ``generic``.
        renderer_name: Renderer implementation identifier.
        renderer_version: Optional renderer package/version identifier.
        quality: Stable renderer quality preset.
    """

    scenario_label: str | None
    seed: int | None
    first_step: int | None
    last_step: int | None
    population_trait_name: str = attrs.field(
        validator=attrs_validators.validate_str,
    )
    focal_trait_name: str | None = None
    focal_label: str | None = None
    focal_lower_bound: int | None = None
    focal_upper_bound: int | None = None
    director_mode: str = "generic"
    renderer_name: str = "manim"
    renderer_version: str | None = None
    quality: CinematicQuality = "medium"

    def __attrs_post_init__(self) -> None:
        """Validate stable manifest scalar and semantic invariants."""
        _validate_optional_label(self.scenario_label, name="scenario_label")
        if self.seed is not None:
            validators.validate_int(self.seed, name="seed")
        _validate_step_range(self.first_step, self.last_step)
        _validate_required_label(
            self.population_trait_name,
            name="population_trait_name",
        )
        _validate_focal_manifest(self)
        _validate_required_label(self.director_mode, name="director_mode")
        _validate_required_label(self.renderer_name, name="renderer_name")
        _validate_optional_label(self.renderer_version, name="renderer_version")
        if self.quality not in ("low", "medium", "high"):
            raise ValueError("quality must be 'low', 'medium', or 'high'.")

    def to_dict(self) -> dict[str, str | int | None]:
        """Return deterministic JSON-ready scalar metadata."""
        return {
            "scenario_label": self.scenario_label,
            "seed": self.seed,
            "first_step": self.first_step,
            "last_step": self.last_step,
            "population_trait_name": self.population_trait_name,
            "focal_trait_name": self.focal_trait_name,
            "focal_label": self.focal_label,
            "focal_lower_bound": self.focal_lower_bound,
            "focal_upper_bound": self.focal_upper_bound,
            "director_mode": self.director_mode,
            "renderer_name": self.renderer_name,
            "renderer_version": self.renderer_version,
            "quality": self.quality,
        }


def build_cinematic_render_manifest(
    timeline: PortfolioAnimationTimeline,
    *,
    scenario_label: str | None = None,
    seed: int | None = None,
    renderer_version: str | None = None,
    quality: CinematicQuality = "medium",
) -> CinematicRenderManifest:
    """Build reproducibility metadata from one prepared cinematic timeline.

    Args:
        timeline: Immutable renderer-owned timeline prepared from committed data.
        scenario_label: Optional stable scenario/configuration identifier.
        seed: Optional deterministic simulation seed.
        renderer_version: Optional installed renderer version identifier.
        quality: Stable renderer quality preset.

    Returns:
        Immutable scalar-only cinematic render manifest.
    """
    if not isinstance(timeline, PortfolioAnimationTimeline):
        raise TypeError("timeline must be a PortfolioAnimationTimeline.")
    first_step = None if not timeline.frames else timeline.frames[0].step_index
    last_step = None if not timeline.frames else timeline.frames[-1].step_index
    focal = timeline.focal_encoding
    return CinematicRenderManifest(
        scenario_label=scenario_label,
        seed=seed,
        first_step=first_step,
        last_step=last_step,
        population_trait_name=timeline.trait_name,
        focal_trait_name=None if focal is None else focal.trait_name,
        focal_label=None if focal is None else focal.label,
        focal_lower_bound=None if focal is None else focal.lower_bound,
        focal_upper_bound=None if focal is None else focal.upper_bound,
        renderer_version=renderer_version,
        quality=quality,
    )


def _validate_step_range(first_step: int | None, last_step: int | None) -> None:
    if first_step is None or last_step is None:
        if first_step is not None or last_step is not None:
            raise ValueError("first_step and last_step must both be present or absent.")
        return
    validators.validate_int_ge(first_step, bound=0, name="first_step")
    validators.validate_int_ge(last_step, bound=0, name="last_step")
    if last_step < first_step:
        raise ValueError("last_step must be greater than or equal to first_step.")


def _validate_focal_manifest(manifest: CinematicRenderManifest) -> None:
    trait_name = manifest.focal_trait_name
    label = manifest.focal_label
    lower_bound = manifest.focal_lower_bound
    upper_bound = manifest.focal_upper_bound
    if (
        trait_name is None
        and label is None
        and lower_bound is None
        and upper_bound is None
    ):
        return
    if (
        trait_name is None
        or label is None
        or lower_bound is None
        or upper_bound is None
    ):
        raise ValueError("focal manifest fields must be supplied together.")
    _validate_required_label(trait_name, name="focal_trait_name")
    _validate_required_label(label, name="focal_label")
    lower = validators.validate_int(lower_bound, name="focal_lower_bound")
    upper = validators.validate_int(upper_bound, name="focal_upper_bound")
    if upper <= lower:
        raise ValueError("focal_upper_bound must be greater than focal_lower_bound.")


def _validate_required_label(value: str, *, name: str) -> None:
    validated = validators.validate_str(value, name=name)
    if not validated.strip():
        raise ValueError(f"{name} must not be empty or whitespace-only.")


def _validate_optional_label(value: str | None, *, name: str) -> None:
    if value is None:
        return
    _validate_required_label(value, name=name)

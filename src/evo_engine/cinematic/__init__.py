"""Deterministic cinematic presentation from committed simulation observations."""

from evo_engine.cinematic.api import AnimationQuality, render_portfolio_animation
from evo_engine.cinematic.events import (
    select_authoritative_events,
    select_authoritative_events_for_process,
    select_first_authoritative_event,
    select_first_authoritative_event_for_process,
)
from evo_engine.cinematic.interpolation import (
    CinematicPosition,
    interpolate_organism_position,
)
from evo_engine.cinematic.manifest import (
    CinematicRenderManifest,
    build_cinematic_render_manifest,
)
from evo_engine.cinematic.primitives import CinematicOrganismPrimitive
from evo_engine.cinematic.timeline import (
    PortfolioAnimationFrame,
    PortfolioAnimationTimeline,
    build_portfolio_animation_timeline,
)

__all__ = [
    "AnimationQuality",
    "CinematicOrganismPrimitive",
    "CinematicPosition",
    "CinematicRenderManifest",
    "PortfolioAnimationFrame",
    "PortfolioAnimationTimeline",
    "build_cinematic_render_manifest",
    "build_portfolio_animation_timeline",
    "interpolate_organism_position",
    "render_portfolio_animation",
    "select_authoritative_events",
    "select_authoritative_events_for_process",
    "select_first_authoritative_event",
    "select_first_authoritative_event_for_process",
]

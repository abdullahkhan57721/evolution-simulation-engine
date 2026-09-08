"""Compatibility facade for renderer-neutral world-presentation values.

The shared contract moved to :mod:`evo_engine.presentation.world` in Q0 after the
native desktop frontend became a second real consumer. The Streamlit reference UI
keeps this import path during migration.
"""

from evo_engine.presentation.world import (
    CarcassPrimitive,
    InterpolatedOrganismPosition,
    MovementTrail,
    OrganismPrimitive,
    ResourcePrimitive,
    WorldPresentationFrame,
    available_step_indices,
    build_world_presentation,
    individual_trait_frame_for_step,
    interpolate_organism_positions,
    organism_marker_size,
    spatial_frame_for_step,
)

__all__ = [
    "CarcassPrimitive",
    "InterpolatedOrganismPosition",
    "MovementTrail",
    "OrganismPrimitive",
    "ResourcePrimitive",
    "WorldPresentationFrame",
    "available_step_indices",
    "build_world_presentation",
    "individual_trait_frame_for_step",
    "interpolate_organism_positions",
    "organism_marker_size",
    "spatial_frame_for_step",
]

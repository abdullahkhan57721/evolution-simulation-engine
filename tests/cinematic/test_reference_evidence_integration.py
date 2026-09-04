"""Integration proof for cinematic preparation over merged B1/B2 evidence."""

from evo_engine.cinematic import build_portfolio_animation_timeline
from evo_engine.ecology import PatchyResourcePlacement, ResourcePatch
from evo_engine.genetics import MAX_SPEED
from evo_engine.observation import IndividualGeneticTraitRecorder, SpatialRecorder
from evo_engine.presentation import ContinuousTraitEncoding
from evo_engine.presets.reference_ecology.config import (
    REFERENCE_TRAIT_DOMAINS,
    ReferenceEcologyConfig,
)
from evo_engine.presets.reference_ecology.observable import build_reference_ecology


def test_cinematic_preparation_consumes_real_b1_b2_committed_evidence() -> None:
    patches = (
        ResourcePatch(center_x=1, center_y=1, radius=1),
        ResourcePatch(center_x=4, center_y=4, radius=1),
    )
    config = ReferenceEcologyConfig(
        width=6,
        height=6,
        initial_population=4,
        max_steps=2,
        seed=17,
        resource_deposits_per_step=2,
        resource_placement_model=PatchyResourcePlacement(patches=patches),
    )
    spatial_recorder = SpatialRecorder()
    individual_recorder = IndividualGeneticTraitRecorder(
        trait_names=(MAX_SPEED,),
    )
    ecology = build_reference_ecology(
        config,
        additional_observers=(spatial_recorder, individual_recorder),
    )

    ecology.engine.run(ecology.simulation)

    lower_bound, upper_bound = REFERENCE_TRAIT_DOMAINS[MAX_SPEED]
    encoding = ContinuousTraitEncoding(
        trait_name=MAX_SPEED,
        label="Maximum speed",
        lower_bound=lower_bound,
        upper_bound=upper_bound,
    )
    timeline = build_portfolio_animation_timeline(
        spatial_history=spatial_recorder.observations,
        population_history=ecology.recorder.observations,
        trait_name=MAX_SPEED,
        individual_trait_history=individual_recorder.observations,
        event_history=ecology.event_recorder.steps,
        focal_encoding=encoding,
    )

    assert timeline.frames
    assert timeline.focal_encoding is encoding
    for frame, individual_observation in zip(
        timeline.frames,
        individual_recorder.observations,
        strict=True,
    ):
        for organism in frame.organisms:
            committed_value = individual_observation.trait_value(
                organism.organism_id,
                MAX_SPEED,
            )
            assert organism.focal_value == committed_value
            assert organism.focal_normalized == encoding.normalize(committed_value)
        assert all(
            _inside_any_patch(resource.x, resource.y, patches)
            for resource in frame.spatial.resources
        )

    assert tuple(
        event
        for frame in timeline.frames
        for event in frame.applied_events
    ) == ecology.event_recorder.events


def _inside_any_patch(
    x: int,
    y: int,
    patches: tuple[ResourcePatch, ...],
) -> bool:
    return any(
        (x - patch.center_x) ** 2 + (y - patch.center_y) ** 2
        <= patch.radius**2
        for patch in patches
    )

"""Prepare the confirmed B3 flagship science for cinematic direction."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import attrs

from evo_engine.cinematic.timeline import (
    PortfolioAnimationTimeline,
    build_portfolio_animation_timeline,
)
from evo_engine.experiments.b3_flagship import (
    B3MatchedPairSummary,
    B3MovementConsumptionEpisode,
    B3RunEvidence,
    B3RunSummary,
    summarize_b3_run,
)
from evo_engine.genetics import MAX_SPEED
from evo_engine.presentation import ContinuousTraitEncoding
from evo_engine.presets.reference_ecology.b3_flagship import (
    B3_CONFIRMATION_SEEDS,
    B3_HIGH_MAX_SPEED,
    B3_LOW_MAX_SPEED,
    B3_PRIMARY_STEP,
    validate_b3_treatment_integrity,
)
from evo_engine.telemetry import AppliedEvent, StepTelemetry

B3_FLAGSHIP_SCENARIO_LABEL = "b3-environment-dependent-max-speed"
B3_REPRESENTATIVE_SEED = 5
B3_DIRECTOR_MODE = "b3_flagship"
B3_CONTROL_LABEL = "Uniform"
B3_TREATMENT_LABEL = "Compact patch"
B3_FOCAL_LABEL = "Maximum speed"

B3_BOUNDED_CONCLUSION = (
    "In the current reference ecology, changing only the spatial organization of "
    "otherwise matched renewable-resource generation changes the evolutionary fate "
    "of standing heritable max_speed variation. Compact radius-1 patches favor the "
    "high-speed strategy relative to matched uniform controls, while the uniform "
    "environment favors the lower-speed strategy in aggregate under the tested "
    "configuration."
)
B3_SCOPE_QUALIFIER = (
    "Illustrative reference-ecology result; not a species-calibrated prediction or "
    "a claim that patchiness universally favors high speed."
)

B3ActKey = Literal[
    "question",
    "environment",
    "individual",
    "repetition",
    "reproduction",
    "population",
    "robustness",
    "conclusion",
]


@attrs.frozen(slots=True, kw_only=True)
class B3DirectorAct:
    """Describe one fixed explanatory job in the B3 flagship film."""

    key: B3ActKey
    title: str
    headline: str


B3_FLAGSHIP_ACTS: tuple[B3DirectorAct, ...] = (
    B3DirectorAct(
        key="question",
        title="What changes selection?",
        headline=(
            "Same starting variation and renewable-resource amount. "
            "Different resource geography."
        ),
    ),
    B3DirectorAct(
        key="environment",
        title="One ecological manipulation",
        headline="Uniform placement versus two compact radius-1 resource patches.",
    ),
    B3DirectorAct(
        key="individual",
        title="Individual consequences",
        headline=(
            "Inherited maximum movement capacity changes ecological opportunity "
            "inside the same reference ecology."
        ),
    ),
    B3DirectorAct(
        key="repetition",
        title="Consequences repeat",
        headline=(
            "Selection emerges through repeated survival, feeding, and reproductive "
            "interactions — not a scripted fitness score."
        ),
    ),
    B3DirectorAct(
        key="reproduction",
        title="Differential reproductive contribution",
        headline="Founder reproductive contribution changes with environment.",
    ),
    B3DirectorAct(
        key="population",
        title="The population evolves",
        headline="Standing genetic variation changes across committed time.",
    ),
    B3DirectorAct(
        key="robustness",
        title="Representative, then replicated",
        headline=(
            "Seed 5 is an illustrative episode; the conclusion is supported across "
            "eight independent confirmation seeds."
        ),
    ),
    B3DirectorAct(
        key="conclusion",
        title="Bounded conclusion",
        headline=B3_BOUNDED_CONCLUSION,
    ),
)


@attrs.frozen(slots=True, kw_only=True)
class B3PreparedArm:
    """Pair one B3 completed run with renderer-ready committed evidence."""

    label: str
    evidence: B3RunEvidence
    summary: B3RunSummary
    timeline: PortfolioAnimationTimeline


@attrs.frozen(slots=True, kw_only=True)
class B3RepresentativeFocus:
    """Identify one B3-declared authoritative mechanism episode for direction."""

    episode: B3MovementConsumptionEpisode
    arm_label: str = B3_TREATMENT_LABEL

    @property
    def first_step(self) -> int:
        """Return the committed frame immediately before the authoritative event."""
        return self.episode.completed_step_index - 1

    @property
    def last_step(self) -> int:
        """Return the committed frame after the authoritative event has committed."""
        return self.episode.completed_step_index


@attrs.frozen(slots=True, kw_only=True)
class B3MatchedGeneticPoint:
    """Store representative matched genetic evidence on one common timestep."""

    step_index: int
    control_high_speed_frequency: float
    treatment_high_speed_frequency: float


@attrs.frozen(slots=True, kw_only=True)
class B3ConfirmationPoint:
    """Store one run-level independent confirmation contrast for presentation."""

    seed: int
    control_high_speed_frequency: float
    treatment_high_speed_frequency: float
    paired_effect: float


@attrs.frozen(slots=True, kw_only=True)
class B3FounderContributionPoint:
    """Store run-level founder reproductive contribution by focal strategy."""

    seed: int
    environment: Literal["uniform", "compact_patch"]
    low_speed_mean: float
    high_speed_mean: float


@attrs.frozen(slots=True, kw_only=True)
class B3FlagshipDirectorPlan:
    """Store deterministic B3-specific cinematic evidence and explanatory order.

    This is a concrete director value for the confirmed B3 flagship, not a generic
    film description language. Scientific values are copied or derived from the
    supplied committed B3 evidence; camera, timing, palette, and transitions remain
    renderer-owned.
    """

    control: B3PreparedArm
    treatment: B3PreparedArm
    focal_encoding: ContinuousTraitEncoding
    acts: tuple[B3DirectorAct, ...]
    representative_focus: tuple[B3RepresentativeFocus, ...]
    representative_genetic_trajectory: tuple[B3MatchedGeneticPoint, ...]
    confirmation_points: tuple[B3ConfirmationPoint, ...] = ()
    founder_contribution_points: tuple[B3FounderContributionPoint, ...] = ()
    broad_patch_step30_mean: float | None = None
    conclusion: str = B3_BOUNDED_CONCLUSION
    scope_qualifier: str = B3_SCOPE_QUALIFIER

    def __attrs_post_init__(self) -> None:
        """Validate the frozen scientific selections used by this B3 director."""
        _validate_prepared_arms(self.control, self.treatment)
        _validate_focal_encoding(self.focal_encoding)
        _validate_act_order(self.acts)
        _validate_representative_focus(self.representative_focus)
        _validate_genetic_trajectory(self.representative_genetic_trajectory)
        _validate_confirmation_points(self.confirmation_points)
        _validate_founder_contributions(self.founder_contribution_points)
        _validate_broad_patch_mean(
            self.broad_patch_step30_mean,
            has_confirmation=bool(self.confirmation_points),
        )
        if self.conclusion != B3_BOUNDED_CONCLUSION:
            raise ValueError("B3 cinematic conclusion must match the confirmed handoff.")
        if self.scope_qualifier != B3_SCOPE_QUALIFIER:
            raise ValueError("B3 cinematic scope qualifier must remain fixed.")

    @property
    def is_full_flagship(self) -> bool:
        """Return whether full confirmation and sensitivity evidence is present."""
        return bool(self.confirmation_points)


def prepare_b3_flagship_director(
    *,
    control_evidence: B3RunEvidence,
    treatment_evidence: B3RunEvidence,
    confirmation_pairs: Sequence[B3MatchedPairSummary] = (),
    broad_patch_summaries: Sequence[B3RunSummary] = (),
) -> B3FlagshipDirectorPlan:
    """Prepare the confirmed B3 science for deterministic cinematic direction.

    Args:
        control_evidence: Completed uniform representative-seed committed evidence.
        treatment_evidence: Completed compact-patch representative-seed evidence.
        confirmation_pairs: Optional full independent B3 matched confirmation set.
            Omit for a reduced director smoke/excerpt.
        broad_patch_summaries: Optional full radius-2 sensitivity summaries. These
            must be supplied together with the full confirmation set.

    Returns:
        Concrete B3 director plan over committed evidence.

    Raises:
        TypeError: If evidence is not the expected B3 committed value type.
        ValueError: If the supplied runs, scientific scale, representative episode,
            confirmation set, or sensitivity set differs from the merged B3 handoff.
    """
    _validate_evidence_type(control_evidence, name="control_evidence")
    _validate_evidence_type(treatment_evidence, name="treatment_evidence")
    validate_b3_treatment_integrity(
        control_evidence.specification,
        treatment_evidence.specification,
    )
    _validate_representative_specifications(control_evidence, treatment_evidence)

    encoding = ContinuousTraitEncoding(
        trait_name=MAX_SPEED,
        label=B3_FOCAL_LABEL,
        lower_bound=B3_LOW_MAX_SPEED,
        upper_bound=B3_HIGH_MAX_SPEED,
    )
    control = _prepare_arm(B3_CONTROL_LABEL, control_evidence, encoding=encoding)
    treatment = _prepare_arm(
        B3_TREATMENT_LABEL,
        treatment_evidence,
        encoding=encoding,
    )
    confirmation = _confirmation_points(tuple(confirmation_pairs))
    founder_contribution = _founder_contribution_points(tuple(confirmation_pairs))
    broad_mean = _broad_patch_mean(
        tuple(broad_patch_summaries),
        require_full=bool(confirmation),
    )
    return B3FlagshipDirectorPlan(
        control=control,
        treatment=treatment,
        focal_encoding=encoding,
        acts=B3_FLAGSHIP_ACTS,
        representative_focus=_representative_focus(treatment.summary),
        representative_genetic_trajectory=_matched_genetic_trajectory(
            control.summary,
            treatment.summary,
        ),
        confirmation_points=confirmation,
        founder_contribution_points=founder_contribution,
        broad_patch_step30_mean=broad_mean,
    )


def _validate_evidence_type(evidence: object, *, name: str) -> None:
    if not isinstance(evidence, B3RunEvidence):
        raise TypeError(f"{name} must be a B3RunEvidence.")


def _validate_representative_specifications(
    control: B3RunEvidence,
    treatment: B3RunEvidence,
) -> None:
    for name, evidence, environment in (
        ("control", control, "uniform"),
        ("treatment", treatment, "compact_patch"),
    ):
        specification = evidence.specification
        if specification.seed != B3_REPRESENTATIVE_SEED:
            raise ValueError(
                f"B3 {name} must use representative seed {B3_REPRESENTATIVE_SEED}."
            )
        if specification.environment != environment:
            raise ValueError(f"B3 {name} has the wrong environment.")
        if specification.founder_assignment != "standard":
            raise ValueError("B3 representative film must use standard founder assignment.")


def _prepare_arm(
    label: str,
    evidence: B3RunEvidence,
    *,
    encoding: ContinuousTraitEncoding,
) -> B3PreparedArm:
    summary = summarize_b3_run(evidence)
    timeline = build_portfolio_animation_timeline(
        spatial_history=evidence.spatial_observations,
        population_history=evidence.population_observations,
        trait_name=MAX_SPEED,
        individual_trait_history=evidence.individual_trait_observations,
        event_history=_step_telemetry(evidence.events),
        focal_encoding=encoding,
    )
    return B3PreparedArm(
        label=label,
        evidence=evidence,
        summary=summary,
        timeline=timeline,
    )


def _step_telemetry(events: tuple[AppliedEvent, ...]) -> tuple[StepTelemetry, ...]:
    grouped: dict[int, list[AppliedEvent]] = {}
    for event in events:
        completed_step = event.event_step_index + 1
        grouped.setdefault(completed_step, []).append(event)
    return tuple(
        StepTelemetry(completed_step_index=step, events=tuple(grouped[step]))
        for step in sorted(grouped)
    )


def _representative_focus(
    treatment_summary: B3RunSummary,
) -> tuple[B3RepresentativeFocus, ...]:
    selectors = (
        (16, 7, B3_LOW_MAX_SPEED),
        (1, 5, B3_HIGH_MAX_SPEED),
    )
    return tuple(
        B3RepresentativeFocus(
            episode=_require_episode(
                treatment_summary,
                organism_id=organism_id,
                completed_step=completed_step,
                speed=speed,
            )
        )
        for organism_id, completed_step, speed in selectors
    )


def _require_episode(
    summary: B3RunSummary,
    *,
    organism_id: int,
    completed_step: int,
    speed: int,
) -> B3MovementConsumptionEpisode:
    for episode in summary.mechanism_episodes:
        if (
            episode.organism_id == organism_id
            and episode.completed_step_index == completed_step
            and episode.max_speed_capacity == speed
        ):
            return episode
    raise ValueError(
        "B3 representative episode is missing from authoritative committed evidence: "
        f"organism {organism_id}, completed step {completed_step}, max_speed {speed}."
    )


def _matched_genetic_trajectory(
    control: B3RunSummary,
    treatment: B3RunSummary,
) -> tuple[B3MatchedGeneticPoint, ...]:
    treatment_by_step = {
        point.step_index: point for point in treatment.genetic_trajectory
    }
    matched: list[B3MatchedGeneticPoint] = []
    for control_point in control.genetic_trajectory:
        treatment_point = treatment_by_step.get(control_point.step_index)
        if treatment_point is None:
            raise ValueError("B3 matched genetic trajectories must share timesteps.")
        if (
            control_point.high_speed_allele_frequency is None
            or treatment_point.high_speed_allele_frequency is None
        ):
            raise ValueError("Confirmed B3 representative trajectories must be non-extinct.")
        matched.append(
            B3MatchedGeneticPoint(
                step_index=control_point.step_index,
                control_high_speed_frequency=control_point.high_speed_allele_frequency,
                treatment_high_speed_frequency=treatment_point.high_speed_allele_frequency,
            )
        )
    if len(matched) != len(treatment.genetic_trajectory):
        raise ValueError("B3 matched genetic trajectories must align one-for-one.")
    return tuple(matched)


def _confirmation_points(
    pairs: tuple[B3MatchedPairSummary, ...],
) -> tuple[B3ConfirmationPoint, ...]:
    if not pairs:
        return ()
    _validate_confirmation_pair_order(pairs)
    points: list[B3ConfirmationPoint] = []
    for pair in pairs:
        control = _required_frequency(pair.control.primary_high_speed_frequency)
        treatment = _required_frequency(pair.treatment.primary_high_speed_frequency)
        effect = pair.primary_effect
        if effect is None:
            raise ValueError("Confirmed B3 paired effect must be defined.")
        points.append(
            B3ConfirmationPoint(
                seed=pair.seed,
                control_high_speed_frequency=control,
                treatment_high_speed_frequency=treatment,
                paired_effect=effect,
            )
        )
    return tuple(points)


def _founder_contribution_points(
    pairs: tuple[B3MatchedPairSummary, ...],
) -> tuple[B3FounderContributionPoint, ...]:
    if not pairs:
        return ()
    _validate_confirmation_pair_order(pairs)
    points: list[B3FounderContributionPoint] = []
    for pair in pairs:
        for summary in (pair.control, pair.treatment):
            if summary.environment not in ("uniform", "compact_patch"):
                raise ValueError("B3 founder contribution requires canonical matched arms.")
            contribution = summary.founder_reproductive_success
            points.append(
                B3FounderContributionPoint(
                    seed=pair.seed,
                    environment=summary.environment,
                    low_speed_mean=contribution.low_speed_mean,
                    high_speed_mean=contribution.high_speed_mean,
                )
            )
    return tuple(points)


def _validate_confirmation_pair_order(
    pairs: tuple[B3MatchedPairSummary, ...],
) -> None:
    seeds = tuple(pair.seed for pair in pairs)
    if seeds != B3_CONFIRMATION_SEEDS:
        raise ValueError(
            "B3 confirmation evidence must contain the frozen independent seeds in "
            "predeclared order."
        )
    if any(pair.founder_assignment != "standard" for pair in pairs):
        raise ValueError("B3 flagship confirmation must use standard founder assignment.")


def _broad_patch_mean(
    summaries: tuple[B3RunSummary, ...],
    *,
    require_full: bool,
) -> float | None:
    if not summaries:
        if require_full:
            raise ValueError(
                "Full B3 flagship preparation requires radius-2 sensitivity evidence."
            )
        return None
    seeds = tuple(summary.seed for summary in summaries)
    if seeds != B3_CONFIRMATION_SEEDS:
        raise ValueError("B3 broad-patch evidence must use all confirmation seeds in order.")
    values: list[float] = []
    for summary in summaries:
        if summary.environment != "broad_patch":
            raise ValueError("B3 sensitivity evidence must use broad_patch specifications.")
        values.append(_required_frequency(summary.primary_high_speed_frequency))
    return sum(values) / len(values)


def _required_frequency(value: float | None) -> float:
    if value is None:
        raise ValueError("Confirmed B3 primary frequency must be defined.")
    return value


def _validate_prepared_arms(control: B3PreparedArm, treatment: B3PreparedArm) -> None:
    if control.label != B3_CONTROL_LABEL or treatment.label != B3_TREATMENT_LABEL:
        raise ValueError("B3 cinematic arm labels must remain fixed.")
    _validate_representative_specifications(control.evidence, treatment.evidence)
    if control.timeline.world_bounds != treatment.timeline.world_bounds:
        raise ValueError("B3 matched cinematic worlds must use identical world bounds.")
    if control.timeline.focal_encoding != treatment.timeline.focal_encoding:
        raise ValueError("B3 matched cinematic arms must share one focal encoding.")


def _validate_focal_encoding(encoding: ContinuousTraitEncoding) -> None:
    if encoding != ContinuousTraitEncoding(
        trait_name=MAX_SPEED,
        label=B3_FOCAL_LABEL,
        lower_bound=B3_LOW_MAX_SPEED,
        upper_bound=B3_HIGH_MAX_SPEED,
    ):
        raise ValueError("B3 flagship focal encoding must remain max_speed on scale 1..4.")


def _validate_act_order(acts: tuple[B3DirectorAct, ...]) -> None:
    if acts != B3_FLAGSHIP_ACTS:
        raise ValueError("B3 flagship director act order must remain deterministic.")


def _validate_representative_focus(
    focus: tuple[B3RepresentativeFocus, ...],
) -> None:
    expected = (
        (16, 7, B3_LOW_MAX_SPEED),
        (1, 5, B3_HIGH_MAX_SPEED),
    )
    actual = tuple(
        (
            item.episode.organism_id,
            item.episode.completed_step_index,
            item.episode.max_speed_capacity,
        )
        for item in focus
    )
    if actual != expected:
        raise ValueError("B3 representative cinematic focus must match the handoff.")


def _validate_genetic_trajectory(
    points: tuple[B3MatchedGeneticPoint, ...],
) -> None:
    if not points:
        raise ValueError("B3 representative genetic trajectory must not be empty.")
    steps = tuple(point.step_index for point in points)
    if steps != tuple(sorted(set(steps))):
        raise ValueError("B3 genetic trajectory steps must be unique and increasing.")
    if B3_PRIMARY_STEP not in steps:
        raise ValueError("B3 representative trajectory must include the primary step.")


def _validate_confirmation_points(points: tuple[B3ConfirmationPoint, ...]) -> None:
    if not points:
        return
    if tuple(point.seed for point in points) != B3_CONFIRMATION_SEEDS:
        raise ValueError("B3 confirmation points must preserve the frozen seed order.")


def _validate_founder_contributions(
    points: tuple[B3FounderContributionPoint, ...],
) -> None:
    if not points:
        return
    expected = tuple(
        (seed, environment)
        for seed in B3_CONFIRMATION_SEEDS
        for environment in ("uniform", "compact_patch")
    )
    actual = tuple((point.seed, point.environment) for point in points)
    if actual != expected:
        raise ValueError("B3 founder-contribution points must preserve matched run order.")


def _validate_broad_patch_mean(
    value: float | None,
    *,
    has_confirmation: bool,
) -> None:
    if has_confirmation and value is None:
        raise ValueError("Full B3 flagship plan requires broad-patch sensitivity evidence.")
    if not has_confirmation and value is not None:
        raise ValueError("Broad-patch mean requires full confirmation evidence.")


__all__ = [
    "B3_BOUNDED_CONCLUSION",
    "B3_CONTROL_LABEL",
    "B3_DIRECTOR_MODE",
    "B3_FLAGSHIP_ACTS",
    "B3_FLAGSHIP_SCENARIO_LABEL",
    "B3_FOCAL_LABEL",
    "B3_REPRESENTATIVE_SEED",
    "B3_SCOPE_QUALIFIER",
    "B3_TREATMENT_LABEL",
    "B3ConfirmationPoint",
    "B3DirectorAct",
    "B3FlagshipDirectorPlan",
    "B3FounderContributionPoint",
    "B3MatchedGeneticPoint",
    "B3PreparedArm",
    "B3RepresentativeFocus",
    "prepare_b3_flagship_director",
]

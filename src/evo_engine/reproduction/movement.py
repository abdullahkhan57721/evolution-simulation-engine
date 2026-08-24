"""Movement adapters and mate-targeting policies for reproduction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from evo_engine.behavior.movement_targeting import MovementTarget
from evo_engine.behavior.purposes import REPRODUCTION
from evo_engine.behavior.selection import behavior_is_allowed
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.reproduction.eligibility import ReproductiveEligibility
from evo_engine.reproduction.mating import MatingCompatibility, MatingPreference
from evo_engine.spatial.distances import Chebyshev, DistanceMetric

if TYPE_CHECKING:
    from evo_engine.engine.simulation_state import SimulationState
    from evo_engine.world.organism import Organism


@attrs.frozen(slots=True, kw_only=True)
class ReproductiveEligibilityMovementCondition:
    """Adapt reproductive eligibility into a movement-intent condition.

    Attributes:
        eligibility: Individual reproductive-eligibility policy to evaluate.
    """

    eligibility: ReproductiveEligibility

    def __attrs_post_init__(self) -> None:
        """Validate the reproductive-eligibility collaborator."""
        if not callable(getattr(self.eligibility, "is_eligible", None)):
            raise TypeError("eligibility must provide a callable is_eligible method.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by reproductive eligibility."""
        return collect_required_traits(self.eligibility)

    def matches(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether the organism is individually ready to reproduce.

        Args:
            organism: Organism considering mate-seeking movement.
            simulation_state: Current simulation state.

        Returns:
            Validated reproductive-eligibility decision.

        Raises:
            TypeError: If the eligibility policy returns a non-Boolean value.
        """
        decision = self.eligibility.is_eligible(
            organism,
            simulation_state=simulation_state,
        )

        if type(decision) is not bool:
            raise TypeError("eligibility.is_eligible must return a Boolean.")

        return decision


@attrs.frozen(slots=True, kw_only=True)
class PreferredMateTarget:
    """Target the highest-preference currently viable mate.

    Candidate organisms must be distinct, individually reproductively eligible,
    behaviorally allowed to reproduce, and accepted by the configured mating
    compatibility policy. Compatible candidates are ranked by descending mating
    preference, then ascending spatial distance, then ascending organism ID.

    The focal organism must itself be individually eligible and behaviorally
    allowed to reproduce. This makes the target model safe to reuse outside a
    particular movement-intent composition.

    Attributes:
        eligibility: Individual reproductive-eligibility policy shared with the
            reproduction process.
        compatibility: Pair compatibility policy shared with parent selection.
        preference: Pair preference policy shared with parent selection.
        distance_metric: Spatial metric used to break equal-preference ties.
    """

    eligibility: ReproductiveEligibility
    compatibility: MatingCompatibility
    preference: MatingPreference
    distance_metric: DistanceMetric = attrs.field(factory=Chebyshev)

    def __attrs_post_init__(self) -> None:
        """Validate mate-targeting collaborators."""
        if not callable(getattr(self.eligibility, "is_eligible", None)):
            raise TypeError("eligibility must provide a callable is_eligible method.")

        if not callable(self.compatibility):
            raise TypeError("compatibility must be callable.")

        if not callable(self.preference):
            raise TypeError("preference must be callable.")

        if not callable(getattr(self.distance_metric, "distance", None)):
            raise TypeError("distance_metric must provide a callable distance method.")

    @property
    def required_traits(self) -> frozenset[str]:
        """Return traits required by mate eligibility, compatibility, and choice."""
        return collect_required_traits(
            self.eligibility,
            self.compatibility,
            self.preference,
        )

    def choose_target(
        self,
        organism: Organism,
        *,
        behavioral_purpose: str,
        simulation_state: SimulationState,
    ) -> MovementTarget | None:
        """Return the current highest-preference viable mate location.

        Args:
            organism: Organism attempting mate-seeking movement.
            behavioral_purpose: Purpose motivating the movement attempt.
            simulation_state: Current simulation state.

        Returns:
            Selected mate coordinate, or ``None`` when mate targeting is
            inactive or no viable mate exists.
        """
        if behavioral_purpose != REPRODUCTION:
            return None

        if not self._is_reproductively_available(
            organism,
            simulation_state=simulation_state,
        ):
            return None

        world = simulation_state.world
        best_key: tuple[int, int, int] | None = None
        best_target: MovementTarget | None = None

        for candidate in world.organisms.values():
            if candidate.id == organism.id:
                continue

            if not self._is_reproductively_available(
                candidate,
                simulation_state=simulation_state,
            ):
                continue

            if not self._can_mate(
                organism,
                candidate,
                simulation_state=simulation_state,
            ):
                continue

            preference_score = self._preference_score(
                organism,
                candidate,
                simulation_state=simulation_state,
            )
            distance = self.distance_metric.distance(
                x1=organism.x,
                y1=organism.y,
                x2=candidate.x,
                y2=candidate.y,
                width=world.width,
                height=world.height,
            )
            candidate_key = (
                -preference_score,
                distance,
                candidate.id,
            )

            if best_key is None or candidate_key < best_key:
                best_key = candidate_key
                best_target = MovementTarget(
                    x=candidate.x,
                    y=candidate.y,
                )

        return best_target

    def _is_reproductively_available(
        self,
        organism: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return validated individual reproductive availability."""
        eligible = self.eligibility.is_eligible(
            organism,
            simulation_state=simulation_state,
        )

        if type(eligible) is not bool:
            raise TypeError("eligibility.is_eligible must return a Boolean.")

        if not eligible:
            return False

        return behavior_is_allowed(
            organism,
            behavioral_purpose=REPRODUCTION,
            simulation_state=simulation_state,
        )

    def _can_mate(
        self,
        first_parent: Organism,
        second_parent: Organism,
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return a validated mating-compatibility decision."""
        decision = self.compatibility(
            first_parent,
            second_parent,
            simulation_state,
        )

        if type(decision) is not bool:
            raise TypeError("compatibility must return a Boolean.")

        return decision

    def _preference_score(
        self,
        first_parent: Organism,
        second_parent: Organism,
        *,
        simulation_state: SimulationState,
    ) -> int:
        """Return a validated mating-preference score."""
        score = self.preference(
            first_parent,
            second_parent,
            simulation_state,
        )

        if type(score) is not int:
            raise TypeError("preference must return an integer.")

        return score

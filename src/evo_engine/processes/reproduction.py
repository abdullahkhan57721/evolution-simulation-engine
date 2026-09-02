"""Reproduction simulation process."""

from __future__ import annotations

from typing import ClassVar

import attrs

from evo_engine.access import EntityAccessModel
from evo_engine.admission import EntityAdmissionModel
from evo_engine.behavior import REPRODUCTION as REPRODUCTION_PURPOSE
from evo_engine.behavior import behavior_is_allowed
from evo_engine.development.models import DeterministicDevelopment, DevelopmentModel
from evo_engine.development.profile import DevelopmentalProfile
from evo_engine.energetics.expenditure import (
    EnergyExpenditurePolicy,
    SpendToZero,
    energy_expenditure_is_allowed,
)
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics import GENETIC_ARCHITECTURE
from evo_engine.genetics.genetic_phenotype import GeneticPhenotype
from evo_engine.genetics.genome import Genome
from evo_engine.genetics.inheritance import InheritanceModel
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.reference import EntityReferenceModel
from evo_engine.reproduction.birth_mass import (
    AdultBodyMassAtBirth,
    OffspringBodyMassModel,
)
from evo_engine.reproduction.contributor_selection import (
    AllParticipantsContribute,
    GeneticContributorSelection,
)
from evo_engine.reproduction.eligibility import ReproductiveEligibility
from evo_engine.reproduction.group_selection import ReproductiveGroupSelection
from evo_engine.reproduction.investment import (
    GeneticPhenotypeEnergyInvestment,
    ParentalInvestment,
)
from evo_engine.reproduction.mating_types import (
    FixedMatingType,
    OffspringMatingTypeModel,
)
from evo_engine.reproduction.offspring_production import (
    BiologicalOffspringProduction,
    OffspringProductionContext,
)
from evo_engine.reproduction.placement import (
    OffspringPlacement,
    RandomParentLocation,
)
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.access import WorldOrganismAccess
from evo_engine.world.admission import WorldOrganismAdmission
from evo_engine.world.organism import Organism
from evo_engine.world.reference import WorldOrganismReference
from evo_engine.world.world_state import WorldState


def _validate_reproduction_proposal(
    instance: object,
    attribute: attrs.Attribute,
    value: object,
) -> None:
    """Validate a materialized event's originating proposal."""
    if not isinstance(value, Reproduction.Proposal):
        raise TypeError(
            f"{attribute.name} must be a Reproduction.Proposal; received {value!r}."
        )


@attrs.frozen(slots=True, kw_only=True)
class Reproduction:
    """Represent a biological reproduction simulation process.

    Eligibility determines which organisms may individually reproduce.
    Reproductive-group selection forms nonempty candidate participant groups.
    Parental investment currently determines one energy cost for each participant,
    and the configured energy expenditure policy determines whether those costs are
    permitted. Stage resolution then chooses which competing participant groups may
    proceed.

    Resolved proposals are materialized before any stage event is applied.
    Materialization first chooses the ordered genetic contributors from the resolved
    participants, then propagates an offspring genome from only those contributor
    states. Biological offspring production still receives the full participant
    tuple in this milestone so placement and other production-source semantics can
    be hardened independently later. Application pays the recorded participant
    energy investments and admits the already-produced offspring.

    Contributor selection occurs only during materialization. This preserves the
    transactional RNG contract: rejected reproductive candidates never consume
    stochastic contributor-selection randomness.

    Attributes:
        eligibility: Policy determining individual reproductive eligibility.
        reproductive_group_selection: Policy proposing nonempty participant groups.
        inheritance_model: Biological adapter propagating an offspring genome from
            selected genetic-contributor states.
        genetic_contributor_selection: Policy choosing the ordered contributor
            subset from each resolved participant group.
        parental_investment: Policy currently determining each participant's energy
            cost.
        energy_expenditure_policy: Policy deciding whether each participant may pay
            its proposed energy contribution.
        development_model: Policy realizing individual developmental targets
            during offspring production.
        offspring_placement: Policy choosing the offspring birth coordinate during
            offspring production.
        offspring_body_mass_model: Policy determining newborn current body mass
            during offspring production.
        offspring_mating_type_model: Policy assigning immutable reproductive mating
            type during offspring production.
        access_model: Policy enumerating and resolving active participant organisms.
        reference_model: Policy deriving state-local organism references used by
            reproductive groups and proposals.
        offspring_admission_model: Policy admitting the fully produced offspring
            into biological world state during mechanical application.
    """

    behavioral_purpose: ClassVar[str] = REPRODUCTION_PURPOSE

    eligibility: ReproductiveEligibility
    reproductive_group_selection: ReproductiveGroupSelection
    inheritance_model: InheritanceModel
    genetic_contributor_selection: GeneticContributorSelection = attrs.field(
        factory=AllParticipantsContribute,
    )
    parental_investment: ParentalInvestment = attrs.field(
        factory=GeneticPhenotypeEnergyInvestment,
    )
    energy_expenditure_policy: EnergyExpenditurePolicy = attrs.field(
        factory=SpendToZero,
    )
    development_model: DevelopmentModel = attrs.field(
        factory=DeterministicDevelopment,
    )
    offspring_placement: OffspringPlacement = attrs.field(
        factory=RandomParentLocation,
    )
    offspring_body_mass_model: OffspringBodyMassModel = attrs.field(
        factory=AdultBodyMassAtBirth,
    )
    offspring_mating_type_model: OffspringMatingTypeModel = attrs.field(
        factory=lambda: FixedMatingType(mating_type="default"),
    )
    access_model: EntityAccessModel[int, WorldState, Organism] = attrs.field(
        factory=WorldOrganismAccess,
    )
    reference_model: EntityReferenceModel[Organism, WorldState, int] = attrs.field(
        factory=WorldOrganismReference,
    )
    offspring_admission_model: EntityAdmissionModel[Organism, WorldState] = attrs.field(
        factory=WorldOrganismAdmission,
    )
    _offspring_production_model: BiologicalOffspringProduction = attrs.field(
        init=False,
        repr=False,
    )

    def __attrs_post_init__(self) -> None:
        """Validate reproduction configuration and compose offspring production."""
        required_methods = (
            (self.eligibility, "is_eligible", "eligibility"),
            (
                self.reproductive_group_selection,
                "propose_reproductive_groups",
                "reproductive_group_selection",
            ),
            (self.inheritance_model, "propagate", "inheritance_model"),
            (
                self.genetic_contributor_selection,
                "select_contributors",
                "genetic_contributor_selection",
            ),
            (
                self.parental_investment,
                "determine_investments",
                "parental_investment",
            ),
            (
                self.energy_expenditure_policy,
                "can_spend",
                "energy_expenditure_policy",
            ),
            (self.access_model, "get", "access_model"),
            (self.access_model, "entities", "access_model"),
            (self.reference_model, "reference", "reference_model"),
            (
                self.offspring_admission_model,
                "admit",
                "offspring_admission_model",
            ),
        )
        for policy, method_name, policy_name in required_methods:
            if not callable(getattr(policy, method_name, None)):
                raise TypeError(
                    f"{policy_name} must provide a callable {method_name} method."
                )

        object.__setattr__(
            self,
            "_offspring_production_model",
            BiologicalOffspringProduction(
                development_model=self.development_model,
                offspring_placement=self.offspring_placement,
                offspring_body_mass_model=self.offspring_body_mass_model,
                offspring_mating_type_model=self.offspring_mating_type_model,
            ),
        )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic phenotype traits required by reproduction policies."""
        return collect_required_traits(
            self.eligibility,
            self.reproductive_group_selection,
            self.inheritance_model,
            self.genetic_contributor_selection,
            self.parental_investment,
            self.energy_expenditure_policy,
            self._offspring_production_model,
            self.offspring_admission_model,
        )

    @staticmethod
    def _validate_investments(
        investments: object,
        *,
        participant_count: int,
    ) -> tuple[int, ...]:
        """Return validated participant energy investments."""
        validated_investments = validators.validate_tuple(
            investments,
            name="participant investments",
        )

        if len(validated_investments) != participant_count:
            raise ValueError(
                "parental_investment must return exactly one investment "
                "for each reproductive participant."
            )

        total_investment = 0

        for index, investment in enumerate(validated_investments):
            validated_investment = validators.validate_int_ge(
                investment,
                bound=0,
                name=f"participant investments[{index}]",
            )
            total_investment += validated_investment

        if total_investment < 1:
            raise ValueError("total reproductive energy investment must be at least 1.")

        return validated_investments

    @attrs.frozen(slots=True, kw_only=True)
    class Proposal:
        """Represent a candidate Reproduction proposal.

        Attributes:
            step_index: Simulation step associated with the proposal.
            participant_energy_contributions: ``(organism_id, energy)`` pairs for
                one or more reproductive participants. A participant may contribute
                zero energy, but total offspring investment must be positive.
            preference_score: Reproductive preference used by resolvers.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        participant_energy_contributions: tuple[tuple[int, int], ...]
        preference_score: int = attrs.field(
            default=0,
            validator=attrs_validators.validate_int,
        )

        def __attrs_post_init__(self) -> None:
            """Validate participant energy contributions."""
            validators.validate_tuple(
                self.participant_energy_contributions,
                name="participant_energy_contributions",
            )

            if not self.participant_energy_contributions:
                raise ValueError(
                    "participant_energy_contributions must contain at least one "
                    "participant."
                )

            participant_ids: set[int] = set()
            total_investment = 0

            for index, contribution in enumerate(
                self.participant_energy_contributions
            ):
                if type(contribution) is not tuple:
                    raise TypeError(
                        f"participant_energy_contributions[{index}] must be a tuple."
                    )

                if len(contribution) != 2:
                    raise ValueError(
                        f"participant_energy_contributions[{index}] must contain "
                        "exactly two items."
                    )

                participant_id, amount = contribution

                validators.validate_int_ge(
                    participant_id,
                    bound=0,
                    name=f"participant_energy_contributions[{index}][0]",
                )
                validators.validate_int_ge(
                    amount,
                    bound=0,
                    name=f"participant_energy_contributions[{index}][1]",
                )

                if participant_id in participant_ids:
                    raise ValueError(
                        "participant_energy_contributions must not contain duplicate "
                        f"participant ID {participant_id}."
                    )

                participant_ids.add(participant_id)
                total_investment += amount

            if total_investment < 1:
                raise ValueError(
                    "total participant energy contribution must be at least 1."
                )

        @property
        def participant_ids(self) -> tuple[int, ...]:
            """Return reproductive participant IDs in recorded order."""
            return tuple(
                participant_id
                for participant_id, _ in self.participant_energy_contributions
            )

        @property
        def initial_energy(self) -> int:
            """Return total reproductive energy invested in the offspring."""
            return sum(
                amount for _, amount in self.participant_energy_contributions
            )

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a materialized Reproduction event.

        ``participant_ids`` records every organism that participated in the
        resolved reproductive episode. ``parent_ids`` exposes only the genetic
        contributors for biological pedigree/ancestry semantics.

        Attributes:
            proposal: Resolved proposal from which the event was materialized.
            offspring: Fully produced newborn, not yet admitted to the world.
            genetic_contributor_ids: Ordered IDs whose transmissible state supplied
                the offspring genome.
        """

        proposal: Reproduction.Proposal = attrs.field(
            validator=_validate_reproduction_proposal,
        )
        offspring: Organism = attrs.field(
            validator=attrs.validators.instance_of(Organism),
        )
        genetic_contributor_ids: tuple[int, ...]

        def __attrs_post_init__(self) -> None:
            """Validate committed energy and contributor/participant consistency."""
            if self.offspring.energy != self.proposal.initial_energy:
                raise ValueError(
                    "offspring energy must equal the proposal's committed "
                    "reproductive energy investment."
                )

            validators.validate_tuple(
                self.genetic_contributor_ids,
                name="genetic_contributor_ids",
            )
            if not self.genetic_contributor_ids:
                raise ValueError("genetic_contributor_ids must not be empty.")

            participant_ids = frozenset(self.proposal.participant_ids)
            seen_ids: set[int] = set()
            for index, contributor_id in enumerate(self.genetic_contributor_ids):
                validators.validate_int_ge(
                    contributor_id,
                    bound=0,
                    name=f"genetic_contributor_ids[{index}]",
                )
                if contributor_id in seen_ids:
                    raise ValueError(
                        "genetic_contributor_ids must not contain duplicate IDs."
                    )
                if contributor_id not in participant_ids:
                    raise ValueError(
                        "genetic_contributor_ids must contain only reproductive "
                        "participants."
                    )
                seen_ids.add(contributor_id)

        @property
        def step_index(self) -> int:
            """Return the simulation step associated with the event."""
            return self.proposal.step_index

        @property
        def participant_energy_contributions(self) -> tuple[tuple[int, int], ...]:
            """Return recorded reproductive-participant energy contributions."""
            return self.proposal.participant_energy_contributions

        @property
        def participant_ids(self) -> tuple[int, ...]:
            """Return all reproductive participant IDs in recorded order."""
            return self.proposal.participant_ids

        @property
        def parent_ids(self) -> tuple[int, ...]:
            """Return genetic parent/contributor IDs in inheritance order."""
            return self.genetic_contributor_ids

        @property
        def initial_energy(self) -> int:
            """Return total reproductive energy invested in the offspring."""
            return self.proposal.initial_energy

        @property
        def offspring_genome(self) -> Genome:
            """Return the produced offspring genome."""
            return self.offspring.genome

        @property
        def offspring_genetic_phenotype(self) -> GeneticPhenotype:
            """Return the produced offspring genetic phenotype."""
            return self.offspring.genetic_phenotype

        @property
        def offspring_developmental_profile(self) -> DevelopmentalProfile:
            """Return the produced offspring developmental profile."""
            return self.offspring.developmental_profile

        @property
        def initial_body_mass(self) -> int:
            """Return the produced offspring initial body mass."""
            return self.offspring.body_mass

        @property
        def offspring_mating_type(self) -> str:
            """Return the produced offspring mating type."""
            return self.offspring.mating_type

        @property
        def x(self) -> int:
            """Return the produced offspring horizontal coordinate."""
            return self.offspring.x

        @property
        def y(self) -> int:
            """Return the produced offspring vertical coordinate."""
            return self.offspring.y

    @property
    def event_type(self) -> type[Reproduction.Proposal]:
        """Return the Reproduction proposal type used for resolution."""
        return self.Proposal

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Reproduction.Proposal]:
        """Propose energetically permitted reproductive events.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Candidate Reproduction proposals permitted by the configured
            expenditure policy.
        """
        world = simulation_state.domain_state
        eligible_participants = self._eligible_participants(simulation_state)
        reproductive_groups = (
            self.reproductive_group_selection.propose_reproductive_groups(
                eligible_participants,
                simulation_state=simulation_state,
                reference_model=self.reference_model,
            )
        )
        participants_by_id = {
            self.reference_model.reference(
                participant,
                state=world,
            ): participant
            for participant in eligible_participants
        }

        proposals: list[Reproduction.Proposal] = []

        for group in reproductive_groups:
            proposal = self._proposal_from_reproductive_group(
                group.participant_ids,
                preference_score=group.preference_score,
                participants_by_id=participants_by_id,
                simulation_state=simulation_state,
            )
            if proposal is not None:
                proposals.append(proposal)

        return proposals

    def _eligible_participants(
        self,
        simulation_state: SimulationState,
    ) -> list[Organism]:
        """Return behaviorally selected, individually eligible participants."""
        eligible_participants: list[Organism] = []
        world = simulation_state.domain_state
        for organism in self.access_model.entities(state=world):
            if not behavior_is_allowed(
                organism,
                behavioral_purpose=self.behavioral_purpose,
                simulation_state=simulation_state,
            ):
                continue

            is_eligible = self.eligibility.is_eligible(
                organism,
                simulation_state=simulation_state,
            )

            if type(is_eligible) is not bool:
                raise TypeError("eligibility.is_eligible must return a Boolean.")

            if is_eligible:
                eligible_participants.append(organism)

        return eligible_participants

    def _proposal_from_reproductive_group(
        self,
        participant_ids: tuple[int, ...],
        *,
        preference_score: int,
        participants_by_id: dict[int, Organism],
        simulation_state: SimulationState,
    ) -> Reproduction.Proposal | None:
        """Return one energetically permitted proposal for a reproductive group."""
        participants = self._participants_from_group(
            participant_ids,
            participants_by_id=participants_by_id,
        )
        investments = self._validate_investments(
            self.parental_investment.determine_investments(
                participants,
                simulation_state=simulation_state,
            ),
            participant_count=len(participants),
        )

        if not self._can_spend_investments(
            participants,
            investments,
            simulation_state=simulation_state,
        ):
            return None

        return self.Proposal(
            step_index=simulation_state.step_index,
            participant_energy_contributions=tuple(
                (participant_id, investment)
                for participant_id, investment in zip(
                    participant_ids,
                    investments,
                    strict=True,
                )
            ),
            preference_score=preference_score,
        )

    def _participants_from_group(
        self,
        participant_ids: tuple[int, ...],
        *,
        participants_by_id: dict[int, Organism],
    ) -> tuple[Organism, ...]:
        """Return validated eligible participants for one proposed group."""
        try:
            return tuple(
                participants_by_id[participant_id]
                for participant_id in participant_ids
            )
        except KeyError as error:
            raise ValueError(
                "reproductive_group_selection proposed an organism that was not "
                "individually eligible to reproduce."
            ) from error

    def _can_spend_investments(
        self,
        participants: tuple[Organism, ...],
        investments: tuple[int, ...],
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether every participant may pay its proposed investment."""
        return all(
            energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                participant,
                energy_cost=investment,
                simulation_state=simulation_state,
            )
            for participant, investment in zip(
                participants,
                investments,
                strict=True,
            )
        )

    def _select_genetic_contributors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return validated canonical contributors selected from participants."""
        selected = validators.validate_tuple(
            self.genetic_contributor_selection.select_contributors(
                participants,
                simulation_state=simulation_state,
                rng=simulation_state.rng,
            ),
            name="genetic contributors",
        )
        if not selected:
            raise ValueError("genetic contributors must not be empty.")

        world = simulation_state.domain_state
        canonical_by_reference = {
            self.reference_model.reference(participant, state=world): participant
            for participant in participants
        }
        seen_references: set[int] = set()
        contributors: list[Organism] = []

        for index, contributor in enumerate(selected):
            if not isinstance(contributor, Organism):
                raise TypeError(
                    f"genetic contributors[{index}] must be an Organism."
                )
            reference = self.reference_model.reference(contributor, state=world)
            try:
                canonical = canonical_by_reference[reference]
            except KeyError as error:
                raise ValueError(
                    "genetic contributors must be drawn only from the resolved "
                    "reproductive participants."
                ) from error
            if reference in seen_references:
                raise ValueError(
                    "genetic contributors must not contain duplicate participants."
                )
            seen_references.add(reference)
            contributors.append(canonical)

        return tuple(contributors)

    def materialize_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Reproduction.Proposal,
    ) -> Reproduction.Event:
        """Materialize a resolved Reproduction proposal.

        Reproductive participation, state propagation, and entity production are
        intentionally distinct. Contributor selection first chooses which resolved
        participants supply transmissible state. Inheritance then propagates a
        genome from only those contributor states. Biological offspring production
        receives the full participant tuple for the current production/placement
        semantics, and admission remains deferred until application.

        Args:
            simulation_state: Current pre-application simulation state.
            resolved_event: Resolved Reproduction proposal to materialize.

        Returns:
            Fully determined Reproduction event ready for mechanical application.

        Raises:
            RuntimeError: If a resolved participant can no longer pay its recorded
                investment under the configured expenditure policy.
        """
        world = simulation_state.domain_state
        participants = tuple(
            self.access_model.get(
                participant_id,
                state=world,
            )
            for participant_id in resolved_event.participant_ids
        )

        for participant_id, amount in resolved_event.participant_energy_contributions:
            participant = self.access_model.get(
                participant_id,
                state=world,
            )
            if not energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                participant,
                energy_cost=amount,
                simulation_state=simulation_state,
            ):
                raise RuntimeError(
                    f"Organism {participant_id} cannot pay its recorded reproductive "
                    "energy investment under the configured energy expenditure "
                    "policy."
                )

        contributors = self._select_genetic_contributors(
            participants,
            simulation_state=simulation_state,
        )
        architecture = simulation_state.context.require(GENETIC_ARCHITECTURE)

        # All stochastic contributor choice and offspring state is deferred until
        # after resolution so rejected reproductive candidates do not consume RNG
        # or generate throwaway individual state.
        offspring_genome = self.inheritance_model.propagate(
            tuple(contributor.transmissible_state for contributor in contributors),
            recipient=None,
            context=architecture,
            rng=simulation_state.rng,
        )
        offspring = self._offspring_production_model.produce(
            offspring_genome,
            source_entities=participants,
            context=OffspringProductionContext(
                simulation_state=simulation_state,
                initial_energy=resolved_event.initial_energy,
            ),
            rng=simulation_state.rng,
        )
        genetic_contributor_ids = tuple(
            self.reference_model.reference(contributor, state=world)
            for contributor in contributors
        )

        return self.Event(
            proposal=resolved_event,
            offspring=offspring,
            genetic_contributor_ids=genetic_contributor_ids,
        )

    def apply_event(
        self,
        simulation_state: SimulationState,
        materialized_event: Reproduction.Event,
    ) -> None:
        """Mechanically apply a materialized Reproduction event.

        Participant expenditure and entity admission are distinct application
        responsibilities. The admission model owns how the already-produced
        offspring becomes part of world state.

        Args:
            simulation_state: Current simulation state.
            materialized_event: Fully determined Reproduction event to apply.

        Raises:
            RuntimeError: If a participant can no longer pay its recorded energy
                contribution under the configured expenditure policy.
        """
        world = simulation_state.domain_state
        resolved_participants: list[tuple[Organism, int]] = []

        for participant_id, amount in (
            materialized_event.participant_energy_contributions
        ):
            participant = self.access_model.get(
                participant_id,
                state=world,
            )

            if not energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                participant,
                energy_cost=amount,
                simulation_state=simulation_state,
            ):
                raise RuntimeError(
                    f"Organism {participant_id} cannot pay its recorded reproductive "
                    "energy investment under the configured energy expenditure "
                    "policy."
                )

            resolved_participants.append((participant, amount))

        # Validate every contribution before charging any participant. This keeps
        # application atomic if a stale materialized event can no longer be
        # permitted.
        for participant, amount in resolved_participants:
            participant.energy -= amount

        self.offspring_admission_model.admit(
            materialized_event.offspring,
            state=world,
        )

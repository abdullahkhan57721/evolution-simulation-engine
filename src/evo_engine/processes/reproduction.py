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
    ReproductiveEnergyInvestment,
)
from evo_engine.reproduction.investor_selection import (
    AllParticipantsInvest,
    ReproductiveInvestorSelection,
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
    RandomProductionSourceLocation,
)
from evo_engine.reproduction.production_source_selection import (
    AllParticipantsAsProductionSources,
    OffspringProductionSourceSelection,
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


def _validate_unique_ids(
    values: object,
    *,
    name: str,
    allow_empty: bool,
) -> tuple[int, ...]:
    """Return validated nonnegative unique integer IDs."""
    validated = validators.validate_tuple(values, name=name)
    if not validated and not allow_empty:
        raise ValueError(f"{name} must not be empty.")

    seen: set[int] = set()
    result: list[int] = []
    for index, value in enumerate(validated):
        item = validators.validate_int_ge(value, bound=0, name=f"{name}[{index}]")
        if item in seen:
            raise ValueError(f"{name} must not contain duplicate IDs.")
        seen.add(item)
        result.append(item)
    return tuple(result)


@attrs.frozen(slots=True, kw_only=True)
class Reproduction:
    """Represent a biological reproduction simulation process.

    Eligibility determines which organisms may individually reproduce.
    Reproductive-group selection forms nonempty candidate participant groups.
    Investor selection then chooses the participant subset whose energy investment
    is considered when deciding whether a proposal is affordable. Stage resolution
    remains based on all reproductive participants rather than investors or genetic
    contributors.

    Resolved proposals are materialized before any stage event is applied.
    Materialization chooses genetic contributors, propagates an offspring genome,
    then chooses the participant subset supplied as offspring-production context.
    Genetic contribution and production context are therefore independent while
    remaining explicitly related to the resolved reproductive episode.

    Investor selection is proposal-time and intentionally non-stochastic because
    affordability determines whether a proposal exists. Genetic-contributor and
    production-source selection occur only during materialization and may consume
    the simulation-owned RNG without rejected candidates consuming stochastic state.

    Attributes:
        eligibility: Policy determining individual reproductive eligibility.
        reproductive_group_selection: Policy proposing nonempty participant groups.
        inheritance_model: Biological adapter propagating an offspring genome from
            selected genetic-contributor states.
        genetic_contributor_selection: Policy choosing ordered genetic contributors
            from each resolved participant group.
        reproductive_investor_selection: Policy choosing the participant subset that
            invests offspring energy during proposal generation.
        reproductive_energy_investment: Policy determining one energy amount for
            each selected investor.
        offspring_production_source_selection: Policy choosing the resolved
            participant subset supplied to biological offspring production.
        energy_expenditure_policy: Policy deciding whether each investor may pay its
            proposed energy contribution.
        development_model: Policy realizing individual developmental targets during
            offspring production.
        offspring_placement: Policy choosing the offspring birth coordinate during
            offspring production.
        offspring_body_mass_model: Policy determining newborn current body mass.
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
    reproductive_investor_selection: ReproductiveInvestorSelection = attrs.field(
        factory=AllParticipantsInvest,
    )
    reproductive_energy_investment: ReproductiveEnergyInvestment = attrs.field(
        factory=GeneticPhenotypeEnergyInvestment,
    )
    offspring_production_source_selection: OffspringProductionSourceSelection = (
        attrs.field(factory=AllParticipantsAsProductionSources)
    )
    energy_expenditure_policy: EnergyExpenditurePolicy = attrs.field(
        factory=SpendToZero,
    )
    development_model: DevelopmentModel = attrs.field(
        factory=DeterministicDevelopment,
    )
    offspring_placement: OffspringPlacement = attrs.field(
        factory=RandomProductionSourceLocation,
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
                self.reproductive_investor_selection,
                "select_investors",
                "reproductive_investor_selection",
            ),
            (
                self.reproductive_energy_investment,
                "determine_investments",
                "reproductive_energy_investment",
            ),
            (
                self.offspring_production_source_selection,
                "select_sources",
                "offspring_production_source_selection",
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
            self.reproductive_investor_selection,
            self.reproductive_energy_investment,
            self.offspring_production_source_selection,
            self.energy_expenditure_policy,
            self._offspring_production_model,
            self.offspring_admission_model,
        )

    @staticmethod
    def _validate_investments(
        investments: object,
        *,
        investor_count: int,
    ) -> tuple[int, ...]:
        """Return validated reproductive-investor energy investments."""
        validated_investments = validators.validate_tuple(
            investments,
            name="investor investments",
        )

        if len(validated_investments) != investor_count:
            raise ValueError(
                "reproductive_energy_investment must return exactly one investment "
                "for each selected investor."
            )

        total_investment = 0
        result: list[int] = []
        for index, investment in enumerate(validated_investments):
            validated_investment = validators.validate_int_ge(
                investment,
                bound=0,
                name=f"investor investments[{index}]",
            )
            total_investment += validated_investment
            result.append(validated_investment)

        if total_investment < 1:
            raise ValueError("total reproductive energy investment must be at least 1.")

        return tuple(result)

    @attrs.frozen(slots=True, kw_only=True)
    class Proposal:
        """Represent a candidate Reproduction proposal.

        Attributes:
            step_index: Simulation step associated with the proposal.
            participant_ids: Ordered reproductive participants used by resolvers.
            investor_energy_contributions: ``(organism_id, energy)`` pairs for the
                participant subset investing offspring energy. An investor may
                contribute zero energy, but total offspring investment is positive.
            preference_score: Reproductive preference used by resolvers.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        participant_ids: tuple[int, ...]
        investor_energy_contributions: tuple[tuple[int, int], ...]
        preference_score: int = attrs.field(
            default=0,
            validator=attrs_validators.validate_int,
        )

        def __attrs_post_init__(self) -> None:
            """Validate participants and investor energy contributions."""
            participants = _validate_unique_ids(
                self.participant_ids,
                name="participant_ids",
                allow_empty=False,
            )
            contributions = validators.validate_tuple(
                self.investor_energy_contributions,
                name="investor_energy_contributions",
            )
            if not contributions:
                raise ValueError("investor_energy_contributions must not be empty.")

            participant_set = frozenset(participants)
            investor_ids: set[int] = set()
            total_investment = 0
            for index, contribution in enumerate(contributions):
                if type(contribution) is not tuple:
                    raise TypeError(
                        f"investor_energy_contributions[{index}] must be a tuple."
                    )
                if len(contribution) != 2:
                    raise ValueError(
                        f"investor_energy_contributions[{index}] must contain "
                        "exactly two items."
                    )

                investor_id, amount = contribution
                investor_id = validators.validate_int_ge(
                    investor_id,
                    bound=0,
                    name=f"investor_energy_contributions[{index}][0]",
                )
                amount = validators.validate_int_ge(
                    amount,
                    bound=0,
                    name=f"investor_energy_contributions[{index}][1]",
                )
                if investor_id not in participant_set:
                    raise ValueError(
                        "investor_energy_contributions must contain only reproductive "
                        "participants."
                    )
                if investor_id in investor_ids:
                    raise ValueError(
                        "investor_energy_contributions must not contain duplicate "
                        f"investor ID {investor_id}."
                    )
                investor_ids.add(investor_id)
                total_investment += amount

            if total_investment < 1:
                raise ValueError("total investor energy contribution must be at least 1.")

        @property
        def investor_ids(self) -> tuple[int, ...]:
            """Return reproductive investor IDs in recorded order."""
            return tuple(
                investor_id for investor_id, _ in self.investor_energy_contributions
            )

        @property
        def initial_energy(self) -> int:
            """Return total reproductive energy invested in the offspring."""
            return sum(amount for _, amount in self.investor_energy_contributions)

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a materialized Reproduction event.

        ``participant_ids`` records every organism in the resolved reproductive
        episode. ``parent_ids`` exposes only genetic contributors for pedigree and
        genetic ancestry. Investor contributions remain on the originating proposal,
        while ``production_source_ids`` records the organisms supplied as biological
        offspring-production context.

        Attributes:
            proposal: Resolved proposal from which the event was materialized.
            offspring: Fully produced newborn, not yet admitted to the world.
            genetic_contributor_ids: Ordered IDs whose transmissible state supplied
                the offspring genome.
            production_source_ids: Ordered participant IDs supplied to biological
                offspring production.
        """

        proposal: Reproduction.Proposal = attrs.field(
            validator=_validate_reproduction_proposal,
        )
        offspring: Organism = attrs.field(
            validator=attrs.validators.instance_of(Organism),
        )
        genetic_contributor_ids: tuple[int, ...]
        production_source_ids: tuple[int, ...]

        def __attrs_post_init__(self) -> None:
            """Validate committed energy and relationship consistency."""
            if self.offspring.energy != self.proposal.initial_energy:
                raise ValueError(
                    "offspring energy must equal the proposal's committed "
                    "reproductive energy investment."
                )

            contributor_ids = _validate_unique_ids(
                self.genetic_contributor_ids,
                name="genetic_contributor_ids",
                allow_empty=False,
            )
            production_source_ids = _validate_unique_ids(
                self.production_source_ids,
                name="production_source_ids",
                allow_empty=True,
            )
            participant_ids = frozenset(self.proposal.participant_ids)
            if not set(contributor_ids).issubset(participant_ids):
                raise ValueError(
                    "genetic_contributor_ids must contain only reproductive "
                    "participants."
                )
            if not set(production_source_ids).issubset(participant_ids):
                raise ValueError(
                    "production_source_ids must contain only reproductive participants."
                )

        @property
        def step_index(self) -> int:
            """Return the simulation step associated with the event."""
            return self.proposal.step_index

        @property
        def participant_ids(self) -> tuple[int, ...]:
            """Return all reproductive participant IDs in recorded order."""
            return self.proposal.participant_ids

        @property
        def investor_energy_contributions(self) -> tuple[tuple[int, int], ...]:
            """Return recorded reproductive-investor energy contributions."""
            return self.proposal.investor_energy_contributions

        @property
        def investor_ids(self) -> tuple[int, ...]:
            """Return reproductive investor IDs in recorded order."""
            return self.proposal.investor_ids

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
        """Propose energetically permitted reproductive events."""
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
            self.reference_model.reference(participant, state=world): participant
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
        investors = self._select_investors(
            participants,
            simulation_state=simulation_state,
        )
        investments = self._validate_investments(
            self.reproductive_energy_investment.determine_investments(
                investors,
                simulation_state=simulation_state,
            ),
            investor_count=len(investors),
        )
        if not self._can_spend_investments(
            investors,
            investments,
            simulation_state=simulation_state,
        ):
            return None

        world = simulation_state.domain_state
        return self.Proposal(
            step_index=simulation_state.step_index,
            participant_ids=participant_ids,
            investor_energy_contributions=tuple(
                (
                    self.reference_model.reference(investor, state=world),
                    investment,
                )
                for investor, investment in zip(investors, investments, strict=True)
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
                participants_by_id[participant_id] for participant_id in participant_ids
            )
        except KeyError as error:
            raise ValueError(
                "reproductive_group_selection proposed an organism that was not "
                "individually eligible to reproduce."
            ) from error

    def _canonical_participant_selection(
        self,
        selected: object,
        participants: tuple[Organism, ...],
        *,
        name: str,
        allow_empty: bool,
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return a canonical unique participant selection."""
        selected_tuple = validators.validate_tuple(selected, name=name)
        if not selected_tuple and not allow_empty:
            raise ValueError(f"{name} must not be empty.")

        world = simulation_state.domain_state
        canonical_by_reference = {
            self.reference_model.reference(participant, state=world): participant
            for participant in participants
        }
        seen_references: set[int] = set()
        canonical: list[Organism] = []
        for index, selected_organism in enumerate(selected_tuple):
            if not isinstance(selected_organism, Organism):
                raise TypeError(f"{name}[{index}] must be an Organism.")
            reference = self.reference_model.reference(selected_organism, state=world)
            try:
                participant = canonical_by_reference[reference]
            except KeyError as error:
                raise ValueError(
                    f"{name} must contain only resolved reproductive participants."
                ) from error
            if reference in seen_references:
                raise ValueError(f"{name} must not contain duplicate participants.")
            seen_references.add(reference)
            canonical.append(participant)
        return tuple(canonical)

    def _select_investors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return canonical proposal-time reproductive investors."""
        return self._canonical_participant_selection(
            self.reproductive_investor_selection.select_investors(
                participants,
                simulation_state=simulation_state,
            ),
            participants,
            name="reproductive investors",
            allow_empty=False,
            simulation_state=simulation_state,
        )

    def _select_genetic_contributors(
        self,
        participants: tuple[Organism, ...],
        *,
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return canonical materialization-time genetic contributors."""
        return self._canonical_participant_selection(
            self.genetic_contributor_selection.select_contributors(
                participants,
                simulation_state=simulation_state,
                rng=simulation_state.rng,
            ),
            participants,
            name="genetic contributors",
            allow_empty=False,
            simulation_state=simulation_state,
        )

    def _select_production_sources(
        self,
        participants: tuple[Organism, ...],
        *,
        genetic_contributors: tuple[Organism, ...],
        simulation_state: SimulationState,
    ) -> tuple[Organism, ...]:
        """Return canonical materialization-time offspring-production sources."""
        return self._canonical_participant_selection(
            self.offspring_production_source_selection.select_sources(
                participants,
                genetic_contributors=genetic_contributors,
                simulation_state=simulation_state,
                rng=simulation_state.rng,
            ),
            participants,
            name="offspring production sources",
            allow_empty=True,
            simulation_state=simulation_state,
        )

    def _can_spend_investments(
        self,
        investors: tuple[Organism, ...],
        investments: tuple[int, ...],
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether every selected investor may pay its proposed investment."""
        return all(
            energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                investor,
                energy_cost=investment,
                simulation_state=simulation_state,
            )
            for investor, investment in zip(investors, investments, strict=True)
        )

    def materialize_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Reproduction.Proposal,
    ) -> Reproduction.Event:
        """Materialize a resolved Reproduction proposal.

        Contributor and production-source selection happen only after conflict
        resolution. Inheritance sees only contributor transmissible state, while
        biological offspring production sees only the independently selected
        production-source tuple.
        """
        world = simulation_state.domain_state
        participants = tuple(
            self.access_model.get(participant_id, state=world)
            for participant_id in resolved_event.participant_ids
        )
        investors = tuple(
            self.access_model.get(investor_id, state=world)
            for investor_id in resolved_event.investor_ids
        )
        investment_amounts = tuple(
            amount for _, amount in resolved_event.investor_energy_contributions
        )
        if not self._can_spend_investments(
            investors,
            investment_amounts,
            simulation_state=simulation_state,
        ):
            raise RuntimeError(
                "One or more reproductive investors cannot pay their recorded "
                "energy investment under the configured expenditure policy."
            )

        contributors = self._select_genetic_contributors(
            participants,
            simulation_state=simulation_state,
        )
        architecture = simulation_state.context.require(GENETIC_ARCHITECTURE)
        offspring_genome = self.inheritance_model.propagate(
            tuple(contributor.transmissible_state for contributor in contributors),
            recipient=None,
            context=architecture,
            rng=simulation_state.rng,
        )
        production_sources = self._select_production_sources(
            participants,
            genetic_contributors=contributors,
            simulation_state=simulation_state,
        )
        offspring = self._offspring_production_model.produce(
            offspring_genome,
            source_entities=production_sources,
            context=OffspringProductionContext(
                simulation_state=simulation_state,
                initial_energy=resolved_event.initial_energy,
            ),
            rng=simulation_state.rng,
        )

        return self.Event(
            proposal=resolved_event,
            offspring=offspring,
            genetic_contributor_ids=tuple(
                self.reference_model.reference(contributor, state=world)
                for contributor in contributors
            ),
            production_source_ids=tuple(
                self.reference_model.reference(source, state=world)
                for source in production_sources
            ),
        )

    def apply_event(
        self,
        simulation_state: SimulationState,
        materialized_event: Reproduction.Event,
    ) -> None:
        """Mechanically charge investors and admit a materialized offspring."""
        world = simulation_state.domain_state
        resolved_investors: list[tuple[Organism, int]] = []
        for investor_id, amount in materialized_event.investor_energy_contributions:
            investor = self.access_model.get(investor_id, state=world)
            if not energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                investor,
                energy_cost=amount,
                simulation_state=simulation_state,
            ):
                raise RuntimeError(
                    f"Organism {investor_id} cannot pay its recorded reproductive "
                    "energy investment under the configured energy expenditure "
                    "policy."
                )
            resolved_investors.append((investor, amount))

        # Validate every contribution before charging any investor so stale events
        # cannot partially mutate state before an affordability failure is detected.
        for investor, amount in resolved_investors:
            investor.energy -= amount

        self.offspring_admission_model.admit(
            materialized_event.offspring,
            state=world,
        )

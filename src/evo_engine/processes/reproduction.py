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
from evo_engine.reproduction.eligibility import ReproductiveEligibility
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
from evo_engine.reproduction.parent_selection import ParentSelection
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
    """Represent a one- or two-parent reproduction simulation process.

    Eligibility determines which organisms may individually reproduce. Parent
    selection forms candidate one- or two-parent groups. Parental investment
    determines each parent's proposed energy cost. The configured energy
    expenditure policy then determines whether each parent may pay that cost,
    and stage resolution chooses which competing proposals may occur.

    Resolved proposals are materialized before any stage event is applied.
    Materialization first propagates transmissible genetic state through the
    configured inheritance model, then delegates concrete offspring construction
    to a biological entity-production model. Application pays the recorded
    energy investments and delegates entry of the already-produced offspring to
    a separate entity-admission model.

    Parent enumeration, resolver-facing reference derivation, and later parent
    resolution are delegated to generic entity lifecycle policies. Biological
    eligibility, mating, inheritance, investment, and offspring construction
    remain reproduction-domain responsibilities.

    Attributes:
        eligibility: Policy determining individual reproductive eligibility.
        parent_selection: Policy proposing one- or two-parent groups.
        inheritance_model: Biological adapter that propagates an offspring genome
            from resolved parent transmissible states.
        parental_investment: Policy determining each parent's energy cost.
        energy_expenditure_policy: Policy deciding whether each parent may pay
            its proposed energy contribution.
        development_model: Policy realizing individual developmental targets
            during offspring production.
        offspring_placement: Policy choosing the offspring birth coordinate
            during offspring production.
        offspring_body_mass_model: Policy determining newborn current body mass
            during offspring production.
        offspring_mating_type_model: Policy assigning immutable reproductive
            mating type during offspring production.
        access_model: Policy enumerating and resolving active parent organisms.
        reference_model: Policy deriving state-local parent references used by
            parent groups and reproduction proposals.
        offspring_admission_model: Policy admitting the fully produced offspring
            into biological world state during mechanical application.
    """

    behavioral_purpose: ClassVar[str] = REPRODUCTION_PURPOSE

    eligibility: ReproductiveEligibility
    parent_selection: ParentSelection
    inheritance_model: InheritanceModel
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
        parent_selection_count = self._validate_parent_count(
            self.parent_selection,
            name="parent_selection",
        )
        inheritance_count = self._validate_parent_count(
            self.inheritance_model,
            name="inheritance_model",
        )

        if parent_selection_count != inheritance_count:
            raise ValueError(
                "parent_selection and inheritance_model must require the "
                "same number of parents."
            )

        required_methods = (
            (self.eligibility, "is_eligible", "eligibility"),
            (
                self.parent_selection,
                "propose_parent_groups",
                "parent_selection",
            ),
            (self.inheritance_model, "propagate", "inheritance_model"),
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
            self.parent_selection,
            self.inheritance_model,
            self.parental_investment,
            self.energy_expenditure_policy,
            self._offspring_production_model,
            self.offspring_admission_model,
        )

    @staticmethod
    def _validate_parent_count(
        policy: ParentSelection | InheritanceModel,
        *,
        name: str,
    ) -> int:
        """Return and validate a policy's required parent count."""
        try:
            parent_count = policy.parent_count
        except AttributeError as error:
            raise TypeError(f"{name} must provide a parent_count property.") from error

        validators.validate_int_in_range(
            parent_count,
            lower=1,
            upper=2,
            name=f"{name}.parent_count",
        )

        return parent_count

    @staticmethod
    def _validate_investments(
        investments: object,
        *,
        parent_count: int,
    ) -> tuple[int, ...]:
        """Return validated parental energy investments."""
        validated_investments = validators.validate_tuple(
            investments,
            name="parental investments",
        )

        if len(validated_investments) != parent_count:
            raise ValueError(
                "parental_investment must return exactly one investment "
                "for each parent."
            )

        total_investment = 0

        for index, investment in enumerate(validated_investments):
            validated_investment = validators.validate_int_ge(
                investment,
                bound=0,
                name=f"parental investments[{index}]",
            )
            total_investment += validated_investment

        if total_investment < 1:
            raise ValueError("total parental energy investment must be at least 1.")

        return validated_investments

    @attrs.frozen(slots=True, kw_only=True)
    class Proposal:
        """Represent a candidate Reproduction proposal.

        Attributes:
            step_index: Simulation step associated with the proposal.
            parent_energy_contributions: ``(organism_id, energy)`` pairs for
                exactly one or two reproductive parents. A parent may
                contribute zero energy, but total offspring investment must be
                positive.
            preference_score: Reproductive preference used by resolvers.
        """

        step_index: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        parent_energy_contributions: tuple[tuple[int, int], ...]
        preference_score: int = attrs.field(
            default=0,
            validator=attrs_validators.validate_int,
        )

        def __attrs_post_init__(self) -> None:
            """Validate parent energy contributions."""
            validators.validate_tuple(
                self.parent_energy_contributions,
                name="parent_energy_contributions",
            )

            if len(self.parent_energy_contributions) not in (1, 2):
                raise ValueError(
                    "parent_energy_contributions must contain exactly one "
                    "or two parents."
                )

            parent_ids: set[int] = set()
            total_investment = 0

            for index, contribution in enumerate(self.parent_energy_contributions):
                if type(contribution) is not tuple:
                    raise TypeError(
                        f"parent_energy_contributions[{index}] must be a tuple."
                    )

                if len(contribution) != 2:
                    raise ValueError(
                        f"parent_energy_contributions[{index}] must contain "
                        "exactly two items."
                    )

                parent_id, amount = contribution

                validators.validate_int_ge(
                    parent_id,
                    bound=0,
                    name=f"parent_energy_contributions[{index}][0]",
                )
                validators.validate_int_ge(
                    amount,
                    bound=0,
                    name=f"parent_energy_contributions[{index}][1]",
                )

                if parent_id in parent_ids:
                    raise ValueError(
                        "parent_energy_contributions must not contain "
                        f"duplicate parent ID {parent_id}."
                    )

                parent_ids.add(parent_id)
                total_investment += amount

            if total_investment < 1:
                raise ValueError("total parent energy contribution must be at least 1.")

        @property
        def parent_ids(self) -> tuple[int, ...]:
            """Return reproductive parent IDs in recorded order."""
            return tuple(parent_id for parent_id, _ in self.parent_energy_contributions)

        @property
        def initial_energy(self) -> int:
            """Return total parental energy invested in the offspring."""
            return sum(amount for _, amount in self.parent_energy_contributions)

    @attrs.frozen(slots=True, kw_only=True)
    class Event:
        """Represent a materialized Reproduction event.

        The event owns the fully produced offspring entity. Compatibility
        properties expose the previously public materialized-offspring fields.

        Attributes:
            proposal: Resolved proposal from which the event was materialized.
            offspring: Fully produced newborn, not yet admitted to the world.
        """

        proposal: Reproduction.Proposal = attrs.field(
            validator=_validate_reproduction_proposal,
        )
        offspring: Organism = attrs.field(
            validator=attrs.validators.instance_of(Organism),
        )

        def __attrs_post_init__(self) -> None:
            """Validate consistency between committed and produced energy."""
            if self.offspring.energy != self.proposal.initial_energy:
                raise ValueError(
                    "offspring energy must equal the proposal's committed "
                    "parental energy investment."
                )

        @property
        def step_index(self) -> int:
            """Return the simulation step associated with the event."""
            return self.proposal.step_index

        @property
        def parent_energy_contributions(self) -> tuple[tuple[int, int], ...]:
            """Return recorded parental energy contributions."""
            return self.proposal.parent_energy_contributions

        @property
        def parent_ids(self) -> tuple[int, ...]:
            """Return reproductive parent IDs in recorded order."""
            return self.proposal.parent_ids

        @property
        def initial_energy(self) -> int:
            """Return total parental energy invested in the offspring."""
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
        """Propose energetically permitted one- or two-parent reproductive events.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Candidate Reproduction proposals permitted by the configured
            expenditure policy.
        """
        world = simulation_state.domain_state
        eligible_parents = self._eligible_parents(simulation_state)
        parent_groups = self.parent_selection.propose_parent_groups(
            eligible_parents,
            simulation_state=simulation_state,
            reference_model=self.reference_model,
        )
        parents_by_id = {
            self.reference_model.reference(
                parent,
                state=world,
            ): parent
            for parent in eligible_parents
        }

        proposals: list[Reproduction.Proposal] = []

        for group in parent_groups:
            proposal = self._proposal_from_parent_group(
                group.parent_ids,
                preference_score=group.preference_score,
                parents_by_id=parents_by_id,
                simulation_state=simulation_state,
            )
            if proposal is not None:
                proposals.append(proposal)

        return proposals

    def _eligible_parents(
        self,
        simulation_state: SimulationState,
    ) -> list[Organism]:
        """Return behaviorally selected, individually eligible parents."""
        eligible_parents: list[Organism] = []
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
                eligible_parents.append(organism)

        return eligible_parents

    def _proposal_from_parent_group(
        self,
        parent_ids: tuple[int, ...],
        *,
        preference_score: int,
        parents_by_id: dict[int, Organism],
        simulation_state: SimulationState,
    ) -> Reproduction.Proposal | None:
        """Return one energetically permitted proposal for a parent group."""
        parents = self._parents_from_group(
            parent_ids,
            parents_by_id=parents_by_id,
        )
        investments = self._validate_investments(
            self.parental_investment.determine_investments(
                parents,
                simulation_state=simulation_state,
            ),
            parent_count=self.inheritance_model.parent_count,
        )

        if not self._can_spend_investments(
            parents,
            investments,
            simulation_state=simulation_state,
        ):
            return None

        return self.Proposal(
            step_index=simulation_state.step_index,
            parent_energy_contributions=tuple(
                (parent_id, investment)
                for parent_id, investment in zip(
                    parent_ids,
                    investments,
                    strict=True,
                )
            ),
            preference_score=preference_score,
        )

    def _parents_from_group(
        self,
        parent_ids: tuple[int, ...],
        *,
        parents_by_id: dict[int, Organism],
    ) -> tuple[Organism, ...]:
        """Return validated eligible parents for one proposed group."""
        required_parent_count = self.inheritance_model.parent_count

        if len(parent_ids) != required_parent_count:
            raise ValueError(
                "parent_selection proposed a group with a parent count "
                "that does not match inheritance_model.parent_count."
            )

        try:
            return tuple(parents_by_id[parent_id] for parent_id in parent_ids)
        except KeyError as error:
            raise ValueError(
                "parent_selection proposed an organism that was not "
                "individually eligible to reproduce."
            ) from error

    def _can_spend_investments(
        self,
        parents: tuple[Organism, ...],
        investments: tuple[int, ...],
        *,
        simulation_state: SimulationState,
    ) -> bool:
        """Return whether every parent may pay its proposed investment."""
        return all(
            energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                parent,
                energy_cost=investment,
                simulation_state=simulation_state,
            )
            for parent, investment in zip(
                parents,
                investments,
                strict=True,
            )
        )

    def materialize_event(
        self,
        simulation_state: SimulationState,
        resolved_event: Reproduction.Proposal,
    ) -> Reproduction.Event:
        """Materialize a resolved Reproduction proposal.

        State propagation and entity production are intentionally distinct.
        Inheritance first propagates a genome from parental transmissible state.
        Biological offspring production then turns that finalized genome into a
        complete newborn organism. Admission remains deferred until application.

        Args:
            simulation_state: Current pre-application simulation state.
            resolved_event: Resolved Reproduction proposal to materialize.

        Returns:
            Fully determined Reproduction event ready for mechanical application.

        Raises:
            RuntimeError: If a resolved parent can no longer pay its recorded
                investment under the configured expenditure policy.
            ValueError: If the resolved parent count conflicts with the
                configured inheritance model.
        """
        world = simulation_state.domain_state
        parents = tuple(
            self.access_model.get(
                parent_id,
                state=world,
            )
            for parent_id in resolved_event.parent_ids
        )

        if len(parents) != self.inheritance_model.parent_count:
            raise ValueError(
                "resolved proposal parent count does not match "
                "inheritance_model.parent_count."
            )

        for parent_id, amount in resolved_event.parent_energy_contributions:
            parent = self.access_model.get(
                parent_id,
                state=world,
            )
            if not energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                parent,
                energy_cost=amount,
                simulation_state=simulation_state,
            ):
                raise RuntimeError(
                    f"Organism {parent_id} cannot pay its recorded reproductive "
                    "energy investment under the configured energy expenditure "
                    "policy."
                )

        architecture = simulation_state.context.require(GENETIC_ARCHITECTURE)

        # All stochastic offspring state is deferred until after resolution so
        # rejected mating candidates do not consume RNG or generate throwaway
        # individual state.
        offspring_genome = self.inheritance_model.propagate(
            tuple(parent.transmissible_state for parent in parents),
            recipient=None,
            context=architecture,
            rng=simulation_state.rng,
        )
        offspring = self._offspring_production_model.produce(
            offspring_genome,
            source_entities=parents,
            context=OffspringProductionContext(
                simulation_state=simulation_state,
                initial_energy=resolved_event.initial_energy,
            ),
            rng=simulation_state.rng,
        )

        return self.Event(
            proposal=resolved_event,
            offspring=offspring,
        )

    def apply_event(
        self,
        simulation_state: SimulationState,
        materialized_event: Reproduction.Event,
    ) -> None:
        """Mechanically apply a materialized Reproduction event.

        Parent expenditure and entity admission are distinct application
        responsibilities. The admission model owns how the already-produced
        offspring becomes part of world state.

        Args:
            simulation_state: Current simulation state.
            materialized_event: Fully determined Reproduction event to apply.

        Raises:
            RuntimeError: If a parent can no longer pay its recorded energy
                contribution under the configured expenditure policy.
        """
        world = simulation_state.domain_state
        resolved_parents: list[tuple[Organism, int]] = []

        for parent_id, amount in materialized_event.parent_energy_contributions:
            parent = self.access_model.get(
                parent_id,
                state=world,
            )

            if not energy_expenditure_is_allowed(
                self.energy_expenditure_policy,
                parent,
                energy_cost=amount,
                simulation_state=simulation_state,
            ):
                raise RuntimeError(
                    f"Organism {parent_id} cannot pay its recorded reproductive "
                    "energy investment under the configured energy expenditure "
                    "policy."
                )

            resolved_parents.append((parent, amount))

        # Validate every contribution before charging any parent. This keeps
        # application atomic if a stale materialized event can no longer be
        # permitted.
        for parent, amount in resolved_parents:
            parent.energy -= amount

        self.offspring_admission_model.admit(
            materialized_event.offspring,
            state=world,
        )

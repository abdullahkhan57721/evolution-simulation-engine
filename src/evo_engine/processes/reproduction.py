"""Reproduction simulation process."""

from __future__ import annotations

import attrs

from evo_engine.development.models import (
    DeterministicDevelopment,
    DevelopmentModel,
    realize_developmental_profile,
)
from evo_engine.development.profile import DevelopmentalProfile
from evo_engine.engine.simulation_state import SimulationState
from evo_engine.genetics.genetic_phenotype import GeneticPhenotype
from evo_engine.genetics.genome import Genome
from evo_engine.genetics.inheritance import InheritanceModel
from evo_engine.genetics.requirements import collect_required_traits
from evo_engine.reproduction.birth_mass import (
    AdultBodyMassAtBirth,
    OffspringBodyMassModel,
)
from evo_engine.reproduction.eligibility import ReproductiveEligibility
from evo_engine.reproduction.investment import (
    GeneticPhenotypeEnergyInvestment,
    ParentalInvestment,
)
from evo_engine.reproduction.parent_selection import ParentSelection
from evo_engine.reproduction.placement import (
    OffspringPlacement,
    RandomParentLocation,
)
from evo_engine.validation import attrs_validators, validators
from evo_engine.world.organism import Organism


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
    determines the energy cost for each candidate group, and stage resolution
    chooses which competing proposals may occur.

    Resolved proposals are materialized before any stage event is applied.
    Materialization performs inheritance, genetic phenotype expression, and offspring
    placement. Application then only pays the recorded energy investments and
    inserts the already-defined offspring into the world.

    Attributes:
        eligibility: Policy determining individual reproductive eligibility.
        parent_selection: Policy proposing one- or two-parent groups.
        inheritance_model: Policy producing an offspring genome from resolved
            parent genomes.
        parental_investment: Policy determining each parent's energy cost.
        development_model: Policy realizing individual developmental targets
            from the offspring genetic phenotype.
        offspring_placement: Policy choosing the offspring birth coordinate.
        offspring_body_mass_model: Policy determining newborn current body
            mass from the developmental profile and parents.
    """

    eligibility: ReproductiveEligibility
    parent_selection: ParentSelection
    inheritance_model: InheritanceModel
    parental_investment: ParentalInvestment = attrs.field(
        factory=GeneticPhenotypeEnergyInvestment,
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

    def __attrs_post_init__(self) -> None:
        """Validate reproduction configuration."""
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
            (
                self.eligibility,
                "is_eligible",
                "eligibility",
            ),
            (
                self.parent_selection,
                "propose_parent_groups",
                "parent_selection",
            ),
            (
                self.inheritance_model,
                "inherit",
                "inheritance_model",
            ),
            (
                self.parental_investment,
                "determine_investments",
                "parental_investment",
            ),
            (
                self.development_model,
                "develop",
                "development_model",
            ),
            (
                self.offspring_placement,
                "choose_location",
                "offspring_placement",
            ),
            (
                self.offspring_body_mass_model,
                "determine_body_mass",
                "offspring_body_mass_model",
            ),
        )

        for policy, method_name, policy_name in required_methods:
            if not callable(
                getattr(
                    policy,
                    method_name,
                    None,
                )
            ):
                raise TypeError(
                    f"{policy_name} must provide a callable {method_name} method."
                )

    @property
    def required_traits(self) -> frozenset[str]:
        """Return genetic phenotype traits required by reproduction policies."""
        return collect_required_traits(
            self.eligibility,
            self.parent_selection,
            self.inheritance_model,
            self.parental_investment,
            self.development_model,
            self.offspring_placement,
            self.offspring_body_mass_model,
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

        Attributes:
            proposal: Resolved proposal from which this event was materialized.
            offspring_genome: Fully determined offspring genome.
            offspring_genetic_phenotype: Genetic phenotype expressed from the
                offspring genome.
            offspring_developmental_profile: Individual developmental targets
                realized from the offspring genetic phenotype.
            initial_body_mass: Current physical mass assigned at birth.
            x: Final offspring horizontal birth coordinate.
            y: Final offspring vertical birth coordinate.
        """

        proposal: Reproduction.Proposal = attrs.field(
            validator=_validate_reproduction_proposal,
        )
        offspring_genome: Genome = attrs.field(
            validator=attrs.validators.instance_of(Genome),
        )
        offspring_genetic_phenotype: GeneticPhenotype = attrs.field(
            validator=attrs.validators.instance_of(GeneticPhenotype),
        )
        offspring_developmental_profile: DevelopmentalProfile = attrs.field(
            validator=attrs.validators.instance_of(DevelopmentalProfile),
        )
        initial_body_mass: int = attrs.field(
            validator=attrs_validators.validate_int_ge(1),
        )
        x: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
        )
        y: int = attrs.field(
            validator=attrs_validators.validate_int_ge(0),
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
    def event_type(self) -> type[Reproduction.Proposal]:
        """Return the Reproduction proposal type used for resolution."""
        return self.Proposal

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[Reproduction.Proposal]:
        """Propose affordable one- or two-parent reproductive events.

        Args:
            simulation_state: Current simulation state.

        Returns:
            Candidate Reproduction proposals.
        """
        eligible_parents = self._eligible_parents(simulation_state)
        parent_groups = self.parent_selection.propose_parent_groups(
            eligible_parents,
            simulation_state=simulation_state,
        )
        parents_by_id = {parent.id: parent for parent in eligible_parents}

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
        """Return organisms that satisfy individual reproductive eligibility."""
        eligible_parents: list[Organism] = []

        for organism in simulation_state.world.organisms.values():
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
        """Return one affordable proposal for a validated parent group."""
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

        if not self._can_afford_investments(
            parents,
            investments,
        ):
            return None

        return self.Proposal(
            step_index=simulation_state.step_index,
            parent_energy_contributions=tuple(
                (parent.id, investment)
                for parent, investment in zip(
                    parents,
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

    @staticmethod
    def _can_afford_investments(
        parents: tuple[Organism, ...],
        investments: tuple[int, ...],
    ) -> bool:
        """Return whether every parent can afford its proposed investment."""
        return all(
            parent.energy >= investment
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

        Inheritance, mutation, recombination, genetic phenotype expression,
        developmental realization, and random offspring placement happen here,
        after resolution but before any event
        in the stage is applied.

        Args:
            simulation_state: Current pre-application simulation state.
            resolved_event: Resolved Reproduction proposal to materialize.

        Returns:
            Fully determined Reproduction event ready for mechanical
            application.

        Raises:
            RuntimeError: If a resolved parent can no longer afford its
                recorded investment.
            ValueError: If the resolved parent count conflicts with the
                configured inheritance model.
        """
        world = simulation_state.world

        parents = tuple(
            world.organisms[parent_id] for parent_id in resolved_event.parent_ids
        )

        if len(parents) != self.inheritance_model.parent_count:
            raise ValueError(
                "resolved proposal parent count does not match "
                "inheritance_model.parent_count."
            )

        for parent_id, amount in resolved_event.parent_energy_contributions:
            if world.organisms[parent_id].energy < amount:
                raise RuntimeError(
                    f"Organism {parent_id} cannot afford its recorded "
                    "reproductive energy investment."
                )

        architecture = simulation_state.genetic_architecture

        # Genetics and placement are deferred until after resolution so
        # rejected mating candidates do not consume RNG or generate throwaway
        # offspring state.
        offspring_genome = self.inheritance_model.inherit(
            tuple(parent.genome for parent in parents),
            genetic_architecture=architecture,
            rng=simulation_state.rng,
        )

        offspring_genetic_phenotype = architecture.express(offspring_genome)

        # Developmental variation is sampled only for resolved births, just
        # like inheritance and placement, so rejected proposals do not consume
        # random draws or create unused individual targets.
        offspring_developmental_profile = realize_developmental_profile(
            self.development_model,
            offspring_genetic_phenotype,
            rng=simulation_state.rng,
            simulation_state=simulation_state,
        )

        initial_body_mass = self.offspring_body_mass_model.determine_body_mass(
            offspring_developmental_profile,
            parents,
            simulation_state=simulation_state,
        )
        validators.validate_int_ge(
            initial_body_mass,
            bound=1,
            name="offspring initial body mass",
        )

        x, y = self.offspring_placement.choose_location(
            parents,
            simulation_state=simulation_state,
            rng=simulation_state.rng,
        )

        return self.Event(
            proposal=resolved_event,
            offspring_genome=offspring_genome,
            offspring_genetic_phenotype=offspring_genetic_phenotype,
            offspring_developmental_profile=(offspring_developmental_profile),
            initial_body_mass=initial_body_mass,
            x=x,
            y=y,
        )

    def apply_event(
        self,
        simulation_state: SimulationState,
        materialized_event: Reproduction.Event,
    ) -> None:
        """Mechanically apply a materialized Reproduction event.

        Args:
            simulation_state: Current simulation state.
            materialized_event: Fully determined Reproduction event to apply.

        Raises:
            RuntimeError: If a parent can no longer afford its recorded
                energy contribution.
        """
        world = simulation_state.world

        for parent_id, amount in materialized_event.parent_energy_contributions:
            parent = world.organisms[parent_id]

            if parent.energy < amount:
                raise RuntimeError(
                    f"Organism {parent_id} cannot afford its recorded "
                    "reproductive energy investment."
                )

        # Validate every contribution before charging any parent. This keeps
        # application atomic if a stale materialized event can no longer be
        # afforded.
        for parent_id, amount in materialized_event.parent_energy_contributions:
            world.organisms[parent_id].energy -= amount

        offspring = Organism(
            age=0,
            energy=materialized_event.initial_energy,
            body_mass=materialized_event.initial_body_mass,
            genome=materialized_event.offspring_genome,
            genetic_phenotype=materialized_event.offspring_genetic_phenotype,
            developmental_profile=(materialized_event.offspring_developmental_profile),
            x=materialized_event.x,
            y=materialized_event.y,
        )

        world.add_organism(offspring)

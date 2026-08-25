"""Represent immutable configuration shared by simulation state snapshots."""

from __future__ import annotations

import attrs

from evo_engine.behavior import BehaviorSelectionModel, UnrestrictedBehavior
from evo_engine.genetics.genetic_architecture import GeneticArchitecture


@attrs.frozen(slots=True, kw_only=True)
class SimulationContext:
    """Hold immutable models shared by every state snapshot in one run.

    Runtime state is transactionally copied from timestep to timestep, while
    configuration models are shared by reference. Keeping those concepts in an
    explicit context prevents mutable state from becoming a container for an
    ever-growing collection of configuration services.

    Attributes:
        genetic_architecture: Shared heritable-state expression and biological
            genetics rules.
        behavior_selection_model: Shared policy deciding whether organisms
            attempt behavioral purposes.
    """

    genetic_architecture: GeneticArchitecture = attrs.field(
        validator=attrs.validators.instance_of(GeneticArchitecture),
    )
    behavior_selection_model: BehaviorSelectionModel = attrs.field(
        factory=UnrestrictedBehavior,
        validator=attrs.validators.instance_of(BehaviorSelectionModel),
    )

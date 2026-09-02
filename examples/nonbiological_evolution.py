"""Run a nonbiological evolutionary simulation of competing information tokens.

Persistent network nodes carry strategy tokens that spread horizontally. A
token's expressed broadcast weight changes how often it becomes a propagation
source, while simulation-RNG-driven variation can flip the copied token. The
node identities and population size remain fixed as token composition evolves.
"""

from __future__ import annotations

import random
from collections import Counter
from typing import Any, Literal

import attrs

from evo_engine.configuration import CompiledSimulation, SimulationSpec
from evo_engine.engine import (
    MaxSteps,
    SequentialStepCoordinator,
    SimulationState,
    StageCoordinator,
)
from evo_engine.evolution import (
    CharacteristicSource,
    TransmissibleStateExpression,
    VariationOperator,
)
from evo_engine.propagation import PropagationModel, TransmissibleStateCarrier
from evo_engine.resolvers import AcceptAll
from evo_engine.telemetry import StepTelemetry

DEFAULT_SEED = 84
DEFAULT_STEPS = 6
BROADCAST_WEIGHT = "broadcast_weight"

type StrategyToken = Literal["amplify", "retain"]
AMPLIFY: StrategyToken = "amplify"
RETAIN: StrategyToken = "retain"


@attrs.define(slots=True, kw_only=True)
class InformationNode:
    """Represent a persistent network node carrying one strategy token."""

    node_id: int
    token: StrategyToken

    @property
    def transmissible_state(self) -> StrategyToken:
        """Return the strategy token available for horizontal propagation."""
        return self.token

    def copy(self) -> InformationNode:
        """Return an independent node with the same identity and token."""
        return InformationNode(node_id=self.node_id, token=self.token)


@attrs.define(slots=True, kw_only=True)
class InformationNetwork:
    """Hold persistent information nodes in deterministic iteration order."""

    nodes: dict[int, InformationNode] = attrs.field(factory=dict)

    def copy(self) -> InformationNetwork:
        """Return an independent transactional copy of the network."""
        return InformationNetwork(
            nodes={node_id: node.copy() for node_id, node in self.nodes.items()}
        )

    def composition(self) -> dict[str, int]:
        """Return counts ordered by the example's public token names."""
        counts = Counter(_transmissible_token(node) for node in self.nodes.values())
        return {
            AMPLIFY: counts[AMPLIFY],
            RETAIN: counts[RETAIN],
        }


@attrs.frozen(slots=True)
class StrategyExpression:
    """Express a token as the influence used during source selection."""

    def express(self, transmissible_state: StrategyToken, /) -> int:
        """Return the operative broadcast weight for a strategy token."""
        return 3 if transmissible_state == AMPLIFY else 1


@attrs.frozen(slots=True, kw_only=True)
class StrategyCharacteristics:
    """Expose expressed token characteristics to transition processes."""

    expression: TransmissibleStateExpression[StrategyToken, int] = attrs.field(
        factory=StrategyExpression
    )

    def value_for(
        self,
        entity: InformationNode,
        characteristic_name: str,
        *,
        context: InformationNetwork,
    ) -> int:
        """Return one named operative characteristic for a network node."""
        del context
        if characteristic_name != BROADCAST_WEIGHT:
            raise KeyError(f"unknown characteristic {characteristic_name!r}.")
        return self.expression.express(_transmissible_token(entity))


@attrs.frozen(slots=True, kw_only=True)
class TokenVariation:
    """Flip copied strategies with a fixed probability per million."""

    probability_ppm: int = 100_000

    def __attrs_post_init__(self) -> None:
        """Validate the configured variation probability."""
        if not 0 <= self.probability_ppm <= 1_000_000:
            raise ValueError("probability_ppm must be between 0 and 1,000,000.")

    def vary(
        self,
        value: StrategyToken,
        *,
        rng: random.Random,
    ) -> StrategyToken:
        """Return a copied strategy, possibly flipped by simulation RNG."""
        if rng.randrange(1_000_000) >= self.probability_ppm:
            return value
        return RETAIN if value == AMPLIFY else AMPLIFY


@attrs.frozen(slots=True, kw_only=True)
class TokenPropagation:
    """Copy one source token to a recipient with possible variation."""

    variation: VariationOperator[StrategyToken] = attrs.field(factory=TokenVariation)

    def propagate(
        self,
        source_states: tuple[StrategyToken, ...],
        *,
        recipient: InformationNode,
        context: None,
        rng: random.Random,
    ) -> StrategyToken:
        """Return a varied copy of exactly one source token."""
        del recipient, context
        if len(source_states) != 1:
            raise ValueError("token propagation requires exactly one source state.")
        return self.variation.vary(source_states[0], rng=rng)


@attrs.frozen(slots=True, kw_only=True)
class PropagationProposal:
    """Propose one opportunity to replace a recipient's token."""

    step_index: int
    recipient_id: int


@attrs.frozen(slots=True, kw_only=True)
class PropagationEvent:
    """Describe one fully materialized token-replacement transition."""

    step_index: int
    recipient_id: int
    source_id: int
    source_state: StrategyToken
    propagated_state: StrategyToken


@attrs.frozen(slots=True, kw_only=True)
class TokenPropagationProcess:
    """Propose, materialize, and apply horizontal token propagation."""

    characteristics: CharacteristicSource[InformationNode, InformationNetwork, int] = (
        attrs.field(factory=StrategyCharacteristics)
    )
    propagation: PropagationModel[StrategyToken, InformationNode, None] = attrs.field(
        factory=TokenPropagation
    )

    @property
    def event_type(self) -> type[PropagationProposal]:
        """Return the proposal type owned by this process."""
        return PropagationProposal

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> list[PropagationProposal]:
        """Propose one replacement opportunity for every persistent node."""
        network = _network_from(simulation_state.domain_state)
        return [
            PropagationProposal(
                step_index=simulation_state.step_index,
                recipient_id=node_id,
            )
            for node_id in network.nodes
        ]

    def materialize_event(
        self,
        simulation_state: SimulationState,
        event: PropagationProposal,
        /,
    ) -> PropagationEvent:
        """Select a weighted source and vary its token using simulation RNG."""
        network = _network_from(simulation_state.domain_state)
        source_nodes = tuple(network.nodes.values())
        weights = tuple(
            self.characteristics.value_for(
                node,
                BROADCAST_WEIGHT,
                context=network,
            )
            for node in source_nodes
        )
        source = simulation_state.rng.choices(source_nodes, weights=weights, k=1)[0]
        propagated_state = self.propagation.propagate(
            (_transmissible_token(source),),
            recipient=network.nodes[event.recipient_id],
            context=None,
            rng=simulation_state.rng,
        )
        return PropagationEvent(
            step_index=event.step_index,
            recipient_id=event.recipient_id,
            source_id=source.node_id,
            source_state=_transmissible_token(source),
            propagated_state=propagated_state,
        )

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: PropagationEvent,
        /,
    ) -> None:
        """Commit one already-materialized recipient token replacement."""
        network = _network_from(simulation_state.domain_state)
        network.nodes[event.recipient_id].token = event.propagated_state


@attrs.frozen(slots=True, kw_only=True)
class CompositionSnapshot:
    """Record transmissible-state composition after one committed state."""

    step_index: int
    composition: tuple[tuple[str, int], ...]


@attrs.define(slots=True)
class EvolutionRecorder:
    """Record committed composition snapshots and propagation events."""

    snapshots: list[CompositionSnapshot] = attrs.field(factory=list)
    events: list[PropagationEvent] = attrs.field(factory=list)

    def should_observe(self, domain_state: Any, /, *, step_index: int) -> bool:
        """Observe every committed network state."""
        del domain_state, step_index
        return True

    def observe(self, domain_state: Any, /, *, step_index: int) -> None:
        """Record one immutable composition snapshot."""
        composition = _network_from(domain_state).composition()
        self.snapshots.append(
            CompositionSnapshot(
                step_index=step_index,
                composition=tuple(composition.items()),
            )
        )

    def should_observe_telemetry(self, telemetry: StepTelemetry) -> bool:
        """Observe every committed simulation step."""
        del telemetry
        return True

    def observe_telemetry(self, telemetry: StepTelemetry) -> None:
        """Record propagation events from one committed step."""
        self.events.extend(
            applied.event
            for applied in telemetry.events
            if isinstance(applied.event, PropagationEvent)
        )


@attrs.frozen(slots=True, kw_only=True)
class NonbiologicalEvolution:
    """Bundle the compiled example and its evidence recorder."""

    compiled: CompiledSimulation
    recorder: EvolutionRecorder


def build_nonbiological_evolution(
    *,
    seed: int = DEFAULT_SEED,
    max_steps: int = DEFAULT_STEPS,
) -> NonbiologicalEvolution:
    """Build the deterministic nonbiological vertical slice."""
    network = InformationNetwork(
        nodes={
            node_id: InformationNode(
                node_id=node_id,
                token=AMPLIFY if node_id < 3 else RETAIN,
            )
            for node_id in range(12)
        }
    )
    recorder = EvolutionRecorder()
    coordinator = SequentialStepCoordinator(
        stages=(
            StageCoordinator(
                processes=(TokenPropagationProcess(),),
                resolver=AcceptAll(),
            ),
        )
    )
    compiled = SimulationSpec(
        initial_domain_state=network,
        step_coordinator=coordinator,
        stopping_condition=MaxSteps(max_steps=max_steps),
        seed=seed,
        observers=(recorder,),
        telemetry_observers=(recorder,),
    ).compile()
    return NonbiologicalEvolution(compiled=compiled, recorder=recorder)


def _network_from(domain_state: object) -> InformationNetwork:
    if not isinstance(domain_state, InformationNetwork):
        raise TypeError("the nonbiological example requires InformationNetwork.")
    return domain_state


def _transmissible_token(
    carrier: TransmissibleStateCarrier[StrategyToken],
) -> StrategyToken:
    return carrier.transmissible_state


def _format_composition(composition: dict[str, int]) -> str:
    return ", ".join(f"{name}={count}" for name, count in composition.items())


def main() -> None:
    """Run the fixed-seed example and print its evolutionary summary."""
    example = build_nonbiological_evolution()
    initial_network = _network_from(example.compiled.simulation.state.domain_state)
    initial_composition = initial_network.composition()

    example.compiled.engine.run(example.compiled.simulation)

    final_network = _network_from(example.compiled.simulation.state.domain_state)
    print(f"Seed: {DEFAULT_SEED}")
    print(f"Completed steps: {example.compiled.simulation.state.step_index}")
    print(f"Initial composition: {_format_composition(initial_composition)}")
    print(f"Final composition: {_format_composition(final_network.composition())}")


if __name__ == "__main__":
    main()

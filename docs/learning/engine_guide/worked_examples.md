# Worked Examples Across the Layers

The fastest way to understand the architecture is to run the **same execution
machinery at three levels of meaning**.

```text
Example 1: Counter
    kernel only

Example 2: Information network
    kernel + general evolution

Example 3: Biological aging
    kernel + biological domain
```

The point is not merely to show three programs. It is to isolate what each layer
adds.

# Example 1 — Counter: kernel only

The repository's kernel tests use a small `CounterState` and `IncrementProcess`
because they make execution semantics visible without domain distractions.

## Domain state

```python
@attrs.define(slots=True)
class CounterState:
    value: int = 0
    notes: list[str] = attrs.field(factory=list)

    def copy(self) -> CounterState:
        return copy.deepcopy(self)
```

What does the kernel know about this class?

Only:

```text
it is the domain_state payload
it has callable copy()
```

The names `value` and `notes` have no kernel meaning.

## Event

```python
@attrs.frozen(slots=True, kw_only=True)
class IncrementEvent:
    step_index: int
    amount: int = 1
```

This satisfies the minimal event contract because it exposes `step_index`.

## Process

```python
@attrs.frozen(slots=True)
class IncrementProcess:
    amount: int = 1

    @property
    def event_type(self) -> type[IncrementEvent]:
        return IncrementEvent

    def propose_events(self, simulation_state: SimulationState):
        return [
            IncrementEvent(
                step_index=simulation_state.step_index,
                amount=self.amount,
            )
        ]

    def apply_event(self, simulation_state, event, /):
        simulation_state.domain_state.value += event.amount
```

Read it architecturally:

```text
proposal
    describes +amount from stage-start state

application
    owns actual counter mutation
```

No materializer is needed because the proposal already contains everything
required for application.

## Assembly

```python
simulation = Simulation(
    initial_domain_state=CounterState(),
    seed=7,
)

stage = StageCoordinator(
    processes=(IncrementProcess(),),
    resolver=AcceptAll(),
)

engine = SimulationEngine(
    step_coordinator=SequentialStepCoordinator(stages=(stage,)),
    stopping_condition=MaxSteps(max_steps=3),
)

engine.run(simulation)
```

Final result:

```text
value      = 3
step_index = 3
```

## What this example proves

It proves the kernel does not require:

```text
Organism
Genome
WorldState
energy
reproduction
evolution
```

It also gives you the smallest environment in which to study transactions,
stages, events, and resolvers.

# Example 1A — Add conflict without changing the process

Imagine the process proposes several increments but a domain rule says only one
may be accepted.

You should not need to rewrite the process's application semantics.

Instead:

```text
IncrementProcess
    still says what an increment means

Resolver
    changes which proposals survive
```

This illustrates why conflict policy is a separate injectable component.

# Example 1B — Add materialization

Now imagine an accepted increment should draw a random amount only after
acceptance.

Proposal:

```text
IncrementProposal(step_index)
```

Materialization:

```text
accepted proposal
    |
    +-- rng.randint(1, 10)
    |
    v
IncrementEvent(step_index, amount)
```

Application remains:

```text
state.value += event.amount
```

This modification teaches materialization without introducing biology.

# Example 2 — Information network: evolution without biology

The repository's
[`examples/nonbiological_evolution.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/examples/nonbiological_evolution.py)
is the most important architecture proof above the kernel.

Persistent nodes carry strategy tokens:

```text
"amplify"
"retain"
```

The population of nodes stays fixed. What evolves is token composition.

## Step 1: evolving entity

```python
@attrs.define(slots=True, kw_only=True)
class InformationNode:
    node_id: int
    token: StrategyToken

    @property
    def transmissible_state(self) -> StrategyToken:
        return self.token
```

Layer interpretation:

```text
[KERNEL]
just an object hidden inside domain_state

[GENERAL EVOLUTION]
persistent entity + TransmissibleStateCarrier capability

[BIOLOGY]
none
```

## Step 2: transactional domain state

`InformationNetwork` owns nodes and implements `copy()` by copying every node.

```text
InformationNetwork.copy()
        |
        v
independent transactional network
```

That satisfies the kernel without importing biological `WorldState`.

## Step 3: expression

```python
class StrategyExpression:
    def express(self, transmissible_state, /) -> int:
        return 3 if transmissible_state == "amplify" else 1
```

General-evolution interpretation:

```text
strategy token
     |
  expression
     |
     v
broadcast weight
```

The raw transmitted token and the operative characteristic are separate.

## Step 4: variation

```python
class TokenVariation:
    def vary(self, value, *, rng):
        if rng.randrange(1_000_000) >= self.probability_ppm:
            return value
        return "retain" if value == "amplify" else "amplify"
```

The important dependency is:

```text
variation consumes supplied simulation RNG
```

not a hidden generator.

## Step 5: propagation

`TokenPropagation` takes exactly one source token in this concrete policy:

```text
(source token, recipient, context, RNG)
        |
        v
possibly varied copied token
```

The **general** `PropagationModel` permits arbitrary source count. The example's
one-source restriction belongs to this concrete policy.

## Step 6: proposal

For every persistent recipient node:

```python
PropagationProposal(
    step_index=simulation_state.step_index,
    recipient_id=node_id,
)
```

Notice what is deliberately missing:

```text
source_id
source_state
propagated_state
```

Those details do not exist yet.

## Step 7: materialization

Only after the proposal is accepted does the process:

```text
compute expressed source weights
        |
        v
choose source with simulation RNG
        |
        v
propagate source token
        |
        v
possibly vary token with same RNG
        |
        v
create PropagationEvent
```

The materialized event records:

```text
recipient_id
source_id
source_state
propagated_state
```

This is exactly the sort of accepted-only stochastic consequence the
materialization phase is designed for.

## Step 8: application

Application is intentionally simple:

```python
network.nodes[event.recipient_id].token = event.propagated_state
```

All stochastic decisions are already committed to the materialized event value.

## Step 9: observation

`EvolutionRecorder` plays two roles:

```text
Observer
    records committed token composition snapshots

TelemetryObserver
    records committed PropagationEvent values
```

So it can answer both:

```text
What composition exists now?
What propagation transitions caused it?
```

## Step 10: compile through `SimulationSpec`

The example assembles:

```python
compiled = SimulationSpec(
    initial_domain_state=network,
    step_coordinator=coordinator,
    stopping_condition=MaxSteps(max_steps=max_steps),
    seed=seed,
    observers=(recorder,),
    telemetry_observers=(recorder,),
).compile()
```

This proves the nonbiological example is using the real public construction path,
not a toy bypass around the kernel.

## What makes this evolutionary?

The causal chain is:

```text
transmissible token variants
        |
        v
expressed broadcast-weight differences
        |
        v
differential chance of becoming propagation source
        |
        v
source -> recipient propagation
        |
        +-- possible variation
        |
        v
changed distribution of transmissible tokens
```

No organism is born. No genome exists. Yet transmissible-state composition changes
through differential propagation and variation.

# Example 3 — Biological aging: the same kernel with richer domain meaning

The repository's
[`examples/basic_aging_simulation.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/examples/basic_aging_simulation.py)
uses the same kernel objects with a biological domain.

## Biological construction

The example creates:

```text
GeneticArchitecture
Genome
WorldState
Organism
```

and adds the organism to the world.

These objects are **not kernel concepts**. They are domain state and configuration
used by a biological process.

## Simulation construction

```python
return Simulation(
    initial_domain_state=world,
    genetic_architecture=genetic_architecture,
    seed=42,
)
```

`world` becomes the opaque `domain_state` payload from the kernel's perspective.

`genetic_architecture=...` is named context-value construction sugar. It is
normalized into immutable `SimulationContext` rather than becoming a synthetic
attribute on `SimulationState`.

## Engine construction

```python
aging_stage = StageCoordinator(
    processes=(Aging(),),
    resolver=AcceptAll(),
)

engine = SimulationEngine(
    step_coordinator=SequentialStepCoordinator(stages=(aging_stage,)),
    stopping_condition=MaxSteps(max_steps=10),
)
```

Compare that with the counter:

```text
Counter example               Aging example
---------------               -------------
IncrementProcess              Aging
AcceptAll                     AcceptAll
StageCoordinator              StageCoordinator
SequentialStepCoordinator     SequentialStepCoordinator
MaxSteps                      MaxSteps
Simulation                    Simulation
SimulationEngine              SimulationEngine
```

The orchestration is unchanged.

Only the domain payload and process meaning changed.

## Crossing the domain boundary deliberately

After the run:

```python
world = simulation.state.domain_state
organism = next(iter(world.organisms.values()))
```

Now the code is explicitly outside the kernel abstraction and knows the payload is
a biological `WorldState`.

This is the correct place to use domain-native vocabulary.

# Side-by-side comparison of all three examples

| Question | Counter | Information network | Biology |
| --- | --- | --- | --- |
| `domain_state` | `CounterState` | `InformationNetwork` | `WorldState` |
| Kernel understands payload? | no | no | no |
| Entity concept needed? | no | `InformationNode` | `Organism` |
| Transmissible state? | no | strategy token | genome |
| Expression? | no | token -> broadcast weight | genetic expression |
| Variation? | optional toy extension | token flip | mutation/recombination |
| Propagation? | no | horizontal token copy | inheritance |
| Entity production? | no | no | reproduction/birth |
| Process | increment | token propagation | aging / biological processes |
| Resolver | `AcceptAll` | `AcceptAll` | `AcceptAll` or domain resolver |
| Kernel transaction | same | same | same |
| Simulation RNG | same ownership | source + variation | biological stochasticity |

The table exposes the architecture's main promise:

> **Richer modeled meaning is layered above stable execution mechanics.**

# A fourth conceptual trace — reproduction

A full reproduction process is more complicated than the aging example, but it is
useful to place it on the same pipeline.

```text
[KERNEL]
propose
    |
    v
[BIOLOGY]
form participant group
select proposal-time investors
check affordability
    |
    v
[KERNEL]
resolver accepts/rejects participant-based candidate
    |
    v
[KERNEL MATERIALIZATION]
    |
    +--> [BIOLOGY] select genetic contributors
    |         |
    |         v
    |     inheritance / propagation
    |         |
    |         v
    |     offspring genome
    |
    +--> [BIOLOGY] select production sources
    |
    +--> other accepted-only offspring details
    |
    v
[KERNEL APPLICATION]
    |
    +--> commit investment/state changes
    +--> produce/admit offspring according to domain process
    |
    v
committed telemetry / pedigree / observation
```

The important lesson is not the exact current reproduction implementation. It is
how the kernel phases create slots where domain responsibilities can occur without
moving those responsibilities into the kernel.

# Trace one concept vertically: randomness

### Counter

No randomness required.

### Information network

```text
materialization
    -> weighted source selection
    -> token variation
```

both use `simulation_state.rng`.

### Biology

Stochastic mating, inheritance, mutation, recombination, placement, or other
policies can also consume the same transaction-owned RNG at the phase appropriate
to their semantics.

The RNG ownership rule does not change just because the domain becomes richer.

# Trace one concept vertically: copying

### Counter

```text
CounterState.copy()
```

copies one value/list.

### Information network

```text
InformationNetwork.copy()
```

copies every node so token replacement in the transaction cannot mutate committed
nodes.

### Biology

```text
WorldState.copy()
```

must preserve transactional isolation for a much richer object graph.

The kernel's contract stays simply:

```text
domain_state must provide a correct independent copy for transactions
```

The domain owns how to achieve that.

# Trace one concept vertically: selection

### Counter

Not evolutionary; selection is absent.

### Information network

Tokens expressing higher broadcast weight become sources more often. Differential
propagation changes composition.

### Biology

Inherited differences can affect survival, mating, reproduction, ecology, and
therefore genetic contribution. Selection emerges from those outcomes.

The kernel does not gain a `fitness` concept at any point.

# Predict-before-running exercises

## Prediction 1 — stage ordering

Start `value = 2`.

```text
Stage 0: +3
Stage 1: multiply by 4
```

What is the final value?

Because stages are sequential:

```text
2 -> 5 -> 20
```

Reversing the stages would be a different configured model:

```text
2 -> 8 -> 11
```

## Prediction 2 — same-stage proposals

Start `resource = 5`.
Two processes in one stage both propose based on resource availability.

If process A's application would reduce resource to 1, does process B see `1`
while proposing?

No. Both proposals were collected before application began.

## Prediction 3 — rejected stochastic proposal

A process proposes candidate A and candidate B. The resolver always rejects B.
Random source selection occurs in `materialize_event`.

Should B consume a source-selection RNG draw?

No. Only resolved/accepted events enter materialization.

# What to study first in the repository

For the counter/kernel mechanics:

1. [`tests/engine/helpers.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/helpers.py)
2. [`tests/engine/test_domain_neutral_kernel.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_domain_neutral_kernel.py)
3. [`tests/engine/test_stage_coordinator.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_stage_coordinator.py)

For general evolution:

1. [`examples/nonbiological_evolution.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/examples/nonbiological_evolution.py)
2. [General Evolution Framework](../../general_evolution_framework.md)

For the simplest biological integration:

1. [`examples/basic_aging_simulation.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/examples/basic_aging_simulation.py)
2. then the relevant `Aging` process source and focused tests.

# You understand this chapter if you can…

- explain what the counter proves that the biological example cannot prove as
  cleanly;
- identify exactly what new semantic structure the information-network example
  adds above the kernel;
- explain why the information network demonstrates evolution without entity
  production;
- compare the counter, information network, and aging example and point out which
  kernel objects remain unchanged;
- trace proposal/materialization/application in the token process;
- explain where a biological reproduction process fits into the same kernel
  phases; and
- design a fourth domain example while leaving the kernel object graph unchanged.

Next: [Reading the Kernel Source](source_code_walkthrough.md).

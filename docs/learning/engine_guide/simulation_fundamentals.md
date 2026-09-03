# Simulation Fundamentals

Before looking at the kernel API, it helps to strip away every biological word and
ask what a simulation engine is doing at the most general level.

## Where you are in the architecture

```text
software-design ideas
        |
        v
YOU ARE HERE: generic simulation
        |
        v
simulation kernel implementation
        |
        v
general evolution
        |
        v
biology
```

The kernel is one professional implementation of the ideas in this chapter.

## The smallest possible simulation model

At its simplest, a discrete simulation repeatedly transforms state:

```text
State(t)
   |
   | transition rule
   v
State(t+1)
```

If the state is a counter and the rule is “add one,” then:

```text
0 -> 1 -> 2 -> 3 -> 4
```

Nothing about this is evolutionary or biological. It is simply a state-transition
system.

A naive Python implementation could be:

```python
for _ in range(10):
    state.value += 1
```

For a toy system, that is excellent code. Architecture becomes necessary only
when the modeled transition semantics become more demanding.

## Why a professional simulation engine becomes more structured

Real models often add several complications at once:

- many different transition mechanisms;
- multiple candidate transitions that may conflict;
- rules that should observe the same pre-change state;
- stochastic choices;
- a need for exact reproducibility;
- failure partway through a step;
- a need to know what changed and why;
- configuration that should remain fixed while state evolves;
- observers that should see committed results, not half-finished work.

Each of those requirements creates a design question.

## State is more than domain data

A useful mental model is:

```text
simulation state
    |
    +-- modeled domain state
    +-- simulation step index
    +-- RNG state
    +-- committed-step telemetry
    +-- reference to immutable context
```

The kernel packages those pieces in `SimulationState` because they need coherent
transaction semantics.

The domain payload itself remains opaque to the kernel. It might be a biological
`WorldState`, an information network, a counter, or something else entirely.

## Authoritative state versus working state

The most important distinction in transactional simulation is between:

- **authoritative/committed state** — the state the simulation currently owns as
  truth;
- **working state** — a copy being mutated while one candidate step executes.

Conceptually:

```text
                 authoritative State(t)
                         |
                      copy()
                         |
                         v
                  working State(t)
                         |
                 run complete step
                   /           \
              failure         success
                |                |
                v                v
             discard          return
                                 |
                                 v
                    authoritative State(t+1)
```

This is much easier to reason about than trying to undo arbitrary mutations after
a failure.

## Why the RNG belongs in the transaction

Suppose a working step draws three random numbers and then fails.

If the domain state rolls back but the committed RNG has already advanced, retrying
from the “same” model state produces a different stochastic trajectory.

That means the model state was not actually restored.

So the transaction must include both:

```text
modeled state
+
random-number-generator state
```

This is why `SimulationState.copy()` clones the RNG's complete internal state
rather than merely sharing the same generator object.

## One step can contain several stages

Many simulations need an ordered sequence of broad phases.

```text
step t
  |
  +-- stage 0
  +-- stage 1
  +-- stage 2
  |
  v
step t+1
```

Stages are **sequential with respect to one another**. Stage 1 receives the working
state after stage 0 has completed.

Within one stage, however, the engine deliberately provides stronger simultaneity
semantics.

## The order-dependence problem

Imagine two processes in the same conceptual phase:

```text
Process A: consume 3 units
Process B: consume 4 units
```

Suppose the resource starts at 5.

A naive loop might be:

```python
for process in processes:
    process.update(state)
```

Then the process listed first may succeed and the second may fail. Reversing the
Python tuple changes the modeled outcome.

Sometimes order really is part of the model. But when two mechanisms are meant to
make decisions from the same state snapshot, accidental list order is the wrong
source of causality.

The kernel's answer is **proposal simultaneity**.

## Proposal: describe what could happen without mutating

A process first proposes candidate transitions from the stage-start state:

```text
stage-start state
    |
    +--> Process A proposes candidate A
    |
    +--> Process B proposes candidate B
    |
    +--> Process C proposes candidate C
```

All three proposals see the same state because no application has happened yet.

This separates two questions:

1. **What transitions are candidates?**
2. **Which candidates are allowed to happen together?**

## Resolution: decide among competing candidates

A resolver receives the stage-start state and the complete proposal sequence.
Its job is selection, not domain mutation.

```text
proposals A, B, C, D
        |
        v
      resolver
        |
        v
accepted B, D
```

The resolver can encode resource capacity, exclusivity, priority, matching, or
another competition rule without forcing those decisions into each process.

A trivial resolver such as `AcceptAll` simply accepts every proposal.

## Why an event exists

An event is a value describing a transition candidate or prepared transition.

Events let the engine separate:

```text
thinking about a change
from
performing the change
```

That separation enables conflict resolution, deferred randomness, telemetry, and
stage simultaneity.

An event is not necessarily “something that already happened.” In this codebase,
the event value can move through several semantic states before application.

## Proposal, resolution, materialization, application

The canonical stage sequence is:

```text
PROPOSE ALL
    |
    v
RESOLVE
    |
    v
MATERIALIZE ALL ACCEPTED
    |
    v
APPLY ACCEPTED
```

Each phase answers a different question.

### Propose

> What transitions are plausible from the common stage-start state?

### Resolve

> Which proposed transitions are compatible, and in what order should accepted
> transitions later be prepared/applied?

### Materialize

> Now that this transition is known to be accepted, what deferred details should
> become concrete?

### Apply

> Mutate the working domain state according to the prepared event.

## Why materialization exists

Some transitions can be fully determined at proposal time. Others should wait
until acceptance.

Imagine a reproduction candidate that will choose a stochastic genetic
contributor only if the candidate survives conflict resolution.

If contributor selection happened during proposal, rejected candidates would
consume random numbers. Adding one doomed proposal could then change random
choices for later accepted events.

Materialization solves that:

```text
cheap/deterministic candidate description
           |
        resolve
           |
accepted? -- no --> no accepted-only RNG consumed
           |
          yes
           |
materialize stochastic/deferred consequence
```

## Why *all* accepted events materialize before any apply

Consider two accepted events in the same stage.

If the engine did this:

```text
materialize event A
apply A
materialize event B
apply B
```

then event B could materialize against state already changed by A.

That weakens the same-stage simultaneity model.

Instead:

```text
materialize A from stage state
materialize B from stage state
apply A
apply B
```

Both accepted events make deferred decisions from the same pre-application stage
state.

Application is still ordered. The resolver controls that accepted-event order.
The key promise is that **proposal and materialization do not accidentally observe
mutations from earlier accepted events in the same stage**.

## Mutation belongs to the process

The resolver decides which transitions survive. It does not own the meaning of
those transitions.

That gives a clean split:

```text
Process
    knows what its event means
    proposes it
    optionally materializes it
    applies it

Resolver
    knows how candidates compete
    selects/order accepted candidates
```

If the resolver also mutated domain state, conflict policy and domain behavior
would become entangled.

## Effects and telemetry

After a transition applies, two related kinds of information may be recorded.

### Applied-event telemetry

The kernel can describe that an event actually committed:

```text
process type
event type
event's step index
stage index
materialized event value
opaque captured effects
```

### Domain effects

Some domains expose an optional effect journal. For example, applying one event
might produce multiple domain consequences.

The kernel can capture those values without understanding them.

This is another boundary:

```text
kernel knows:
    “these opaque effects occurred during this application”

domain knows:
    what those effects mean
```

## Observation happens after commit

An observer should not participate in conflict resolution or mutate committed
state merely because it is measuring it.

Conceptually:

```text
complete transaction
      |
      v
commit new SimulationState
      |
      +--> telemetry observers
      |
      +--> domain-state observers
```

This gives observers an authoritative snapshot rather than half-finished stage
state.

## Configuration should not evolve accidentally

Many components need stable services or configuration while the domain state
changes.

That information belongs in immutable `SimulationContext` rather than being mixed
with the mutable domain payload.

Why share context across state copies?

Because if the context is immutable, transactional duplication is unnecessary:

```text
State(t) -----------+
                    |
                    +--> same immutable context
                    |
Working State(t) ---+
```

The mutable parts are copied; immutable configuration can safely be shared.

## Preflight versus execution

A simulation should reject static wiring errors before mutable runtime begins when
possible.

Examples:

```text
component requires capability X
configuration provides no X
```

or:

```text
configured observer does not satisfy observer contract
```

That is the role of generic preflight around `SimulationSpec`.

It is different from runtime facts such as:

```text
entity 17 no longer exists
candidate cannot currently afford an action
```

Those facts only exist because state evolves.

## A stripped-down pedagogical runtime

Ignoring telemetry, validation, context, and performance details, the kernel's
logic can be approximated by:

```python
class TinyStage:
    def coordinate(self, state):
        proposed = []
        for process in self.processes:
            proposed.extend(process.propose_events(state))

        accepted = self.resolver.resolve_events(state, proposed)

        prepared = []
        for event in accepted:
            process = self.process_for(type(event))
            if hasattr(process, "materialize_event"):
                event = process.materialize_event(state, event)
            prepared.append((process, event))

        for process, event in prepared:
            process.apply_event(state, event)


class TinyStepCoordinator:
    def coordinate(self, committed_state):
        working_state = committed_state.copy()
        for stage in self.stages:
            stage.coordinate(working_state)
        working_state.step_index += 1
        return working_state


class TinyEngine:
    def run(self, simulation):
        while not self.stopping_condition.should_stop(simulation.state):
            simulation.state = self.step_coordinator.coordinate(simulation.state)
```

The production kernel adds important validation, event dispatch, optional effect
capture, committed telemetry, observers, typed context, generic preflight, and
performance work. But if you lose the thread while reading production code, come
back to this skeleton.

## A useful mental model: the kernel is a transaction scheduler

The kernel does not know *why* an event matters.

It knows how to guarantee things like:

```text
all same-stage proposals share one starting snapshot
accepted-only deferred work happens after resolution
all accepted materialization precedes same-stage application
process owns mutation
RNG participates in rollback
only a completed step replaces authoritative state
committed transitions can be observed afterward
```

That is the essential job.

## Misconception checks

### “A stage is simultaneous, so applications happen simultaneously.”

No. Applications happen in resolver order. The simultaneity contract concerns the
state seen during proposal and accepted-event materialization.

### “The resolver performs the winning transition.”

No. The resolver selects accepted events. The owning process performs mutation.

### “Materialization is just another word for application.”

No. Materialization determines deferred details of an accepted event without
performing the event's domain mutation.

### “Rollback means the engine reverses mutations.”

No. The engine mutates a working copy and simply fails to replace authoritative
state if the transaction does not complete.

### “Randomness makes the engine nondeterministic.”

Not in the reproducibility sense. With the same initial state, configuration,
seed, and component ordering, simulation-owned RNG gives a reproducible stochastic
trajectory.

## Predict before continuing

Suppose stage state starts at `counter = 10` and has two materialized accepted
events. Each materializer records the counter value it observes; each application
subtracts one.

What should the observations be?

```text
A. [10, 9]
B. [10, 10]
C. [9, 8]
```

The kernel contract requires **B**. Both materializers run before either
application.

## You understand this chapter if you can…

- explain why direct sequential mutation can accidentally turn Python ordering
  into model semantics;
- distinguish proposal, resolution, materialization, and application;
- explain why rejected events should usually not consume accepted-only RNG;
- explain why all accepted events materialize before any same-stage application;
- distinguish authoritative state from working transactional state;
- explain why RNG state must roll back with domain state;
- explain why resolvers choose transitions but processes mutate the domain; and
- reduce the production kernel to the tiny conceptual runtime above without
  losing its essential semantics.

Next: [General Evolution](general_evolution.md).

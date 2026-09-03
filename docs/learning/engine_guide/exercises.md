# Exercises: Build Design Judgment, Not Just Recall

These exercises make you predict, compare, explain, test, and build. Write down
your reasoning before opening source code or running the debugger.

A strong answer usually explains:

```text
owning architectural layer
visible state at that phase
decision authority
mutation authority
RNG timing
protected invariant
```

For computational analysis, continue afterward to
[Complexity and Performance Exercises](complexity_exercises.md).

## Exercise 1 — Which layer owns it?

Classify each concept as primarily **[KERNEL]**, **[GENERAL EVOLUTION]**,
**[BIOLOGY]**, or **[COMPOSITION]**.

1. Every accepted stochastic event detail is determined before any same-stage
   application.
2. A genome can contain four homologous chromosome copies.
3. Transmissible components may be co-transmitted non-independently.
4. Run a preset for 500 steps and export allele frequencies.
5. A reproductive participant may invest energy without contributing genetic
   state.
6. A failed step must not advance the committed random stream.
7. Construct propagated state from three source states and a recipient.
8. Pair homologs before segregation into gametes.

### Self-check

```text
1 KERNEL
2 BIOLOGY
3 GENERAL EVOLUTION
4 COMPOSITION
5 BIOLOGY
6 KERNEL
7 GENERAL EVOLUTION
8 BIOLOGY
```

The important part is explaining why the neighboring layer should **not** own the
concept.

## Exercise 2 — Object identity in a transaction

Suppose:

```python
committed = simulation.state
working = committed.copy()
```

Predict identity/value relationships for:

```text
committed vs working
committed.domain_state vs working.domain_state
committed.context vs working.context
committed.rng vs working.rng
committed.rng.getstate() vs working.rng.getstate()
```

Expected architecture:

```text
SimulationState identity   different
Domain-state identity      different
Context identity           same
RNG object identity        different
Initial RNG state          same
```

Explain every row rather than memorizing it.

## Exercise 3 — Failed transaction

Initial committed state:

```text
value = 100
RNG state = R0
step_index = 8
```

A working step copies the state, subtracts 20, consumes two random draws, then a
later stage raises.

Predict the authoritative domain value, RNG state, and step index after the
exception.

Then answer:

> Where is the rollback code?

A strong answer explains why no explicit inverse-mutation procedure is required.

## Exercise 4 — Why immutable context?

Imagine a process mutates `SimulationContext` during a working transaction and a
later stage fails.

Because context is shared across state copies, what would leak into the committed
simulation? Use that failure mode to explain why context immutability is
architectural rather than stylistic.

## Exercise 5 — Same-stage visibility

Initial domain state:

```text
x = 10
```

Process A and Process B are in the same stage.

- A proposes “set x to 100”.
- B proposes an event whose recorded amount equals the current `x` it observes.
- Both are accepted in A-then-B application order.

Predict what B sees while proposing and the final `x` if B adds its recorded
amount.

### Self-check

```text
B proposes from x = 10
B records 10
A applies -> 100
B applies -> 110
```

Application order exists, but it does not retroactively alter proposal-time
visibility.

## Exercise 6 — Cross-stage visibility

Move B into the next stage. What value does it see while proposing now?

Explain why later-stage visibility of earlier-stage mutation does not violate
same-stage simultaneity.

## Exercise 7 — Materialize-all-before-apply

Initial `x = 10`. Two accepted same-stage events each materialize by recording the
current `x`. Applying each event subtracts one.

Predict:

```text
materialized observed values = ?
final x = ?
```

What alternative observed values would reveal accidental
materialize/apply interleaving?

## Exercise 8 — Resolver injection

A resolver receives `IncrementEvent` proposals but returns a `ForeignEvent` no
configured process owns.

What should the stage do? Why is “search for any process with a compatible method
signature” the wrong fallback?

## Exercise 9 — Candidate RNG or accepted-only RNG?

For each random choice, decide whether it naturally belongs during proposal,
materialization, observation, or another explicit phase. Explain why.

1. A stochastic choice determines whether a movement candidate exists at all.
2. A resolved reproductive event chooses genetic contributors.
3. An accepted offspring genome mutates.
4. An observer samples 1% of entities for a report.
5. A candidate's random intention changes which resource it claims during
   conflict resolution.

The guiding question is:

> Does this random value define candidate existence/competition, or is it a
> consequence that should exist only for accepted events?

## Exercise 10 — Rejected candidates and RNG

A process proposes 100 candidates. The resolver accepts one. Materialization draws
one random number per accepted event.

How many materialization draws occur?

Now suppose proposal generation also draws once for every candidate. How many
simulation-RNG draws have occurred before application?

Explain why this changes stochastic semantics, not merely runtime.

## Exercise 11 — Propagation without reproduction

A fleet of persistent robots copies route-planning heuristic bundles horizontally.
The robots never reproduce. Copied bundles sometimes vary; some bundles cause their
carriers to be encountered more often and therefore copied more often.

Identify:

```text
evolving entity
transmissible state
expression
propagation source
recipient
variation
entity production
selection
```

Does evolution require robot birth?

## Exercise 12 — Propagation versus production

Invent:

1. a system with propagation but no entity creation;
2. a system that creates entities after transmissible state has already been
   determined elsewhere.

Explain why one universal propagation+production interface would blur two
independent questions.

## Exercise 13 — Selection without a fitness field

Construct variants A and B with no stored scalar `fitness`. Give A an expressed
characteristic that causes more successful future propagation.

Write the causal chain:

```text
transmissible difference
    -> operative difference
    -> interaction/persistence/propagation difference
    -> differential future contribution
    -> changed variant frequency
```

Explain where selection appears in that chain.

## Exercise 14 — Do not collapse phenotype layers

Classify these as transmissible state, genetic expression result, developmental
realization, or current mutable physiological state:

```text
genome
expressed genetic body-size target
body size realized after nutrient-limited development
current stomach contents
current energy reserve
expressed trait value before environmental realization
```

What modeling errors become likely if all are stored in one mutable “phenotype”
dictionary?

## Exercise 15 — Four reproductive relationships

Name the current responsibility corresponding to each:

1. organisms whose simultaneous reproductive opportunities consume resolver
   capacity;
2. organisms whose committed energy makes the candidate affordable;
3. organisms whose genomes become inheritance source states;
4. organisms supplied as production context for newborn/placement policy.

Which one defines genetic pedigree parentage?

## Exercise 16 — Timing of reproductive selectors

Why is investor selection proposal-time while genetic-contributor and
production-source selection are materialization-time?

Give one stochastic or correctness problem caused by moving each decision to the
wrong phase.

## Exercise 17 — Future tetraploid inheritance

A future inheritance model needs explicit chromosome copy expectations, homolog
pairing, segregation, gamete copy counts, and crossover policy.

Where do those concepts belong? Would inheritance complexity alone justify adding
ploidy concepts to `SimulationState`, `StageCoordinator`, or generic
`PropagationModel`?

State what evidence would be needed before a frozen-kernel change were justified.

## Exercise 18 — Compare two stage algorithms

### Design A

```python
for process in processes:
    events = process.propose_events(state)
    for event in resolver.resolve_events(state, events):
        event = maybe_materialize(process, state, event)
        process.apply_event(state, event)
```

### Design B

```python
proposals = propose_from_all_processes(state)
accepted = resolver.resolve_events(state, proposals)
prepared = materialize_all(state, accepted)
apply_all(state, prepared)
```

Compare exact consequences for:

```text
cross-process conflict visibility
same-stage proposal state
materialization visibility
rejected-event RNG
ability to test invariants
```

Do not say “B is cleaner.” Explain the semantic differences.

## Exercise 19 — Resolver mutation review

Consider this API:

```python
def resolve_and_apply(state, proposed_events) -> None: ...
```

List at least four costs of merging selection and mutation in this engine.

Then identify a small one-off program where a combined function might be perfectly
reasonable. Architecture should respond to requirements rather than become dogma.

## Exercise 20 — Wrong-but-plausible independent RNG

A process creates `random.Random()` internally because it needs only one random
choice.

Review this design across:

```text
reproducibility
transaction rollback
checkpoint/resume
seed control
testing
hidden dependency
```

## Exercise 21 — Write tests from invariants

Without reading the focused stage tests first, write tests for:

```text
duplicate process proposal type rejected
unknown resolver event type rejected
all materialization before any application
all same-stage proposals from common start state
```

Then compare your tests with `tests/engine/test_stage_coordinator.py`.

What did the production tests make more precise than your mental model?

## Exercise 22 — Transaction failure test

Design a test that proves:

```text
working domain state mutates
working RNG advances
later stage raises
committed domain state remains unchanged
committed RNG remains unchanged
committed step_index remains unchanged
```

Assert observable semantics rather than private coordinator implementation fields.

## Exercise 23 — Observer purity

Design a test that would reveal an observer changing the simulation trajectory.

Which parts can the kernel enforce structurally, and which remain obligations of
observer implementations?

## Exercise 24 — Ten-minute cold source read

Open `src/evo_engine/engine/stage_coordinator.py`. Before reading private helpers in
detail, write down:

```text
public responsibility
semantic phases
mutation location
RNG-capable phase(s)
main invariants
support/optimization structures to postpone
```

Then compare with [Reading the Kernel Source](source_code_walkthrough.md).

## Exercise 25 — Explain code at two levels

For each, state both its Python-level operation and its architectural meaning:

```python
working_state = simulation_state.copy()
```

```python
resolved_events = self.resolver.resolve_events(...)
```

```python
materialized_event = dispatch.materialize_event(...)
```

```python
process.apply_event(simulation_state, event)
```

```python
simulation.state = self.step_coordinator.coordinate(...)
```

If the architecture explanation merely rephrases the syntax, try again.

# Build a pedagogical mini-kernel

This is the most valuable implementation exercise.

Build roughly 100–150 lines in a scratch file containing:

```text
TinyState
TinyEvent
TinyProcess
TinyResolver
TinyStage
TinyStepCoordinator
TinyEngine
```

Required semantics:

1. copy isolates domain state and clones RNG;
2. all same-stage processes propose before resolution/application;
3. resolver sees the complete proposal sequence;
4. optional materialization occurs only for accepted events;
5. all accepted events materialize before any apply;
6. step coordinator mutates a copy and returns completed state;
7. engine commits by replacing the authoritative state reference.

Do **not** initially implement telemetry, effect journals, dependency preflight,
optimized dispatch caches, or extensive validation.

Then compare the toy implementation with production and classify each extra
production mechanism as:

```text
semantic contract
validation
diagnostics/telemetry
typing
performance optimization
configuration/preflight
```

Ask what real problem each piece solves.

# Design a new evolutionary domain

Invent a nonbiological evolutionary system substantially different from the
information-network example.

Specify first:

```text
entities
transmissible state
expression
realization/context dependence
propagation source count
recipient semantics
variation
linkage, if any
persistence/departure
entity production, if any
competition
how selection emerges
```

Then design:

```text
domain_state
process/event types
resolver(s)
materialization responsibilities
application responsibilities
context services
observers
telemetry questions
stopping condition
```

Finally answer:

> Did the frozen kernel need to change?

A strong solution will normally compose existing kernel and general-evolution
contracts.

# Self-assessment

You are moving beyond API familiarity when you can:

```text
RECOGNIZE  identify the roles in source
EXPLAIN    state why each separation exists
PREDICT    predict state/RNG/phase behavior
DIAGNOSE   find an invariant violation in plausible code
DESIGN     place a new requirement in the correct layer yourself
```

Next, add the computational lens with
[Complexity and Performance Exercises](complexity_exercises.md), then attempt the
[Capstone Challenges](capstones.md).
# Exercises: Build Design Judgment, Not Just Recall

These exercises are designed to make you **predict, compare, explain, and build**.
Do not rush to the source code. Write down your reasoning first, then use tests,
the debugger, or the implementation to check it.

A good answer usually explains:

```text
which layer owns the concept
what state is visible at that phase
who has decision authority
who may mutate
when RNG may be consumed
which invariant is being protected
```

## How to use these exercises

For each problem:

1. **Predict** before running anything.
2. **Name the architecture concept** involved.
3. **Identify the relevant public contract.**
4. **Find a focused test** that is similar, if one exists.
5. Only then inspect or write implementation code.

The point is to practice the same workflow you will use when reviewing future
engine changes.

# Part I — Architecture classification

## Exercise 1 — Which layer owns it?

Classify each proposed concept as primarily **[KERNEL]**, **[GENERAL EVOLUTION]**,
**[BIOLOGY]**, or **[COMPOSITION]**.

1. “All accepted stochastic event details must be determined before any
   same-stage application.”
2. “A genome can contain four homologous copies of chromosome 2.”
3. “Transmissible components may be co-transmitted non-independently.”
4. “Run this preset for 500 steps and export allele frequencies.”
5. “A reproductive participant may invest energy without contributing genetic
   state.”
6. “A failed step must not advance the committed random stream.”
7. “Construct propagated state from three source states and a recipient.”
8. “Pair homologs before segregation into gametes.”

### Check your reasoning

The intended primary layers are:

```text
1. KERNEL
2. BIOLOGY
3. GENERAL EVOLUTION
4. COMPOSITION
5. BIOLOGY
6. KERNEL
7. GENERAL EVOLUTION
8. BIOLOGY
```

The important skill is explaining **why the neighboring layer should not own it**.

## Exercise 2 — Too generic or not generic enough?

Consider these proposed names:

```text
KernelGenomeState
GenericParent
UniversalFitness
StatePropagation
WorldState
TransmissibleStateCarrier
```

For each, decide whether the name belongs naturally at a generic boundary, a
biological boundary, or nowhere in the current architecture.

Then explain why “more generic sounding” does not automatically mean “better
abstraction.”

# Part II — State and transaction reasoning

## Exercise 3 — Object identity prediction

Suppose:

```python
committed = simulation.state
working = committed.copy()
```

Predict whether each pair should have the same identity (`is`) and the same value
(`==` or equivalent state):

```text
committed vs working
committed.domain_state vs working.domain_state
committed.context vs working.context
committed.rng vs working.rng
committed.rng.getstate() vs working.rng.getstate()
```

### Expected reasoning

```text
SimulationState identity          different
Domain-state identity             different
Context identity                  same
RNG object identity               different
Initial RNG internal state        same
```

Explain the architectural reason for every row.

## Exercise 4 — Failed transaction

Initial committed state:

```text
value = 100
RNG state = R0
step_index = 8
```

A working step:

1. copies the state;
2. stage 0 subtracts 20;
3. stage 0 consumes two RNG draws;
4. stage 1 raises an exception.

Predict the authoritative values after the exception.

Then answer:

> Where is the rollback code?

The best answer explains why there does not need to be an “undo 20 and rewind two
random draws” procedure.

## Exercise 5 — Context mutation thought experiment

Imagine `SimulationContext` were mutable and a process changed a configuration
service during a working transaction.

Because context is shared across copies, what would happen to the authoritative
simulation even if the transaction later failed?

Use that failure mode to explain why context immutability is structural rather
than stylistic.

# Part III — Stage semantics

## Exercise 6 — Same-stage visibility

Initial domain state:

```text
x = 10
```

Two processes are in the same stage.

- Process A proposes “set x to 100”.
- Process B proposes an event whose amount equals the current `x` it observes.

Both are accepted. Resolver order is A then B.

Predict:

1. What value does B observe while proposing?
2. If B's event simply adds its recorded amount, what value does B add during
   application?
3. What is the final `x` if A sets `x = 100`, then B adds its recorded amount?

### Answer

```text
B proposes from x = 10
B records amount = 10
A applies -> x = 100
B applies -> x = 110
```

The subtle point is that application order exists, but it does not retroactively
change proposal-time observations.

## Exercise 7 — Cross-stage visibility

Move Process B into the next stage.

Now what does B observe while proposing?

Explain why this is not a violation of simultaneity.

## Exercise 8 — Materialization visibility

Initial `x = 10`.
Two accepted same-stage events each materialize by storing the current `x`.
Application of each event subtracts one.

Predict:

```text
materialized observed values = ?
final x = ?
```

Then explain which alternative result would reveal an accidental
materialize/apply interleaving bug.

## Exercise 9 — Resolver injection

A resolver receives `IncrementEvent` proposals but returns a new `ForeignEvent`
that no configured process owns.

What should the stage do?

Why is “find any process with a compatible `apply_event` signature” the wrong
fallback?

# Part IV — Randomness and phase placement

## Exercise 10 — Proposal-time or materialization-time RNG?

Classify each random decision by the phase where it most naturally belongs.

1. A candidate process samples which direction an organism *intends* to move, and
   that intention itself determines conflict claims.
2. A reproductive candidate that has already won conflict chooses one of several
   eligible genetic contributors.
3. A proposal exists only with a stochastic probability that is itself part of
   the modeled proposal mechanism.
4. An accepted offspring genome undergoes mutation.
5. An observer randomly samples 1% of entities for a diagnostic report.

There is not always one universal answer. Explain the semantic consequence of
moving a draw earlier or later.

### Guiding principle

Ask:

> Does the random outcome define **candidate existence/competition**, or is it an
> **accepted-only consequence**?

Observer sampling is not a simulation decision and should not consume the
simulation's causal RNG unless that sampling itself is modeled state.

## Exercise 11 — Rejected candidates and RNG

A process proposes 100 candidate events. The resolver accepts exactly one.
Materialization draws one random number per accepted event.

How many materialization draws occur?

Now suppose proposal generation also draws one random number for every candidate.
How many total simulation RNG draws occur before application?

Explain why these are different semantics rather than merely different
performance costs.

# Part V — General evolution

## Exercise 12 — Identify the abstract evolutionary system

A fleet of autonomous robots shares route-planning heuristics. Each robot keeps
its identity. When robots meet, one may copy a heuristic bundle from another.
Copied bundles occasionally change. Some bundles cause robots to be encountered
more often and therefore copied more often.

Identify:

```text
evolving entity
transmissible state
expression
realization, if any
propagation
recipient
variation
entity production
selection
```

Does evolution require robots to reproduce?

## Exercise 13 — Propagation versus production

Design two systems:

1. propagation without entity production;
2. entity production where the production mechanism itself does not determine
   transmissible state.

For each, explain why combining `PropagationModel` and entity production into one
universal interface would make the model less clear.

## Exercise 14 — Linkage outside genetics

Invent a nonbiological transmissible state with at least five components where
nearby components should tend to remain associated during transmission.

Define conceptually:

```text
linkage groups
positions
regions with high breakage tendency
regions with low breakage tendency
```

Then map the design back to the generic linkage concepts without using chromosome
terminology in the generic description.

## Exercise 15 — Selection without `fitness`

Construct a tiny example with variants `A` and `B` where:

```text
A has no stored fitness value
B has no stored fitness value
```

but A nevertheless increases in frequency because of modeled interactions.

Write the causal chain from transmissible difference to differential future
contribution.

# Part VI — Biological specialization

## Exercise 16 — Do not collapse phenotype layers

For each quantity, classify it most naturally as:

```text
transmissible state
genetic expression result
developmental realization
current mutable physiological state
```

Candidates:

- genome sequence/copy collection;
- genetically encoded maximum body-size target;
- body size actually reached after nutrient-limited development;
- current stomach contents;
- current energy reserve;
- an expressed trait value before environmental realization.

Then explain what modeling error occurs if all six are placed in one mutable
“phenotype” dictionary.

## Exercise 17 — Four reproductive roles

For each relationship, name the current biological responsibility:

1. organisms whose simultaneous reproductive opportunities consume resolver
   capacity;
2. organisms whose committed energy makes the candidate affordable;
3. organisms whose genomes become inheritance source states;
4. organisms supplied as entity-production source context for placement/newborn
   policies.

Then answer:

> Which of these defines pedigree genetic parentage?

## Exercise 18 — Timing of reproductive selectors

Why is investor selection proposal-time while contributor and production-source
selection are materialization-time?

Give one concrete bug or stochastic-trajectory problem that would arise from
moving each decision to the wrong phase.

## Exercise 19 — Future ploidy feature

Suppose you want tetraploid inheritance.

Which proposed changes belong in biology?

```text
expected chromosome copy count
homolog pairing
segregation rule
gamete copy count
crossover policy
```

Would you modify `StageCoordinator`, `SimulationState`, or `PropagationModel`
merely because the inheritance algorithm became more complex?

Explain what evidence would be necessary before a kernel change became justified.

# Part VII — Design comparison

## Exercise 20 — Compare two stage designs

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

Compare them on:

```text
same-stage proposal semantics
cross-process conflict visibility
materialization visibility
rejected-event RNG
ability to test invariants
```

Do not say “B is more professional.” Explain the exact semantic differences.

## Exercise 21 — Resolver owns mutation?

A proposed resolver API is:

```python
def resolve_and_apply(state, proposed_events) -> None:
    ...
```

List at least four architectural costs of merging resolution and application this
way.

Then identify a situation where a combined function *would* be reasonable in a
small application with no need for this engine's extensibility. The goal is to
avoid dogma: designs are responses to requirements.

# Part VIII — Build a mini-kernel

This is the most valuable exercise in the chapter.

## Goal

Build a deliberately simplified kernel in a scratch file. Do **not** copy the
production source.

Keep it around 100–150 lines.

Implement:

```text
TinyState
TinyEvent protocol/shape
TinyProcess contract
TinyResolver
TinyStage
TinyStepCoordinator
TinyEngine
```

Required semantics:

1. `TinyState.copy()` isolates domain state and clones RNG.
2. Every process in a stage proposes before resolution/application.
3. Resolver sees the complete proposal sequence.
4. Optional materialization happens only for accepted events.
5. All accepted events materialize before any apply.
6. Step coordinator works on a copy and returns the completed state.
7. Engine commits by replacing the simulation's state reference.

Do **not** implement:

```text
telemetry
effect journal
dependency preflight
optimized dispatch caching
complex validation
MkDocs-quality docstrings
```

## Then compare with production

Open:

- `engine/stage_coordinator.py`
- `engine/step_coordinator.py`
- `engine/simulation_engine.py`

For every production feature absent from your mini-kernel, classify it:

```text
semantic contract
validation
diagnostics/telemetry
typing
performance optimization
configuration/preflight
```

Ask:

> What real problem does this extra production machinery solve?

This comparison is one of the best ways to stop seeing the real kernel as
“mysterious framework code.”

# Part IX — Write tests from invariants

## Exercise 22 — Test before implementation

Without reading `test_stage_coordinator.py`, write tests for:

```text
duplicate process event type rejected
unknown resolver event type rejected
all materialization before application
all proposals from same stage-start state
```

Then compare your test design with the repository's focused tests.

What did the existing tests encode more clearly than yours? What did yours reveal
about your mental model?

## Exercise 23 — Transaction failure test

Write a focused test that proves:

```text
working-state domain mutation occurs
working RNG advances
later stage raises
committed domain state is unchanged
committed RNG state is unchanged
step_index is unchanged
```

The test should assert externally visible semantics, not private implementation
fields of the coordinator.

## Exercise 24 — Observer purity test

Design a test that would fail if enabling an observer changed the simulation's
trajectory.

What exactly can the public contract enforce mechanically, and what remains a
behavioral convention that observer implementations must respect?

# Part X — Source-reading exercises

## Exercise 25 — Ten-minute cold read

Open `src/evo_engine/engine/stage_coordinator.py` with a ten-minute timer.

Before reading helpers in detail, write:

```text
public responsibility
semantic phases
main invariants
mutation location
RNG-capable phase(s)
performance/support structures you can postpone
```

Then compare with the
[Source Code Walkthrough](source_code_walkthrough.md).

## Exercise 26 — Explain one line at two levels

For each line, write both:

```text
Python-level meaning
architecture-level meaning
```

Lines:

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

If your architecture explanation is merely a paraphrase of the syntax, try again.

# Capstone — Design a new evolutionary domain

Invent a nonbiological evolutionary system substantially different from the
information-network example.

Before writing code, specify:

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
competition/conflict
how selection would emerge
```

Then design the kernel integration:

```text
domain_state
process(es)
event proposal types
resolver(s)
materialization responsibilities
application responsibilities
context services
observers
telemetry questions
stopping condition
```

Finally answer:

> Did you need to modify the kernel?

A strong design should normally demonstrate a new domain by composing the frozen
kernel and general-evolution contracts rather than adding domain vocabulary to
them.

# Self-assessment rubric

You are moving beyond API familiarity when you can do the following without
looking up class names first:

### Level 1 — Recognition

You can identify processes, stages, resolvers, events, state, and observers in
existing code.

### Level 2 — Prediction

You can predict what each phase sees and when mutation/RNG consumption occurs.

### Level 3 — Explanation

You can explain why the architecture separates responsibilities and what failure
mode each invariant prevents.

### Level 4 — Design

You can place a new modeled concept in the correct layer and compose existing
contracts before proposing new ones.

### Level 5 — Review

You can read a PR and identify semantic changes, accidental domain leakage,
transaction/RNG problems, hidden order dependence, or needless abstraction based
on repository contracts and tests.

The goal of this textbook is Level 4–5 understanding, not merely remembering how
to instantiate `SimulationEngine`.

Next: use the [Glossary](glossary.md) and [Cheat Sheet](cheatsheet.md) as ongoing
references.

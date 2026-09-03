# Reasoning About Proposed Changes

This chapter turns the architecture into a decision tool. The goal is not merely
to know where existing code lives; it is to decide where **new** behavior belongs,
which contract should change, and when the correct answer is "the lower layer does
not need to change at all."

## The core decision sequence

For any proposed feature, ask:

```text
1. What scientific/domain concept is this?
2. Which layer owns that meaning?
3. What mutable state does it require?
4. What immutable configuration/policy does it require?
5. What transition does it propose?
6. Can candidates conflict?
7. When should stochastic details become concrete?
8. Who owns mutation?
9. What should be observed after commit?
10. Is a lower-level contract genuinely unable to express this?
```

Only the last question can justify changing a lower abstraction merely because a
new feature is convenient.

## Example: pregnancy status

Proposal:

> Add `pregnancy_status` to `SimulationState`.

Walk the questions:

```text
What concept is it?
    biological lifecycle/reproductive state

Does the kernel need to interpret it?
    no

Can the opaque domain state represent it?
    yes

Does transactional execution already copy domain state?
    yes

Is a generic execution deficiency demonstrated?
    no

Correct direction:
    biological/world state above the kernel
```

The fact that every simulation step carries `SimulationState` does not make every
modeled fact a `SimulationState` field.

## Example: three or four genetic contributors

Proposal:

> Generalize the kernel because reproduction may have more than two parents.

Ask:

```text
Does the kernel know what a parent is?
    no

Does general propagation permit multiple source states?
    yes

Does biology distinguish reproductive participants from genetic contributors?
    yes

Where does source-count meaning belong?
    concrete biological inheritance/propagation policy
```

This is a specialization problem, not a kernel problem.

## Example: accepted-only stochastic investment

Suppose a new policy needs randomness to decide a consequence that matters only
for an already accepted reproductive event.

Ask:

```text
Should rejected proposals consume that randomness?
    no

Does the decision affect proposal existence/affordability?
    if no, defer it

Existing phase for accepted-only stochastic consequences?
    materialization
```

The architecture gives you a place to put the decision without inventing a new
execution phase.

## Example: random choice affects proposal affordability

Now suppose randomness determines which participant invests energy, and that
choice determines whether a proposal can exist at all.

The question changes:

```text
Does this fact determine whether the proposal exists?
    yes

Can it be deferred until after resolution without changing candidate validity?
    no
```

That may require a different biological policy design. It does **not** automatically
justify using hidden randomness during proposal formation. The design must preserve
the project's rule that rejected-candidate stochastic work should not silently
advance committed RNG unless those semantics are explicitly intended and safely
transactional.

This example illustrates why phase placement is a semantic decision, not merely a
code-organization choice.

## Example: territorial competition

Suppose organisms propose occupying territory cells.

Reasoning:

```text
modeled meaning:
    biological/ecological spatial competition

candidate transition:
    entity attempts to claim/move into territory

conflict:
    several candidates may target same territory

resolver responsibility:
    select compatible winners

process responsibility:
    apply selected territorial state changes

kernel change:
    probably none
```

The generic resolver/stage machinery already exists precisely to avoid embedding
territorial conflict semantics in the kernel.

## Example: a true kernel deficiency

A kernel change becomes plausible when you can state something like:

> A domain-neutral class of state transitions cannot be represented correctly
> because the current transaction/stage contract forces observable semantic
> corruption even when domain code follows all public contracts.

Then the analysis should identify:

```text
current invariant
required generic behavior
why existing extension points cannot express it
nonbiological reproducer
impact on determinism/transactions
new contract
migration/tests/ADR needs
```

"This biological feature would be easier if the kernel knew about it" is not that
evidence.

# The Architecture Worksheet

Use this template when planning a new milestone.

```text
Feature / change:
____________________________________________

Scientific/domain meaning:
____________________________________________

Correct owning layer:
____________________________________________

Mutable state required:
____________________________________________

Immutable configuration/policies required:
____________________________________________

Candidate event/proposal:
____________________________________________

Potential conflicts:
____________________________________________

When should randomness be consumed?
____________________________________________

Does accepted-only materialization help?
____________________________________________

Who owns domain mutation?
____________________________________________

Telemetry / observation needed:
____________________________________________

Important scaling variables:
____________________________________________

Expected time complexity / delegated costs:
____________________________________________

Memory size + lifetime considerations:
____________________________________________

Likely execution frequency / hot path?
____________________________________________

Invariants and focused tests:
____________________________________________

What would break in the naive design?
____________________________________________

Does a lower-level public contract genuinely need to change?
____________________________________________
```

## Use the worksheet to resist two opposite errors

### Error 1: push everything downward

```text
new biology
    -> add generic kernel flag
    -> add another kernel field
    -> add another special case
```

This destroys domain neutrality.

### Error 2: refuse all lower-level changes dogmatically

A frozen/maintenance-mode kernel is not sacred if a genuine generic correctness or
expressiveness defect is demonstrated. The burden is evidence, not prohibition.

# Change radius

Before changing a public contract, estimate the change surface.

A private helper may affect:

```text
one implementation file
focused tests
```

A small public Protocol can affect:

```text
all implementations
callers
composition roots
examples
static typing
runtime structural checks
architecture docs
tests
external users
```

Small line count does not imply small architectural impact.

When reviewing a change, ask:

```text
What depends on this contract?
What assumptions do tests encode?
What docs/ADRs explain its rationale?
Can the same goal be achieved by adding a policy implementation instead?
```

# Compare two designs

Suppose you need mating preference.

### Design A

Add fields and branches to `StageCoordinator`:

```text
if mating:
    rank by mate preference
```

### Design B

Keep stage orchestration generic and express preference through biological
selector/resolver policies.

Evaluate:

| Lens | Design A | Design B |
| --- | --- | --- |
| domain neutrality | poor | preserved |
| local convenience | high | moderate |
| extensibility | kernel grows branches | policies vary independently |
| testability | kernel/domain semantics intertwined | domain policy can be focused-tested |
| maintenance | generic path knows biology | ownership remains clear |
| likely choice | reject | prefer |

The point is not "always use a strategy object." The point is to preserve the
correct ownership boundary.

# Wrong-but-plausible review example

```python
class PredatorResolver:
    def resolve_events(self, simulation_state, proposed_events):
        winner = choose_winner(proposed_events)
        simulation_state.domain_state.remove_prey(winner.prey_id)
        return [winner]
```

It looks efficient: choose and mutate in one place.

But ask the review card:

```text
resolver authority:
    choose transitions

mutation authority:
    owning process

problem:
    the resolver now owns two responsibilities
```

Consequences include harder isolated testing, blurred stage semantics, and greater
risk that conflict resolution changes domain state before the apply phase.

# Architecture smells to watch during change design

```text
BIOLOGY LEAK
A generic API starts naming organism/genome/energy/mating concepts.

GOD PROCESS
One component proposes, resolves, applies, observes, and configures policy.

HIDDEN DEPENDENCY
Behavior reaches a global service/random generator rather than explicit state/context.

ORDER-DEPENDENT SCIENCE
The modeled outcome changes merely because same-stage process order changes.

DUPLICATED POLICY
Several packages independently encode the same scientific rule.

BOOLEAN EXPLOSION
A generic class gains flags for individual domain variants.

PREMATURE GENERALIZATION
A new abstraction has no current use or semantic pressure.

FAST-PATH EXPLOSION
Several optimized execution algorithms must preserve the same semantics.
```

# Healthy patterns

```text
small capability contract
explicit composition
policy object for a real axis of variation
immutable configuration
transactional state
resolver/process separation
accepted-only materialization
focused invariant test
measured optimization
```

Do not apply these mechanically. A one-function implementation can be healthier
than five layers of factories when there is no real axis of variation.

# The Code Review Worksheet

Use this when opening an unfamiliar file or reviewing a PR.

```text
Responsibility:
____________________________________________

Architectural layer:
____________________________________________

Inputs / outputs:
____________________________________________

What does it read?
____________________________________________

What may it mutate?
____________________________________________

What authority does it have?
____________________________________________

Core algorithm:
____________________________________________

Scaling variables:
____________________________________________

Time complexity / delegated costs:
____________________________________________

Allocations and memory lifetime:
____________________________________________

Execution frequency:
____________________________________________

Measured hotspot or theoretical concern?
____________________________________________

Invariants:
____________________________________________

Focused tests:
____________________________________________

Essential semantics versus support/optimization plumbing:
____________________________________________

Readability concerns:
____________________________________________

Maintainability / change radius:
____________________________________________

What would be dangerous to simplify?
____________________________________________

What could vary behind an existing contract?
____________________________________________
```

# PR review exercise

Imagine this diff:

```python
for proposed_event in proposed_events:
    materialized.append(process.materialize_event(state, proposed_event))

accepted = resolver.resolve_events(state, materialized)
```

Before looking at the answer, review it across these lenses:

```text
correctness
RNG semantics
stage simultaneity
wasted work
complexity
readability
maintainability
```

## Review

The diff is not a harmless refactor. It changes the public stage semantics:

- deferred consequences happen for rejected proposals;
- rejected candidates can consume randomness;
- expensive materialization work occurs before conflict resolution;
- resolver inputs are no longer the same kind of candidate transition;
- focused materialize-before-apply/accepted-only semantics would need to change.

The code can even look shorter while being architecturally worse.

# Levels of understanding

Use these five levels for major architecture concepts.

```text
1. RECOGNIZE
   I know the term or pattern.

2. EXPLAIN
   I can explain why it exists.

3. PREDICT
   I can predict behavior from the contract.

4. DIAGNOSE
   I can identify a violation or bug.

5. DESIGN
   I can decide whether/how a change belongs in the architecture.
```

For stage materialization:

```text
recognize:
    I know materialization is a stage phase.

explain:
    I know why it follows resolution.

predict:
    I know which state and RNG each materializer sees.

diagnose:
    I can spot eager rejected-candidate materialization.

design:
    I can decide whether new stochastic work belongs in proposal,
    materialization, application, or a domain policy outside the kernel.
```

The textbook's capstone target is level 5 for the core concepts.

# Capstone preview

The final exercises ask you to:

1. explain the engine without using its class names;
2. derive a minimal kernel from required semantics; and
3. review a deliberately flawed feature across architecture, correctness,
   complexity, memory, performance, readability, maintainability, and testability.

If you can do those independently, the architecture has become a reasoning tool
rather than a memorized diagram.

## You understand this chapter if you can...

- place a new scientific behavior in the correct layer without using package names
  as a crutch;
- distinguish a domain convenience request from a genuine generic deficiency;
- identify phase placement and RNG timing as semantic design decisions;
- estimate the change radius of a public-contract modification;
- use the architecture and code-review worksheets without needing a worked
  example; and
- reject both over-generalization and rigid refusal to evolve a lower contract
  when real generic evidence appears.

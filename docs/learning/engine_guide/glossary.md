# Glossary: Architecture, Kernel, and Evolution Vocabulary

This glossary uses the meanings intended by this project. It is a learning aid,
not a replacement for authoritative contracts.

When two terms are easy to confuse, they are grouped together deliberately.

# Architecture vocabulary

## Abstraction

A representation that preserves the structure relevant to a responsibility while
ignoring details that do not matter there.

Project example:

```text
PropagationModel
```

preserves source states, recipient, context, RNG, and resulting state without
requiring biological parents, genomes, or offspring.

## Abstract

Conceptual rather than tied to one concrete implementation.

Examples:

```text
propagation
variation
state transition
conflict resolution
```

Do not treat **abstract** as a synonym for **generic**.

## Generic

Code or contracts designed to operate across multiple concrete domains/types.

Examples:

```text
SimulationState
StageCoordinator
PropagationModel
```

## Concrete

A specific implementation or domain realization.

Examples:

```text
AcceptAll
Aging
Genome
TokenPropagation
```

## Generalization

Moving from a narrower/specific concept toward a broader one that captures shared
structure.

```text
biological inheritance -> propagation
```

is a conceptual generalization.

## Specialization

Giving a broad concept stronger domain-specific meaning or constraints.

```text
transmissible state -> genome
propagation -> biological inheritance
```

## Contract / interface

A promise about what a role can do, independent of one implementation.

In Python this project often expresses contracts with `Protocol`.

Example:

```text
Resolver
```

promises `resolve_events(...)`.

## Implementation

A concrete object/class that fulfills a contract.

```text
AcceptAll implements Resolver behavior.
```

## Policy

A replaceable decision rule.

Examples:

```text
resolver policy
contributor-selection policy
inheritance policy
placement policy
```

A policy is usually injected/composed rather than hard-coded into orchestration.

## Capability

A narrow behavior or property a caller needs from an object.

Example:

```text
TransmissibleStateCarrier
```

is a capability exposing `transmissible_state` without requiring one universal
“evolving entity” base interface.

## Adapter

A component that lets one contract/domain vocabulary satisfy or connect to
another without collapsing the two responsibilities.

Biological inheritance can adapt biological genome semantics to a general
propagation contract.

## Composition

Building behavior by assembling separate components.

Example:

```python
StageCoordinator(
    processes=(...),
    resolver=resolver,
)
```

rather than defining one subclass for every possible stage/domain combination.

## Inheritance (software)

A class relationship where one class derives from another. Distinguish this from
**biological inheritance**.

The engine generally favors explicit composition for configurable simulation
behavior.

## Separation of concerns

Keeping responsibilities that can vary independently in separate components or
layers.

Example:

```text
resolver selects
process mutates
observer measures
```

rather than one function doing all three.

## Single responsibility

The design idea that a component should have one coherent primary reason to
change.

It does not mean “every class must have one method.”

## Coupling

How much one component depends on details of another.

The domain-neutral kernel intentionally has low coupling to biology.

## Cohesion

How strongly the contents of a component belong to the same responsibility.

`StageCoordinator` is cohesive around one-stage transition orchestration.

## Layer

A conceptual level of responsibility.

The important project layers are:

```text
[KERNEL]
[GENERAL EVOLUTION]
[BIOLOGY]
[COMPOSITION]
```

## Boundary

A point where one layer deliberately stops knowing details owned by another.

`SimulationState.domain_state` is the most important kernel/domain boundary.

## Dependency

One component's need for another contract, object, service, or capability.

## Dependency direction

The intended direction in which layers may know about one another.

Broadly:

```text
generic foundations
 -> kernel
 -> general evolution
 -> biology
 -> processes/presets/interfaces
```

Lower/general layers must not import upward merely for domain convenience.

## Dependency injection

Supplying a component's dependency from outside rather than constructing or
secretly discovering it internally.

Example:

```python
StageCoordinator(..., resolver=AcceptAll())
```

## Dependency inversion

Designing higher-level behavior against a stable abstraction rather than one
specific low-level implementation, allowing implementations to be substituted.

## Orchestration

Code that coordinates other components and their order without owning their
domain-specific meaning.

Examples:

```text
SimulationEngine
SequentialStepCoordinator
StageCoordinator
```

## Side effect

An observable change beyond returning a value: mutating state, consuming RNG,
writing data, performing I/O, etc.

The engine does not eliminate side effects; it controls **where and when** modeled
side effects are allowed.

## Mutation

Changing an existing mutable object.

Process application mutates the working `domain_state`.

## Immutable

Not publicly changeable after construction.

`SimulationContext` is immutable so transaction snapshots can safely share it by
reference.

## Transaction

A unit of work whose result becomes authoritative only as a complete whole.

A simulation step is transactional:

```text
copy -> mutate working state -> success/return -> commit
```

Failure discards the working state.

## Commit

The point at which a completed transaction becomes authoritative.

In the run loop, the critical operation is the assignment of the step
coordinator's successful return value to `simulation.state`.

## Rollback

Restoring/retaining the previous authoritative state after failed work.

The kernel achieves rollback by isolation: failed work mutates a copy, so there is
usually nothing to “undo” on committed state.

## Determinism

For this engine, reproducibility under equal initial state, configuration, seed,
and component ordering.

A simulation may use randomness and still be deterministic in this sense.

## Preflight

Validation performed before mutable runtime begins, especially for static
component wiring/dependency facts.

`SimulationSpec` is the generic compilation/preflight boundary.

## Invariant

A property the architecture promises remains true.

Example:

> All accepted events in a stage materialize before any accepted event in that
> stage applies.

Tests often encode invariants directly.

## Syntactic sugar

A more convenient language syntax for an underlying operation.

## Construction/API sugar

An informal project use of “sugar” for a convenient construction surface that
normalizes into another representation.

Example: named context values passed to `Simulation(...)` are normalized into
`SimulationContext`; they do not become synthetic state attributes.

# Kernel vocabulary

## Simulation

The runtime object that owns the authoritative current `SimulationState`.

## SimulationState

The kernel-owned transactional envelope for one simulation snapshot.

Fields include:

```text
domain_state
context
step_index
rng
last_step_telemetry
```

## domain_state

The opaque mutable modeled-domain payload inside `SimulationState`.

The kernel requires callable `copy()` for transactional isolation but does not
interpret biological/ecological meaning.

## SimulationContext

Immutable configuration/service container shared across transactional snapshots.

## ContextKey[T]

A typed key pairing a context-service name with runtime value validation and a
static return type.

## SimulationEngine

The runtime orchestrator that:

```text
observes initial state
checks stopping condition
coordinates steps
commits returned state
observes telemetry/state
```

It does **not** own authoritative state itself.

## StepCoordinator

Contract for coordinating one complete simulation update and returning a completed
`SimulationState`.

## SequentialStepCoordinator

The standard step coordinator. It copies the input state, runs configured stages
sequentially, increments the step index, attaches step telemetry, and returns the
completed working state.

## StageCoordinator

Coordinates one stage with the public semantic order:

```text
propose all
-> resolve
-> materialize all accepted
-> apply accepted
```

## Stage

One ordered phase inside a step. Stages are sequential relative to one another.

Within a stage, all processes propose from the same stage-start state.

## SimulationEvent

The minimal event contract. An event exposes `step_index`.

Concrete events carry domain/process-specific transition data.

## Proposed event / proposal

A candidate transition produced by `Process.propose_events(...)`.

It describes what **could** happen and has not yet been accepted/applied.

## Resolved event

A proposal returned by the resolver as accepted, in the order chosen for later
preparation/application.

## Materialized event

An accepted transition whose deferred/stochastic details have been determined by
an optional `EventMaterializer` before any same-stage application begins.

It may be the same Python type as the proposal or a richer type.

## AppliedEvent

Immutable telemetry describing one successfully applied materialized event inside
a completed transaction.

Do not confuse `AppliedEvent` with the domain event object it contains.

## Process

The contract owning one proposed transition family and its domain mutation
semantics.

A process:

```text
declares event_type
proposes candidate events
optionally materializes accepted events
applies materialized events
```

## event_type

The concrete **proposal type** owned by a process. Proposal event types must be
unique within one `StageCoordinator`.

## EventMaterializer

Optional capability for converting an accepted/resolved event into a prepared
materialized event before stage application begins.

Use it for accepted-only deferred consequences such as stochastic outcomes.

## Resolver

Contract that receives stage-start state plus the complete proposal sequence and
returns accepted events/order.

A resolver selects transitions; it does not own domain mutation.

## AcceptAll

A simple resolver that accepts every proposed event in original order.

## StoppingCondition

Contract deciding whether the run should terminate from the current authoritative
`SimulationState`.

## MaxSteps

Simple stopping condition that stops when completed `step_index` reaches the
configured maximum.

## Observer

Reads committed domain state after/before run steps according to
`should_observe(...)`.

Observation is descriptive and should not participate in mutation/conflict
resolution.

## TelemetryObserver

Reads committed `StepTelemetry` rather than domain-state snapshots.

## Telemetry

Descriptive causal records of committed transition applications.

## StepTelemetry

Immutable group of `AppliedEvent` records for one completed step.

## Effect

An opaque domain-defined consequence optionally captured around a process
application via the domain effect journal.

The kernel records effects but does not interpret them.

## effect_count / effects_since

Optional structural domain-state journal capability used to capture effects caused
by one application.

## SimulationSpec

Frozen description of a complete domain-neutral simulation before mutable runtime
exists.

Compilation runs generic preflight and creates matching `Simulation` and
`SimulationEngine` objects.

## CompiledSimulation

Bundle containing:

```text
simulation
engine
dependency_report
```

after successful `SimulationSpec.compile()`.

## Dependency

A named generic capability that a configured component may require or provide.

## DependencyReport

Summary of required, provided, and missing dependencies, including requirement
provenance where available.

# General evolution vocabulary

## Evolving entity

A conceptual persistent unit whose state can affect persistence, interactions, or
contribution to future transmissible state.

It is not a mandatory universal marker interface.

## Transmissible state

Information that can be copied, combined, modified, or otherwise propagated to a
recipient or future state.

This is the canonical general-evolution term.

## TransmissibleStateCarrier

Small capability exposing a `.transmissible_state` property.

## Expression

Mapping transmissible state to expressed/operative characteristics.

## TransmissibleStateExpression

General contract:

```text
express(transmissible_state) -> expressed value
```

## Expressed state / operative characteristic

A characteristic derived from transmissible state and available to influence
modeled interactions/transition decisions.

## Realization

Context-dependent production of actual operative characteristics from transmitted
information plus environment, mutable state, history, development, or stochastic
influences.

## Propagation

Construction of transmissible state for a recipient from zero or more source
states, immutable context, and the simulation RNG.

## PropagationModel

General propagation contract:

```text
(source_states, recipient, context, rng) -> propagated state
```

## Source state

A transmissible-state value that contributes to a propagation outcome.

## Recipient

The entity or recipient descriptor receiving the propagated state. It is modeled
separately from source states.

## Variation

Change to transmissible information during or between propagation.

## VariationOperator

General contract:

```text
vary(value, rng) -> varied-or-unchanged value
```

## Linkage

Non-independent co-transmission relationship among transmissible components.

## Linkage component

One addressable component of transmissible state participating in linkage
structure.

## Linkage group

A group of components that may remain associated during transmission.

## Linkage position

An ordering/coordinate of a component within a linkage group.

## Linkage map

Model of local tendency for associations to be broken across positions/regions.

## Entity production

Construction of an entity from already-determined state/context.

It is deliberately separate from propagation.

## Admission

Adding a produced/existing entity to active domain membership.

## Departure

Removing an entity from active domain membership. Departure is broader than
biological death.

## Access

Domain-neutral ability to retrieve entities from modeled state.

## Reference

Domain-neutral derivation/use of stable entity references/identifiers.

## Persistence

Continued presence/contribution of an entity in the active system.

## Selection

The emergent pattern of differential future contribution when transmissible
variation influences persistence or propagation success.

Selection is not required to exist as an intrinsic scalar field.

## Fitness

A domain/analysis-specific measure or estimate of success, often inferred from
survival, lineage, or reproductive contribution.

Distinguish a **fitness measurement** from the general phenomenon of selection.

## Evolution

Change through time in the distribution or structure of transmissible information
in a population/system.

# Biological specialization vocabulary

## Organism

Biological evolving entity/domain object.

## Genome

Biological transmissible state.

## Genetic architecture

Biological expression model that maps genome information into genetic phenotype
traits/values.

## Genetic phenotype

Result of genetic expression before broader environmental/developmental
realization.

## Development / G×E

Biological context-dependent realization of genetic potential under environmental
and developmental influences.

## Inheritance (biology)

Biological specialization of general propagation, using selected source genomes
to produce offspring/recipient genome state.

## Mutation

Biological variation that changes genetic information.

## Recombination

Biological restructuring/co-transmission breakage among linked genetic components.

## Chromosome

Biological specialization of a linkage group.

## Locus position

Biological specialization of linkage position.

## Reproductive participant

An organism in the resolver-facing reproductive group used for mating/conflict
semantics.

## Reproductive investor

A selected participant whose committed energy investment contributes to proposal
affordability.

Investor selection occurs at proposal time in the current architecture and does
not receive the simulation RNG.

## Genetic contributor

A selected participant whose genome becomes a source state for biological
inheritance.

Contributor selection occurs during accepted-event materialization and may use
the simulation RNG.

Genetic contributors define genetic/pedigree parentage.

## Offspring-production source

A selected participant supplied as biological entity-production source context,
for example to placement/newborn-state policies.

Production-source selection occurs during materialization and may use simulation
RNG.

## ReproductiveGroup

Ordered, nonempty group of unique reproductive participants.

## Mating type

Immutable reproductive identity stored on an organism under the current mating
system infrastructure.

## Reproductive role

Contextual capability in a mating system, derived by policy and not necessarily
stored as permanent organism identity.

## Ploidy

Biological chromosome-copy count structure. The `Genome` container can already
represent arbitrary copy collections, while explicit copy-count/pairing/
segregation semantics remain biological policy concerns.

## Segregation

Biological rules determining how chromosome copies are distributed into
transmitted gamete/genetic state.

# Terminology families at a glance

## Event family

```text
proposal
 -> resolved event
 -> materialized event
 -> process application
 -> AppliedEvent telemetry
```

## State/configuration family

```text
Simulation
    owns authoritative SimulationState

SimulationState
    contains mutable transaction state + RNG + context reference

SimulationContext
    immutable shared services/configuration

SimulationSpec
    pre-runtime complete configuration description
```

## Evolution family

```text
transmissible state
 -> expression
 -> realization
 -> operative characteristic
 -> interaction/persistence/propagation
 -> changed transmissible-state distribution
```

## Reproduction family

```text
participants
    |-- investors
    |-- genetic contributors -> pedigree parentage
    `-- production sources
```

The three subsets may all equal the participant set under simple defaults, but the
architecture does not define them as the same concept.

## Quick disambiguation questions

If you are unsure which term to use, ask:

```text
Is this about execution mechanics?             -> kernel vocabulary
Is this about transmissible information?       -> general-evolution vocabulary
Is this specifically genetics/organisms?       -> biological vocabulary
Is this deciding among alternatives?           -> policy/resolver/selector
Is this mutating modeled state?                 -> process application
Is this describing what committed?             -> telemetry
Is this determining state for a recipient?      -> propagation
Is this constructing a new entity?              -> production
Is this inserting/removing domain membership?   -> admission/departure
```

See the [Cheat Sheet](cheatsheet.md) for a more compact one-page-style reference.

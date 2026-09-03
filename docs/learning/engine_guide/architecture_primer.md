# Software Architecture Primer for This Engine

This chapter teaches the software-design ideas that make the Evolution Simulation
Engine readable. It assumes you already understand ordinary Python objects,
packages, type annotations, and the basic purpose of interfaces/`Protocol`.

The goal is not to memorize software-engineering vocabulary. It is to learn a
small set of questions that let you recognize **why code is shaped the way it is**.

## Where you are in the architecture

```text
YOU ARE HERE
    |
    v
software-design ideas
    |
    v
simulation mechanics
    |
    v
general evolution
    |
    v
biology
```

Later chapters will reuse these ideas repeatedly.

## Syntax, semantics, and sugar

**Syntax** is how a program is written. **Semantics** is what the program means or
does.

For example:

```python
x += 1
```

and the simpler mental expansion

```python
x = x + 1
```

express almost the same intent. The compact spelling is convenient syntax.

### Literal syntactic sugar

In programming-language discussions, **syntactic sugar** usually means a nicer
surface syntax for something that could be expressed more primitively.

A decorator is a useful example:

```python
@decorate
class Example:
    ...
```

is conceptually similar to:

```python
class Example:
    ...

Example = decorate(Example)
```

The syntax changes; the underlying conceptual operation is still “pass this
class through a decorator.”

### Construction or API sugar

The repository sometimes uses **sugar** more informally to mean a convenience API.
For example, `Simulation` and `SimulationState` can accept named context values at
construction time:

```python
simulation = Simulation(
    initial_domain_state=world,
    genetic_architecture=architecture,
)
```

That does **not** mean the kernel dynamically creates
`simulation.genetic_architecture`. The convenience keyword is normalized into an
immutable `SimulationContext` and retrieved from there.

So when the code says “construction sugar,” read:

> A convenient spelling for constructing the real underlying representation.

This distinction matters because convenient syntax must not trick you into the
wrong ownership model.

## Abstraction: preserve what matters, discard what does not

An **abstraction** is not merely something vague or high level. A good abstraction
keeps the structure that matters for a responsibility and intentionally ignores
details that do not.

Imagine two systems.

Biological inheritance may involve:

```text
organisms
parental roles
genomes
gamete formation
recombination
offspring
```

Horizontal cultural transmission may involve:

```text
speakers
listeners
ideas
copying
modification
```

A general state-propagation component may not need to know any of those nouns. It
may only need:

```text
zero or more source states
recipient
immutable context
RNG
    |
    v
resulting propagated state
```

That preserved shape is the useful abstraction.

The repository's `PropagationModel` is deliberately written at that level. Biology
then gives the general slots stronger meanings such as contributor genomes and
inheritance.

### Abstraction is responsibility-relative

There is no single “most abstract” description that is automatically best.

For a renderer, an organism might be a drawable shape.
For a pedigree recorder, it might be a lineage participant.
For inheritance, it might be a carrier of a genome.
For the kernel, it is not an organism at all: it is hidden inside opaque
`domain_state`.

A useful question is therefore:

> **What does this component need to know to perform its own responsibility?**

Everything else is a candidate to remain behind a boundary.

## Abstract, generic, concrete, and specialized

These words are related but not identical.

### Abstract

An **abstract concept** captures a meaningful idea independent of one particular
implementation.

Examples in this project:

```text
state transition
transmissible state
propagation
variation
conflict resolution
```

### Generic

**Generic code** is implementation written to operate across multiple concrete
cases.

Examples:

```text
SimulationState
StageCoordinator
PropagationModel contract
```

An abstraction is mainly a modeling/design idea. Generic code is often an
implementation of an abstraction.

### Concrete

A **concrete implementation** commits to specific behavior or domain meaning.

Examples:

```text
Aging
Genome
WorldState
AcceptAll
```

### Specialization

A **specialization** gives a general concept stronger domain-specific meaning.

```text
transmissible state
    -> genome

propagation
    -> biological inheritance

entity production
    -> biological offspring production
```

A specialization should use the richer vocabulary of its domain. We do not rename
`Genome` to something vague merely because it participates in a generic contract.

## Contract versus implementation

A **contract** says what a role promises.
An **implementation** says how one concrete object fulfills that promise.

For a kernel process, the contract is roughly:

```text
own one proposal event type
propose zero or more candidate transitions
apply events belonging to the process
optionally materialize accepted events
```

`Aging`, `Movement`, and a nonbiological token-propagation process can all fulfill
that same role while doing completely different domain work.

### Interface versus policy

An **interface/contract** defines the shape of a role.
A **policy** is an interchangeable choice about what decision should be made.

For example:

```text
Resolver          -> contract/role
AcceptAll         -> one concrete policy
preference order  -> another policy
```

This distinction lets orchestration remain stable while decision rules vary.

## Capability-oriented design

A **capability** is a small behavior an object can provide without forcing it into
a giant inheritance hierarchy.

The general evolution layer no longer requires every evolving thing to implement
one enormous `EvolutionaryEntity` interface. If an algorithm only needs
transmissible state, it asks for the narrower capability:

```text
TransmissibleStateCarrier
    .transmissible_state
```

This is useful because “evolving entity” is a conceptual category, while different
algorithms need different operational capabilities.

A reading question to develop:

> Why does this caller need this Protocol? What is the *smallest capability* it is
> trying to use?

## Composition versus inheritance

**Inheritance** says one class derives behavior/identity from another class.
**Composition** assembles behavior by holding or receiving separate components.

The engine strongly favors composition for simulation behavior.

A stage is assembled from processes and a resolver:

```python
StageCoordinator(
    processes=(process_a, process_b),
    resolver=resolver,
)
```

The stage is not a subclass of `AgingStage`, `PredationStage`, or
`ReproductionStage`. The domain composes those behaviors from smaller objects.

Why prefer composition here?

- policies can be replaced independently;
- responsibilities stay smaller;
- tests can isolate one component;
- new biology does not require redesigning an inheritance tree;
- the same orchestration can host nonbiological behavior.

This does not mean inheritance is always bad. It means the architecture should
not use inheritance merely to create a taxonomy when explicit composition better
matches how responsibilities vary.

## Separation of concerns and single responsibility

**Separation of concerns** means different kinds of decisions should not be mixed
into one component when they can evolve independently.

A naive reproduction function might:

```text
find partners
choose who wins conflicts
choose who pays energy
choose genetic contributors
perform inheritance
create offspring
choose placement
mutate the world
record statistics
```

That may be concise initially, but every future mating system, genetics model, or
placement rule must modify the same object.

The current architecture instead separates questions such as:

```text
who participates?
who invests?
which participant genomes contribute?
how is transmissible state propagated?
which participants provide production context?
how is an entity produced?
where is it admitted?
what telemetry/observation records the result?
```

The point is not “more classes are always better.” The point is that **independent
reasons to change deserve independent responsibilities** when the separation
clarifies the model.

## Coupling and cohesion

**Coupling** describes how much one component depends on details of another.
**Cohesion** describes how strongly the contents of one component belong to the
same responsibility.

Good architecture generally aims for:

```text
low unnecessary coupling
high responsibility cohesion
```

The domain-neutral kernel is a strong example. It does not import organisms,
genomes, reproduction, or ecology. That reduces coupling between execution
mechanics and modeled meaning.

Meanwhile, `StageCoordinator` is cohesive around one responsibility: coordinating
proposal, resolution, materialization, application, and telemetry for one stage.

## Layers and boundaries

A **layer** groups responsibilities at a similar conceptual level.
A **boundary** is where one layer deliberately stops knowing details owned by
another.

For this project:

```text
[KERNEL]
execution mechanics
    |
    | boundary: domain_state is opaque
    v
[GENERAL EVOLUTION]
transmissible information and evolutionary semantics
    |
    v
[BIOLOGY]
genomes, organisms, inheritance, development, ecology
```

The expression

```python
simulation_state.domain_state
```

is therefore more than a field access. It marks an important boundary.

Inside generic kernel code, the payload is opaque.
Once biological domain code deliberately unwraps it into `WorldState`, normal
biological names such as `world`, `organism`, and `energy` are appropriate.

### Boundary test

Ask:

> Could the lower layer still run if this domain were replaced with a completely
> different one?

The repository contains an executable nonbiological evolution example precisely
because this is stronger evidence than merely claiming the boundary is generic.

## Dependency direction

A **dependency** exists when one component needs another component's contract or
implementation.

The architectural direction is broadly:

```text
generic foundations
       |
       v
simulation kernel
       |
       v
general evolution
       |
       v
biology
       |
       v
processes / presets / experiments
```

Higher/domain-rich layers may depend on lower/general layers. Lower layers should
not reach upward to domain-specific implementations.

This prevents a biological convenience from silently becoming a generic kernel
assumption.

### Dependency inversion

**Dependency inversion** means high-level policy does not have to depend directly
on one low-level concrete implementation. Both can meet a stable abstraction.

In practical project terms, a process can depend on a general policy contract and
receive a concrete implementation through composition rather than constructing
that implementation internally.

This creates replaceable decision points without making orchestration know every
possible domain rule.

### Dependency injection

**Dependency injection** is the act of supplying a dependency from outside rather
than having a component secretly construct or discover it.

For example:

```python
StageCoordinator(
    processes=(...),
    resolver=AcceptAll(),
)
```

The resolver is injected explicitly.

`SimulationContext` provides another form of explicit dependency access for
immutable configuration/services. A domain package defines the meaning of a
context service; the kernel merely carries the context.

Dependency injection is useful because ownership and configuration become visible
at construction time.

## Orchestration versus domain logic

**Orchestration** determines which components run and in what sequence without
owning the domain meaning of their work.

Examples:

```text
SimulationEngine
    orchestrates run / stop / observe

SequentialStepCoordinator
    orchestrates ordered stages in one transaction

StageCoordinator
    orchestrates propose / resolve / materialize / apply
```

A process, by contrast, owns domain-specific transition meaning and mutation.

This is a powerful source-reading distinction:

> If a method mostly calls other components in a meaningful order, it may be
> orchestration code. Read it for sequencing and invariants, not hidden biology.

## Policy objects and adapters

A **policy object** encapsulates a replaceable decision rule.

Examples include:

- resolver policies;
- contributor-selection policies;
- inheritance policies;
- placement policies.

An **adapter** translates between contracts or vocabularies while preserving the
underlying responsibility.

For example, biological inheritance can adapt biological genome semantics to the
general `PropagationModel` shape without forcing the general layer to learn about
chromosomes or parents.

Use adapters when two layers should cooperate but should not collapse into one.

## State versus configuration/context

This distinction is foundational.

### Mutable state

**State** is information that changes as the simulation evolves.

Examples:

```text
organism age
energy
positions
current transmissible token
population membership
simulation step index
RNG state
```

### Configuration/context

**Configuration/context** is stable information or a stable service used while
state changes.

Examples can include:

```text
genetic architecture
model policies
immutable lookup services
fixed parameters
```

The kernel carries immutable configuration through `SimulationContext` and
transactional evolving information through `SimulationState`.

A common design smell is hiding evolving state inside “configuration” or mutating
shared configuration during a run. That breaks the very distinction that makes
transactional reasoning manageable.

## Mutability and side effects

A **side effect** is an observable change outside a function's returned value:
mutating an object, consuming RNG state, writing telemetry storage, performing
I/O, and so on.

Side effects are not inherently bad. A simulation must eventually mutate modeled
state. The architectural question is:

> **Where is mutation allowed, and at what phase?**

The kernel deliberately constrains this:

```text
proposal       -> read candidate state
resolution     -> choose transitions, no domain mutation
materialize    -> determine accepted deferred consequences
application    -> process owns domain mutation
observation    -> descriptive, no committed-state mutation
```

Making side effects phase-specific is one of the main reasons the runtime can be
reasoned about.

## Transactions, commit, and rollback

A **transaction** is a unit of work that either becomes authoritative as a whole
or is discarded.

The kernel's step transaction is conceptually:

```text
committed State(t)
      |
      v
copy domain state + clone RNG
      |
      v
working State(t)
      |
      v
run all stages
      |
      +---- failure ----> discard working state
      |
      v
return completed state
      |
      v
replace simulation.state
      |
      v
committed State(t+1)
```

There is no magical “undo every mutation” routine. Rollback is achieved by never
mutating the authoritative input in the first place.

This is why `SimulationState.copy()` is architecturally important rather than just
a convenience method.

## Determinism and RNG ownership

A stochastic simulation can still be **deterministic with respect to its seed and
inputs**.

For reproducibility, random decisions cannot come from invisible generators
scattered across components. The simulation RNG therefore belongs to
`SimulationState`.

When the state is copied transactionally, the complete RNG state is cloned too.
If the working transaction fails, random draws made there disappear with it.

The useful invariant is:

```text
same initial state
+ same immutable configuration
+ same seed
+ same component ordering
= same kernel trajectory
```

This is why “just create `random.Random()` inside the process” is not a harmless
local implementation choice.

## Ownership, responsibility, and authority are different

These words are easy to use interchangeably, but separating them makes complex
code much easier to read.

Ask several questions:

```text
Who contains/owns the object?
Who is allowed to mutate it?
Who decides whether a transition occurs?
Who decides what the transition means?
Who decides when the phase executes?
Who owns randomness?
Who observes the result?
```

In the kernel:

| Question | Primary answer |
| --- | --- |
| Who owns authoritative run state? | `Simulation` |
| Who owns modeled-state meaning? | the domain |
| Who owns the simulation RNG? | `SimulationState` |
| Who owns one transition's domain meaning/mutation? | its `Process` |
| Who decides which competing proposals survive? | `Resolver` |
| Who orders stage phases? | `StageCoordinator` |
| Who orders stages in a transaction? | `SequentialStepCoordinator` |
| Who decides when the run stops? | `StoppingCondition` |
| Who reads committed domain state? | `Observer` |
| Who reads committed event history? | telemetry observers |

Notice that `SimulationEngine` orchestrates execution but does **not** own the
simulation's authoritative state.

## Telemetry versus observation

Both are descriptive, but they answer different questions.

**Observation** asks:

> What does committed domain state look like now?

**Telemetry** asks:

> Which materialized transitions actually committed, through which process/stage,
> and what opaque domain effects were captured?

A population recorder may tell you that abundance changed. Event telemetry can
help tell you which committed events caused that change.

Neither belongs in conflict resolution, and neither should mutate committed
simulation state as a side effect of observing it.

## Preflight versus runtime validation

Some facts can be checked before a simulation starts:

```text
Does this component graph provide required capabilities?
Does this object satisfy the expected structural contract?
```

Those belong at configuration/compilation boundaries such as `SimulationSpec`.

Other facts only exist because state evolves:

```text
Is this particular entity still present?
Can this particular candidate afford an action now?
```

Those are runtime facts.

The architecture tries not to repeatedly rediscover static configuration errors in
the middle of a run.

## A compact reading checklist

When you open an unfamiliar file, ask:

1. Which layer am I in: kernel, general evolution, biology, or composition?
2. Is this file defining a contract, a policy, domain state, or orchestration?
3. What responsibility does it own?
4. What details does it deliberately *not* know?
5. Which objects are injected into it?
6. What may it mutate?
7. Can it consume simulation RNG?
8. Which invariant would break if I moved this responsibility elsewhere?
9. Is this line essential semantics, validation, diagnostics, or optimization?
10. Which focused test demonstrates the intended behavior?

## Misconception check

**“More abstract” does not mean “better.”**

The kernel should not learn about genomes because genomes are irrelevant to its
responsibility. Biology *should* use the word genome because that specificity is
valuable once the domain boundary has been crossed.

The goal is not maximum genericity. The goal is **the right knowledge at the right
layer**.

## You understand this chapter if you can…

- explain abstraction as preserving responsibility-relevant structure rather than
  merely “making things generic”;
- distinguish contract, policy, implementation, adapter, and orchestration using
  examples from this repository;
- explain why `simulation_state.domain_state` is an architectural boundary;
- distinguish state from immutable configuration/context;
- explain how a transaction can roll back without running an undo procedure;
- distinguish ownership, mutation rights, decision authority, and observation;
- look at `resolver.resolve_events(...)` and say “selection among candidates, not
  domain mutation”; and
- explain why explicit composition/dependency injection makes domain policies
  replaceable without changing kernel orchestration.

Next: [Simulation Fundamentals](simulation_fundamentals.md).

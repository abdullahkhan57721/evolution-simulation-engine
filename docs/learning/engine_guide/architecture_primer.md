# Software Architecture Primer

This chapter gives you the software-design ideas needed to understand why the
Evolution Simulation Engine is arranged the way it is. It assumes you already
know ordinary Python objects, modules, type annotations, and the basic idea of an
interface.

> **Mental model:** architecture is mostly about deciding **where knowledge and
> responsibility are allowed to live** so future change does not force unrelated
> parts of the system to change together.

## Why architecture matters here

A tiny biological simulation could be written as one loop:

```python
for organism in organisms:
    organism.age += 1
    organism.energy -= 5
```

That may be perfectly reasonable for a small one-off model. Our engine has harder
requirements:

```text
many modeled mechanisms
competing simultaneous transitions
stochastic outcomes
rollback on failure
reproducibility
multiple evolutionary domains
rich biological specialization
observation and causal history
future extension without kernel redesign
```

Architecture is the response to those pressures.

# Family 1 — Modeling abstractions

## Abstraction

An **abstraction** keeps the structure that matters for a problem while hiding
irrelevant detail.

A good abstraction is not merely “more generic.”

For the kernel, this:

```text
copyable mutable modeled state
```

is useful.

This would not be:

```text
organism world containing genomes and energy
```

because those details are irrelevant to generic transactional execution.

### Abstraction ladder

```text
state transition
    -> transmissible-state propagation
        -> biological inheritance
            -> Mendelian sexual inheritance
                -> one configured model
```

Each level adds meaning. Lower levels should not pretend to know details belonging
to higher ones.

## Contract versus implementation

A **contract** says what behavior a collaborator must provide. An
**implementation** supplies one concrete way to provide it.

For example, conceptually:

```python
class Resolver(Protocol):
    def resolve_events(self, simulation_state, proposed_events): ...
```

The kernel needs a policy that selects compatible events. It does not need every
resolver to inherit from one base class or use one algorithm.

That distinction enables:

```text
StageCoordinator
    depends on resolver contract
        |
        +-- AcceptAll
        +-- preference/capacity policy
        `-- future conflict policy
```

## Generalization and specialization

**Generalization** asks what several concrete systems genuinely share.
**Specialization** adds stronger domain meaning.

In this project:

```text
propagation             general evolution
    |
    v
biological inheritance  biology
```

Inheritance is not a synonym for generic propagation. It is a biologically
stronger specialization.

Likewise:

```text
transmissible state -> genome
entity             -> organism
linkage group      -> chromosome
```

The general layer remains useful to nonbiological systems.

## Generic, abstract, and concrete

These words overlap but answer different questions.

- **abstract**: focuses on essential conceptual structure;
- **generic**: code/contract can operate across multiple concrete types/domains;
- **concrete**: a specific implementation or domain object.

Examples:

```text
abstract idea:     competing state transitions

generic contract: Resolver

concrete policy:   AcceptAll

concrete biology:  Organism / Genome
```

Do not judge an abstraction by how abstract its name sounds. Judge whether it
captures a real shared responsibility.

# Family 2 — Composition and dependency design

## Composition

**Composition** builds a larger behavior from smaller collaborators.

A configured stage is composed from:

```text
StageCoordinator
    + Process(es)
    + Resolver
```

The coordinator does not need subclasses for every ecological stage. Different
process/policy objects can be assembled instead.

This is one reason the project favors composition over deep inheritance
hierarchies.

## Dependency

A dependency exists when one component needs another component or contract to do
its job.

Example:

```text
StageCoordinator -> Resolver
```

The arrow means the coordinator needs resolver behavior.

Architecture becomes easier to reason about when dependency direction follows the
conceptual layers:

```text
kernel
  ^
  |
general evolution
  ^
  |
biology
```

Higher/domain-specific layers may use lower/generic layers. Lower layers must not
reach upward and import biological meaning.

## Dependency injection

**Dependency injection** means a component receives a dependency rather than
constructing or locating it secretly.

Compare:

```python
stage = StageCoordinator(processes=processes, resolver=resolver)
```

with a hidden design where `StageCoordinator` internally decides which resolver to
construct.

Injected dependencies make variation, testing, and ownership explicit.

## Dependency inversion

The useful mental model is:

> High-level orchestration should depend on the **capability it needs**, not on one
> low-level concrete implementation.

So:

```text
StageCoordinator -> Resolver contract <- AcceptAll
```

rather than:

```text
StageCoordinator -> AcceptAll specifically
```

This is why a small structural contract can be architecturally important even
when the Python syntax is simple.

# Family 3 — Responsibility design

## Separation of concerns

Different kinds of decisions should live in different places when they vary for
different reasons.

A stage separates:

```text
Process
    what candidate transition means
    how selected transition mutates domain

Resolver
    which candidates survive conflict

StageCoordinator
    when proposal/resolution/materialization/application happen
```

If one object owns all three, changing competition policy can accidentally change
domain mutation or execution semantics.

## Cohesion

A component is **cohesive** when its responsibilities belong together.

`SequentialStepCoordinator` is cohesive around one idea:

> Execute one complete transactional step across ordered stages.

It does not also decide biological inheritance or stopping rules.

## Coupling

**Coupling** measures how much one component needs to know about another.

The kernel is deliberately weakly coupled to modeled domains:

```text
kernel knows:
    domain_state is copyable

kernel does not know:
    organisms
    genomes
    energy
    mating
    coordinates
```

Weak coupling is valuable when the hidden details need to evolve independently.

## Orchestration versus domain behavior

**Orchestration** determines who runs, when, and in what sequence.

**Domain behavior** determines what a transition means.

```text
SequentialStepCoordinator / StageCoordinator
    orchestration

Aging / Movement / Reproduction / other Process
    domain behavior
```

This distinction is one of the most useful ways to read the repository.

## Policy object

A **policy object** packages a replaceable decision rule.

Examples include:

```text
resolver policy
stopping condition
inheritance model
variation operator
mating/group selection policy
```

Use a policy abstraction when there is a real axis of variation. Do not invent
layers merely because “strategy pattern” sounds sophisticated.

## Capability-oriented design

A **capability** contract asks whether an object can provide one small behavior.

Examples in the broader engine include carrying transmissible state or providing
optional event materialization.

This avoids forcing every evolutionary object into one giant inheritance
hierarchy.

## Adapter

An adapter lets one domain-specific concept satisfy a more general contract while
retaining stronger domain vocabulary.

Biological inheritance can satisfy general propagation semantics while the biology
layer still speaks naturally about genomes and inheritance.

# Family 4 — State and execution

## State versus configuration

This distinction is foundational.

| State | Configuration/context |
| --- | --- |
| changes as simulation runs | stable for a run |
| transactionally isolated | safely shared when immutable |
| modeled current facts | policies/services/parameters |
| belongs in `domain_state` or kernel snapshot values | belongs in `SimulationContext` |

Examples:

```text
current organism energy      state
current world membership     state
step index                   state
RNG internal state           state

genetic architecture policy configuration/service
fixed domain model           configuration/service
```

Putting evolving facts in immutable context breaks the model. Putting fixed
configuration into mutable transaction state creates needless copying and hidden
mutation risk.

## Mutation and side effects

A **side effect** is an externally visible change caused by executing code.

In this kernel, process application is deliberately the domain-mutation phase:

```text
proposal        reads, creates candidates
resolution      chooses
materialization determines deferred accepted details
application     mutates working domain state
```

Separating these phases makes state visibility predictable.

## Transaction

A transaction gives us an all-or-nothing boundary.

```text
committed state
    |
    v
copy state + RNG
    |
    v
working transaction
    |
  stages mutate
    |
 success? ---------------- no -> discard working state
    |
   yes
    v
replace committed state
```

There is no complicated “undo every mutation” routine. Rollback works because the
authoritative input was never mutated.

## Determinism and reproducibility

The simulation RNG lives inside `SimulationState` and is cloned with the modeled
state. Therefore state and randomness commit or roll back together.

This avoids a subtle failure mode:

```text
model state rolled back
RNG secretly advanced
```

which would make retry/failure behavior change the stochastic trajectory.

## Immutability

`SimulationContext` is immutable because transactional copies share it by
reference.

If shared configuration were mutable, a failed working transaction could mutate a
shared object and leak changes into the authoritative state even though the domain
copy was discarded.

Immutability here is an architectural guarantee, not a style preference.

# Interface versus policy versus mechanism

These terms are easy to blend.

```text
contract/interface
    shape of collaboration

policy
    replaceable decision rule

mechanism
    machinery that performs a general operation

implementation
    concrete code realizing any of the above
```

For example:

```text
Resolver protocol   contract
AcceptAll            policy implementation
StageCoordinator     orchestration mechanism
```

# Ownership, responsibility, and authority are different

When reading code, ask several separate questions:

```text
Who contains this object?
Who is allowed to mutate it?
Who decides whether a transition occurs?
Who defines what that transition means?
Who decides when it executes?
Who owns randomness?
Who observes the result?
```

In the kernel:

```text
Simulation
    owns authoritative SimulationState

SimulationState
    owns transaction envelope + RNG

StageCoordinator
    owns phase ordering

Resolver
    owns acceptance/order policy

Process
    owns transition meaning + application mutation

Observer
    reads committed results
```

The answers intentionally differ.

# Syntax, semantics, and “sugar”

## Syntax versus semantics

Syntax is how something is written. Semantics is what it means.

```python
working_state = simulation_state.copy()
```

Syntax-level reading:

> Call `copy()` and assign the result.

Architecture-level semantic reading:

> Begin a transaction whose modeled state and RNG can advance independently of the
> committed snapshot.

The textbook trains both levels, especially the second.

## Literal syntactic sugar

Syntactic sugar is alternate language syntax for an operation expressible more
explicitly.

For teaching purposes:

```python
x += 1
```

is a compact syntax for updating `x` through augmented assignment semantics.

## Construction/API sugar

Repository prose may also use **construction sugar** more informally: a convenient
API that normalizes into the canonical representation.

For example, named context values accepted during construction are normalized into
`SimulationContext`; they do not become magical dynamic state fields.

That is API convenience, not a new architecture concept.

## Decorators

A decorator modifies/replaces the object produced by a class/function definition.
In this project decorators such as `@attrs.frozen(...)` matter because they help
encode properties like immutability and generated data-model behavior.

Focus first on the architectural guarantee, then on the decorator mechanics.

## Positional-only `/` and keyword-only `*`

In a signature:

```python
def apply_event(self, simulation_state, event, /) -> None: ...
```

`/` says preceding parameters are positional-only.

This can matter at generic contract boundaries because specializations remain free
to use more domain-specific local parameter names without promising those names as
part of keyword-call compatibility.

Keyword-only `*` does the inverse for parameters after it, making call sites more
explicit where that improves clarity.

# Wrong-but-plausible architecture

Suppose a resolver does this:

```python
class PredatorResolver:
    def resolve_events(self, simulation_state, proposed_events):
        winner = choose_winner(proposed_events)
        simulation_state.domain_state.remove_prey(winner.prey_id)
        return [winner]
```

It looks convenient, but it merges two responsibilities:

```text
select transition
+
apply domain mutation
```

That makes phase semantics and testing harder and violates the resolver/process
boundary. The healthier design returns the selected event and lets its owning
process apply it.

# Architecture quality preview

A design is not “good” merely because it uses abstractions. Ask:

```text
Does each abstraction isolate a real responsibility or variation?
Can the important control flow be seen directly?
Are dependencies explicit?
Is domain knowledge kept in the correct layer?
Can invariants be tested locally?
Does the design add fewer concepts than the problem requires?
```

Continue to [Architecture Quality](architecture_quality.md) for a systematic
framework.

# You understand this chapter if you can...

- explain abstraction as preserving relevant structure rather than maximizing
  genericity;
- distinguish contract, policy, mechanism, and implementation;
- explain dependency injection and inversion using this project;
- separate orchestration from modeled-domain behavior;
- distinguish ownership, authority, and mutation rights;
- explain why mutable state and immutable context are separate;
- derive transaction/RNG semantics from failure/reproducibility needs;
- identify a biology leak or god-object responsibility collapse; and
- interpret important Python syntax by its architectural role rather than only its
  mechanics.

## Next

Read [Architecture Quality](architecture_quality.md), then
[Computational Complexity and Performance Thinking](computational_complexity.md).
# Engineering Anatomy of the Kernel

This chapter rereads the kernel through several engineering lenses at once.
Earlier chapters establish what the kernel means. Here the goal is to practice the
kind of review you would perform on an unfamiliar production subsystem:

```text
correctness
semantics
algorithmic complexity
memory behavior
execution frequency
measured performance
readability
maintainability
extensibility
testability
```

> **[KERNEL]** Complexity formulas below describe kernel structural work unless
> explicitly stated otherwise. Pluggable process, resolver, observer, and domain
> algorithms can dominate total cost. See
> [Computational Complexity and Performance Thinking](computational_complexity.md)
> first if the notation is unfamiliar.

## A reusable Engineering Review Card

For every important component ask:

| Lens | Question |
| --- | --- |
| Responsibility | What problem does this component own? |
| Semantic contract | What must remain true even after refactoring? |
| Time | How does structural work scale? Which delegated costs are unknown? |
| Memory | What is allocated, retained, copied, or cached? For how long? |
| Frequency | Once per run, step, stage, proposal, or event? |
| Measured performance | Is it a real hotspot or only a theoretical concern? |
| Readability | Can a reader see the semantic algorithm? |
| Maintainability | How many paths/rules must future changes preserve? |
| Extensibility | What can vary without editing this code? |
| Testability | Which focused tests prove the important guarantees? |
| Optimization boundary | What tempting shortcut would create more risk than value? |

Use this card later on other codebases too.

## Frequency map of the kernel

Before analyzing local operations, place them in the run hierarchy:

```text
SimulationSpec.compile()
    once before mutable runtime

SimulationEngine.run()
    once per simulation run

while-loop body
    once per completed step

SequentialStepCoordinator.coordinate()
    once per step

StageCoordinator.coordinate()
    once per stage per step

Process.propose_events()
    once per configured process per stage execution

per-proposal resolver work
    depends on resolver

materialize_event()
    at most once per accepted event that needs it

apply_event()
    once per accepted/materialized event

AppliedEvent construction
    once per committed event

Observer / TelemetryObserver
    according to observation policy after commits
```

This hierarchy explains why a simple per-event operation can matter more than a
complicated one-time preflight.

# `SimulationState.copy()`

The transaction begins here.

Conceptually:

```python
copied_rng = clone_rng_state(self.rng)
return SimulationState(
    domain_state=self.domain_state.copy(),
    context=self.context,
    step_index=self.step_index,
    rng=copied_rng,
)
```

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Create an independent transactional snapshot. |
| Semantic contract | Domain state and RNG are independent; immutable context is shared; prior telemetry is not carried as the new step's result. |
| Time | `C_domain_copy(N) + O(1)` fixed kernel envelope/RNG-state work with respect to domain scale. |
| Memory | `M_domain_copy(N) + O(1)` fixed envelope/RNG state. |
| Frequency | Once per simulation step. |
| Measured performance | Copy cost can matter when domain state is large; normal `SimulationState` constructor validation was measured small enough that a second trusted constructor was rejected. |
| Readability | Strong: copy semantics are explicit in one method. |
| Maintainability | Stronger with one validated construction path than parallel trusted/public constructors. |
| Extensibility | Any domain may define its own semantic `copy()` behavior while the kernel remains opaque to the payload. |
| Testability | Focused RNG-copy tests prove exact generator-state cloning and independence. |
| Optimization boundary | Do not weaken rollback/isolation or add constructor paths for tiny measured savings. |

### Why it is not simply `O(1)`

The kernel cannot know the cost of:

```python
self.domain_state.copy()
```

A world containing `N` independently copied entities might use Theta(N) time and
space; another domain might have a different representation. The honest analysis
keeps the domain cost symbolic.

### Time-space tradeoff

The architecture deliberately pays copy time and memory to obtain:

```text
simple rollback
+ RNG rollback
+ clear authoritative/working-state separation
+ deterministic failure semantics
```

Performance work should ask whether domain copying becomes a measured bottleneck
at target scales, not remove the transaction preemptively.

# `Simulation`

`Simulation` owns the authoritative `SimulationState`.

Its constructor performs setup work once:

```text
validate copyability / seed / context form
copy initial domain state
create simulation-owned RNG
create SimulationState
```

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Own the authoritative evolving snapshot for one run. |
| Time | Initial domain copy plus small setup work. |
| Memory | One initial independent domain state plus state/RNG envelope. |
| Frequency | Construction once; `state` replacement once per successful step from the engine. |
| Hot-path status | Constructor is not a per-event hot path. |
| Readability | Very high; ownership is explicit. |
| Maintainability | Good because engine orchestration does not also own state. |
| Extensibility | Arbitrary copyable domain payload/context. |
| Key misconception | `SimulationEngine` runs the simulation but does **not** own authoritative state. |

# `SequentialStepCoordinator.coordinate()`

The semantic skeleton is deliberately linear:

```python
working_state = simulation_state.copy()

for stage in stages:
    stage.coordinate(working_state)

advance_step_and_attach_telemetry(working_state)
return working_state
```

Let `S` be the number of stages and `E` the total committed events in the step.

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Execute one complete transactional step across ordered stages. |
| Semantic contract | Authoritative input is untouched until caller accepts the returned completed state; later stages see earlier-stage mutations. |
| Time | `C_copy(N) + Σ stage_cost_i + O(E)` telemetry aggregation/envelope work. |
| Memory | `M_copy(N) + O(E)` applied-event references/step telemetry plus stage-local temporaries. |
| Frequency | Once per step. |
| Main cost risks | Domain copy and delegated stage/domain work. |
| Readability | Excellent: procedural flow mirrors the transaction semantics. |
| Maintainability | Excellent: one transaction path, no success/failure fast-path duplication. |
| Extensibility | Stage composition changes without modifying step logic. |
| Testability | Transaction/RNG and stage-sequencing semantics can be tested independently. |
| Optimization boundary | Do not mutate authoritative input directly to avoid copying. |

### Why "O(S)" is misleading

The loop itself visits `S` stages, but each stage can do arbitrary work. A useful
analysis retains `Σ stage_cost_i` instead of pretending every stage is constant.

### Memory lifetime

The working state usually lives for the step. Stage proposal/preparation lists
have shorter stage-local lifetimes. `StepTelemetry` becomes part of the completed
state and survives until replaced by a later committed step unless another
consumer retains it.

# `StageCoordinator`

This is the most important kernel performance/semantics case study.

Its public semantic algorithm is:

```text
propose all
    -> resolve
    -> materialize all accepted
    -> apply
```

Let:

```text
P = processes in the stage
Q = total proposals
R = resolved/accepted events
```

## Proposal aggregation

Kernel structural work is approximately:

```text
O(P + Q) time
O(Q) proposal-list memory
```

plus the sum of all `Process.propose_events()` algorithm costs.

A domain process may be O(N), O(N log N), O(N^2), or something else. That is not
`StageCoordinator` overhead merely because the kernel invoked it.

## Resolution

The resolver is deliberately pluggable, so keep its cost symbolic:

```text
C_resolve(Q)
M_resolve(Q)
```

`AcceptAll` can be linear because it returns the proposal sequence as accepted
values. A preference resolver that sorts may require O(Q log Q). A more complex
conflict algorithm can differ again.

## Materialization/preparation

For `R` accepted events, dispatch lookup through the cached dictionary is average
O(1) per event, giving O(R) structural dispatch work, plus:

```text
Σ materialization_cost_j
```

for processes that materialize.

Prepared-application storage is O(R).

## Application/telemetry

There is one application per accepted event and one committed `AppliedEvent`
record per successful application:

```text
O(R) structural iteration
+ Σ apply_cost_j
+ optional effect-journal costs
```

The telemetry records themselves contribute O(R) aggregate record/reference
storage for the stage, excluding the memory of referenced event/effect objects.

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Preserve stage simultaneity while coordinating candidate transitions. |
| Semantic contract | Common stage-start proposal state; resolver selects but does not mutate; all accepted events materialize before any applies; resolver order controls application order. |
| Structural time | `O(P + Q + R) + C_resolve(Q)` excluding delegated proposal/materialization/application work. |
| Structural memory | `O(Q + R)` for proposals/prepared applications plus committed telemetry/effects. |
| Frequency | Once per stage per step; several operations occur per proposal/accepted event. |
| Measured performance | Historically a kernel optimization focus because repeated per-event inspection/metadata work was measurable. Remaining generic per-event cost includes real telemetry allocation. |
| Readability | Strong: `coordinate()` visibly follows the semantic phases. |
| Maintainability | Stronger because optimization uses cached metadata around one semantic path rather than parallel algorithms. |
| Extensibility | New processes, materializers, and resolver policies compose without changing stage orchestration. |
| Testability | Same-stage simultaneity, materialize-before-apply, resolver injection rejection, and effects are focused-testable. |
| Optimization boundary | Never trade stage semantics for a small fast path; dynamic effect-journal behavior must remain correct. |

## Why the dispatch dictionary matters

At construction, `StageCoordinator` builds roughly O(P) dispatch metadata.

That buys average O(1) process lookup for each accepted event:

```text
cached dictionary dispatch: O(R)
linear process search:       O(RP)
```

This is a classic time-space tradeoff: spend O(P) stable memory and setup work to
avoid repeated hot-path discovery.

## Why materialization after resolution can improve performance too

The semantic reason comes first: rejected candidates should not consume deferred
randomness or become concrete outcomes.

It can also avoid expensive rejected work.

```text
10,000 proposals
100 accepted
```

If inheritance/recombination is expensive:

```text
materialize every proposal first -> 10,000 calculations
resolve, then materialize        -> 100 calculations
```

The same architecture can therefore improve semantics **and** computational work.

## Readability versus micro-optimization

The current implementation intentionally preserves one clear flow. A tempting
alternative could create separate algorithms for:

```text
with materializers
without materializers
with effect journal
without effect journal
```

That may shave branches in some cases, but it multiplies semantic paths that must
remain equivalent. The project explicitly prefers the readable single flow unless
measurement demonstrates a sufficiently important structural need.

# Resolver policies

Resolvers demonstrate why complexity belongs partly to replaceable policy objects.

```text
AcceptAll
    simple linear acceptance

preference sorting resolver
    potentially O(Q log Q)

capacity/conflict resolver
    cost depends on data structures and conflict rules
```

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Decide which candidate transitions survive and in what order. |
| Semantic boundary | Selection only; no domain mutation. |
| Complexity | Policy-specific; do not assign one universal resolver Big-O. |
| Extensibility | High: conflict policy can change independently of processes/stages. |
| Testability | High: proposals in, accepted sequence out. |
| Smell to watch | Resolver that starts applying domain changes or accumulating unrelated domain behavior. |

# `AppliedEvent` and `StepTelemetry`

Telemetry is descriptive committed history, not modeled state-transition policy.

For `R` applied events:

```text
AppliedEvent records: Theta(R) allocations
aggregate reference storage: O(R)
```

Each record has a fixed set of metadata fields, but referenced event/effect values
can themselves have domain-dependent memory.

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Preserve committed causal metadata without coupling kernel telemetry to domain event classes. |
| Time | O(1) structural construction per applied event; O(R) aggregate per stage/step. |
| Memory | O(1) fields per record; O(R) aggregate records/references, plus effects. |
| Frequency | Once per committed event — potentially very high. |
| Measured performance | Real allocation/immutable assignment is a remaining generic per-event cost after redundant validation work was reduced. |
| Readability | Explicit immutable records make meaning clear. |
| Maintainability | Public validation remains while trusted kernel construction avoids some duplicate work. |
| Optimization boundary | Do not replace expressive telemetry merely to reduce allocation without an independent architectural reason. |

### Important Big-O lesson

An optimization can make telemetry noticeably faster while both versions remain:

```text
O(R)
```

Big-O did not change. Constant per-event work did.

# Optional effect journal

The domain may expose `effect_count` and `effects_since(...)` dynamically.

Reading the current effect checkpoint before each application creates repeated
per-event work, but that dynamic behavior is part of the contract. Caching "this
state has no journal" for the whole stage could be faster and still be wrong if
journal capability can appear dynamically.

This is a textbook example of **semantics-sensitive optimization**.

# `SimulationContext`

`SimulationContext` stores immutable services in a private tuple and memoizes
successful typed lookups.

Let:

```text
K = configured context values
C = distinct typed keys successfully cached
```

Conceptually:

```text
first uncached typed lookup: O(K) scan
later cached typed lookup:   average O(1)
cache memory:                O(C)
```

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Hold immutable shared configuration/services. |
| Time-space tradeoff | Small typed cache spends O(C) memory to avoid repeated linear lookup. |
| Frequency | Context reads can occur throughout domain execution; exact hotness depends on domain code. |
| Readability | Explicit `require(key)` makes dependencies visible. |
| Maintainability | Private storage allows representation changes without widening public API. |
| Extensibility | Domains define typed keys/services without kernel domain vocabulary. |
| Optimization caution | Do not redesign a small immutable configuration store solely from theoretical lookup complexity; measure realistic use. |

# `SimulationSpec.compile()` and dependency preflight

Compilation happens before mutable runtime exists.

The important performance insight is frequency: even if dependency traversal is
more complicated than a per-event dictionary lookup, it normally runs once.

A configuration-object traversal that visits `V` reachable objects and `A`
relationships/containment edges is naturally reasoned about as graph traversal:

```text
time:   O(V + A) plus validation/provider work
memory: O(V) for visited-object tracking plus report storage
```

Exact implementation details belong to the configuration package, but the broader
lesson is stable: startup validation can spend reasonable work to move failures out
of expensive runtime loops.

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Validate generic structure/dependencies before runtime object creation. |
| Frequency | Once at compile/preflight, not per simulation event. |
| Performance tradeoff | More startup validation can reduce repeated defensive runtime checks and improve diagnostics. |
| Readability | Explicit compilation boundary separates static setup facts from evolving-state checks. |
| Maintainability | Dependency requirements stay close to components that own them. |
| Optimization boundary | Avoid moving valid static checks into hot runtime paths to make compile superficially cheaper. |

# `SimulationEngine.run()`

The engine's loop looks simple:

```text
observe initial committed state
while not stopped:
    coordinate one step
    replace simulation.state with completed state
    observe telemetry
    observe committed domain state
```

Let `T` be completed steps. Saying the method is merely O(T) hides the important
work. A better expression is:

```text
Σ over steps t:
    stopping_cost(t)
    + step_cost(t)
    + telemetry_observation_cost(t)
    + domain_observation_cost(t)
```

If domain size changes through time, write `step_cost(N_t)` rather than assuming
constant per-step work.

## Engineering Review Card

| Lens | Analysis |
| --- | --- |
| Responsibility | Run completed transactional steps until stopping, then expose committed observations. |
| Semantic contract | Assignment to `simulation.state` is the commit point from the engine's perspective. |
| Time | Sum of all step/stopping/observation costs across the run. |
| Memory | Small engine-owned orchestration memory; observers may retain arbitrarily large histories. |
| Frequency | Loop once per completed step. |
| Readability | Strong: commit and post-commit observation are visible in order. |
| Maintainability | State ownership remains with `Simulation`, avoiding mixed authority. |
| Extensibility | Stopping/step/observer policies are replaceable contracts. |
| Optimization caution | Do not fold observation or resolution into the run loop merely to remove calls. |

# Observation and long-run memory

Observers deserve separate memory analysis because they can retain history beyond
one transaction.

```text
live domain state
    maybe O(N_t)

one-step temporary proposals
    released after stage

recorder storing O(N_t) snapshot every step
    cumulative O(Σ N_t)
```

For approximately stable `N` across `T` steps, that historical recorder can be
O(TN) memory even though the live domain state is only O(N).

This is why the repository separates reference-core and reference-observed
performance scenarios: observability is valuable but not computationally free.

# Readability: make the algorithm visible

Use concrete criteria rather than saying "this feels readable."

## Control-flow locality

Can you see the semantic algorithm in one place?

`StageCoordinator.coordinate()` scores well because the four phases appear in
order at the top level.

## Naming

Do names reveal architectural meaning?

`working_state`, `resolved_events`, and `prepared_applications` explain more than
names such as `tmp`, `data`, or `items`.

## Cognitive load

How many concepts must the reader hold simultaneously? Private dispatch metadata
adds complexity, but keeping it outside the public semantic flow reduces the load
on a first read.

## Hidden state and hidden dependencies

Explicit context and simulation-owned RNG make dependencies visible. A global
random generator or service locator would make local code shorter while making the
system harder to reason about.

## Distance between cause and effect

Proposal, resolution, materialization, and application are intentionally separate,
but the coordinator keeps their order together so the relationship remains clear.

# Maintainability: estimate the future change surface

Maintainability is not "more abstraction."

Ask:

```text
How many semantic paths exist?
How many components know this rule?
Is the rule duplicated?
Can a policy vary independently?
Are dependencies explicit?
Which tests localize failures?
How wide is the public contract change radius?
```

A private helper change can be local. A `Process` or `PropagationModel` contract
change can affect many implementations, tests, composition roots, examples, and
documentation.

Small public contracts therefore deserve more design care than their line count
suggests.

# Extensibility: real axes of change, not speculative abstraction

For each abstraction ask:

```text
What can vary without modifying this component?
What has this layer intentionally frozen?
Is the variation demonstrated or merely hypothetical?
```

Examples:

- Resolver policy varies without changing `StageCoordinator`.
- Domain state shape varies without changing `SimulationState`.
- Biological inheritance varies above generic propagation.
- The kernel does **not** need a pregnancy, chromosome, energy, or mating flag for
  each domain feature.

An abstraction is useful when it corresponds to a real axis of variation. More
interfaces are not automatically more maintainable.

# Architecture smells and healthy patterns

| Smell | Why it is suspicious | Healthier pattern |
| --- | --- | --- |
| biology leak into kernel | lower layer now understands one domain | domain specialization above opaque kernel state |
| god process | selection, mutation, telemetry, and policy collapse together | small process + resolver + supporting policies |
| hidden mutable dependency | behavior depends on globals/service lookup | explicit immutable context / state input |
| order-dependent science | execution order becomes accidental modeled causality | stage simultaneity + explicit stages |
| duplicated policy | same rule maintained in several places | one policy/contract owner |
| boolean/special-case explosion | generic component accumulates domain flags | composition/policy objects |
| premature generalization | abstraction exists for imagined future only | smallest contract supported by real need |
| performance fast-path explosion | several algorithms must preserve identical semantics | one readable path + measured stable caches |

# Safe versus dangerous performance changes

## Structurally safer example

Move stable event-type/materializer discovery from a per-event path to stage
construction and cache it.

Why safer:

```text
same semantics
same RNG timing
same state visibility
less repeated stable work
```

## Semantics-sensitive example

Materialize every proposal before resolution.

Why dangerous:

```text
rejected candidates consume deferred work/randomness
stage semantics change
reproducibility behavior can change
```

## Architecture-changing example

Replace immutable `AppliedEvent` records with a compressed shared representation.

This might reduce allocation but changes telemetry representation and potentially
public expectations. It requires independent architectural justification, not only
a benchmark.

# Scaling thought experiments

Practice asking "what if the scientific scale changes?"

### 10x more processes in a stage

Kernel proposal-loop overhead grows roughly linearly with `P`, but domain proposal
production may dominate.

### 10x more proposals with same acceptance ratio

Proposal storage and linear orchestration rise ~10x. Resolver cost depends on its
algorithm: a sorting resolver rises somewhat more than 10x.

### 10x more organisms in an all-pairs mating search

If the domain algorithm is O(N^2), candidate comparisons rise roughly 100x even
though the kernel remains linear in the proposals it receives.

### 10x more simulation steps

If per-step workload stays comparable, total run work grows roughly 10x. If the
population grows through time, total work can grow faster.

### Record every entity every step

Historical memory can grow with the sum of population sizes across steps rather
than the final population alone.

# A code-review decision procedure

When you encounter a proposed optimization or refactor:

```text
1. Which layer owns the behavior?
2. What invariant does the current code preserve?
3. What are the scale variables?
4. What is the structural complexity now?
5. What is actually measured as expensive?
6. Does the change alter RNG timing, ordering, or state visibility?
7. Does it add another semantic path?
8. Is the readability/maintenance cost proportional to the measured benefit?
9. Which focused tests prove equivalence?
10. Would an algorithm/data-structure improvement be better than interpreter tricks?
```

# You understand this chapter if you can...

- derive `StageCoordinator` structural time/memory while keeping resolver/domain
  costs explicit;
- explain why `SimulationState.copy()` has domain-parameterized complexity;
- identify the frequency layer of any kernel operation;
- distinguish a theoretical scaling hazard from a measured hotspot;
- explain why dispatch caching is a reasonable time-space tradeoff;
- explain why materialize-after-resolution has both semantic and potential
  performance benefits;
- identify which memory is stage-local, step-local, persistent, or historically
  retained;
- evaluate readability and maintainability using concrete criteria;
- spot project-relevant architecture smells; and
- review an optimization for correctness, performance evidence, and change-surface
  cost rather than speed alone.

## Practice next

Use the [Reading the Kernel Source](source_code_walkthrough.md) chapter with this
review card, then complete the engineering/code-review exercises in
[Exercises](exercises.md).

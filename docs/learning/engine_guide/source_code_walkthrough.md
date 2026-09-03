# Reading the Kernel Source

This chapter is designed for the moment you open `src/evo_engine/engine/` and want
to understand the real production code quickly.

The central rule is:

> **Do not read an unfamiliar subsystem as a novel from line 1 to EOF. Read its
> public contracts, focused tests, semantic center, then supporting plumbing.**

## Recommended reading order

| Order | File | Difficulty | Main question |
| ---: | --- | :---: | --- |
| 1 | `engine/protocols.py` | ★★☆☆☆ | What roles exist? |
| 2 | `engine/simulation_state.py` | ★★★☆☆ | What is one transactional snapshot? |
| 3 | `engine/simulation.py` | ★☆☆☆☆ | Who owns authoritative state? |
| 4 | `engine/step_coordinator.py` | ★★☆☆☆ | Where is the step transaction? |
| 5 | `engine/stage_coordinator.py` | ★★★★☆ | What are the exact stage semantics? |
| 6 | `engine/simulation_engine.py` | ★★☆☆☆ | How does the run loop commit and observe? |
| 7 | `engine/stopping_conditions.py` | ★☆☆☆☆ | How does termination plug in? |
| 8 | `context.py` | ★★★☆☆ | How is immutable configuration carried? |
| 9 | `telemetry/records.py` | ★★★☆☆ | What committed causal data is stored? |
| 10 | `configuration/spec.py` | ★★★☆☆ | How is a complete simulation compiled? |
| 11 | `configuration/dependencies.py` | ★★★★☆ | How does generic dependency preflight work? |

Difficulty means “how much incidental machinery surrounds the central idea,” not
“quality” or importance.

## Before implementation: read these tests

Three test files make excellent executable documentation:

1. [`tests/engine/test_domain_neutral_kernel.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_domain_neutral_kernel.py)
2. [`tests/engine/test_stage_coordinator.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_stage_coordinator.py)
3. [`tests/engine/test_simulation_state_copy_semantics.py`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/tests/engine/test_simulation_state_copy_semantics.py)

They tell you what must remain true before you inspect how production code achieves
it.

# 1. `engine/protocols.py`

## Question this file answers

> What are the domain-neutral roles the kernel coordinates?

## Read first

Ignore the variance names initially and scan the Protocols:

```text
SimulationEvent
Process
EventMaterializer
Resolver
StepCoordinator
StoppingCondition
Observer
```

Write one sentence beside each.

```text
SimulationEvent    value carrying step_index
Process            propose + apply one transition family
EventMaterializer  optional accepted-only preparation
Resolver           select/order proposals
StepCoordinator    produce one completed transactional state
StoppingCondition  decide run termination
Observer           read committed domain state
```

If you can do that, you understand the semantic purpose of the file.

## Read second: `Process`

The heart is:

```python
class Process(Protocol[ProposedEventT_co, MaterializedEventT_contra]):
    @property
    def event_type(self) -> type[ProposedEventT_co]: ...

    def propose_events(
        self,
        simulation_state: SimulationState,
    ) -> Sequence[ProposedEventT_co]: ...

    def apply_event(
        self,
        simulation_state: SimulationState,
        event: MaterializedEventT_contra,
        /,
    ) -> None: ...
```

Read it as:

```text
one process owns
    a proposal type
    candidate generation
    application semantics
```

## Then understand `EventMaterializer`

```python
@runtime_checkable
class EventMaterializer(Protocol[...]):
    def materialize_event(...): ...
```

`runtime_checkable` matters because `StageCoordinator` uses `isinstance` during
construction to detect this optional capability.

## What to postpone

The `TypeVar` covariance/contravariance declarations support correct typing around
proposal and materialized event directions. Understand them if you are editing the
public typing contract. They are **not required to understand runtime phase
semantics** on your first pass.

# 2. `engine/simulation_state.py`

## Question this file answers

> What must travel together when one simulation snapshot is copied, mutated, or
> committed?

## Read the fields first

```python
domain_state
context
step_index
rng
last_step_telemetry
```

Immediately classify them:

```text
domain_state          mutable, independently copied
context               immutable, shared
step_index            value state
rng                    mutable stochastic state, independently cloned
last_step_telemetry    description of prior committed step
```

## Read `_validate_domain_state`

Do not overinterpret it. The kernel asks only for:

```text
callable copy()
```

That is the generic transaction capability.

## Read the custom `__init__`

The important architectural behavior is:

```text
context + context_values cannot both be supplied
named context_values become SimulationContext
missing rng becomes a new generator
```

The calls to `object.__setattr__` are implementation mechanics needed because
`attrs` field behavior is being controlled explicitly. The architecture is the
normalization/validation, not the spelling.

## Read `copy()` carefully

This is one of the most important methods in the kernel:

```python
copied_rng = random.Random.__new__(random.Random)
copied_rng.setstate(self.rng.getstate())
return SimulationState(
    domain_state=self.domain_state.copy(),
    context=self.context,
    step_index=self.step_index,
    rng=copied_rng,
    last_step_telemetry=None,
)
```

Translate every line into architecture:

```text
new Random object
    -> no shared mutable RNG identity

set exact RNG state
    -> deterministic transaction clone

domain_state.copy()
    -> domain mutation isolation

context=self.context
    -> immutable service sharing

last_step_telemetry=None
    -> new transaction has not completed a step yet
```

The comment about bypassing `Random.__init__` is a micro-optimization/readability
detail. It preserves the same semantic requirement: exact generator cloning.

# 3. `engine/simulation.py`

## Question this file answers

> Who owns the authoritative simulation snapshot?

The answer is `Simulation`.

## Read the constructor as ownership establishment

```text
caller supplies initial_domain_state
        |
        v
validate copy capability
        |
        v
copy initial domain state
        |
        v
create seeded RNG
        |
        v
construct SimulationState
        |
        v
self.state = initial state
```

The initial copy prevents the caller's mutable object from becoming the same object
used as authoritative runtime state.

## `context` property

```python
@property
def context(self) -> SimulationContext:
    return self.state.context
```

This is convenience access, not a second context owner.

# 4. `engine/step_coordinator.py` — heavily annotated

This is the best file to read line-by-line because it is small and semantically
central.

## Full semantic method

```python
def coordinate(
    self,
    simulation_state: SimulationState,
) -> SimulationState:
    working_state = simulation_state.copy()
    applied_events: list[AppliedEvent] = []

    for stage_index, stage in enumerate(self.stages):
        stage_events = stage.coordinate(
            simulation_state=working_state,
            stage_index=stage_index,
        )
        applied_events.extend(stage_events)

    working_state.step_index += 1
    working_state.last_step_telemetry = StepTelemetry._from_kernel_values(
        completed_step_index=working_state.step_index,
        events=tuple(applied_events),
    )

    return working_state
```

Now annotate it architecturally.

### Signature

```python
def coordinate(self, simulation_state: SimulationState) -> SimulationState:
```

Input is the caller's current authoritative snapshot. Output is a **different
completed state** suitable for commit.

### Transaction boundary

```python
working_state = simulation_state.copy()
```

This is not routine defensive copying. It begins the transaction.

If anything later raises, the caller still owns the untouched input snapshot and
its untouched RNG stream.

### Telemetry accumulator

```python
applied_events: list[AppliedEvent] = []
```

This accumulates committed-within-the-working-transaction application records
across all stages.

It is separate from domain state because telemetry describes transitions rather
than becoming modeled domain data.

### Stage loop

```python
for stage_index, stage in enumerate(self.stages):
```

Configured tuple order is semantic stage order.

Unlike same-stage processes, later stages are intentionally allowed to observe
mutations from earlier stages.

### Pass the same working transaction

```python
stage_events = stage.coordinate(
    simulation_state=working_state,
    stage_index=stage_index,
)
```

No new state copy is made per stage. All stages participate in one step
transaction.

### Preserve applied-event ordering

```python
applied_events.extend(stage_events)
```

Telemetry remains ordered by stage, then by resolver/application order inside the
stage.

### Advance completed-step index

```python
working_state.step_index += 1
```

Only after every stage succeeds does the state become “one completed step later.”

### Attach step telemetry

```python
working_state.last_step_telemetry = StepTelemetry._from_kernel_values(...)
```

The returned snapshot carries the causal record of the step that produced it.

### Return, do not commit

```python
return working_state
```

This method does not know which object owns authoritative state. It returns a
completed candidate. `SimulationEngine.run()` performs the replacement.

## The method in one sentence

> Copy the committed snapshot, run every stage against that transaction, package
> the causal record, advance the step index, and return the completed snapshot.

If you can explain that sentence, you can read the entire method.

# 5. `engine/stage_coordinator.py`

## Question this file answers

> How does one stage preserve proposal/materialization simultaneity while still
> resolving conflicts, applying transitions, and recording telemetry efficiently?

This file is conceptually simple but implementation-dense.

## Do not start at `_ProcessDispatch`

First locate `StageCoordinator.coordinate()`:

```python
proposed_events = self._propose_events(simulation_state)
resolved_events = self.resolver.resolve_events(...)
prepared_applications = self._prepare_applications(...)
return _apply_prepared_applications(...)
```

That is the semantic heart.

Rewrite it mentally as:

```text
propose
resolve
materialize/prepare
apply + telemetry
```

Everything else supports those four lines.

## Then read `_propose_events()`

```python
for process in self.processes:
    proposed_events.extend(process.propose_events(simulation_state))
```

Question:

> Has anything applied yet?

No. Therefore all proposals observe the common stage-start state.

## Then read `_prepare_applications()`

For each resolved event it:

1. gets the dispatch entry for the proposal type;
2. raises if no process owns that resolved type;
3. calls cached materializer if present;
4. stores process + materialized event + telemetry naming data.

Crucially, this loop completes before `_apply_prepared_applications()` begins.

## Then read `_apply_prepared_applications()`

For each prepared event:

```text
checkpoint optional effect journal
process.apply_event(...)
capture effects since checkpoint
create AppliedEvent
```

This is the mutation/telemetry half of the stage.

## Only now return to constructor dispatch machinery

`__init__()` builds:

```text
proposal event type
    -> process
    -> optional cached materialize_event callable
    -> stable process/event type names
```

Why?

Because runtime resolved events need fast, unambiguous routing back to their
process owner.

### `_ProcessDispatch`

This is not a new architecture concept. It is a compact record of cached routing
metadata.

### `_PreparedApplication`

A plain tuple stores exactly what the application hot path needs.

The source comment explicitly says the tuple choice is about keeping hot-path data
minimal. Treat it as performance-oriented representation, not stage semantics.

### `_event_type_names`

Caches fully qualified type names for telemetry. Again: diagnostics/telemetry
support, not domain behavior.

## The key reading distinction

```text
SEMANTIC CORE
    _propose_events
    resolver.resolve_events
    _prepare_applications as materialize-all phase
    _apply_prepared_applications

SUPPORT
    dispatch dictionaries
    NamedTuple metadata
    cached callables
    type-name caches
    effect-journal structural validation
```

If you mix those categories, the file looks much harder than it is.

# 6. `engine/simulation_engine.py`

## Question this file answers

> How does a configured simulation repeatedly commit transactions and expose
> committed observations?

Read `run()` first:

```python
self._observe(simulation.state)
while not self.stopping_condition.should_stop(simulation.state):
    simulation.state = self.step_coordinator.coordinate(
        simulation_state=simulation.state,
    )
    self._observe_telemetry(simulation.state)
    self._observe(simulation.state)
```

You should be able to label every line:

```text
initial snapshot observation
stop check on authoritative state
coordinate transaction
commit by assignment
observe committed causal telemetry
observe committed domain state
```

Then read `_observe` and `_observe_telemetry`; they are straightforward loops over
configured observers.

## Important negative fact

There is no `self.state`.

That absence is architecturally meaningful: the `Simulation` object owns the
mutable authoritative snapshot.

# 7. `engine/stopping_conditions.py`

## Question this file answers

> What does a simple termination policy look like?

`MaxSteps` is intentionally boring:

```python
return simulation_state.step_index >= self.max_steps
```

That is valuable because it shows stopping conditions are ordinary injected
policies rather than special engine branches.

# 8. `context.py`

## Question this file answers

> How can domain-specific immutable services be available to processes without
> expanding the generic state API?

## Read `ContextKey[T]`

It pairs:

```text
name
runtime value_type
static generic T
```

A typed key therefore provides both runtime validation and static return typing.

## Read `SimulationContext.require()`

Its conceptual algorithm:

```text
normalize key to name
find bound value
if typed key:
    validate value type
    memoize validated lookup
return value
```

The private tuple/cache representation is implementation detail.

## Why `attrs.frozen`

The context is designed to be immutable shared configuration. The `frozen`
decorator is therefore not stylistic decoration; it supports the transaction
architecture by making shared references safe.

# 9. `telemetry/records.py`

## Question this file answers

> What immutable information does the kernel retain about committed transitions?

Read the data fields before helper constructors.

### `AppliedEvent`

```text
event_step_index
stage_index
process_type
event_type
event
effects
```

### `StepTelemetry`

```text
completed_step_index
events
```

The private `_from_kernel_values` constructors exist because the kernel supplies
metadata and needs validation specialized to that trusted construction path.

Do not let those helpers distract from the simple data model.

# 10. `configuration/spec.py`

## Question this file answers

> How do we describe and validate a complete simulation before mutable runtime
> exists?

Read `SimulationSpec` fields first.

Then read `compile()`:

```text
SimulationSpecValidator.validate(self)
        |
        +--> dependency report / fail if missing
        |
        v
Simulation(...)
SimulationEngine(...)
        |
        v
CompiledSimulation(...)
```

That is the whole conceptual purpose.

`from_iterables()` is normalization convenience: it turns flexible iterable inputs
into the immutable tuple/frozenset representation required by the spec.

# 11. `configuration/dependencies.py`

## Question this file answers

> How can configured components declare generic capabilities they need, and how
> can preflight discover those requirements through a composed object graph?

This is more infrastructure-heavy than the runtime kernel.

Read in this order:

1. `Dependency`
2. `DependencyRequirementProvider`
3. `DependencyReport.missing`
4. `DependencyReport.require_satisfied()`
5. `dependency_report(...)`
6. only then the recursive object-graph traversal helpers.

The object traversal exists to inspect a configured component graph recursively.
Do not mistake traversal mechanics for a simulation runtime algorithm.

# How to read `attrs` in this codebase

`attrs` declarations carry both data-model and architectural information.

### `@attrs.frozen`

Ask:

> Why is this object intended not to mutate after construction?

For events, immutability helps treat transitions as values.
For context, it supports safe sharing across transactions.

### `@attrs.define`

Ask:

> Is this intentionally mutable modeled/runtime state?

Do not infer that every non-frozen object is “bad architecture.” Mutability is
necessary where the model evolves.

### Validators

Validators usually encode object-local invariants. Distinguish them from
cross-component preflight and evolving-state runtime rules.

# How to read positional-only `/`

You will see:

```python
def apply_event(self, simulation_state, event, /):
```

At the Python level, arguments before `/` cannot be passed by keyword.

At the contract-design level, this also means a structural implementation can use
a domain-native parameter name without promising that the generic parameter name
is part of the call API.

The general `TransmissibleStateExpression` uses the same idea so biology can write
`express(genome)` naturally.

# How to read type variance without getting stuck

Names such as:

```text
ProposedEventT_co
MaterializedEventT_contra
```

are there to make static substitutability precise.

For a first runtime reading:

```text
_co      -> value flows out of the contract in that role
_contra  -> value flows into the contract in that role
```

You do not need a full type-theory derivation to understand the simulation
algorithm. Return later when modifying generic typing.

# A source-reading workflow to practice

For any unfamiliar subsystem:

```text
1. Find public exports / Protocols.
2. Read authoritative contract docs.
3. Read one focused happy-path test.
4. Read one edge-case/invariant test.
5. Locate the orchestration method.
6. Rewrite it as 5-10 lines of pseudocode.
7. Classify remaining code:
       semantic
       validation
       diagnostics/telemetry
       typing
       performance
8. Only then read helper internals line-by-line.
```

This is often faster and more reliable than starting from imports and reading
straight down.

# “What is this line doing architecturally?” examples

```python
working_state = simulation_state.copy()
```

Syntax: call a method.
Architecture: establish transaction isolation including RNG rollback.

```python
resolved_events = self.resolver.resolve_events(...)
```

Syntax: call a method.
Architecture: externalize conflict/competition policy before mutation.

```python
materialized_event = dispatch.materialize_event(...)
```

Syntax: call cached bound method.
Architecture: determine accepted-only deferred transition details while preserving
pre-application stage state.

```python
process.apply_event(simulation_state, event)
```

Syntax: method call.
Architecture: enter the process-owned domain mutation phase.

```python
simulation.state = self.step_coordinator.coordinate(...)
```

Syntax: assignment from function result.
Architecture: commit the complete successful transaction by replacing the
authoritative state reference.

# What to ignore on the first pass

You can safely postpone deep understanding of:

```text
qualified type-name caching
exact tuple-vs-NamedTuple hot-path choices
memoization implementation inside SimulationContext
validator helper internals
full TypeVar variance details
recursive dependency graph traversal internals
```

until the semantic skeleton is clear.

Do **not** postpone:

```text
state copying
RNG ownership
phase ordering
resolver/process responsibility split
materialize-all-before-apply
state commit assignment
observer placement
```

Those are the architecture.

# Master check: explain `stage_coordinator.py` without looking

You should eventually be able to say:

> At construction, a stage freezes its process sequence, validates unique proposal
> event ownership, and caches dispatch/materializer/type metadata. At runtime it
> collects all proposals against one stage-start transactional state, gives the
> complete sequence to the resolver, maps accepted proposals back to owning
> processes, materializes every accepted event before any application begins, then
> applies events in resolver order while capturing optional domain effects and
> building `AppliedEvent` telemetry.

If that paragraph makes sense before you look at the code, the file becomes a
verification exercise rather than a puzzle.

# You understand this chapter if you can…

- read `SequentialStepCoordinator.coordinate()` line-by-line and state the
  architecture meaning of every line;
- open `StageCoordinator` and immediately locate the semantic core before reading
  dispatch caches;
- classify code as semantic, validation, telemetry/diagnostics, typing, or
  performance support;
- explain why `Simulation` rather than `SimulationEngine` contains authoritative
  state;
- read `SimulationState.copy()` as transaction semantics rather than utility code;
- use focused tests to infer a file's promises before implementation details; and
- decide which parts of the kernel source can be postponed on a first reading
  without missing the architecture.

Next: [Debugger Labs](debugger_labs.md).

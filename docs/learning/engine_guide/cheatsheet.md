# Evolution Simulation Engine Cheat Sheet

Use this page when you already understand the concepts and need a fast orientation
while reading code.

## The three-layer question

```text
[BIOLOGY]
What does this mean biologically?
        ^
        |
[GENERAL EVOLUTION]
What makes this evolutionary?
        ^
        |
[KERNEL]
How are transitions executed safely/reproducibly?
```

If a proposed kernel change contains biological vocabulary, challenge the layer
placement first.

# Kernel object map

```text
Simulation
    |
    `-- state : SimulationState  <-- authoritative snapshot
            |
            +-- domain_state     mutable, domain-owned meaning
            +-- context          immutable shared services
            +-- rng              simulation-owned RNG
            +-- step_index
            `-- last_step_telemetry

SimulationEngine
    |
    +-- step_coordinator
    |       `-- SequentialStepCoordinator
    |               `-- StageCoordinator(s)
    |                       +-- Process(es)
    |                       `-- Resolver
    +-- stopping_condition
    +-- observers
    `-- telemetry_observers
```

**Remember:** `Simulation` owns authoritative state. `SimulationEngine` orchestrates
its replacement.

# One run loop

```text
observe initial committed state
        |
while not stopped
        |
        v
coordinate one transactional step
        |
        v
simulation.state = returned state   <-- COMMIT
        |
        +--> telemetry observers
        +--> state observers
        |
        `--> repeat
```

# One step

```text
authoritative SimulationState
        |
        v
copy()
        |
        +-- copy domain_state
        +-- clone exact RNG state
        `-- share immutable context
        |
        v
working state
        |
        +--> stage 0
        +--> stage 1
        +--> ...
        |
        v
increment step_index
attach StepTelemetry
        |
        v
return completed state
```

Failure before return means the authoritative state/RNG remain unchanged.

# One stage

```text
PROPOSE ALL
all processes see same stage-start state
        |
        v
RESOLVE
resolver chooses accepted events/order
        |
        v
MATERIALIZE ALL ACCEPTED
accepted-only/deferred details; still pre-application state
        |
        v
APPLY ACCEPTED
process owns domain mutation, in resolver order
        |
        v
AppliedEvent telemetry
```

# Phase permissions

| Phase | Reads stage state? | May consume simulation RNG? | Mutates domain? | Main responsibility |
| --- | :---: | :---: | :---: | --- |
| propose | yes | if proposal semantics require | no | create candidates |
| resolve | yes | normally policy-dependent; preserve intended semantics | no | choose/order candidates |
| materialize | yes | yes, ideal for accepted-only RNG | no domain application | determine deferred outcome |
| apply | yes | should usually apply already-determined event; domain contract decides | **yes** | commit process transition to working state |
| observe | committed state | not for modeled causal decisions | no | describe results |

The key rule is not “RNG is forbidden everywhere except materialization.” The key
question is whether the random decision semantically defines candidate existence or
belongs only to an accepted transition.

# Event terminology

```text
proposed event
    candidate
        |
        v
resolved event
    accepted by resolver
        |
        v
materialized event
    accepted deferred details determined
        |
        v
process.apply_event
    working domain mutation
        |
        v
AppliedEvent
    immutable committed-transition telemetry value
```

A proposal and materialized event may share one Python type, but the semantic
stages are still distinct.

# Who owns what?

| Question | Answer |
| --- | --- |
| authoritative current state? | `Simulation` |
| transaction envelope semantics? | `SimulationState` |
| modeled payload meaning? | domain |
| simulation RNG? | `SimulationState` |
| run/stop/observe loop? | `SimulationEngine` |
| one-step transaction? | `SequentialStepCoordinator` |
| stage phase ordering? | `StageCoordinator` |
| candidate transition meaning? | `Process` |
| domain mutation? | owning `Process.apply_event` |
| conflict acceptance/order? | `Resolver` |
| accepted-only deferred event detail? | optional `EventMaterializer` |
| fixed services/config? | `SimulationContext` |
| static generic preflight? | `SimulationSpec` |
| committed state measurement? | `Observer` |
| committed transition history? | telemetry observer / `StepTelemetry` |

# Public API map

```text
ASSEMBLE / RUN
    Simulation
    SimulationEngine
    StageCoordinator
    SequentialStepCoordinator
    MaxSteps
    SimulationSpec
    SimulationContext

IMPLEMENT / EXTEND
    SimulationEvent
    Process
    EventMaterializer (optional)
    Resolver
    StepCoordinator
    StoppingCondition
    Observer
    TelemetryObserver
```

# Code -> concept

```text
simulation_state.copy()
    TRANSACTION BOUNDARY

simulation_state.domain_state
    KERNEL/DOMAIN BOUNDARY

simulation_state.rng
    TRANSACTION-OWNED RANDOMNESS

simulation_state.context.require(...)
    IMMUTABLE CONFIG/SERVICE LOOKUP

process.propose_events(...)
    CANDIDATE GENERATION

resolver.resolve_events(...)
    COMPETITION / ACCEPTANCE POLICY

process.materialize_event(...)
    ACCEPTED-ONLY DEFERRED CONSEQUENCE

process.apply_event(...)
    PROCESS-OWNED DOMAIN MUTATION

simulation.state = coordinator.coordinate(...)
    TRANSACTION COMMIT

StepTelemetry.events
    COMMITTED CAUSAL HISTORY
```

# Essential kernel invariants

1. Kernel treats `domain_state` as opaque modeled payload.
2. Step execution mutates a transactional copy, not authoritative input.
3. RNG state is copied/committed with modeled state.
4. All same-stage processes propose before application.
5. Resolver selects events; process owns mutation.
6. All accepted events materialize before any same-stage application.
7. Rejected proposals do not enter accepted-only materialization.
8. Proposal event types are unique per process within one stage.
9. Resolver cannot return an event type with no registered process owner.
10. Immutable context is shared by reference across transactions.
11. Telemetry describes applied transitions; observation is descriptive.
12. Static generic dependency errors should fail at preflight.

# General evolution map

```text
transmissible state
        |
        +--> variation
        |
        v
     expression
        |
        v
expressed characteristics
        |
 + environment / state / history
        |
        v
    realization
        |
        v
operative characteristics
        |
        v
interactions / persistence / propagation
        |
        v
future transmissible-state distribution
        |
        v
     EVOLUTION
```

Selection is typically the emergent pattern of **differential future
contribution**, not a mandatory stored scalar.

# General evolution -> biology

| General | Biology |
| --- | --- |
| evolving entity | organism |
| transmissible state | genome |
| expression | genetic expression |
| expressed state | genetic phenotype |
| realization | development / G×E / plasticity |
| propagation | inheritance |
| variation | mutation / recombination |
| linkage group | chromosome |
| linkage position | locus position |
| production | offspring production/birth |
| admission | newborn enters world |
| departure | death/migration/other removal |
| selection | differential survival/genetic contribution |
| lineage | pedigree/genetic ancestry |

# Propagation is not production

```text
PROPAGATION
source state(s) + recipient + context + RNG
    -> recipient transmissible state

PRODUCTION
already-determined state/context
    -> entity

ADMISSION
entity
    -> active domain membership
```

Horizontal propagation can occur without producing any entity.

# Biological reproduction: four relationships

```text
                 PARTICIPANTS
             resolver-facing group
          /          |           \
         /           |            \
        v            v             v
 INVESTORS     GENETIC          PRODUCTION
 proposal-time CONTRIBUTORS      SOURCES
 affordability materialization   materialization
        |            |             |
        v            v             v
 committed      source genomes   production/
 energy              |          placement context
                     v
                 inheritance
                     |
                     v
              offspring genome
```

Defaults may select all participants for every role, but the concepts remain
independent.

**Pedigree genetic parentage follows genetic contributors.**

# State versus configuration

```text
MUTABLE / TRANSACTIONAL
    domain_state
    step_index
    RNG state
    current telemetry reference

IMMUTABLE / SHARED
    SimulationContext
    fixed policies/services/configuration values
```

Named context kwargs are construction sugar, not dynamic `SimulationState`
attributes.

# Source-reading order

```text
1. engine/protocols.py
2. engine/simulation_state.py
3. engine/simulation.py
4. engine/step_coordinator.py
5. engine/stage_coordinator.py
6. engine/simulation_engine.py
7. engine/stopping_conditions.py
8. context.py
9. telemetry/records.py
10. configuration/spec.py
11. configuration/dependencies.py
```

Before implementation, read focused tests:

```text
test_domain_neutral_kernel.py
test_stage_coordinator.py
test_simulation_state_copy_semantics.py
test_kernel_determinism.py
```

# `StageCoordinator` reading shortcut

First locate:

```text
coordinate()
    _propose_events()
    resolver.resolve_events()
    _prepare_applications()
    _apply_prepared_applications()
```

Only afterward study:

```text
_ProcessDispatch
cached materializer callables
type-name caches
_PreparedApplication tuple
effect-journal helpers
```

The first group is semantic architecture. The second group supports performance,
telemetry, and validation.

# Architecture review questions

When evaluating new code, ask:

```text
Which layer owns this concept?
Is this domain meaning or execution mechanics?
What state may this phase observe?
Who has authority to decide?
Who may mutate?
When should RNG be consumed?
Could rejected work perturb accepted outcomes?
Does Python ordering accidentally become model causality?
Is configuration being confused with evolving state?
Is telemetry being confused with modeled state?
Which invariant/test protects this behavior?
Can the existing frozen kernel already express it?
```

# Five mental anchors

If you remember only five things:

1. **`Simulation` owns authoritative state.**
2. **A step mutates a copy; commit is state replacement after success.**
3. **Within a stage: propose all -> resolve -> materialize all -> apply.**
4. **Resolver chooses; process mutates.**
5. **Kernel executes transitions; general evolution defines evolutionary
   relationships; biology gives them biological meaning.**

For deeper definitions, use the [Glossary](glossary.md). For the full course,
return to [Start Here](index.md).

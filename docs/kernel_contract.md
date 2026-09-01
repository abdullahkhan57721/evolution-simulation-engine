# Simulation Kernel Contract

The simulation kernel is the domain-neutral execution layer of the Evolution Simulation Engine. Its job is to coordinate state transitions reproducibly and transactionally without assigning biological, ecological, spatial, genetic, or other modeled meaning to those transitions.

The kernel is considered complete for the current architecture. New modeled behavior should be implemented above this boundary unless an existing kernel contract cannot express the required semantics correctly.

## Canonical vocabulary

`SimulationState` is the kernel-owned transactional envelope for one committed simulation snapshot.

`domain_state` is the opaque mutable payload owned by the modeled domain. The kernel requires the payload to provide `copy()` for transactional isolation but otherwise does not interpret its contents.

`SimulationContext` is immutable configuration and service state shared across transactional copies. Components retrieve configuration explicitly through typed or named context keys.

An `event` is a proposed, resolved, and optionally materialized transition. A process owns the event type it proposes and applies.

An `effect` is an opaque committed consequence optionally exposed by `domain_state` for telemetry. A domain may provide `effect_count` and `effects_since(checkpoint)`; the kernel does not interpret the returned values.

## Execution contract

A simulation step is coordinated by `SequentialStepCoordinator` across an ordered sequence of stages. Each `StageCoordinator` executes four phases:

1. **Propose.** Every process proposes against the same stage-start `SimulationState`.
2. **Resolve.** The stage resolver selects compatible proposed events.
3. **Materialize.** Every selected event is materialized before any selected event is applied.
4. **Apply.** Prepared events are applied in resolver order and committed telemetry is recorded.

Materialize-before-apply is part of the public semantics. It preserves stage simultaneity while allowing stochastic or otherwise deferred consequences to be determined only for accepted events.

## Transaction and randomness contract

The engine performs updates against transactional state copies. A `SimulationState.copy()` independently copies `domain_state` and clones the complete RNG state while sharing immutable `SimulationContext` by reference.

The simulation RNG belongs to `SimulationState`. Processes that require stochastic behavior consume `simulation_state.rng`; they should not create hidden independent generators for simulation decisions. Equal initial state, configuration, seed, and component ordering must therefore reproduce equal kernel outcomes.

A failed or discarded transaction must not advance the committed simulation state or committed RNG state.

## Process and event contract

A process:

- declares one concrete `event_type`;
- proposes zero or more events from the supplied state;
- applies events of its declared type;
- may implement `EventMaterializer` when accepted events require post-resolution materialization.

Event `step_index` is supplied by the process and validated by committed telemetry. The kernel does not rewrite process-authored event time.

Within one stage, process event types must be unique so a resolved event maps unambiguously back to its owning process.

## Resolver contract

A resolver receives the stage-start state and the complete proposed-event sequence. It decides which proposals survive conflict resolution and in what order selected events are subsequently prepared and applied.

Resolvers choose among transitions; they do not own domain mutation. Mutation of `domain_state` remains the responsibility of the process that owns the selected event.

## Effect-journal contract

Effect capture is optional. If `domain_state.effect_count` is absent or `None`, the kernel applies the event without effect capture.

When present, `effect_count` must be a nonnegative integer. The checkpoint is read immediately before each application rather than cached for the whole stage. After application, `effects_since(checkpoint)` must return a tuple. This permits a domain to expose the journal capability dynamically while keeping effects opaque to the kernel.

## Telemetry contract

`AppliedEvent` records the committed process type, event type, process-authored event step, stage index, event value, and zero or more opaque effects. `StepTelemetry` groups committed applied events for one step.

Telemetry is descriptive. Observation and telemetry consumers must not participate in conflict resolution or mutate the committed simulation state as a side effect of observation.

## Configuration and preflight contract

`SimulationSpec` is the domain-neutral compilation boundary. It validates structural runtime protocols and generic dependency declarations before constructing mutable runtime objects.

Components may declare required `Dependency` values. Compilation aggregates those requirements across the configured component graph and rejects missing capabilities before simulation runtime begins. Missing-dependency diagnostics include the configured component type that declared the requirement when provenance is available.

Domain-specific compilers may build on `SimulationSpec`, but domain-specific validation belongs above this generic preflight layer.

## Explicit non-responsibilities

The kernel does **not** define or understand:

- organisms, populations, death, birth, mating, or reproduction;
- genomes, alleles, mutation, recombination, or inheritance;
- energy, metabolism, growth, feeding, predation, or resources;
- spatial worlds, coordinates, neighborhoods, environments, or carcasses;
- fitness, selection semantics, biological lifecycle ordering, or ecological meaning.

Those concepts may be implemented by domain packages using the generic kernel contracts. Their existence must not change the meaning of `SimulationState`, `domain_state`, events, resolvers, stages, effects, or telemetry.

## Change policy

The kernel is now in maintenance mode. A kernel change should satisfy at least one of these conditions:

- a required domain behavior cannot be represented correctly through the existing contracts;
- a correctness, determinism, isolation, or diagnostics defect exists in the generic layer;
- measured evidence identifies a structural performance problem in generic orchestration;
- a public contract can be simplified without moving modeled-domain semantics into the kernel.

Convenience for one modeled domain is not sufficient justification for a kernel abstraction.

The quality gate protects this boundary with Ruff, Pyright, Import Linter, Complexipy, focused Kernel Contracts tests, full pytest with coverage, synthetic kernel and reference performance profiles, and strict MkDocs.

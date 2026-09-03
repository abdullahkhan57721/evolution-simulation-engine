# Architecture Index

This page is the human-maintained map of the Evolution Simulation Engine's
architecture. Use it to decide where to read next; it is not a replacement for
the subsystem documents themselves.

## Reading order

For a new contributor or agent, the recommended order is:

1. [`AGENTS.md`](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/AGENTS.md) for durable working rules and source-of-truth
   conventions.
2. [Current Project State](../development/current_state.md) for a concise
   orientation snapshot.
3. [Architectural Roadmap](../development/roadmap.md) for milestone-level
   direction and dependency ordering.
4. [Simulation Kernel Contract](../kernel_contract.md) for the frozen generic
   execution semantics.
5. [General Evolution Framework](../general_evolution_framework.md) for the
   domain-neutral evolutionary layer above the kernel.
6. [Architecture Guardrails](https://github.com/abdullahkhan57721/evolution-simulation-engine/blob/main/.github/ARCHITECTURE_GUARDRAILS.md) for the
   dependency directions that are mechanically enforced.
7. [Architecture Decisions](../decisions/README.md) for the rationale behind
   major settled choices.
8. The subsystem document and active GitHub Issue relevant to the current work.

The current-state and roadmap pages are navigation aids. Current `main`, tests,
CI, authoritative subsystem docs/ADRs, and active Issues/PRs remain higher-trust
sources when anything disagrees.

## Architectural layers

The project intentionally separates execution mechanics from modeled meaning:

```text
validation / context / generic foundations
                    |
                    v
             simulation kernel
                    |
                    v
         general evolution abstractions
                    |
                    v
      biological/domain specializations
                    |
                    v
        processes and resolvers
                    |
                    v
       presets / experiments / interfaces
```

This is a dependency direction, not a requirement that every package occupy a
single vertical layer. The enforceable boundaries are defined by Import Linter
contracts and focused architecture tests.

## Simulation kernel

The kernel owns transaction and orchestration semantics, not biological meaning.
Its canonical modeled-state field is `SimulationState.domain_state`.

Read:

- [Simulation Kernel Contract](../kernel_contract.md)
- `src/evo_engine/engine/`
- `src/evo_engine/configuration/`
- `src/evo_engine/telemetry/`
- `tests/engine/test_domain_neutral_kernel.py`
- `tests/engine/test_stage_coordinator.py`

Important invariant:

```text
propose all
→ resolve
→ materialize all accepted events
→ apply accepted events
```

The kernel is in maintenance mode. New biological or ecological behavior should
normally be expressed above this layer.

## General evolution layer

`evo_engine.evolution` captures concepts that make sense for evolutionary
systems without assuming DNA, chromosomes, organisms, sex, energy, age, or
spatial ecology.

Read:

- [General Evolution Framework](../general_evolution_framework.md)
- `src/evo_engine/evolution/`

Biological genetics specializes this layer rather than defining the generic
kernel's vocabulary.

## Biological and ecological domains

Domain packages own modeled meaning. Important packages include:

- `genetics` — alleles, loci, chromosomes, genomes, expression, inheritance,
  recombination, and genetic phenotype.
- `development` — developmental realization and G×E variation.
- `life_history` — reusable organism strategy abstractions.
- `growth` — potential body-mass gain policies.
- `behavior` — behavioral purpose, intent, sensing, targeting, and selection.
- `energetics` — metabolic/locomotion cost and expenditure policies.
- `feeding` — intake and assimilation physiology.
- `predation` — predation eligibility and preference policies.
- `reproduction` — reproductive eligibility and group selection, investor and
  genetic-contributor selection, reproductive energy investment, inheritance
  composition, movement adapters, offspring-production source selection/context,
  mating-type assignment, newborn body mass, and placement.
- `ecology` — reusable environmental policy, including temporal forcing and
  simulation-RNG-owned spatial resource-placement models. Renewable-resource
  quantity/cadence remains process responsibility while placement policy chooses
  where each deposit occurs.
- `spatial` — geometry, neighborhoods, distance, and boundary behavior.
- `world` — mutable biological/ecological domain state.
- `observation` — committed population/evolution measurements.

See the MkDocs navigation for subsystem-specific design notes.

## Processes, resolvers, and composition

Concrete `processes` propose and apply modeled events. `resolvers` decide which
proposed events survive conflicts. These responsibilities remain separate.

`presets` is an intentional high-level composition root and may depend on engine,
domain, process, and resolver packages to assemble complete simulations. Lower
layers must not depend back on presets.

`experiments` owns reproducible experiment-running/reporting concerns and is not
a dependency of production simulation packages.

## Configuration and context

`SimulationContext` is immutable shared configuration/service state. Domain
packages own typed `ContextKey[T]` values for the services they define. The
kernel carries context but does not assign modeled meaning to values.

`SimulationSpec` is the generic compilation/preflight boundary. Domain-specific
configuration layers may build on it and add domain validation.

## Observation and telemetry

Committed telemetry records what the kernel applied and opaque domain effects.
Observers consume authoritative committed state. Neither mechanism participates
in conflict resolution or mutates committed simulation state as a side effect of
observation.

Read:

- [Event Telemetry and Causal History](../event_telemetry.md)
- [Evolution Observability](../observability.md)

## Performance boundary

Use synthetic domain-neutral kernel benchmarks for claims about generic kernel
performance. Reference-ecology profiles intentionally remain useful integration
signals, but their timings include domain-process costs.

Read:

- [Performance Measurement](../performance.md)
- `scripts/profile_kernel.py`
- `scripts/profile_reference.py`

## Generated architecture artifacts

Machine-generated diagrams and reports live in `docs/architecture/generated/`.
Treat generated files as outputs. Modify their generator or source configuration
rather than hand-editing generated content.

## Changing architecture

Before changing a public contract or dependency direction:

1. inspect current `main`, `docs/development/current_state.md`, and the relevant
   roadmap milestone;
2. inspect the relevant existing ADRs;
3. identify which executable guardrails/tests express the current contract;
4. decide whether a new ADR is warranted;
5. update architecture documentation and tests in the same PR;
6. update `current_state.md` or `roadmap.md` if the milestone materially changes
   the orientation/direction they summarize;
7. run `./scripts/architecture` and `./scripts/kernel_contracts` in addition to
   the broader quality gate.

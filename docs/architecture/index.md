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

`DependencyReport` already provides the structured generic dependency facts needed
by lower preflight: required/provided dependencies, missing dependencies, and the
requiring component type. `SimulationSpecValidator` owns the generic raising
boundary. `BiologicalSimulationSpec` and `GeneticArchitecture` retain biological
and genetic validation authority respectively; higher product layers should not
reimplement those checks.

## Evolution Experiment Workbench

The Workbench is a scientific-study authoring layer over existing typed
composition, not an alternate simulation engine. It persists human-visible semantic
intent, immutable resolved scientific meaning, evidence intent, lineage/design
metadata, and run-to-manifest provenance, then compiles through existing preset,
scenario, and experiment builders plus the ordinary scientific/biological/generic
validation path.

Read:

- [Evolution Experiment Workbench Architecture](../evolution_experiment_workbench.md)
- [Workbench UI reference product](../workbench_ui.md)
- [Native Desktop Workbench](../desktop_workbench.md)
- [Workbench Architecture Review](../workbench_architecture_review.md)
- [WB4 Bounded Reference-Ecology Recipe](../wb4_bounded_reference_ecology.md)
- [WB5 Results and Presentation](../wb5_results_presentation.md)
- [ADR 0010 — Use PySide6 and Qt Quick for the primary Workbench frontend](../decisions/0010-use-pyside6-qt-quick-for-primary-workbench-frontend.md)
- `src/evo_engine/workbench/`
- `tests/workbench/`

WB1 established bounded controlled-locomotion authoring. WB2 pressure-tested exact
reproduction against trusted B3 and established scenario origin versus validated
scenario identity. WB3 added concrete controlled-experiment authoring. WB4 proved
the same principles scale to richer bounded reference ecology through explicit
support tiers and recipe-local applicability/normalization. WB5 integrated Results
and downstream V2/V3 presentation without duplicate science. WB6 audited the whole
implementation and moved the Workbench foundation into maintenance-and-extension
mode.

The WB6 review found one genuinely earned shared abstraction: a small
Workbench-owned diagnostic value with stable code, severity, optional semantic
slot/context, concise message, and optional remediation. It covers only Workbench-
owned support/status facts demonstrated across WB1–WB5. It does not replace lower
validation and is not a universal diagnostic framework.

The durable Workbench distinction remains:

```text
engine-valid
    ≠ Workbench-supported
    ≠ Guided
    ≠ experiment factor levels
```

Lower engine/domain/science packages must not depend on `evo_engine.workbench`.
Workbench must not depend on renderer packages. UI, desktop, and cinematic code may
consume Workbench downstream.

## Product frontends

WU1–WU5 established the complete Streamlit reference product over the settled
Workbench contracts: Home/New/Open, the persistent five-section Study shell,
semantic authoring, Evidence and concrete Experiment workflows, immutable revisions,
Run Plan/execution, family-specific Results, recorded-state world replay, and the B3
cinematic handoff. Streamlit remains a semantic compatibility frontend during native
migration.

ADR 0010 makes **PySide6 + Qt Quick/QML the primary product frontend architecture**.
The native dependency direction is:

```text
Qt Quick / QML
        ↓
curated QObject controller / Qt item models
        ↓
existing Workbench/application semantics
        ↓
experiments / presets / renderer-neutral presentation
        ↓
biology
        ↓
frozen kernel
```

QML receives intentionally exposed scalar properties, signals, slots, and item-model
roles rather than arbitrary mutable Workbench/domain object graphs. Scientific edits
must commit through existing concrete Workbench APIs, and exact persistence remains
the existing concrete Workbench formats. PySide6 is an optional downstream desktop
dependency; lower packages must not depend on `evo_engine.desktop` or PySide6.

Q0 proves the Reference Ecology vertical, GUI-thread separation for the synchronous
runner, native `WorldPresentationFrame` rendering, and standalone deployment. Q1 is
the next product milestone and should build the persistent native Study shell plus
concrete routing without inventing a universal Study schema. See
`docs/desktop_workbench.md` for the exact handoff.

## Observation and telemetry

Committed telemetry records what the kernel applied and opaque domain effects.
Observers consume authoritative committed state. Neither mechanism participates
in conflict resolution or mutates committed simulation state as a side effect of
observation.

Read:

- [Event Telemetry and Causal History](../event_telemetry.md)
- [Evolution Observability](../observability.md)

Population summaries, spatial state, selected per-individual genetic-phenotype
traits, genetic composition, events, and pedigree/life-history evidence remain
separate committed observation concerns that downstream consumers can compose.
Spatial frames are not universal presentation snapshots.

## Scientific visualization

Scientific presentation remains downstream of committed evidence. Scenario-level
scientific meaning is shared across presentation media, while concrete graphics,
interaction, camera, timing, and choreography belong to each renderer.

Read:

- [Scientific Visualization Architecture](scientific_visualization.md)
- [ADR 0009 — Separate scientific encoding from renderer choreography](../decisions/0009-separate-scientific-encoding-from-renderer-choreography.md)

The durable responsibility split is:

```text
committed scientific evidence
        ↓
scenario-specific scientific encoding
        ↓
renderer-specific primitives and choreography
```

Workbench result/presentation integration follows the same rule. Missing evidence
can produce structured Workbench remediation, but Streamlit/QML/cinematic code must
never reconstruct scientific events, genetics, pedigree, or spatial history that
were not recorded.

Do not put renderer metadata into modeled entities or committed scientific records,
and do not introduce a universal scene/replay abstraction merely because multiple
renderers share a conceptual visual vocabulary.

## Performance boundary

Use synthetic domain-neutral kernel benchmarks for claims about generic kernel
performance. Reference-ecology profiles intentionally remain useful integration
signals, but their timings include domain-process costs.

WB6 found no measured Workbench bottleneck requiring optimization. Spatial replay
already carries a bounded evidence-volume advisory; do not optimize Workbench,
desktop rendering, or kernel behavior speculatively.

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
7. follow `docs/development/validation_workflow.md`: focused checks and
   `./scripts/fix` while iterating, the fast checkpoint for ordinary draft work, and
   the complete local/non-draft gate only for a functionally complete merge
   candidate; add architecture/kernel checks when the changed boundary requires them.

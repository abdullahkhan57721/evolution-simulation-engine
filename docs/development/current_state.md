# Current Project State

This page is a concise orientation snapshot for contributors and AI agents. It
answers **where the project is now** without replacing live repository state.

## Authority and staleness boundary

When anything here disagrees with the repository, use this order:

1. current `main`, tests, and CI;
2. root `AGENTS.md`;
3. authoritative architecture/subsystem documentation and ADRs;
4. active GitHub Issues and PR recovery checkpoints;
5. this orientation snapshot;
6. conversation history.

Do not store volatile commit SHAs, CI run status, detailed ticket progress, or a
full PR history here.

## v0.1.0 baseline

The repository is organized around a **v0.1.0 portfolio baseline**: a stable
simulation architecture plus one reproducible end-to-end evolutionary
demonstration and two downstream presentation paths.

The architectural direction is:

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

Presentation is separately downstream:

```text
simulation/domain layers
        |
        v
committed scientific evidence
        |
        +-------------------------+
        |                         |
        v                         v
interactive presentation     cinematic presentation
```

Neither presentation path is a second simulation architecture.

## Settled architectural capabilities

### Frozen domain-neutral kernel

The simulation kernel is complete for the current architecture and is in
maintenance mode. It owns generic deterministic execution rather than modeled
biology. Durable semantics include:

- opaque `SimulationState.domain_state`;
- immutable `SimulationContext`;
- transactional model-state and RNG copying/commit behavior;
- stage-start proposal simultaneity;
- propose → resolve → materialize-all-accepted → apply ordering;
- resolver selection without domain mutation;
- committed event/effect telemetry;
- generic `SimulationSpec` structural/dependency preflight.

New modeled behavior normally belongs above the kernel unless a genuine generic
kernel deficiency is demonstrated.

### General evolution layer

The domain-neutral evolution layer covers transmissible-state expression,
variation, linkage/co-transmission, propagation, entity production,
access/reference, and admission/departure without assuming organisms, DNA,
chromosomes, sex, energy, or ecology.

`transmissible state` is the canonical general term. Biological genomes and
inheritance specialize that layer rather than redefining the kernel vocabulary.
The nonbiological vertical slice remains the executable proof that these contracts
work outside biological simulation objects.

### Biological specialization

The biological stack composes genetics, inheritance, development, life history,
growth, energetics, feeding, behavior, movement, predation, reproduction, spatial
ecology, and biological world state above the generic layers.

Shared reproduction orchestration is arity-neutral. It distinguishes:

- reproductive **participants** used for mating and resolver conflicts;
- reproductive **investors** whose committed energy determines affordability;
- genetic **contributors** whose transmissible states feed inheritance; and
- offspring-production **sources** supplied as biological production context.

Concrete clonal and current sexual inheritance policies retain their own stronger
source-count requirements. Pedigree genetic parentage follows genetic contributors,
not every participant or production source.

Chromosome transmission also has an explicit responsibility split:

```text
Genome
  |
  v
GenomeStructure + GeneticArchitecture validation
  |
  v
ChromosomePairingModel
  |
  v
ChromosomeAssociation(s)
  |
  v
RecombinationModel
  |
  v
ChromosomeSegregationModel
  |
  v
Gamete
```

`Genome` remains permissive inherited-state data. `GenomeStructure` supplies
chromosome-specific copy expectations without a foundational organism-wide
`ploidy` scalar. Pairing chooses temporary associations, recombination operates
inside those associations, and segregation determines transmitted copies. Current
built-in policies intentionally preserve simple singleton/diploid Mendelian
behavior; richer higher-copy biology should be added as explicit policies against
these settled interfaces.

Spatial resource generation has an explicit ecological responsibility split:

```text
ResourceGeneration
    | quantity / cadence
    v
ResourcePlacementModel
    | coordinate choice using SimulationState.rng
    v
ResourceGeneration.Event
    |
    v
WorldState.add_resources()
```

Uniform placement preserves the ordinary baseline and historical RNG draw order.
Patchy placement adds static weighted circular resource regions with world-bounded
grid sampling. Placement models are immutable ecological configuration; resource
mutation remains owned by `WorldState`, and committed spatial observations reveal
the resulting real resource geography without renderer metadata.

The existing reference biology also has an evidence-backed heritable performance
tradeoff at `max_speed`. Balanced founder standing variation can be constructed for
an existing reference integer trait. Under the ordinary reference mechanisms,
higher realized speed reaches farther toward the same target but the speed-4
background incurs one additional maintenance-energy unit per timestep relative to
speed 1. Existing sexual inheritance transmits the speed variants. This establishes
a concrete benefit/cost axis without adding a generic strategy or scalar-fitness
abstraction; integrated long-run environment-dependent selection remains a
scenario/experiment concern above these mechanisms.

### Reproducibility, observation, and experiments

Committed evidence is a first-class architectural layer. The repository includes:

- population/evolution observations;
- immutable spatial observations;
- selective per-organism genetic-phenotype integer-trait observations;
- allele and genotype composition records;
- pedigree and lifetime reproductive-contribution records;
- committed causal event/effect telemetry;
- deterministic seeded execution;
- exact checkpoint/resume;
- reproducible multi-seed experiments;
- JSON and CSV experiment export.

`IndividualGeneticTraitRecorder` is opt-in and records only explicitly selected
integer genetic-phenotype traits for active organisms. It remains separate from
`SpatialObservation`, allowing downstream presentation to join scientific values
to spatial replay through committed `(step_index, organism_id)` identity without
recording full genomes or renderer metadata.

Observers receive only authoritative committed states. Presentation code consumes
immutable completed values rather than retaining a live mutable simulation owner.

### Scientific visualization boundary

Scientific presentation follows a durable three-layer responsibility split:

```text
committed scientific evidence
        |
        v
scenario-specific scientific encoding
        |
        v
renderer-specific primitives and choreography
```

Visual primitives are a shared conceptual vocabulary, not a universal runtime
scene graph. Scenario-specific encoding determines what scientific variables and
comparisons mean visually without containing CSS, Plotly traces, Blender materials,
camera timing, or other renderer implementation. Interactive and cinematic media
independently own interaction, layout, camera, timing, interpolation, and
storytelling.

The first concrete cross-renderer scientific encoding is intentionally small:
`ContinuousTraitEncoding` stores only a committed trait name, human-readable label,
and fixed numeric bounds/normalization. It contains no renderer color, material,
widget, camera, timing, easing, or scene-order configuration.

The cinematic preparation path joins committed spatial and optional per-organism
trait evidence by `(step_index, organism_id)` and attaches committed `StepTelemetry`
separately. Identity appearance/departure remains renderer continuity metadata, not
birth/death evidence. Cinematic event selection therefore uses actual committed
`AppliedEvent` values in commit order. Presentation interpolation preserves exact
committed endpoints but is never scientific evidence.

Presentation interpolation is never scientific evidence. Configuration context,
committed state, committed events, derived statistics, interpolation, and authored
annotations remain conceptually distinct. A broad shared scenario-presentation
schema should be introduced only after repeated concrete consumers establish the
fields that genuinely repeat.

### Portfolio interfaces

`evo_engine.ui` remains the current optional top-level Streamlit/Plotly consumer.
Its application flow separates full-window configuration from a completed-run,
world-centered workspace. Session state owns immutable `DashboardRun` values plus
view/navigation state rather than live simulation objects. The generic interactive
world has first-class committed-step selection, scrub/previous/next/playback
controls, view-only resource/carcass/trail/label controls, stable neutral organism
encoding, body-mass sizing, selection through a reserved outline channel, and an
authoritative selected-organism inspector. Recent movement trails and optional
position interpolation are presentation-derived from committed spatial history and
never become scientific or exported values. Existing evolutionary/genetic
analytics, life-history views, experiment comparison, and export remain downstream
of the same completed evidence.

`evo_engine.cinematic` remains the current optional sibling Manim consumer. Its
`PortfolioAnimationTimeline` is renderer-owned presentation ordering over committed
`SpatialObservation`, `PopulationObservation`, optional
`IndividualGeneticTraitObservation`, and committed event telemetry values, not a
generic replay contract. Prepared organism primitives contain immutable copied
scientific values rather than live domain objects. Generic mode remains available
without a focal encoding; a focal view can bind one committed continuous trait to
organism fill with an explicit legend while secondary categories do not reuse that
channel. Rendering occurs only after simulation completion and the heavy Manim
dependency remains outside the core/default runtime.

The cinematic package also provides presentation-only endpoint-preserving position
interpolation, authoritative event selection, and scalar reproducibility metadata.
These are renderer-side capabilities, not modeled dynamics or a general film DSL.
A B3-specific cinematic director remains separate and should consume the final
renderer-neutral scenario storyboard rather than manufacture scientific episodes.

The next presentation generation may replace renderer implementations, but it must
preserve the committed-evidence and scientific-encoding boundaries rather than
moving visualization semantics into the simulation.

### Flagship evolutionary demonstration

The v0.1 flagship is a thin composition above the ordinary reference ecology, not
a separate model architecture. It starts with balanced standing variation at the
existing `max_intake_rate` locus, isolates mutation and predation for causal
clarity, and reuses the existing ecology, genetics, reproduction, observation,
experiment, dashboard, and cinematic paths.

The canonical fixed-seed run uses seed `41` for `40` steps. The canonical
robustness set is:

```text
11, 23, 37, 41, 59, 73, 89, 101
```

The protected tests assert qualitative evidence: all canonical runs remain alive
through the demonstration window and finish with the high-intake allele above its
initial `0.50` frequency. The scenario is illustrative and not empirically
calibrated.

## Release and quality posture

The v0.1.0 release surface includes a reviewer-oriented README, public MkDocs/GitHub
Pages documentation, an MIT license, package release metadata, documented clean
Python 3.12 installation, optional UI and Manim dependency paths, the flagship
scenario, experiments/export, and protected CI.

The repository quality gate includes Ruff, Pyright, Import Linter architecture
contracts, kernel-contract regressions, Complexipy, pytest with coverage, strict
MkDocs, reference/kernel performance checks, and a stable protected aggregate
status. Headless Streamlit interaction tests exercise the real dashboard path.
Manim has a separate real render/decode smoke workflow that covers both the generic
cinematic path and a short science-aware B1/B2 focal-evidence path without making a
full portfolio film part of routine CI.

## Current development front

Post-v0.1 development has **two coordinated parallel fronts**:

1. **modeled-domain/scenario enrichment** — compose the now-available static
   resource heterogeneity and heritable speed performance/cost mechanisms into a
   robust environment-dependent selection scenario without changing the frozen
   kernel; and
2. **presentation refinement** — build world-centered interactive and cinematic
   experiences above committed evidence while sharing scientific meaning rather
   than renderer mechanics.

The immediate integration question is no longer whether patchy resources, a
heritable performance tradeoff, a generic interactive world, or renderer-neutral
focal-trait cinematic replay exist: all now have concrete implementations and
evidence. B3 scenario discovery must still determine the simplest robust causal
demonstration and provide its durable scientific storyboard. The interactive front
can proceed from generic world primitives toward scenario-specific scientific
encoding, legends/accessibility, matched comparison, and deeper analysis while
consuming the selective per-organism trait observation seam. The cinematic front
now has science-aware committed-evidence preparation/rendering and should consume
B3's final scientific meaning rather than infer or invent it. The two media remain
sibling renderer concerns rather than one shared scene runtime.

Other longer-term modeled fronts remain:

1. richer genetic expression;
2. richer chromosome pairing/recombination against the explicit transmission
   interfaces;
3. richer mating systems using the existing participant/investor/contributor/
   production-source separation;
4. richer development and G×E;
5. richer evolutionary ecology that exercises those capabilities.

Presentation work may run concurrently with these fronts, but it must not define
or distort ecological semantics for renderer convenience. Shared-data gaps should
be solved at the appropriate domain/observation layer first.

A native Rust/C++ execution backend remains a separate, evidence-driven future
front. Python should continue to own high-level modeling/configuration until a
measured workload demonstrates the need for a compiled execution plan/backend.
Do not speculate a backend contract into the kernel merely for future possibility.

See `docs/development/roadmap.md` for milestone-level sequencing.

## Known architectural friction

### Built-in chromosome transmission is intentionally conservative

The public chromosome-copy/pairing/recombination/segregation responsibilities are
explicit, but production policies model only current simple needs.
`SameNameBivalentPairing` rejects same-name groups larger than two and current
single-crossover support is limited to the supported singleton/two-copy
associations.

This is a capability limitation of concrete policies, not a structural ambiguity
in `Genome` or `GeneticArchitecture`.

### Scientific scope remains intentionally illustrative

The reference ecology is an integration baseline, and the current flagship
scenario is an evidence-backed software demonstration. Neither should be described
as a species-calibrated or predictive ecological model without future empirical
work.

## Collaboration model

Use ChatGPT Chat primarily for architecture, roadmap sequencing, consequential
public-contract decisions, tightly scoped sequential implementation, and
independent PR review/merge decisions.

Use Codex selectively for execution-heavy work behind settled interfaces: broad
mechanical migrations, analogous test expansion, validation/debug cycles, or
independently parallelizable repository iteration.

Do not delegate merely because a milestone is substantial. Optimize for total
cycle time, architectural correctness, recoverability, and user attention.

## Recent significant milestones

Newest first; this is a capability summary, not a changelog.

- **Science-aware cinematic foundation:** joined committed spatial, selective
  per-organism focal-trait, and event evidence into deterministic cinematic
  preparation; added a minimal shared continuous-trait encoding, authoritative
  event selection, presentation-only interpolation, reproducibility metadata, and
  generic/focal Manim rendering without live simulation ownership.
- **Interactive world presentation foundation:** established immutable UI-only
  world primitives over committed spatial evidence, first-class committed-step
  playback/scrubbing, view-only environmental layers and movement trails, stable
  generic visual channels, selection/inspection semantics, and display-only
  position interpolation without creating a shared cinematic scene runtime.
- **Scientific visualization evidence boundary:** added selective committed
  per-organism genetic-phenotype trait observation and formalized the separation
  among scientific evidence, scenario-specific visual meaning, and renderer-owned
  primitives/choreography.
- **Spatial resource landscapes:** separated renewable-resource generation amount
  and cadence from immutable ecology-owned placement, preserving exact uniform
  default RNG behavior while adding opt-in static weighted patch placement that is
  naturally visible through committed spatial observations.
- **Heritable speed tradeoff:** added reusable balanced standing variation for
  existing reference integer traits and verified `max_speed` as an inherited
  benefit/cost axis using existing movement, maintenance, and inheritance
  mechanisms.
- **v0.1 portfolio baseline:** integrated release-facing documentation,
  installation/release metadata, dashboard, experiments/export, cinematic replay,
  flagship demonstration, and protected verification into one reviewer-facing
  release surface.
- **Flagship demonstration:** added the balanced standing-variation
  `max_intake_rate` scenario, canonical fixed/multi-seed helpers, dashboard route,
  and cinematic input used for the portfolio story.
- **Renderer-neutral cinematic proof:** added optional Manim rendering directly
  from committed spatial/population observations.
- **Adaptive portfolio configuration:** made real supported mutation/recombination
  choices conditional while preserving typed configuration and explicit run
  semantics.
- **Portfolio observation/interface stack:** added immutable committed spatial
  history and a Streamlit/Plotly dashboard above existing observation/experiment
  contracts.
- **Chromosome-transmission foundation:** separated chromosome structure, pairing,
  recombination eligibility, and segregation while preserving current Mendelian
  behavior and demonstrating higher-copy architectural extensibility.
- **Reproduction boundary hardening:** separated participants, investors, genetic
  contributors, and production sources and removed universal one/two-participant
  assumptions from shared orchestration.
- **General-evolution normalization:** established transmissible-state terminology
  and a nonbiological vertical proof above the frozen kernel.
- **Frozen kernel/collaboration hardening:** documented kernel maintenance rules,
  architecture guardrails, ADRs, Issues/PR recovery checkpoints, and repository-
  native collaboration memory.

Use Git history and merged PRs for exact implementation details.

## Where to read next

For a fresh session:

1. `AGENTS.md` — durable working rules and source-of-truth hierarchy.
2. This file — concise current orientation.
3. `docs/development/roadmap.md` — rolling milestone direction.
4. `docs/architecture/index.md` — subsystem map and reading order.
5. `docs/architecture/scientific_visualization.md` for the presentation truth and
   responsibility model.
6. `docs/kernel_contract.md` and `docs/general_evolution_framework.md` — core
   contracts.
7. Relevant ADRs in `docs/decisions/`.
8. The active GitHub Issue and PR for exact live work.

## Maintenance rule

Update this file only when a merged milestone materially changes architectural
capability, the current development front, a major public contract, known
architectural friction, collaboration policy, or the small set of recent
milestones needed for orientation. Do not turn it into a changelog or CI ledger.

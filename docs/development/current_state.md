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

The repository is now organized around a **v0.1.0 portfolio baseline**: a stable
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

The presentation direction is separately downstream:

```text
simulation/domain layers
        |
        v
committed observation / experiment values
        |
        +-------------------------+
        |                         |
        v                         v
Streamlit / Plotly             Manim
interactive exploration       cinematic replay
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

### Reproducibility, observation, and experiments

Committed evidence is a first-class architectural layer. The repository includes:

- population/evolution observations;
- immutable spatial observations;
- allele and genotype composition records;
- pedigree and lifetime reproductive-contribution records;
- committed causal event/effect telemetry;
- deterministic seeded execution;
- exact checkpoint/resume;
- reproducible multi-seed experiments;
- JSON and CSV experiment export.

Observers receive only authoritative committed states. Presentation code consumes
immutable completed values rather than retaining a live mutable simulation owner.

### Portfolio interfaces

`evo_engine.ui` is an optional top-level Streamlit/Plotly consumer. It provides
curated typed reference-ecology configuration, conditional mutation/recombination
controls, spatial playback, evolutionary/genetic analytics, event/life-history
views, experiment comparison, and export. Hidden UI state is not implicit engine
configuration; selected values normalize into typed configuration before execution.

`evo_engine.cinematic` is an optional sibling Manim consumer. Its
`PortfolioAnimationTimeline` is renderer-owned ordering/interpolation state over
committed `SpatialObservation` and `PopulationObservation` values, not a generic
replay contract. Rendering occurs only after simulation completion and the heavy
Manim dependency remains outside the core/default runtime.

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
Manim has a separate real render/decode smoke workflow so the heavy renderer does
not become a core dependency.

## Current development front

The portfolio architecture is no longer the development frontier. **Post-v0.1
work should return to modeled-domain capability only when a concrete use case
justifies it.**

Likely fronts are:

1. richer genetic expression;
2. richer chromosome pairing/recombination against the explicit transmission
   interfaces;
3. richer mating systems using the existing participant/investor/contributor/
   production-source separation;
4. richer development and G×E;
5. richer evolutionary ecology that exercises those capabilities.

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

The reference ecology is an integration baseline, and the flagship scenario is an
evidence-backed software demonstration. Neither should be described as a
species-calibrated or predictive ecological model without future empirical work.

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
5. `docs/kernel_contract.md` and `docs/general_evolution_framework.md` — core
   contracts.
6. Relevant ADRs in `docs/decisions/`.
7. The active GitHub Issue and PR for exact live work.

## Maintenance rule

Update this file only when a merged milestone materially changes architectural
capability, the current development front, a major public contract, known
architectural friction, collaboration policy, or the small set of recent
milestones needed for orientation. Do not turn it into a changelog or CI ledger.

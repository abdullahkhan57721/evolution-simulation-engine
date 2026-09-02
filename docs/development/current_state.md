# Current Project State

This page is a concise orientation snapshot for contributors and AI agents. It
answers **where the project is now** without replacing live repository state.

## Authority and staleness boundary

This document is intentionally subordinate to executable and authoritative
sources. When anything here disagrees with the repository, use this order:

1. current `main`, tests, and CI;
2. root `AGENTS.md`;
3. authoritative architecture/subsystem documentation and ADRs;
4. active GitHub Issues and PR recovery checkpoints;
5. this orientation snapshot;
6. conversation history.

Do not store volatile commit SHAs, CI run status, detailed ticket progress, or a
full PR history here. Verify those directly in GitHub.

## What the engine is now

The Evolution Simulation Engine is a layered Python simulation system whose
execution kernel is domain-neutral and whose evolutionary and biological meaning
lives above that kernel.

The architectural shape is:

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

The kernel owns deterministic transactional execution, stage coordination,
committed telemetry, and generic preflight. It does not own organisms, genomes,
reproduction, energy, ecology, or other modeled-domain semantics.

## Established architectural capabilities

### Frozen simulation kernel

The simulation kernel is complete for the current architecture and is in
maintenance mode. Its durable semantics include:

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

### General evolutionary foundations

The project has domain-neutral foundations for:

- evolving entities as an architectural concept and small capability contracts;
- transmissible-state expression;
- variation;
- linkage and co-transmission structure;
- source-state/recipient propagation;
- entity production;
- entity access/reference;
- admission/departure and generic conflict/effect foundations.

`transmissible state` is the canonical general-evolution term for information
that may be expressed, varied, or propagated. `TransmissibleStateExpression`
models expression, while `TransmissibleStateCarrier` and `PropagationModel`
model the independent carrier/propagation capabilities. The former redundant
`EvolutionaryEntity.heritable_state` contract is intentionally removed; see ADR
0007.

Propagation is broader than biological inheritance: it accepts zero or more
source states, a separately modeled recipient, immutable propagation
configuration/context, and the simulation-owned RNG.

### Biological specialization

Biological packages specialize the generic layers rather than defining kernel
vocabulary. Existing capabilities include genomes and genetic architecture,
inheritance, mutation/recombination, sexual inheritance, development, organism
production, lifecycle behavior, energetics, feeding, movement, predation,
reproduction, spatial ecology, and biological world state.

Biology keeps its domain-native terms where they carry stronger semantics:
`Organism.genome` is also exposed through the generic `transmissible_state`
carrier capability, while inheritance remains the biological specialization of
general propagation.

The design should remain extensible toward richer genetics, dominance and other
non-additive expression, ploidy variation, chromosome-specific recombination,
richer mating systems, and variable reproductive contributors.

### Observation, experiments, and reproducibility

The repository includes committed telemetry and observation layers for population
and evolutionary state, causal event history, pedigree/lifetime contribution,
genetic composition, reproducible experiments/export, and exact checkpoint/resume
behavior.

### Performance and quality boundaries

Kernel performance work is evidence-driven and uses domain-neutral synthetic
benchmarks. Reference-ecology profiles remain integration signals but do not
substitute for kernel-specific evidence. Readability and semantic correctness are
hard constraints on performance changes.

The repository quality gate includes Ruff, Pyright, Import Linter/architecture
checks, kernel-contract regressions, Complexipy, pytest/coverage, reference and
kernel performance checks, strict MkDocs, and a stable final aggregator status.

## Most recent architectural proof

Issue #84 / PR #85 added a deterministic nonbiological information-propagation
vertical slice through the real `SimulationSpec` and frozen kernel.

That proof demonstrates:

```text
transmissible strategy token
        |
        v
expressed operative characteristic
        |
        v
differential propagation
        |
        v
source/recipient propagation + RNG variation
        |
        v
committed token replacement
        |
        v
changed transmissible-state composition
```

The example uses no biological `Organism`, `Genome`, biological world, genetics,
or reproduction implementation. This is executable evidence that the general
evolution architecture is genuinely usable outside biology.

Issue #86 / PR #90 then used that evidence to normalize the remaining generic
expression vocabulary around transmissible state without changing the example's
behavior or the propagation/kernel semantics.

## Current development front

The next architectural front is **biological specialization hardening**.

With the generic transmissible-state vocabulary settled, the next milestone
should audit the biological genetics/reproduction path against those contracts
before substantially richer genetics or reproduction behavior is added. The goal
is to remove accidental specialization mismatches, not to rewrite working
biology.

A dedicated implementation Issue should be scoped against current `main` before
that milestone begins. See `docs/development/roadmap.md` for the milestone-level
direction.

## Known architectural friction

### General evolution versus biological specialization

The generic layer is now proven outside biology and its transmissible-state
terminology is settled. Biology should be rechecked against those contracts
before adding substantially richer genetics/reproduction behavior. This is a
specialization-hardening step, not a rewrite of the mature biological model.

## Current collaboration model

ChatGPT Chat is the default place for:

- architecture and consequential design decisions;
- architecture-heavy or tightly scoped sequential implementation;
- public-contract decisions;
- small refactors where conversation context materially improves correctness;
- independent PR architecture review and merge decisions.

Codex is used selectively for work that is primarily execution-heavy, repetitive,
large-scale, migration-oriented, validation-intensive, independently
parallelizable, or otherwise benefits from unattended repository iteration behind
settled interfaces.

Do not delegate to Codex merely because a ticket is substantial. Optimize for
total cycle time to a correct merged change.

## Recent significant milestones

Newest first; this is a milestone summary, not a changelog.

- **#86 / #90 — transmissible-state terminology normalization:** made
  `transmissible state` the single generic expression/variation/propagation
  vocabulary, removed the redundant evolving-entity carrier Protocol, and kept
  biological inheritance terminology as a specialization.
- **#84 / #85 — nonbiological evolution proof:** demonstrated genuine evolution
  through generic contracts without biological simulation objects and supplied
  the evidence used by #86.
- **#81 / #83 — collaboration workflow hardening:** made Issues, PR recovery
  checkpoints, manual verification, and repository-native agent handoff more
  explicit.
- **#77 / #78 — repository as durable collaboration memory:** added `AGENTS.md`,
  architecture index, ADR structure, Issue/PR templates, and focused kernel
  contract verification.
- **#75 / #76 — frozen kernel contract:** documented and mechanically hardened the
  domain-neutral kernel boundary and maintenance policy.
- **#74 — kernel nomenclature/readability:** completed the public move from generic
  `world` vocabulary to `domain_state` and clarified the execution algorithm.
- **#41–#52 — domain-neutral configuration/evolution lifecycle foundations:**
  generalized configuration/context and separated propagation, production,
  admission/departure, access/reference, conflicts, and committed effects from
  biological assumptions.

Use Git history and merged PRs for exact implementation details.

## Where to read next

For a fresh session, use this sequence:

1. `AGENTS.md` — durable working rules and source-of-truth hierarchy.
2. This file — concise current orientation.
3. `docs/development/roadmap.md` — rolling milestone-level direction.
4. `docs/architecture/index.md` — architecture map and subsystem reading order.
5. `docs/kernel_contract.md` and `docs/general_evolution_framework.md` — core
   execution/evolution contracts.
6. Relevant ADRs in `docs/decisions/` — why settled choices exist.
7. The active GitHub Issue and PR — exact live scope, status, and recovery state.

## Maintenance rule

Update this file when a merged milestone materially changes one or more of:

- architectural capability;
- current development front;
- an important public contract;
- known architectural friction;
- collaboration/delegation policy;
- the set of recent milestones needed to orient a fresh contributor.

Do not update it for trivial bug fixes, mechanical maintenance, every PR, current
SHAs, transient CI state, or detailed ticket progress. Keep it concise enough to
read in a few minutes.

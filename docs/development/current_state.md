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

## Architectural baseline

The repository is organized around a frozen domain-neutral transactional kernel
with general-evolution and biological specialization above it:

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

The kernel is in maintenance mode. It owns generic deterministic transactional
execution, not organisms, genomes, ecology, reproduction, or presentation. New
modeled behavior normally belongs above it unless a genuine generic deficiency is
demonstrated.

Presentation remains separately downstream:

```text
committed scientific evidence
        |
        v
scenario-specific scientific meaning
        |
        +-------------------------+
        |                         |
        v                         v
interactive presentation     cinematic presentation
```

Neither presentation path is a second simulation architecture.

## Settled modeling capabilities

### General evolution and biological specialization

The general-evolution layer models transmissible state, expression, variation,
linkage/co-transmission, propagation, entity production, access/reference, and
admission/departure without assuming biology. The biological stack composes
concrete genetics, inheritance, development, life history, growth, energetics,
feeding, behavior, movement, predation, reproduction, spatial ecology, and
biological world state above those generic contracts.

Shared reproduction distinguishes reproductive participants, investors, genetic
contributors, and production sources. Chromosome transmission separately models
structure, pairing, recombination, segregation, and gamete formation. Current
simple diploid/Mendelian policies are concrete policies rather than universal
architecture rules, preserving room for richer ploidy, recombination, mating, and
inheritance systems.

### Spatial ecology and heritable performance

B1 separated renewable-resource quantity/cadence from immutable ecological
placement policy. Uniform placement remains the ordinary baseline; static weighted
circular patches provide explicit spatial resource heterogeneity while preserving
world-state ownership and simulation-owned RNG.

B2 established existing `max_speed` as a real inherited performance/cost axis in
the richer reference biology. Higher capacity can produce farther realized
movement, while the reference physiological-maintenance model can impose a higher
ongoing energetic cost. Existing inheritance transmits the standing variation. No
generic strategy or scalar-fitness abstraction was introduced.

## Scientific evidence and experiment semantics

Committed evidence is a first-class layer. Available evidence includes population
observations, spatial observations, selective per-organism genetic-phenotype trait
records, allele/genotype composition, pedigree/reproductive contribution, causal
event/effect telemetry, deterministic seeded execution, exact checkpoint/resume,
and reproducible multi-seed experiment export.

`IndividualGeneticTraitRecorder` remains opt-in and separate from spatial replay,
allowing scientific consumers to join committed trait values by
`(step_index, organism_id)` without broadening presentation snapshots.

E1 established the experimental-science boundary:

```text
modeled system
        ↓
committed state / committed events
        ↓
pure scientific measurement
        ↓
replicate outcome
        ↓
treatment comparison
        ↓
reporting / presentation
```

One simulation run/seed is the experimental replicate; organisms within a run are
not independent replicates. Event step `t` aligns to committed state `t + 1`.
Denominators, right-censoring, extinction, discovery versus confirmation, and
representative-run roles remain explicit. `ScientificRunProvenance` carries
scientific treatment identity, and concrete experiments may audit their one
declared treatment difference without a generic configuration-diff language.

E1's first concrete measurement consumer derives attempted displacement, realized
displacement, and locomotion-energy expenditure from authoritative applied movement
evidence. Simulation/domain packages remain independent of the experiment-analysis
layer, and no universal metric/statistics framework has been introduced.

## Controlled experimental-evolution sequence

E1–E4 now form a completed causal proof sequence above the frozen kernel and
separate from the richer reference ecology.

```text
E1 measurement semantics and reproducibility
        ↓
E2 minimal controlled locomotion mechanics
        ↓
E3 monomorphic ecological-performance landscape
        ↓
E4 selection on standing inherited variation
```

### E2 — controlled clonal locomotion mechanics

E2 provides a deliberately minimal one-locus `max_speed` composition using existing
`SingleParent`, `ClonalInheritance`, and `NoMutation` contracts with fixed nonfocal
biology, perfect full-world resource sensing, deterministic nearest-resource
targeting, endpoint feeding, seed-randomized scarce-resource allocation, and
power-law locomotion-use cost.

The controlled baseline omits mate search, predation, metabolic maintenance,
growth, aging, renewable generation, and `max_speed` maintenance cost. Focused
real-simulation assays validate capacity-limited target-directed movement, no
target overshoot, quadratic distance cost in the canonical configuration,
stationary behavior after depletion, exact clonal propagation, edge-neutral
canonical geometry, and known integer-grid bearing anisotropy.

`max_speed` remains inherited/operative maximum movement capacity, not actual
realized displacement. E2 itself makes no adaptation claim.

### E3 — confirmed ecological-performance landscape

E3 disables focal evolution and measures the causal ladder from monomorphic
`max_speed` through committed movement, locomotion expenditure, resource
acquisition, population energy, and fixed-horizon reproduction/survival.

The frozen speed grid is `1..10`. Two matched environments hold total initial
resources and nonfocal biology fixed:

- a local-resource null requiring no travel;
- an axis-aligned separated-resource corridor requiring repeated travel.

Independent confirmation shows the local arm is exactly speed-neutral, while the
corridor has an interior performance maximum at `max_speed = 3`. A bounded
zero-locomotion-cost sensitivity removes the high-speed penalty, supporting the
mechanism that locomotor capacity creates resource-access benefit while quadratic
locomotion-use expenditure creates the canonical high-speed cost.

E3 freezes the directional standing-variation prediction consumed by E4. See
`docs/e3_ecological_performance.md`.

### E4 — confirmed standing-variation selection

E4 introduces known inherited speeds `1`, `3`, and `9` at equal initial frequency
with mutation still off. All founders are co-located, removing strategy-specific
founder position. Because E2 assigns founder IDs in caller order, E4 cycles three
predeclared speed-to-founder-ID assignments across seeds and separately checks a
reversed founder order.

The primary evidence is the complete committed focal composition through time, not
a population mean. Strategy-specific movement, locomotion expenditure, resource
acquisition, and reproduction remain separate mechanism evidence. One run/seed is
the replicate.

The canonical design was frozen after a six-seed discovery phase without biological
or scenario tuning. Independent confirmation then used nine disjoint seeds.

Results are exact across confirmation replicates:

- **local resource:** every run starts at `(1/3, 1/3, 1/3)` and finishes at
  `(1/3, 1/3, 1/3)`; each strategy produces three births;
- **separated corridor:** every run finishes at `(1/6, 2/3, 1/6)`; speed 3 alone
  produces three births while speeds 1 and 9 produce none.

Thus the corridor changes speed-3 frequency by `+1/3`, while speeds 1 and 9 each
change by `-1/6`. The local arm has zero focal frequency change. The bounded
canonical-versus-reversed founder-order sanity check produces identical focal and
mechanism outcomes on all tested seeds.

E4 therefore supports E3's independently frozen prediction: under this controlled
finite-horizon ecology, the separated corridor selects for the intermediate
speed-3 strategy while the local-resource environment is frequency-neutral.
Mutation is off, so this is selection on standing variation rather than de novo
mutation-driven adaptation. The result is not a universal optimum or long-run
fixation claim. See `docs/e4_standing_variation.md`.

## Confirmed B3 scientific flagship

B3 remains the richer integrated reference-ecology flagship and is not replaced or
reinterpreted by E2–E4.

Its central matched question is whether compact spatial resource geography changes
selection on existing heritable `max_speed` standing variation relative to a
uniform-resource environment in the ordinary sexual reference ecology.

The frozen comparison uses 20 balanced homozygous `max_speed = 1` / `4` founders,
mutation disabled, ordinary sexual inheritance, mating radius 3, 50 committed
steps, and identical ecology except resource placement. Independent confirmation
shows a positive compact-minus-uniform high-speed allele-frequency effect at the
predeclared step-30 readout in all eight matched seeds, with founder reproductive
success supporting the demographic mechanism. Radius sensitivity and founder-label
counterbalancing bound the interpretation.

The representative storytelling run and real committed explanatory episodes are
recorded in `docs/flagship_evolution_demo.md`.

The B3 claim is environment-dependent and specific to its tested reference ecology.
It should not be generalized to universal optimal speed, generic patchiness, or
species-calibrated prediction.

## Scientific visualization boundary

The shared scientific-presentation layer remains deliberately small.
`ContinuousTraitEncoding` stores a committed trait name, human-readable label, and
fixed numeric scale only. It contains no renderer color, material, widget, camera,
timing, easing, or scene-order configuration.

The interactive application owns view state and presentation of completed committed
runs. The cinematic package prepares renderer-owned timelines from committed
spatial, population, focal-trait, and event evidence. Presentation interpolation is
never scientific evidence.

V2 and V3 should consume the B3 scientific handoff rather than independently invent
its treatment/control semantics.

## Current development front

The planned E1→E4 controlled-science sequence is complete. It now provides a clean
causal chain from mechanics to ecological performance to environment-dependent
selection on inherited standing variation, alongside the richer independently
confirmed B3 flagship.

There is **no repository-defined E5 milestone** at this point. Do not invent one in
implementation chats. The next controlled-science or architecture milestone should
be chosen through roadmap reassessment and an explicit Issue if/when a concrete
scientific or architectural question earns it.

Independent work can continue on the already-settled presentation track:

```text
confirmed B3 scientific evidence/storyboard
        |
        +-------------------------+
        |                         |
        v                         v
interactive B3 comparison     cinematic B3 director
(V2 continuation)             (V3 continuation)
```

Longer-term modeled fronts remain richer genetic expression, chromosome
pairing/recombination, mating systems, development/G×E, and evolutionary ecology.
Those directions are not implied E5 work; sequence them only after a concrete
question and dependency analysis.

A native Rust/C++ backend remains a separate evidence-driven future concern. Python
continues to own high-level modeling/configuration until measured workloads justify
a compiled execution plan/backend.

See `docs/development/roadmap.md` for milestone-level direction.

## Known architectural friction

### Built-in chromosome transmission remains intentionally conservative

The public copy-structure/pairing/recombination/segregation responsibilities are
explicit, but production policies model current simple needs. This is a limitation
of concrete policies, not a structural ambiguity in `Genome` or
`GeneticArchitecture`.

### Scientific scope remains intentionally illustrative

The reference ecology, B3 flagship, and E2–E4 controlled experiments are
software/modeling demonstrations. They are not species-calibrated predictive
ecological models. The controlled E2–E4 program remains intentionally distinct
from the integrated reference-ecology flagship.

### Public presentation naming still contains v0.1 history

Some dashboard/cinematic entry points and helper names still call the older
`max_intake_rate` demonstration the flagship. V2/V3 should migrate the public story
to B3 deliberately while preserving compatibility where required.

## Collaboration model

Use ChatGPT primarily for architecture, roadmap sequencing, consequential public
contract decisions, tightly scoped sequential implementation, and independent PR
review/merge decisions.

Use Codex selectively for execution-heavy work behind settled interfaces: broad
mechanical migrations, analogous test expansion, validation/debug cycles, or
independently parallelizable repository iteration.

For substantial repository work, follow the Issue → branch → implementation →
early PR → CI → exact-head review → squash merge → `main` verification workflow in
`AGENTS.md`.

## Recent significant milestones

Newest first; this is a capability summary, not a changelog.

- **Confirmed standing-variation selection:** introduced equal-frequency inherited
  speeds 1/3/9 into the frozen E2/E3 controlled ecology with mutation off,
  counterbalanced founder-ID assignment, preserved full committed focal
  composition, independently confirmed speed-3 frequency gain only in the
  separated corridor, tied that change to strategy-specific reproduction/resource/
  locomotion evidence, and reproduced the result under a reversed founder-order
  sanity check without adding a fitness abstraction.
- **Confirmed ecological-performance landscape:** measured the monomorphic
  `max_speed` causal ladder, independently confirmed an interior speed-3 corridor
  performance maximum and exact local-resource neutrality, and demonstrated that
  removing locomotion cost removes the high-speed penalty.
- **Controlled clonal locomotion mechanics:** added the minimal one-locus clonal
  locomotion composition and validated movement, energetic cost, endpoint feeding,
  anisotropy, competition, and inheritance semantics without changing the kernel
  or richer genetics architecture.
- **Experimental science foundation:** established exact event/state alignment,
  run-level replicate/provenance semantics, explicit fixed-horizon censoring,
  treatment-integrity checking, and pure movement measurement from authoritative
  evidence without a universal statistics framework.
- **Confirmed B3 environment-dependent selection:** froze and independently
  confirmed the richer matched uniform-versus-compact `max_speed` reference-ecology
  flagship, including reproductive mechanism evidence, sensitivity,
  counterbalancing, representative-run selection, and bounded claims.

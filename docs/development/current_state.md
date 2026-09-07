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

E1–E5 now form a completed causal proof sequence above the frozen kernel and
separate from the richer reference ecology.

```text
E1 measurement semantics and reproducibility
        ↓
E2 minimal controlled locomotion mechanics
        ↓
E3 monomorphic ecological-performance landscape
        ↓
E4 selection on standing inherited variation
        ↓
E5 finite-population drift and weak selection
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


### E5 — confirmed finite-population stochasticity and weak selection

E5 derives A/B ancestry only in the analysis layer from existing founder IDs and
`PedigreeRecorder`; neutral labels never enter modeled biology. Neutral runs use
identical speed-3 founders. Weak-selection runs compare speeds 3 and 4 with
founder-ID assignment counterbalanced and one run/seed as the replicate.

After one pre-confirmation resource correction exposed E2's existing randomized
scarce-resource allocation, the design was frozen. A single bounded 3-vs-2
diagnostic was rejected because it was substantially stronger than 3-vs-4.
Independent confirmation on 24 disjoint seeds shows neutral frequency-change SD
contracting across founder counts 2, 8, and 32 (`0.0319`, `0.0168`, `0.0102`).
The favored speed-3 strategy decreases in 2/24 weak-selection runs at two founders,
1/24 at eight founders, and 0/24 at 32 founders. Thus finite-run stochasticity can
obscure or reverse weak selection at small modeled population size.

No lineage loss, fixation, or whole-population extinction was observed within the
60-step confirmation horizon; those outcomes remain right-censored. The minimal
controlled composition has no ordinary aging/metabolic/density-independent
turnover, so E5 does not manufacture fixation. A later rare-lineage invasion must
use a matched neutral rare-lineage control with the same introduction state,
rarity, ecology, population context, and horizon rather than treating an unmatched
rare founder as the control. See `docs/e5_drift_weak_selection.md`.

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
recorded in `docs/flagship_evolution_demo.md` and consumed directly by the B3
cinematic director.

The B3 claim is environment-dependent and specific to its tested reference ecology.
It should not be generalized to universal optimal speed, generic patchiness, or
species-calibrated prediction.

## Scientific visualization boundary

The shared scientific-presentation layer remains deliberately small.
`ContinuousTraitEncoding` stores a committed trait name, human-readable label, and
fixed numeric scale only. It contains no renderer color, material, widget, camera,
timing, easing, or scene-order configuration.

The interactive application owns view state and presentation of completed committed
runs. The cinematic package retains its generic renderer-owned timeline path and
also provides a concrete B3 flagship director above that foundation:

```text
B3 committed evidence
        ↓
B3 renderer-neutral scientific handoff
        ↓
B3-specific director preparation
        ↓
existing cinematic timelines / prepared values
        ↓
Manim-only camera, timing, focus, and charts
```

The B3 director consumes the shared fixed `max_speed` scale, the predeclared
representative seed and committed episodes, run-level confirmation evidence,
founder reproductive contribution, radius-2 sensitivity, and the bounded B3 claim.
Organism fill encodes focal `max_speed`; body size remains authoritative body mass;
focus is a separate halo/camera channel. Identity appearance/departure is continuity
metadata and is never promoted to biological birth/death evidence.

Routine CI renders generic, science-aware, and reduced real-B3 cinematic smokes.
The full high-quality B3 film is a deliberate reproducible artifact path rather
than an every-commit quality gate. See `docs/cinematic_flagship.md`.

Presentation interpolation is never scientific evidence. V2 should consume the
same B3 scientific handoff rather than independently invent treatment/control
semantics.

## Current development front

The E1→E5 controlled-science sequence is complete through the finite-population
baseline. It provides a causal chain from mechanics to ecological performance,
selection on inherited standing variation, and the stochastic reliability of weak
selection across modeled founder-count regimes, alongside the richer independently
confirmed B3 flagship.

The next controlled-science pressure is rare-lineage invasion. Any such milestone
must preserve E5's key interpretation boundary: disappearance of a rare lineage is
not by itself evidence of selective disadvantage. If the invasion design can lose
a rare lineage, it must include a matched neutral control using the same
introduction mechanism/state, initial rarity, population context, ecology, horizon,
and censoring semantics. Do not retrofit mortality or generic population-genetics
machinery merely to obtain textbook fixation behavior.

The B3 cinematic continuation is implemented as the V3 flagship path. The remaining
presentation continuation is the interactive matched-comparison experience:

```text
confirmed B3 scientific evidence/storyboard
        |
        +-------------------------+
        |                         |
        v                         v
interactive B3 comparison     B3 flagship cinematic
(V2 continuation)             (implemented V3 path)
```

Both media must preserve B3's treatment/control semantics, common scientific trait
scale, committed timestep convention, evidence hierarchy, representative-run versus
multi-seed distinction, and bounded claim. Renderer-specific mechanics remain
presentation concerns.

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

The reference ecology, B3 flagship, and E2–E5 controlled experiments are
software/modeling demonstrations. They are not species-calibrated predictive
ecological models. The controlled E2–E5 program remains intentionally distinct
from the integrated reference-ecology flagship.

### Public presentation naming still contains v0.1 history

Some dashboard/helper names still call the older `max_intake_rate` demonstration
the flagship. The B3 cinematic path does not require renaming those compatibility
surfaces. V2 should migrate the interactive public story deliberately rather than
through broad compatibility churn.

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

- **Confirmed drift and weak-selection baseline:** derived neutral ancestry only in
  the analysis layer from existing pedigree evidence, independently confirmed that
  neutral frequency-change spread contracts across founder counts 2/8/32, showed
  weak 3-vs-4 selection reversing in individual small-population runs, preserved
  unobserved loss/fixation/extinction as right-censored, and froze a matched-neutral
  rare-lineage control requirement for later invasion without adding mortality,
  fitness, or generic population-genetics machinery.
- **B3 flagship cinematic director:** turns the confirmed renderer-neutral B3
  storyboard into a deterministic explanatory Manim film with matched
  treatment/control framing, authoritative representative episodes, repeated
  interaction, founder reproductive contribution, population genetic evidence,
  independent confirmation, radius-2 sensitivity, fixed scientific scales, and a
  reproducibility manifest while preserving the generic cinematic path.
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

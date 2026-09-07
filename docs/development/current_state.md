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

Do not store volatile commit SHAs, CI run state, detailed ticket progress, or a full
PR history here.

## Architectural baseline

The repository is organized around a frozen domain-neutral transactional kernel
with general-evolution and biological specialization above it:

```text
validation / context / generic foundations
                    ↓
             simulation kernel
                    ↓
         general evolution abstractions
                    ↓
      biological/domain specializations
                    ↓
        processes and resolvers
                    ↓
       presets / experiments / interfaces
```

The kernel is in maintenance mode. New modeled behavior normally belongs above it
unless a genuine generic deficiency is demonstrated.

Scientific evidence and presentation remain downstream:

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
scenario-specific scientific meaning
        ↓
interactive / cinematic presentation
```

Presentation interpolation, camera behavior, layout, and renderer state are never
scientific evidence.

## Settled modeling capabilities

The general-evolution layer models transmissible state, expression, variation,
linkage/co-transmission, propagation, entity production, access/reference, and
admission/departure without assuming biology. Biological specialization composes
concrete genetics, inheritance, development, life history, growth, energetics,
feeding, behavior, movement, predation, reproduction, spatial ecology, and
biological world state above those contracts.

Reproduction distinguishes participants, investors, genetic contributors, and
production sources. Chromosome transmission separately models copy structure,
pairing, recombination, segregation, and gamete formation. Current simple
Mendelian/diploid policies are concrete policies, not universal architectural
rules.

B1 added immutable spatial renewable-resource placement policies. B2 established
`max_speed` as a real inherited benefit/cost axis in the richer reference ecology.
Neither change introduced a kernel-owned fitness abstraction.

## Scientific evidence and experiment semantics

Committed evidence is first-class. Existing evidence includes population and
spatial observations, selective individual genetic-trait records, allele/genotype
composition, pedigree/life-history evidence, causal event/effect telemetry,
deterministic seeded execution, checkpoint/resume, and reproducible multi-seed
experiment export.

`IndividualGeneticTraitRecorder` remains opt-in and separate from spatial replay so
scientific consumers can join committed values by `(step_index, organism_id)`
without bloating presentation snapshots.

E1 established the durable scientific boundary:

- one simulation run/seed is the current experimental replicate;
- organisms within a run are dependent observations, not extra replicates;
- event step `t` aligns to committed state `t + 1`;
- denominators, extinction, right-censoring, discovery/confirmation roles, and
  representative storytelling remain explicit;
- `ScientificRunProvenance` carries treatment/run identity;
- pure scientific measurements consume committed evidence rather than mutable
  simulation objects.

No universal metric registry, statistics DSL, or simulation dependency on analysis
code exists.

## Controlled experimental-evolution sequence

E1–E6 form a completed causal proof sequence separate from the richer B3 reference
flagship:

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
        ↓
E6 rare-lineage invasion and candidate stability
```

### E2 — controlled mechanics

E2 composes a minimal one-locus clonal `max_speed` system using existing biological
contracts. It validates capacity-limited targeted movement, locomotion-use cost,
endpoint feeding, scarce-resource competition, exact clonal propagation, and known
integer-grid anisotropy while omitting unrelated richer-reference pathways.

### E3 — ecological performance

E3 disables focal evolution and measures the causal ladder from monomorphic
`max_speed` through realized movement, locomotion expenditure, resource acquisition,
energy, and fixed-horizon demography. The local-resource arm is speed-neutral; the
separated corridor independently confirms an interior performance maximum at speed
3. Removing locomotion cost removes the canonical high-speed penalty.

### E4 — standing-variation selection

E4 introduces inherited speeds 1, 3, and 9 at equal starting frequency with
mutation off, co-located founders, counterbalanced speed-to-founder-ID assignment,
and complete focal-composition evidence. The local environment remains
frequency-neutral. In the separated corridor, independent confirmation increases
speed-3 frequency from `1/3` to `2/3` while speeds 1 and 9 fall to `1/6`, with
resource, movement, locomotion-energy, and reproduction evidence supporting the
mechanism. Reversed founder order reproduces the result.

### E5 — drift and weak selection

E5 assigns neutral ancestry only in analysis from existing founder IDs/pedigree.
Independent confirmation shows neutral frequency-change spread contracting with
founder count while weak 3-vs-4 selection can reverse direction in individual
small-population runs. Loss, fixation, and extinction remain right-censored when
unobserved; the experiment does not add artificial turnover merely to force
absorption.

### E6 — rare-lineage invasion

E6 runs resident burn-in, then forks the exact committed state and RNG into matched
neutral/mutant external-admission arms. Rare ancestry remains analysis-only.
Independent confirmation shows speed-3 mutants can reproduce and expand against
speed-4 residents while reciprocal speed-4 mutants do not expand. This is bounded
candidate invasion stability against reciprocal speed 4, not a formal ESS,
fixation result, or universal optimum.

See the dedicated E3–E6 documents for complete designs, numeric results, and claim
boundaries.

## Confirmed B3 scientific flagship

B3 remains the richer integrated reference-ecology flagship and is not replaced by
the controlled E sequence.

It compares matched uniform renewable-resource placement with two equal-weight
radius-1 patches at `(2, 5)` and `(9, 5)` using balanced homozygous
`max_speed = 1 / 4` standing variation, ordinary sexual inheritance, mutation off,
and a fixed horizon. Independent confirmation uses seeds
`5, 17, 29, 43, 61, 79, 97, 113`.

At committed step 30, compact treatment exceeds matched uniform control in all
eight confirmation seeds. Founder reproductive contribution, founder-label
counterbalancing, and radius-2 geometry sensitivity support and bound the
interpretation. Representative seed 5 and its real committed mechanism episodes
were selected by the predeclared B3 scientific rule, not by UI or cinematic code.

Scenario origin and validated scenario identity are distinct: the radius-2
sensitivity fork retains B3 origin but does not retain canonical radius-1 validated
identity or automatically inherit its headline claim/story semantics.

## Evolution Experiment Workbench

WB1–WB5 establish a concrete Study workflow above existing typed/scenario
composition without creating a second simulation architecture:

```text
semantic Study / curated scenario / concrete experiment definition
        ↓
bounded recipe or experiment-pattern resolution
        ↓
immutable manifest / concrete treatment specification
        ↓
existing typed or scenario-specific composition
        ↓
authoritative lower scientific/biological validation and preflight
        ↓
frozen kernel
        ↓
committed evidence and existing scientific results
        ↓
Study-facing result navigation
        ↓
downstream presentation
```

### WB1 — bounded controlled-locomotion Study

WB1 introduced stable semantic intent, immutable explicit/derived manifests,
evidence intent, compatibility-aware exact save/load, fresh runtime reconstruction,
run-to-manifest provenance, immutable fork lineage, and recipe-scoped semantic diff
for the bounded E3-controlled locomotion surface.

### WB2 — curated B3 reproduction and fork lineage

WB2 represents canonical B3 as a trusted frozen multi-run Study with a rich
resolved manifest. It establishes scenario origin versus validated identity and one
supported radius-1→radius-2 scientific fork. Exact reproduction loads the stored
resolved manifest rather than silently inheriting future defaults. Existing B3
evidence, analysis, robustness, representative-run selection, and claim boundaries
remain authoritative.

### WB3 — controlled experiment authoring

WB3 adds two concrete persisted experiment definitions rather than a generic DSL:
an E3-style max-speed sweep and an E4-style matched environment comparison.
Semantic factor identity is stable; treatment expansion is deterministic;
one run/seed remains the replicate; E4 counterbalancing stays separate from primary
factor meaning; existing E3/E4 result contracts and integrity checks remain
authoritative.

### WB4 — bounded rich reference-ecology Study

WB4 adds `bounded-reference-ecology` v1 over existing reference composition.
Guided/Advanced support, recipe-local applicability, stale inactive-state
normalization, explicit/derived manifest meaning, compatibility fingerprinting,
concrete population/event/pedigree/genetic/spatial EvidencePlans, exact run
provenance, and immutable fork/diff semantics all remain bounded to the recipe.
Spatial replay is opt-in and carries a storage-volume advisory.

### WB5 — Results and Presentation integration

WB5 completes the first end-to-end Study responsibility chain after execution.
`workbench.results` adds thin navigation over existing WB1, E3, E4, WB4, and B3
scientific artifacts while validating exact revision, manifest, EvidencePlan,
treatment, factor, replicate, and counterbalance identity. It does not recalculate
scientific outcomes.

Missing evidence is explicit. If a requested result/presentation needs evidence the
run did not record, the view is unavailable and the caller is told which evidence
is missing and that the Study must be rerun with the appropriate EvidencePlan.

The interactive and cinematic adapters are deliberately downstream:

```text
model / evidence / experiments
        ↓
     Workbench
        ↓
   +----+----+
   |         |
   v         v
  UI      cinematic
```

The V2 adapter builds existing `WorldPresentationFrame` values from recorded WB4 or
B3 evidence while preserving Study/run/seed/arm context. The B3 cinematic adapter
feeds only validated canonical B3 results into the existing B3-specific director.
A B3-derived radius-2 fork is inspectable but does not inherit the validated
headline/story cinematic handoff.

WB5 confirms that Results is primarily a Study-facing navigation concept and that
Presentation remains downstream. No universal result hierarchy, presentation
schema, scene graph, generic director, or new renderer-neutral abstraction was
earned. Existing `ContinuousTraitEncoding` plus concrete scientific handoffs are
sufficient.

See `docs/wb5_results_presentation.md`.

## Study product-model classification

The user-facing labels do not imply one class per section:

- **Study:** recipe-specific saved revision, lineage, manifest, EvidencePlan, and
  run provenance; also a product/navigation concept.
- **Simulation:** persisted semantic intent + resolved manifest; compilation/run are
  actions and mutable runtime graphs are reconstructed.
- **Evidence:** evidence intent is persisted; committed observations/telemetry are
  existing scientific artifacts; post-run availability is a view.
- **Experiment:** concrete WB3 definitions persist; expansion/execution are actions;
  E3/E4 science owns results.
- **Results:** principally views over existing artifacts plus exact association
  identity; there is no universal persisted Results root.
- **Presentation:** UI/cinematic values and renderer settings are downstream. WB5
  persists no presentation preferences because no current workflow requires them;
  presentation changes leave scientific identity unchanged.
- **Run:** an action whose provenance and produced artifacts are retained.

## Scientific visualization boundary

`ContinuousTraitEncoding` remains the small shared renderer-neutral value for a
committed trait label and fixed numeric scale. It owns no colors, materials,
widgets, camera, timing, easing, layout, or scene order.

The B3 cinematic path remains:

```text
B3 committed evidence
        ↓
B3 renderer-neutral scientific handoff
        ↓
B3-specific director preparation
        ↓
existing cinematic timelines/prepared values
        ↓
renderer-owned camera, timing, focus, charts, and rendering
```

The V2 Workbench adapter now consumes the same scientific identity/evidence layer
rather than independently inventing treatment/control meaning. Interactive
visibility, selection, trails, layout, and animation remain presentation concerns.

## Current development front

Two orthogonal fronts are now ready:

### Controlled science: E7

The next planned controlled-science milestone is **E7 — Mutation-Driven Adaptation
and Convergence**. It should ask whether independent populations with focal-only
`max_speed` mutation converge toward the performance/selection/invasion region
identified by E3–E6. Multiple predeclared low/near/high starting conditions, an
explicit mutation rate/step distribution, a legal range wider than the expected
adaptive region, and full trait-distribution evidence are required. Boundary
pile-up, polymorphism, stationary variation, directional evolution, and extinction
must remain distinguishable.

### Workbench: WB6

The next Workbench milestone is **WB6 — Diagnostics and Support-Envelope
Hardening**. It should improve only diagnostics and support behavior demonstrated
by WB1–WB5: incomplete/unsupported/irrelevant choices, missing evidence with rerun
remediation, scenario-identity loss, exact-reproduction compatibility,
experiment-specific integrity failures, and blocking versus advisory status.

WB6 must not parse arbitrary exception prose into invented scientific semantics or
become a universal validation/capability framework. Lower biological/scientific
validators remain authoritative. See
`docs/development/wb6_workbench_handoff.md`.

E7 must not acquire a Workbench dependency merely because both fronts exist.

## Known architectural friction

### Concrete Workbench persistence is still intentional

WB1, WB2, WB3, and WB4 persist different concrete shapes because their
responsibilities differ. WB5 did not reveal enough common persistence shape to
earn a universal Study/Experiment/Results root. Repeated future consumers must earn
that abstraction.

### Diagnostics/remediation are the next real Workbench pressure

WB1–WB5 now provide concrete evidence that users need structured remediation for
Workbench-owned support failures, especially irrelevant conditional parameters,
missing evidence, scenario identity loss, and exact reproduction incompatibility.
This pressure motivates WB6. It does not justify copying lower validators into
Workbench.

### Presentation bundles remain purpose-specific

The existing V2 `DashboardRun` is useful for its current UI path but is not a
universal scientific result model. WB5 therefore uses thin downstream adapters
rather than forcing WB4 evidence, E3/E4 results, and B3 artifacts into that shape.

### Public presentation naming still contains v0.1 history

Some compatibility/dashboard names still call the older `max_intake_rate`
demonstration the flagship. The B3 cinematic and WB5 integration do not require a
broad rename. Interactive public-story migration should remain deliberate.

### Built-in chromosome transmission remains conservative

Public copy-structure/pairing/recombination/segregation responsibilities are
explicit, but production policies model current simple needs. This is a limitation
of concrete policies, not a reason to broaden the frozen kernel.

### Scientific scope is illustrative

The reference ecology, B3 flagship, and E2–E6 controlled program are software and
modeling demonstrations, not species-calibrated predictive ecological models.

## Longer-term modeled fronts

Richer genetic expression, chromosome pairing/recombination, mating systems,
development/G×E, and evolutionary ecology remain separate additive fronts. Keep
inheritance, expression, development, environment, and current mutable state
separate. Selection should continue to emerge from differential persistence and
propagation rather than a kernel-owned scalar fitness field.

A native Rust/C++ backend remains evidence-driven future work. Python continues to
own high-level modeling/configuration until profiling demonstrates a stable subset
worth compiling.

## Collaboration model

Use ChatGPT primarily for architecture, roadmap sequencing, consequential public
contracts, tightly scoped sequential implementation, and independent PR
review/merge decisions.

Use Codex selectively for execution-heavy work behind settled interfaces: broad
mechanical migrations, analogous test expansion, validation/debug cycles, or
independently parallelizable iteration.

For substantial work follow:

```text
Issue → branch → implementation → early PR → CI → exact-head review
      → squash merge → main verification
```

## Recent significant milestones

Newest first; this is a capability summary, not a changelog.

- **WB5 Results and Presentation integration:** added exact Study-facing result
  navigation across WB1/WB3/WB4/B3 artifacts, explicit evidence insufficiency,
  downstream V2 world-presentation and validated B3 cinematic adapters, and
  dependency guards preserving Workbench as renderer-neutral science-facing
  integration rather than a new analysis/presentation framework.
- **E6 rare-lineage invasion:** added exact resident state/RNG forking, matched
  external admission, analysis-only ancestry, reciprocal speed-3/speed-4 invasion,
  and bounded candidate-stability evidence.
- **WB4 bounded reference ecology:** added rich Guided/Advanced authoring,
  applicability/normalization, compatibility-aware manifests, concrete evidence,
  persistence/fork/diff, and unchanged lower preflight.
- **WB3 controlled experiments:** added concrete E3 sweep and E4 matched comparison
  authoring with stable factors, deterministic expansion, explicit evidence needs,
  existing integrity authority, and unchanged scientific result types.
- **WB2 curated B3:** added exact trusted B3 reproduction, scenario origin versus
  validated identity, and bounded radius-2 fork semantics while reusing existing B3
  science.
- **WB1 controlled-locomotion Workbench foundation:** added semantic intent,
  immutable manifests, evidence plans, exact persistence, run provenance, fork
  lineage, and semantic diff above existing E2/E3 composition.
- **E5 drift and weak selection:** confirmed finite-population stochasticity and
  weak-selection reversals while preserving right-censored outcomes.
- **B3 flagship cinematic director:** turned the confirmed B3 handoff into a
  deterministic explanatory cinematic while preserving renderer/science
  boundaries.
- **E4 standing-variation selection:** independently confirmed speed-3 frequency
  gain in the corridor with complete focal composition and mechanism evidence.
- **E3 ecological performance:** independently confirmed the speed-3 corridor
  performance region and local neutrality with locomotion-cost sensitivity.
- **E2 controlled mechanics / E1 experimental science:** established the minimal
  causal mechanics and evidence/measurement/provenance foundation used by later
  controlled experiments.

See `docs/development/roadmap.md` for milestone-level direction.

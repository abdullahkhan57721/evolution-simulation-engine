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

## Settled capabilities

### Frozen kernel and general evolution

The kernel is in maintenance mode. It owns generic deterministic transactional
execution rather than organisms, genomes, ecology, reproduction, or other domain
meaning. Its durable stage order is:

```text
propose all
→ resolve
→ materialize all accepted events
→ apply accepted events
```

The general-evolution layer models transmissible state, expression, variation,
linkage/co-transmission, propagation, entity production, access/reference, and
admission/departure without assuming biology. The nonbiological vertical slice
remains the proof that these contracts are domain-neutral.

### Biological specialization

The biological stack composes genetics, inheritance, development, life history,
growth, energetics, feeding, behavior, movement, predation, reproduction, spatial
ecology, and biological world state above the generic layers.

Shared reproduction distinguishes reproductive participants, investors, genetic
contributors, and production sources. Chromosome transmission separately models
structure, pairing, recombination, segregation, and gamete formation. Current
simple diploid/Mendelian policies are concrete policies rather than universal
architecture rules.

### Spatial resource landscapes and heritable performance

B1 separated renewable-resource quantity/cadence from immutable ecological
placement policy. Uniform placement remains the ordinary baseline; static weighted
circular patches provide explicit spatial resource heterogeneity while preserving
world-state ownership and simulation-owned RNG.

B2 established existing `max_speed` as a real inherited performance/cost axis in
the reference biology. Higher capacity can produce farther realized movement
toward the same target, while the ordinary physiological-maintenance model imposes
higher ongoing energetic cost. Existing sexual inheritance transmits the standing
variation. No generic strategy or scalar-fitness abstraction was added.

### Observation, experiments, and scientific measurement

Committed evidence is a first-class layer. Available evidence includes:

- population/evolution observations;
- immutable spatial observations;
- selective per-organism genetic-phenotype integer-trait observations;
- allele/genotype composition;
- pedigree and lifetime reproductive contribution;
- committed causal event/effect telemetry;
- deterministic seeded execution and exact checkpoint/resume;
- reproducible multi-seed experiments and export.

`IndividualGeneticTraitRecorder` remains opt-in and intentionally separate from
`SpatialObservation`, allowing presentation to join scientific values to replay by
committed `(step_index, organism_id)` identity without broadening spatial snapshots.

The experimental-science foundation now makes the downstream measurement boundary
explicit. One simulation run/seed is the experimental replicate; organisms within
that run are not independent replicates; event step `t` aligns to committed state
`t + 1`; denominators and right-censoring remain explicit; discovery,
confirmation, and representative roles stay distinct; and concrete experiments may
audit their one declared treatment difference without a generic configuration-diff
language.

`ScientificRunProvenance` carries treatment-aware scientific identity without
changing legacy/reference `RunMetadata`. `FixedHorizonTimeToEvent` preserves
observed versus right-censored outcomes. The first concrete measurement consumer
derives attempted displacement, realized displacement, and locomotion-energy
expenditure from authoritative committed movement evidence, with applied movement
as the explicit denominator. Simulation/domain code remains independent of this
analysis layer, and no universal metric/statistics framework has been introduced.

### Scientific visualization boundary

The shared scientific-presentation layer remains deliberately small.
`ContinuousTraitEncoding` stores a committed trait name, human-readable label, and
fixed numeric scale only. It contains no renderer color, material, widget, camera,
timing, easing, or scene-order configuration.

Interactive and cinematic consumers independently own layout, interaction,
interpolation, camera, timing, and storytelling. Presentation interpolation is
never scientific evidence.

### Interactive and cinematic foundations

The interactive application has a full-window configuration → completed-run
world-workspace flow. It owns immutable presentation/run values and view state,
not live simulation ownership. The world view supports committed-step playback,
selection/inspection, environmental layers, trails, labels, neutral generic
organism encoding, and optional focal-trait encoding from committed scientific
evidence.

The cinematic package prepares renderer-owned timelines from committed spatial,
population, selective focal-trait, and event evidence. Generic and focal modes
remain available without turning Manim or any future renderer into a simulation
contract.

V2 and V3 have the science-aware infrastructure needed to consume a scenario
handoff; they should not invent B3 treatment/control semantics independently.

## Confirmed B3 scientific flagship

B3 has now identified and independently confirmed the primary scientific flagship
for the next presentation generation.

The question is:

> Does compact spatial resource geography change selection on existing heritable
> `max_speed` standing variation relative to a matched uniform-resource
> environment in the current richer reference ecology?

The frozen matched comparison keeps the ordinary sexual reference ecology and
changes only renewable-resource placement:

- control: uniform placement;
- treatment: two equal-weight radius-1 patches centered at `(2, 5)` and `(9, 5)`;
- 32 deposits/timestep, 6 resource units/deposit;
- 20 balanced homozygous `max_speed = 1` / `4` founders;
- initial high-speed allele frequency `0.50`;
- shared `max_intake_rate = 8`;
- mutation disabled;
- predation isolated through the frozen attack/defense background;
- mating radius `3`;
- 50 committed timesteps.

Discovery seeds and confirmation seeds are intentionally disjoint. The independent
confirmation set is:

```text
5, 17, 29, 43, 61, 79, 97, 113
```

At the predeclared step-30 readout:

- mean uniform high-speed allele frequency: **0.3423**;
- mean compact radius-1 frequency: **0.6266**;
- mean paired compact-minus-uniform effect: **+0.2843**;
- compact exceeded matched uniform in **8/8** confirmation seeds.

Founder realized reproductive success provides the primary demographic mechanism:
uniform favored lower-speed founders in 6/8 runs with two ties, while compact
radius-1 treatment favored higher-speed founders in 7/8 runs.

A predeclared radius-2 sensitivity weakened the compact advantage in aggregate
(step-30 mean **0.5049**), and a bounded founder-label swap preserved a positive
compact-vs-uniform effect in both tested confirmation seeds.

The representative storytelling run is confirmation seed **5**, chosen by the
predeclared median-effect/legible-episode rule rather than by visual convenience.
Its real committed movement/resource-consumption episodes are documented in
`docs/flagship_evolution_demo.md`.

The bounded claim is environment-dependent: under this tested reference-ecology
configuration, compact radius-1 resource geography favors the high-speed strategy
relative to matched uniform controls, while uniform favors the lower-speed
strategy in aggregate. Do not generalize this to universal optimal speed, generic
patchiness, species-calibrated prediction, or isolated locomotion-cost causality.

The original v0.1 `max_intake_rate` flagship remains a secondary historical
regression/integration example. Its existing helper and presentation entry points
remain for compatibility until the V2/V3 B3-specific presentation work replaces
the public story.

## Current development front

The key integration uncertainty that motivated B1/B2/B3 is resolved: the project
now has a confirmed environment-dependent selection scenario and a renderer-neutral
scientific handoff. The experimental-science foundation also establishes the
measurement semantics needed to begin a deliberately simpler causal experiment
track without changing the richer B3 flagship.

Two fronts can therefore proceed independently:

```text
confirmed B3 scientific evidence/storyboard
        |
        +-------------------------+
        |                         |
        v                         v
interactive B3 comparison     cinematic B3 director
(V2 continuation)             (V3 continuation)

experimental-science foundation (E1)
        |
        v
minimal clonal locomotion mechanics (E2)
        |
        v
controlled ecological performance landscape (E3)
        |
        v
standing-variation selection test (E4)
```

The presentation media should consume the B3 treatment/control semantics, fixed
`max_speed` scale, matched comparison, representative seed/episodes, evidence
hierarchy, and claim boundaries from `docs/flagship_evolution_demo.md`. They remain
free to make renderer-specific choices without changing scientific meaning.

The E2–E4 experimental track is intentionally separate from B3. It should isolate
locomotor mechanics first, measure phenotype-to-performance without focal
evolution second, and only then ask whether standing inherited variation changes
in the independently predicted direction. E2 may compose new controlled biology
above the frozen kernel but must not simplify general genetics or redesign B3.

All fronts should preserve:

- common scientific trait scales across matched arms where comparison requires it;
- committed timestep semantics;
- authoritative committed event/state evidence;
- separation of configured treatment context from committed state and events;
- representative-run storytelling versus multi-seed robustness evidence;
- explicit claim/nonclaim boundaries.

Longer-term modeled fronts remain richer genetic expression, chromosome
pairing/recombination, mating systems, development/G×E, and evolutionary ecology.
Those fronts need not serialize behind presentation or E2 when their public
boundaries are already settled.

A native Rust/C++ backend remains a separate evidence-driven future concern.
Python continues to own high-level modeling/configuration until measured workloads
show that a compiled execution plan/backend is justified.

See `docs/development/roadmap.md` for milestone-level sequencing.

## Known architectural friction

### Built-in chromosome transmission remains intentionally conservative

The public copy-structure/pairing/recombination/segregation responsibilities are
explicit, but production policies model current simple needs. This is a limitation
of concrete policies, not a structural ambiguity in `Genome` or
`GeneticArchitecture`.

### Scientific scope remains intentionally illustrative

The reference ecology and B3 flagship are evidence-backed software/modeling
demonstrations. They are not species-calibrated or predictive ecological models.
The isolated E2–E4 experimental-evolution program remains distinct from this
integrated reference-ecology flagship.

### Public presentation naming still contains v0.1 history

Some existing dashboard/cinematic entry points and helper names still call the
older `max_intake_rate` demonstration the flagship. B3 intentionally does not
rewrite renderer choreography. V2/V3 should migrate the public presentation story
to the confirmed B3 scenario while preserving compatibility or making any API
rename deliberate.

## Collaboration model

Use ChatGPT Chat primarily for architecture, roadmap sequencing, consequential
public-contract decisions, tightly scoped sequential implementation, and
independent PR review/merge decisions.

Use Codex selectively for execution-heavy work behind settled interfaces: broad
mechanical migrations, analogous test expansion, validation/debug cycles, or
independently parallelizable repository iteration.

## Recent significant milestones

Newest first; this is a capability summary, not a changelog.

- **Experimental science foundation:** established exact committed event/state
  alignment, run-level replicate and treatment provenance, explicit fixed-horizon
  censoring semantics, thin normalization/equality treatment-integrity checking,
  and pure locomotion measurement from authoritative applied movement effects and
  energy evidence without introducing a statistics DSL or simulation dependency.
- **Confirmed B3 environment-dependent selection:** froze the matched
  uniform-versus-compact `max_speed` scenario before confirmation, executed a
  disjoint eight-seed confirmation set without filtering, confirmed the step-30
  genetic reversal in aggregate, supported the mechanism with founder reproductive
  contribution, founder-label counterbalancing and radius-2 sensitivity, selected
  representative seed 5 deterministically, and published the renderer-neutral
  scientific storyboard.
- **Science-aware interactive trait encoding:** joined committed per-organism focal
  trait evidence to interactive world replay while preserving generic neutral mode
  and independent selection semantics.
- **Science-aware cinematic foundation:** joined committed spatial, selective
  focal-trait, and event evidence into deterministic cinematic preparation with
  renderer-neutral scientific encoding and renderer-owned choreography.
- **Spatial resource landscapes:** separated renewable-resource quantity/cadence
  from immutable ecological placement and added static patchy placement.
- **Heritable speed tradeoff:** verified inherited `max_speed` benefit/cost using
  existing movement, maintenance, and inheritance mechanisms.
- **v0.1 portfolio baseline:** integrated documentation, dashboard,
  experiments/export, deterministic Manim replay, the original max-intake
  demonstration, and protected verification into one reviewer-facing release.

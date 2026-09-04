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

### Observation and experiments

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

### Scientific visualization boundary

The shared scientific-presentation layer remains deliberately small.
`ContinuousTraitEncoding` stores a committed trait name, human-readable label, and
fixed numeric scale only. It contains no renderer color, material, widget, camera,
timing, easing, or scene-order configuration.

Interactive and cinematic consumers independently own layout, interaction,
interpolation, camera, timing, and storytelling. Presentation interpolation is
never scientific evidence.

### Interactive and cinematic presentation

The interactive application has a full-window configuration → completed-run
world-workspace flow. It owns immutable presentation/run values and view state,
not live simulation ownership. The world view supports committed-step playback,
selection/inspection, environmental layers, trails, labels, neutral generic
organism encoding, and optional focal-trait encoding from committed scientific
evidence.

The cinematic package retains its generic renderer-owned timeline path and now
also contains a concrete B3 flagship director above that foundation. The B3 path
consumes the frozen scientific handoff rather than rediscovering scenario meaning:

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

The director uses the shared fixed `max_speed` scale, B3-declared representative
seed and episodes, run-level confirmation evidence, founder reproductive
contribution, radius-2 sensitivity, and the bounded B3 claim. Organism fill remains
focal `max_speed`; body size remains authoritative body mass; focus uses a separate
halo/camera channel. Identity appearance/departure remains continuity metadata and
is never promoted to birth/death evidence.

Routine CI renders the generic, science-aware, and reduced real-B3 cinematic
smokes. The full high-quality B3 film is a deliberate reproducible artifact path,
not an every-commit quality gate. See `docs/cinematic_flagship.md`.

## Confirmed B3 scientific flagship

B3 has identified and independently confirmed the primary scientific flagship for
the current presentation generation.

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
`docs/flagship_evolution_demo.md` and are consumed directly by the cinematic
director.

The bounded claim is environment-dependent: under this tested reference-ecology
configuration, compact radius-1 resource geography favors the high-speed strategy
relative to matched uniform controls, while uniform favors the lower-speed
strategy in aggregate. Do not generalize this to universal optimal speed, generic
patchiness, species-calibrated prediction, or isolated locomotion-cost causality.

The original v0.1 `max_intake_rate` flagship remains a secondary historical
regression/integration example. Its existing helper and presentation entry points
remain for compatibility.

## Current development front

The science and cinematic explanatory path for B3 are now settled. The immediate
presentation front is the interactive B3 matched-comparison continuation, while
future modeled work can proceed independently behind the already established
boundaries:

```text
confirmed B3 scientific evidence/storyboard
        |
        +-------------------------+
        |                         |
        v                         v
interactive B3 comparison     B3 flagship cinematic
(V2 continuation)             (implemented V3 path)
```

Both media consume the B3 treatment/control semantics, fixed `max_speed` scale,
matched comparison, representative seed/episodes, evidence hierarchy, and claim
boundaries from `docs/flagship_evolution_demo.md`. Renderer-specific choices must
not change scientific meaning.

Presentation work should preserve:

- common scientific trait scales across matched arms;
- committed timestep semantics;
- authoritative committed event/state evidence;
- separation of renewable-generation provenance from total world resource state;
- representative-run storytelling versus multi-seed robustness evidence;
- explicit claim/nonclaim boundaries.

Longer-term modeled fronts remain richer genetic expression, chromosome
pairing/recombination, mating systems, development/G×E, and evolutionary ecology.
Those fronts need not serialize behind presentation when their public boundaries
are already settled.

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
The later isolated experimental-evolution program should remain distinct from this
integrated reference-ecology flagship.

### Public presentation naming still contains v0.1 history

Some existing dashboard/helper names still call the older `max_intake_rate`
demonstration the flagship. The new B3 cinematic path does not require renaming
those compatibility surfaces. V2 should migrate the interactive public story to
the confirmed B3 scenario deliberately rather than through broad compatibility
churn.

## Collaboration model

Use ChatGPT Chat primarily for architecture, roadmap sequencing, consequential
public-contract decisions, tightly scoped sequential implementation, and
independent PR review/merge decisions.

Use Codex selectively for execution-heavy work behind settled interfaces: broad
mechanical migrations, analogous test expansion, validation/debug cycles, or
independently parallelizable repository iteration.

## Recent significant milestones

Newest first; this is a capability summary, not a changelog.

- **B3 flagship cinematic director:** turns the confirmed renderer-neutral B3
  storyboard into a deterministic explanatory Manim film with matched
  treatment/control framing, authoritative representative episodes, repeated
  interaction, founder reproductive contribution, population genetic evidence,
  independent confirmation, radius-2 sensitivity, fixed scientific scales, and a
  reproducibility manifest while preserving the generic V3 I1 path.
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

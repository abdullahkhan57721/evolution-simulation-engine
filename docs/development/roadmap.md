# Architectural Roadmap

This page answers **where the project is going** at the level of coherent
architectural milestones. It is a rolling planning aid, not an implementation
ticket system.

## Authority and maintenance boundary

GitHub Issues remain authoritative for active scope, acceptance criteria, status,
and dependencies. Architecture/subsystem docs and ADRs remain authoritative for
settled contracts and rationale.

Update this roadmap only when milestone ordering or architectural direction
materially changes. Do not mirror every Issue, PR, commit, or CI result here.

## Guiding direction

The project should continue toward a simulation engine in which:

1. the frozen kernel provides domain-neutral deterministic transactional execution;
2. the general-evolution layer expresses evolution without assuming biology;
3. genetics, reproduction, development, and ecology specialize those settled
   general contracts;
4. richer modeled biology is added against explicit public responsibilities rather
   than by broadening lower layers speculatively;
5. observation, experiments, and presentation remain downstream of committed
   simulation evidence;
6. performance/native-backend work begins only from measured need.

The kernel is not the development frontier. New modeled behavior normally belongs
above it unless a genuine generic deficiency is demonstrated.

## Stable scientific and presentation boundaries

The durable evidence path is:

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
experiment-level reporting/export
        ↓
presentation
```

One simulation run/seed is the current stochastic experimental replicate. Event
step `t` aligns to committed state `t + 1`; denominators, extinction,
right-censoring, discovery versus confirmation, and representative storytelling
remain explicit.

Presentation then branches by medium:

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

Scientific meaning can be shared across media. Renderer primitives, layout,
interaction, camera, timing, interpolation, and choreography remain independent.
Presentation interpolation is never scientific evidence.

## Completed post-v0.1 integration sequence

The B1/B2/B3 scientific flagship and the V3 cinematic continuation have crossed
their intended integration gates:

```text
v0.1.0 portfolio baseline
        |
        +--------------------------+
        |                          |
        v                          v
B1 spatial resources        presentation foundations
        |                          |
        v                          +------+
B2 max_speed tradeoff              |      |
        |                          v      v
        +--------------------> interactive cinematic
        |                      science-aware foundations
        v
B3 matched scenario discovery
        |
        v
frozen disjoint confirmation
        |
        v
confirmed renderer-neutral B3 scientific handoff
        |
        v
concrete B3 flagship cinematic director
```

B1 established immutable ecological resource-placement policy. B2 demonstrated an
inherited `max_speed` benefit/cost axis in the richer reference ecology. B3
confirmed a robust environment-dependent selection demonstration without kernel
changes or a generic fitness abstraction. V3 then turned the frozen B3 scientific
handoff into a reproducible explanatory film while keeping camera, timing, focus,
and chart choreography in the cinematic layer.

## Confirmed B3 scientific contract

The current richer scientific flagship compares:

```text
uniform renewable-resource placement
        versus
two equal-weight radius-1 resource patches
at (2, 5) and (9, 5)
```

Both arms retain matched renewable-resource quantity, founder construction,
nonfocal biology, sexual inheritance, and simulation horizon. Founders begin with
balanced homozygous `max_speed = 1` / `4` standing variation and high-speed allele
frequency `0.50`.

Independent confirmation uses the frozen disjoint seed set:

```text
5, 17, 29, 43, 61, 79, 97, 113
```

At committed step 30, compact radius-1 treatment exceeded matched uniform control
in all eight confirmation seeds. Aggregate mean high-speed allele frequency was
`0.6266` in compact treatment versus `0.3423` in uniform control. Founder realized
reproductive contribution, a bounded founder-label counterbalance, and a radius-2
geometry sensitivity support the environment-dependent mechanism.

Representative storytelling seed `5` and its real committed episodes were chosen
by the predeclared scientific rule, not by the renderer. The complete
claim/nonclaim boundary and renderer-neutral storyboard live in
`docs/flagship_evolution_demo.md`.

The old `max_intake_rate` v0.1 demonstration remains a secondary historical
regression/integration example.

## Completed E1–E5 controlled-science sequence

A separate controlled program now provides a deliberately simpler causal proof
sequence:

```text
E1 experimental-science foundation
        ↓
E2 minimal clonal locomotion mechanics
        ↓
E3 monomorphic ecological-performance landscape
        ↓
E4 selection on standing inherited variation
        ↓
E5 finite-population drift and weak selection
```

### E1 — measurement semantics and reproducibility

E1 established treatment-aware scientific provenance, exact committed event/state
alignment, fixed-horizon censoring, thin experiment-specific treatment-integrity
auditing, and pure locomotion measurements from authoritative movement evidence.
It deliberately did not create a metric registry, universal analysis plan,
statistics DSL, or simulation dependency on analysis code.

### E2 — controlled locomotion mechanics

E2 composed a minimal one-locus clonal system from existing general and biological
contracts. It validated capacity-limited targeted movement, locomotion-use cost,
endpoint feeding, scarce-resource competition, exact clonal propagation, and known
integer-grid anisotropy while omitting unrelated richer-reference-ecology pathways.
The kernel and general genetics remained unchanged.

### E3 — ecological-performance landscape

E3 disabled focal evolution and measured the causal ladder from monomorphic
`max_speed` through realized movement, locomotion expenditure, resource acquisition,
energy, and fixed-horizon demographic performance. The local-resource arm was
speed-neutral; the separated-resource corridor independently confirmed an interior
performance maximum at `max_speed = 3`. Removing locomotion cost removed the
canonical high-speed penalty, strengthening the causal interpretation.

That result froze the directional prediction consumed by E4 rather than tuning E4
toward a desired outcome.

### E4 — selection on standing variation

E4 introduced inherited speeds `1`, `3`, and `9` at equal starting frequency with
mutation disabled, co-located founders, counterbalanced speed-to-founder-ID
assignment, complete committed focal composition, and independent confirmation
seeds.

The local-resource environment remained frequency-neutral. In the separated
corridor, independent confirmation consistently increased speed-3 frequency from
`1/3` to `2/3` while speeds 1 and 9 each fell to `1/6`, with reproduction,
resource-acquisition, and locomotion evidence supporting the mechanism. Reversed
founder-order checks reproduced the focal and mechanism outcomes.

Thus E4 fulfilled E3's independently frozen prediction for this controlled
finite-horizon ecology without adding a scalar fitness abstraction. It is selection
on standing variation, not a universal optimum, fixation claim, or de novo
mutation result.

### E5 — drift, population size, and weak selection

E5 asks how reliable a weak selection signal remains under finite-population
stochasticity. It assigns neutral A/B ancestry only in analysis from founder IDs
and the existing clonal pedigree, so neutral lineages have identical modeled
biology. Founder counts 2, 8, and 32 are modeled regimes rather than real-world
effective population-size claims.

Independent confirmation shows neutral frequency-change spread contracting with
founder count while the small positive 3-vs-4 directional effect remains similar.
The favored speed-3 strategy reverses direction in some small-population runs but
not at the largest tested founder count. Loss/fixation/extinction remain outcomes
and are right-censored when absent; E5 does not introduce turnover merely to force
absorption.

The rare-invasion handoff is explicit: later invasion must compare disappearance
against a neutral lineage introduced in the same state and at the same rarity under
the same ecology, population context, and horizon. A rare founder is not
automatically a valid control for a de-novo mutant. Reuse E5's pedigree-derived
ancestry and run-level censoring rather than building a generic population-genetics
layer.

E1–E5 are intentionally separate from B3. B3 remains the richer integrated
reference-ecology flagship; the E sequence isolates causal mechanics and does not
retroactively simplify B3.

## Presentation integration front

The B3 cinematic path is now an implemented sibling renderer path. The remaining
presentation continuation is the interactive B3 matched-comparison experience:

```text
confirmed B3 evidence/storyboard
        |
        +-------------------------+
        |                         |
        v                         v
V2 interactive B3            V3 B3 flagship film
comparison                   implemented
```

### Interactive continuation

The interactive experience should build on the existing world-centered workspace
and science-aware focal-trait encoding. It should add the B3 matched comparison as
a scientific experience rather than hardcoding new simulation meaning in UI code.

Preserve:

- control/treatment semantics from B3;
- fixed shared `max_speed` capacity scale `1..4`;
- matched committed timestep convention;
- common world geometry/scale where comparison requires it;
- allele/genotype/focal-trait evidence;
- founder reproductive-contribution evidence;
- representative seed storytelling versus multi-seed robustness;
- explicit claim/nonclaim boundaries.

Renderer-specific controls, layout, charts, animation rate, accessibility, and
interaction remain UI responsibility.

### Cinematic baseline to preserve

The B3 cinematic director is intentionally concrete rather than a universal film
DSL. Its durable lessons are:

- B3 science is consumed from the renderer-neutral handoff and committed evidence;
- fixed scientific scales are shared across matched arms;
- representative organisms/events are selected by B3, not by the renderer;
- focal fill, authoritative body size, and presentation focus are separate channels;
- committed events support causal labels while identity continuity remains
  non-causal;
- representative-run episodes explain mechanism while run-level confirmation
  supports robustness;
- camera, shot timing, temporal compression, and evidence-chart choreography remain
  renderer-only concerns;
- the full portfolio film is a deliberate reproducible artifact while routine CI
  retains short generic, science-aware, and real-B3 smokes.

Do not generalize this into a broad camera DSL or scenario-presentation schema
without multiple future films demonstrating a genuinely repeated contract.

## Next controlled-science pressure

E5 establishes the finite-population baseline needed before rare-lineage invasion.
The next controlled-science milestone should test invasion only after its
introduction semantics are explicit enough to construct a matched neutral control.
That control must share the mutant treatment's introduction state, rarity,
population context, ecology, horizon, and evidence/censoring semantics.

Do not interpret disappearance as selection merely because a lineage is rare, and
do not add generic fixation/population-genetics architecture ahead of concrete
consumers. Longer-term modeled fronts remain directions rather than preauthorized
implementations.

## Front A — Richer genetic expression

**Goal:** extend the existing copy-count-aware, multi-locus expression framework
with explicit biological policies such as incomplete dominance, codominance,
epistasis, dosage-sensitive expression, or richer quantitative architectures.

Preserve:

```text
genome
  |
  v
genetic expression
  |
  v
genetic phenotype
  |
  v
development / environment-dependent realization
  |
  v
current physiological state
```

Do not collapse those layers into a catch-all phenotype object.

## Front B — Richer chromosome pairing and recombination

Current public responsibilities already separate chromosome-copy structure,
pairing, recombination eligibility, segregation, and gamete formation.

Future biological cases may justify higher-copy pairing, preferential versus random
bivalent formation, multivalent models, chromosome-specific crossover behavior,
multiple crossovers, or lifecycle/mating-type-sensitive gamete formation. Add only
the policies required by concrete modeled biology. Do not push meiosis vocabulary
into the frozen kernel or general propagation contracts.

## Front C — Richer mating systems

Shared reproduction already separates participants, investors, genetic
contributors, and production sources. Future cases may explore asymmetric or
ordered roles, multi-participant groups, hermaphroditic systems, role-sensitive
mate choice, contributor/investor subsets, or lifecycle-specific production
sources. Mating-system composition should remain separate from low-level
inheritance.

## Front D — Richer development and G×E

Potential concrete directions include nonlinear reaction norms, developmental
stages/history, richer developmental stochasticity, and reversible adult
plasticity distinct from lifetime developmental targets. Preserve distinctions
among inheritance, genetic expression, development, environment, and current
mutable state.

## Front E — Richer evolutionary ecology

The ecological foundation now includes explicit static resource geography, a
confirmed richer reference-ecology selection use case, and a controlled
mechanics→performance→selection sequence. Future ecology should continue to drive
requests for new biology where possible.

Possible directions include richer resource competition, movement/behavior
tradeoffs, predation/prey coevolution, life-history tradeoffs, spatial or
biogeographic structure, and fluctuating or heterogeneous selection regimes.
Selection should continue to emerge from differential persistence and propagation,
not from a kernel-owned scalar `fitness` field.

## Observation and statistical analysis

E1–E5 provide concrete consumers for the scientific-measurement boundary without
justifying a broad statistics framework. Future repeated experimental patterns may
earn additional reusable statistical contracts, but only after concrete consumers
show what actually repeats.

Preserve:

```text
committed state/events
        ↓
pure scenario-specific scientific measurements
        ↓
replicate outcomes / treatment comparisons
        ↓
experiment-level inference/reporting
        ↓
presentation
```

Do not put arbitrary metric/property bags into simulation or observation layers.
Undefined post-extinction quantities remain undefined rather than becoming zero,
and presentation remains a consumer rather than an authoritative calculator.

## Future native execution backend

A Rust/C++ backend remains an evidence-driven future front rather than a current
architecture target.

If measured workloads justify it, the desired shape is approximately:

```text
Python modeling / configuration
        |
        v
validated static typed simulation plan
        |
        v
backend execution boundary
        |
        +----------------------+
        |                      |
        v                      v
Python reference backend   native backend
        |                      |
        +----------+-----------+
                   |
                   v
        committed result values
```

Do not create this abstraction until real profiling demonstrates both the need and
the stable subset worth compiling.

## Architectural constraints that should survive future work

- Preserve the frozen transactional kernel unless a true generic deficiency is
  demonstrated.
- Preserve simulation-owned RNG and materialize-before-apply semantics.
- Preserve domain-neutral general-evolution vocabulary.
- Keep reproduction participant/investor/contributor/production-source roles
  separate.
- Keep chromosome structure, pairing, recombination, and segregation separate.
- Keep genetic expression, development, and current state separate.
- Keep scientific measurement downstream of committed evidence and upstream of
  experiment-level reporting/presentation.
- Keep presentation downstream of committed evidence and scientific meaning.
- Share scenario-level scientific meaning across media without forcing renderer
  mechanics into a universal scene/runtime abstraction.
- Keep spatial observation focused; add selective sibling scientific records when
  a real per-individual data need appears.
- Distinguish configured treatment context, committed state, committed events,
  derived measurements, representative examples, and robustness evidence.
- Preserve run/seed as the experimental replicate for current stochastic treatment
  comparisons unless a later concrete design justifies another unit.
- Prefer readable, maintainable architecture over micro-optimization.
- Require evidence before performance/backend work.

## ChatGPT versus Codex allocation

Use ChatGPT Chat primarily for architecture-heavy work, consequential public
contracts, tightly scoped sequential implementation, roadmap sequencing, and
independent review/merge decisions.

Use Codex selectively for execution-heavy work behind settled contracts, broad
analogous migrations, repetitive test expansion, validation/debug cycles, and
independently parallelizable repository iteration.

## Planning rule

Before opening each new milestone Issue:

1. re-read current `main` and `docs/development/current_state.md`;
2. verify whether earlier work changed assumptions in this roadmap;
3. start from a concrete modeled or presentation use case;
4. settle consequential public architecture in Chat when needed;
5. create one focused Issue with boundaries, traps, acceptance criteria, automated
   tests, and manual verification where material;
6. update this roadmap in the same PR only when ordering or architectural direction
   materially changes.

A roadmap is a hypothesis about the best sequence. Repository evidence may change
it.

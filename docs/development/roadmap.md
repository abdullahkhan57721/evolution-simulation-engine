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
5. scientific measurement and presentation remain downstream of committed
   simulation evidence;
6. performance/native-backend work begins only from measured need.

The kernel is not the development frontier. New modeled behavior normally belongs
above it unless a genuine generic deficiency is demonstrated.

## Stable evidence and presentation boundary

The durable direction is:

```text
simulation/domain layers
        |
        v
committed scientific evidence
        |
        v
pure measurement / scenario meaning
        |
        +-------------------------+
        |                         |
        v                         v
interactive presentation     cinematic presentation
```

Scientific meaning can be shared across media; renderer primitives, layout,
interaction, camera, timing, interpolation, and choreography remain independent.
Presentation interpolation is never scientific evidence.

## Completed post-v0.1 integration sequence

The first post-v0.1 scenario/presentation sequence has crossed both its scientific
and cinematic integration gates:

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

B1 established immutable ecological resource-placement policy. B2 demonstrated
an inherited `max_speed` benefit/cost axis using existing movement, maintenance,
and sexual inheritance. B3 confirmed that the two mechanisms compose into a
robust environment-dependent selection demonstration without kernel changes or a
generic fitness abstraction. V3 turns that frozen scientific handoff into a
reproducible explanatory film without moving camera/timing concerns into the
domain model.

## Confirmed B3 scientific contract

The current integrated flagship compares:

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

The representative storytelling seed is `5`, chosen by the predeclared
median-effect/legible-episode rule. The complete claim/nonclaim boundary and
renderer-neutral storyboard live in `docs/flagship_evolution_demo.md`.

The old `max_intake_rate` v0.1 demonstration is a secondary historical
regression/integration example rather than the primary scientific flagship.

## Experimental-science foundation and controlled sequence

E1 establishes a durable but deliberately thin scientific-analysis boundary above
committed evidence:

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

The experimental unit is one simulation run/seed rather than one organism. Event
step `t` aligns exactly to committed state `t + 1`; denominators, extinction,
exposure, and right-censoring remain explicit; same-seed comparisons are blocking
rather than an automatic perfect-common-random-number claim; and discovery,
confirmation, and representative storytelling retain different roles.

E1 adds treatment-aware scientific provenance, fixed-horizon censoring semantics,
a thin equality-after-experiment-specific-normalization treatment audit, and the
first pure locomotion measurement derived from committed movement evidence. It
does not add a metric registry, universal analysis plan, statistics DSL, or new
statistics dependency.

The controlled experimental-evolution sequence is:

```text
E1 experimental-science foundation
        |
        v
E2 minimal clonal locomotion system
   + mechanics validation
        |
        v
E3 ecological performance landscape
   with focal evolution disabled
        |
        v
E4 standing variation +
   environment-dependent selection
```

E2 should isolate one inherited locomotor-capacity trait in a deliberately simple
clonal composition, validate target-directed displacement and locomotion-use cost,
and avoid the mating/predation/nonfocal genetic pathways of the richer reference
ecology. It must not redesign the frozen kernel or general genetics around
cloning.

E3 should measure the `max_speed` capacity → realized movement → movement energy →
resource/energy/survival/reproduction causal ladder across controlled monomorphic
speed treatments. Focal evolution remains off, and the resulting replicate-level
performance landscape should produce a predeclared prediction for E4 rather than
forcing a desired optimum.

E4 should finally introduce known standing inherited speed variation with mutation
still off and ask whether strategy/focal-trait frequencies move in the direction
predicted independently by E3. Founder positions/labels must be counterbalanced,
and disagreement with E3 is a scientific result to investigate rather than tune
away.

This sequence is intentionally separate from B3. B3 remains the richer integrated
reference-ecology flagship; E2–E4 are controlled causal experiments that may reuse
general contracts without retroactively simplifying or rewriting B3.

## Presentation integration front

The cinematic B3 continuation is now a concrete sibling renderer path. The
remaining B3 presentation front is the interactive matched comparison, while the
E2–E4 controlled experiment track can proceed independently:

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

The presentation should preserve:

- control/treatment semantics from B3;
- fixed shared `max_speed` capacity scale `1..4`;
- matched committed timestep convention;
- common world geometry/scale where comparison requires it;
- primary allele/genotype/focal-trait evidence;
- founder reproductive-contribution evidence;
- distinction between representative seed storytelling and multi-seed robustness;
- claim/nonclaim boundaries.

Renderer-specific controls, layout, charts, animation rate, accessibility, and
interaction remain UI responsibility.

### Cinematic baseline to preserve

The B3 cinematic director is intentionally concrete rather than a universal film
DSL. Its durable lessons are:

- B3 science is consumed from the renderer-neutral handoff and committed evidence;
- fixed scientific scales are shared across matched arms;
- representative organisms/events are selected by B3, not by the renderer;
- focus is a presentation channel independent of scientific fill and body size;
- committed events support causal labels, while identity continuity remains
  non-causal;
- representative-run episodes explain mechanism, while run-level confirmation
  supports robustness;
- camera, shot timing, temporal compression, and evidence-chart choreography remain
  renderer-only concerns;
- the full portfolio film is a deliberate reproducible artifact, while routine CI
  retains short generic/science-aware/B3 smokes.

Do not generalize this into a broad camera DSL or scenario-presentation schema
without multiple future films demonstrating a genuinely repeated contract.

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

Future biological cases may justify higher-copy pairing policies, preferential or
random bivalent formation, multivalent models, chromosome-specific crossover
behavior, multiple crossovers, or lifecycle-sensitive gamete formation. Add only
the policies required by concrete modeled biology. Do not push meiosis vocabulary
into the frozen kernel or general propagation contracts.

## Front C — Richer mating systems

Shared reproduction already separates participants, investors, genetic
contributors, and production sources. Future cases may explore asymmetric roles,
multi-participant groups, hermaphroditic systems, role-sensitive mate choice,
contributor/investor subsets, or lifecycle-specific production sources. Mating
system composition should remain separate from low-level inheritance.

## Front D — Richer development and G×E

Potential concrete directions include nonlinear reaction norms, developmental
stages/history, richer developmental stochasticity, and reversible adult
plasticity distinct from lifetime developmental targets. Preserve distinctions
among inheritance, genetic expression, development, environment, and current
mutable state.

## Front E — Richer evolutionary ecology

The ecological foundation includes explicit static resource geography and a
confirmed environment-dependent selection use case. Future ecology should continue
to drive requests for new biology where possible: richer resource competition,
movement/behavior tradeoffs, predation/prey coevolution, life-history tradeoffs,
spatial structure, and fluctuating or heterogeneous selection regimes.

Selection should continue to emerge from differential persistence and propagation,
not from a kernel-owned scalar `fitness` field.

## Observation and statistical analysis

E1 defines the durable scientific-measurement semantics needed by the current
controlled experiment sequence while deliberately stopping short of a broad
statistics framework. Future repeated experimental patterns may justify additional
reusable statistical contracts, but only after concrete consumers establish what
actually repeats.

Preserve the distinction among:

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

Do not put arbitrary metric/property bags into the simulation or observation
layers. Undefined post-extinction quantities remain undefined rather than becoming
zero, and presentation remains a consumer rather than an authoritative calculator.

## Future native execution backend

A Rust/C++ backend remains an evidence-driven future front rather than a current
architecture target. If measured workloads justify it, the desired direction is a
validated static typed simulation plan feeding interchangeable Python-reference and
native execution backends that produce the same committed result values.

Do not create that abstraction until real profiling demonstrates both the need and
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
- Preserve run/seed as the experimental replicate for stochastic treatment
  comparisons unless a later concrete design justifies another experimental unit.
- Prefer readable maintainable architecture over micro-optimization.
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

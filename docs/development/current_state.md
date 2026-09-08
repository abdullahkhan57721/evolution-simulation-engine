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

Do not store volatile commit SHAs, CI state, detailed ticket progress, or full PR
history here.

## Architectural baseline

The repository retains a frozen domain-neutral transactional kernel with general
evolution and biological specialization above it:

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
renderer-neutral scientific meaning
        ↓
interactive / cinematic presentation
```

Presentation interpolation, camera behavior, layout, and renderer state are never
scientific evidence.

## Settled modeled/scientific capabilities

The general-evolution layer remains domain-neutral. Biological specialization owns
concrete genetics, inheritance, development, life history, growth, energetics,
feeding, movement, predation, reproduction, spatial ecology, and biological world
state above those contracts.

Reproduction distinguishes participants, investors, genetic contributors, and
production sources. Chromosome transmission separates copy structure, pairing,
recombination, segregation, and gamete formation. Current simple Mendelian/diploid
policies remain concrete policies rather than universal architecture rules.

B1 added immutable spatial renewable-resource placement policies. B2 established
`max_speed` as a real inherited benefit/cost axis in the richer reference ecology.
B3 independently confirmed a bounded environment-dependent selection story with
mechanism, counterbalance, sensitivity, and representative-run evidence. None of
these changes introduced a kernel-owned scalar fitness abstraction.

Committed evidence is first-class. Existing evidence includes population and
spatial observations, selected individual genetic-trait records, allele/genotype
composition, pedigree/life-history evidence, causal event/effect telemetry,
deterministic seeded execution, checkpoint/resume, and reproducible multi-seed
experiment export.

## Controlled experimental-evolution sequence

E1–E7 form a completed first causal proof sequence separate from the richer B3
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
        ↓
E7 focal mutation, adaptation, and convergence
```

The durable experiment semantics are:

- one simulation run/seed is the current experimental replicate;
- organisms within a run are dependent observations, not extra replicates;
- event step `t` aligns to committed state `t + 1`;
- denominators, extinction, right-censoring, discovery/confirmation roles, and
  representative storytelling remain explicit;
- pure scientific measurements consume committed evidence;
- experiment-specific integrity checks remain concrete;
- no universal metric registry, statistics DSL, or simulation dependency on
  analysis code exists.

E3 independently confirmed a speed-3 performance region in its separated-resource
corridor while the local-resource arm remains speed-neutral. E4 confirmed selection
on equal standing variation toward speed 3 in that corridor, with full focal
composition and counterbalanced founder-ID assignment. E5 demonstrated
finite-population stochasticity and weak-selection reversals without manufacturing
fixation. E6 added exact resident-state/RNG forking and matched rare-lineage
admission, supporting speed 3 as a bounded candidate invasion-stable strategy
against reciprocal speed 4 rather than a formal ESS.

E7 added only a narrow optional focal mutation-policy seam to controlled locomotion;
existing E2–E6 callers remain mutation-off by default. Its frozen high-mutation,
full-distribution confirmation **does not show cross-start convergence**. Starts 1
and 7 remain strongly separated from the reference region while start 3 stays
bounded inside speeds 2..4. The mechanism evidence shows why: speed-6/8 descendants
from the high start do not reproduce within the horizon, so repeated first-step
mutation does not propagate toward lower speeds; the low start can reproduce through
speed 2 toward speed 3 but also accumulates substantial mass at the legal speed-0
boundary. E7 therefore bounds the E3–E6 story: favorable performance, selection,
and invasion when a strategy is already present do not guarantee mutation-driven
accessibility from distant starting states.

See `docs/e7_mutation_driven_adaptation.md` for the frozen assay, confirmation
criteria, mechanism evidence, and bounded nonclaims.

## Confirmed B3 flagship

B3 remains the richer integrated reference-ecology flagship. It compares matched
uniform renewable-resource placement against compact radius-1 patches using
balanced homozygous `max_speed = 1 / 4` standing variation, ordinary sexual
inheritance, mutation off, and a fixed horizon.

Independent confirmation shows the compact treatment exceeds matched uniform
control at the predeclared step-30 focal readout across the frozen confirmation
seeds. Founder reproductive contribution, founder-label counterbalancing, and
radius-2 geometry sensitivity support and bound the interpretation. Representative
seed 5 and its real committed mechanism episodes are selected by B3 science, not
presentation code.

Scenario origin and validated scenario identity remain distinct. The radius-2
sensitivity fork keeps B3 origin but loses canonical radius-1 validated identity and
cannot automatically inherit the original B3 representative/headline cinematic
handoff.

## Evolution Experiment Workbench — stable foundation

WB1–WB6 now establish and review the complete first Workbench architecture:

```text
semantic Study / curated scenario / concrete experiment definition
        ↓
bounded recipe or experiment-pattern resolution
        ↓
immutable manifest / treatment specification
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

### Durable Workbench contracts

- editable semantic intent is separate from immutable resolved manifest meaning;
- stable scientific IDs do not depend on Python paths or object identity;
- exact save/load uses the stored manifest rather than re-resolving current defaults;
- incompatible exact reproduction fails explicitly rather than migrating silently;
- mutable recorder/spec/runtime objects are reconstructed fresh;
- EvidencePlan remains separate from simulation intent;
- runs retain exact revision, manifest digest, EvidencePlan, and scientific
  provenance;
- forks create new immutable revisions and preserve parent history;
- scenario origin is distinct from validated scenario identity;
- factor, treatment, counterbalance/blocking, replicate, and measurement remain
  separate concepts;
- Results navigation does not recalculate authoritative science;
- missing evidence makes an analysis unavailable rather than inferable;
- scientific encodings remain renderer-neutral;
- presentation settings do not alter scientific manifests.

### WB1–WB5 product capabilities

WB1 provides bounded controlled-locomotion authoring over the characterized E3
surface. WB2 provides canonical B3 exact reproduction plus one explicit radius-2
scientific fork. WB3 provides concrete E3 max-speed sweep and E4 matched-environment
experiment definitions. WB4 provides the first richer bounded reference-ecology
custom Study with explicit Guided/Advanced/Expert/Extension support metadata and
recipe-local applicability/normalization. WB5 adds Study-facing Results navigation
and downstream V2/V3 presentation adapters without creating duplicate science or a
universal result/presentation framework.

The WD2 labels `Study / Simulation / Evidence / Experiment / Results /
Presentation` remain a product/navigation model rather than a required class
hierarchy. `Run` remains an action.

### WB6 architecture review and diagnostics

WB6 confirms the Workbench foundation is stable enough for incremental future
growth. It found no need to alter `SimulationSpec`, `BiologicalSimulationSpec`,
`GeneticArchitecture`, the kernel, experiment science, or presentation ownership.

One shared abstraction is now genuinely earned: a small Workbench-owned diagnostic
value carrying stable code, severity, optional semantic slot/context, concise
message, and optional remediation. It is used only for Workbench-owned support
facts demonstrated by WB1–WB5:

- incomplete/unsupported authoring choices;
- irrelevant conditional values normalized away by WB4;
- exact saved-manifest reproduction incompatibility;
- B3 validated-scenario identity loss;
- unavailable analysis/presentation because required evidence was not recorded.

`WorkbenchReadiness` remains small: Draft, Blocked, or Ready. Readiness diagnostics
are blocking errors. Warnings/advisories such as irrelevant-state notices,
scenario-identity loss, and high-volume spatial evidence remain distinct.

Lower-layer diagnostics remain authoritative. `DependencyReport` already exposes
structured missing requirements and requiring-component provenance;
`SimulationSpecValidator` owns generic preflight, `BiologicalSimulationSpec` owns
biological preflight, and `GeneticArchitecture` owns genetic coherence. WB6 does
not add a second non-raising lower preflight API or parse arbitrary lower exception
prose into Workbench codes.

See `docs/workbench_architecture_review.md` for the complete post-WB6 architecture
review.

## Workbench application shell and scientific execution

WU1 integrates the settled Workbench into the Streamlit application without adding
another scientific schema. The application enters through Home, then opens a
persistent Study shell with `Simulation / Evidence / Experiment / Results /
Presentation`; `Run` is an action rather than a sixth page.

New Study exposes only current supported concrete families: canonical radius-1 B3,
controlled single-run/max-speed-sweep/environment-selection workflows, and bounded
Reference Ecology. Open/Save dispatches directly through the concrete Workbench
format and pattern identities and each owning `from_json()` / `to_json()` contract.
The UI does not re-resolve stored intent, migrate unknown formats, wrap artifacts in
a universal Study envelope, or reconstruct unavailable historical result payloads.

WU2 fills the Simulation section without adding another authoring framework.
Controlled-locomotion Studies edit only their existing semantic slots. Reference
Ecology uses the current WB4 Guided/Advanced metadata, applicability, readiness, and
normalization contracts; Guided and Advanced are disclosure levels over the same
intent, Expert remains empty, and Extension/internal capability is not editable.
The page distinguishes explicit selections from derived and frozen recipe meaning.

Saved scientific revisions remain immutable. UI draft state is transient; saving an
edit calls the existing concrete fork API and creates a child revision with parent
lineage. The UI renders the existing controlled/reference/B3 semantic-diff contracts
rather than a new diff engine. Canonical B3 remains read-only except for the explicit
supported radius-2 sensitivity fork, which preserves B3 origin while losing validated
radius-1 identity.

WU3 completes the first end-to-end scientific execution path through the same shell.
Evidence is first-class: controlled/reference plans use their existing concrete
EvidencePlan types and immutable fork APIs, Reference Ecology surfaces its existing
non-blocking advisories, and frozen/experiment-required B3/E3/E4 evidence stays
locked. Experiment authoring remains concrete: E3 edits only max-speed levels and
replicate seeds, E4 keeps its resource-geography factor, control/treatment roles,
standing focal composition, and counterbalance fixed while editing supported seeds,
and B3 remains curated/read-only. Displayed run matrices and B3 case counts come from
the authoritative Workbench expansion/compilation functions rather than UI-owned
design logic.

Readiness continues to come from the existing Workbench contracts. `Run` opens a
reviewable Run Plan derived from the exact current artifact before synchronous
execution. Revision-backed pending Simulation/Evidence edits receive one immutable
child revision before execution; E3/E4 keep their existing immutable experiment-value
ownership rather than gaining invented revision lineage. Execution delegates only to
the five existing concrete Workbench runners. Successful revision-owned runs attach
returned provenance with existing `.with_run(...)` semantics, while authoritative
result objects remain session-owned for downstream Results work. Compile/preflight
failure leaves the saved artifact unchanged and is surfaced without fabricated
Workbench diagnostics.

WU3 Results is intentionally a thin completion handoff: existing run/revision
identity when owned, recorded evidence, simulation count, and honest handling of
historical run references whose full payload is unavailable. Complete Study analysis,
Run Explorer, world embedding, cinematic integration, and renderer controls remain
downstream work.

The prior world-centered V2 workspace and renderer implementation remain available
for later integration rather than being redefined by WU1–WU3. See
`docs/workbench_ui.md`.

## Official Workbench support envelope

The distinction remains:

```text
engine-valid
    ≠ Workbench-supported
    ≠ Guided
    ≠ experiment factor levels
```

Controlled locomotion remains bounded to `max_speed` 1..10, the two characterized
E3 geographies, explicit seed, and its concrete evidence streams. Canonical B3 is a
curated exact-reproduction workflow; radius-2 remains a specific supported
sensitivity fork rather than generic authoring.

WB4 remains the explicit tiered recipe:

- **Guided:** world/founder/run settings, founder performance/sensing values,
  supported exploration movement, and uniform/two-patch geography;
- **Advanced:** Gaussian spread when applicable, renewable resource quantity and
  cadence, two-patch geometry, mutation controls, and recombination probability;
- **Expert:** intentionally empty;
- **Extension/internal:** arbitrary resource/policy graphs, extra traits/tradeoffs,
  genetics/expression/ploidy, inheritance, reproduction, lifecycle, targeted
  movement, and development/G×E editing.

WU2/WU3 promote no capability merely because the lower engine can represent it.

## Results and presentation boundary

Workbench Results is thin navigation over authoritative artifacts plus exact
association/provenance. It does not calculate E1/E3/E4/B3 science.

If an analysis or presentation requires evidence the run did not record, the
Workbench exposes structured remediation naming the missing evidence and requiring
rerun of the same scientific Study revision with an appropriate EvidencePlan. It
never reconstructs events, genetics, pedigree, or spatial history from weaker
artifacts.

Presentation stays downstream:

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

The V2 adapter builds existing `WorldPresentationFrame` values from recorded WB4/B3
evidence. The V3 adapter feeds validated canonical B3 results into the existing
B3-specific director. Renderer-specific layout, controls, camera, timing, materials,
charts, and animation remain presentation concerns.

## Current development front

The Workbench foundation, the first E-series controlled-science program, and the
first end-to-end Workbench scientific execution path are now settled enough to move
past foundational authoring/execution integration.

WU1–WU3 provide the persistent Study shell, bounded Simulation and Evidence
authoring, concrete E3/E4/B3 Experiment presentation, immutable revision/fork
behavior, Workbench readiness, reviewable Run Plan, authoritative synchronous
execution, provenance attachment, and a thin session-owned Results handoff. The next
product front is downstream Results/world/presentation integration through the same
shell. It should consume existing WB5 result/presentation contracts and authoritative
WU3 result ownership rather than reopen the Workbench backend or create a statistics
framework. The exact next WU milestone identity should be set by its focused Issue
against current `main` rather than invented in this orientation document.

E7 closes the current E1–E7 causal sequence with a confirmed negative convergence
result. Do not post-hoc lengthen, enrich, or retune E7 to manufacture convergence.
A future controlled-science milestone should begin from a new predeclared question
and new scientific identity. Potential pressure includes evolutionary accessibility
across longer generational turnover, richer reproduction/resource opportunity,
richer genetics, or changing ecology, but none of those is automatically the next
milestone merely because E7 exposed the mechanism.

Longer-term modeled fronts remain richer genetic expression, chromosome
pairing/recombination, mating systems, development/G×E, and evolutionary ecology.
A native Rust/C++ execution backend remains evidence-driven future work.

## Known architectural friction

### Concrete persistence remains intentional

WB1, WB2, WB3, and WB4 persist different shapes because their responsibilities
still differ. WB5/WB6 and WU1–WU3 do not reveal enough identical persistence or
execution responsibility to earn a universal saved Study/Experiment/Results root.

### Broader Workbench diagnostics remain bounded

The shared diagnostic value is not a universal validation system. A future UI may
eventually need aggregate readiness across simulation, evidence, experiment, and
analysis, but that should be designed from the actual workflow rather than added as
a speculative state machine.

### Presentation bundles remain purpose-specific

The existing UI/cinematic bundles are not universal scientific result or scene
models. New media should reuse renderer-neutral scientific meaning where it truly
repeats while keeping renderer mechanics local.

### Scientific scope remains illustrative

The reference ecology, B3 flagship, and E2–E7 controlled sequence are software and
modeling demonstrations, not species-calibrated predictive ecological models.

## Collaboration model

Use ChatGPT primarily for architecture, roadmap sequencing, consequential public
contracts, tightly scoped sequential implementation, and independent PR
review/merge decisions. Use Codex selectively for execution-heavy work behind
settled interfaces.

For substantial work follow:

```text
Issue → branch → implementation → early PR → CI → exact-head review
      → squash merge → main verification
```

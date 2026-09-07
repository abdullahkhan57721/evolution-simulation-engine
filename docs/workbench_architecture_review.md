# Workbench Architecture Review

WB6 is the first full architecture review of the implemented Evolution Experiment
Workbench after WB1–WB5. The review starts from repository behavior rather than the
pre-implementation WD studies. Its conclusion is that the Workbench foundation is
stable and future product growth should normally be additive.

## Executive conclusion

The implemented Workbench preserves both intended authority chains:

```text
Workbench semantic authoring
        ↓
bounded recipe / concrete experiment pattern
        ↓
existing preset, scenario, or experiment composition
        ↓
BiologicalSimulationSpec
        ↓
SimulationSpec
        ↓
frozen kernel
```

and:

```text
modeled simulation
        ↓
committed evidence
        ↓
pure scientific measurement
        ↓
replicate outcome
        ↓
treatment comparison
        ↓
renderer-neutral scientific meaning
        ↓
presentation
```

WB6 found no reason to alter the kernel, `SimulationSpec`,
`BiologicalSimulationSpec`, `GeneticArchitecture`, the established experiments, or
the scientific visualization boundary. The one shared abstraction newly earned by
WB1–WB5 is a small Workbench-owned diagnostic value with stable code, severity,
optional semantic context, human explanation, and optional remediation. It does
not replace lower validation or become a validation engine.

The practical answer to the milestone's final question is **yes**: the Workbench is
now stable enough that future growth should primarily add bounded recipes, semantic
choices, evidence options, concrete experiment patterns, or evidence-backed support
promotions rather than redesigning the Workbench foundation.

## 1. Final implemented architecture

The Workbench is a scientific-study product layer. It owns the association among
human semantic authoring, exact resolved scientific meaning, evidence intent,
experiment design where applicable, saved revision lineage, completed-run
provenance, result navigation, and downstream presentation routing.

It does **not** own biological truth, kernel execution semantics, scientific
measurement formulas already owned by experiments, or renderer choreography.

The implemented product path is:

```text
Study
  ├─ Simulation authoring
  │    └─ semantic intent → immutable resolved manifest → existing composition
  ├─ Evidence intent
  │    └─ fresh existing recorders before lower preflight
  ├─ Experiment
  │    └─ concrete factor/treatment expansion where the pattern owns it
  ├─ Results
  │    └─ views over authoritative evidence/outcomes with exact provenance
  └─ Presentation
       └─ downstream UI/cinematic adapters over recorded scientific artifacts
```

`Run` remains an action. The product labels do not require a Python class hierarchy.

## 2. Final dependency graph

The durable dependency graph is:

```text
configuration / kernel / general evolution / biology
                         ↑
                       presets
                         ↑
                    experiments
                         ↑
                     Workbench
                      ↙     ↘
                    UI     cinematic
```

More precisely, Workbench may use existing presets, experiment contracts,
observation values, telemetry, and scientific encodings. Lower engine/domain/science
packages do not import Workbench. Workbench does not import UI or cinematic code.
UI and cinematic code may consume Workbench values because they are downstream
presentation consumers.

Architecture tests permanently encode these directions. WB5 corrected an earlier
guard that was too coarse by distinguishing legitimate downstream UI/cinematic
imports from forbidden lower-layer Workbench dependencies.

## 3. Durable Workbench contracts

The following contracts are now durable:

1. authoring intent is semantic, immutable, and distinct from its resolved manifest;
2. resolved manifests are immutable scientific values, not editable forms;
3. scientific identity uses stable recipe/factor/slot IDs, never Python class paths;
4. exact save/load deserializes the stored manifest instead of re-resolving old
   intent under current defaults;
5. exact reproduction requires declared compatible recipe/compiler/software
   identity and fails explicitly when it cannot be honored;
6. mutable runtime recorders/specifications are reconstructed fresh;
7. EvidencePlan remains separate from simulation intent;
8. lower scientific, biological, genetic, and generic validation remains
   authoritative;
9. a completed run remains tied to exact revision, manifest digest, EvidencePlan,
   and existing scientific provenance;
10. forks create new immutable revisions and never mutate their parent;
11. semantic diff is recipe-scoped and based on stable scientific meaning;
12. scenario origin is distinct from validated scenario identity;
13. experiment factor identity is distinct from implementation fields;
14. factor, treatment, counterbalance/blocking, replicate, and measurement remain
   different concepts;
15. Results navigation does not recalculate authoritative science;
16. missing evidence makes an analysis unavailable rather than inferable;
17. scientific encodings remain renderer-neutral;
18. presentation settings do not change scientific manifests.

## 4. Transient and internal concepts

Several values remain intentionally runtime/internal:

- mutable recorder instances;
- compiled `SimulationSpec` / `BiologicalSimulationSpec` object graphs;
- runtime engines and `SimulationState` values;
- Streamlit/Plotly/Manim/renderer state;
- interactive visibility and selection state;
- camera, timing, focus, layout, and choreography;
- temporary expansion objects used to run concrete experiment treatments.

They are not persisted as scientific identity.

## 5. Product/navigation concepts that did not become classes

`Study`, `Simulation`, `Evidence`, `Experiment`, `Results`, and `Presentation` are
useful product sections but are not one-to-one framework classes.

- **Study** is the containing user concept and is represented by concrete saved
  revision contracts where persistence is required.
- **Simulation** is represented by recipe-specific intent and manifest values;
  compile/run are actions.
- **Evidence** is represented by concrete EvidencePlans and existing committed
  artifacts.
- **Experiment** is represented by concrete WB3 definitions only where an actual
  experiment pattern exists.
- **Results** is primarily navigation over existing outcomes/evidence.
- **Presentation** is downstream and renderer-owned.

No universal `StudyRoot`, `SimulationBlueprint`, `Experiment`, `Result`, or
`PresentationSpec` was needed.

## 6. Final official support envelope

Support remains deliberately narrower than engine validity.

### Controlled-locomotion recipe

Official Workbench support remains the characterized WB1/E3 surface:

- `max_speed` 1 through 10;
- `local_resource` and `separated_corridor` geographies;
- explicit reproducibility seed;
- concrete population focal-trait and committed-event evidence.

The lower controlled-locomotion configuration accepts a broader domain. That lower
range is not automatically Workbench support.

### Curated B3

Canonical B3 remains a trusted curated exact-reproduction workflow. The radius-2
resource-geometry variant remains one explicitly supported B3-derived sensitivity
fork. It is **not** promoted into generic Guided resource editing and does not
inherit canonical B3 validated identity, representative-story semantics, or the
headline-claim cinematic handoff.

### Controlled experiments

WB3 officially supports two concrete experiment patterns:

- max-speed sweep over the stable controlled-locomotion max-speed factor;
- matched local-versus-separated E4 resource-environment comparison with frozen
  standing composition and explicit founder-ID counterbalance.

Recipe eligibility does not make every authorable slot factorable.

### Bounded reference ecology

WB4's persisted support metadata remains authoritative for that recipe.

**Guided** includes world dimensions, founder population/energy, horizon, seed,
founder max speed, founder sensory range/accuracy, the four supported exploration
movement choices, and uniform versus bounded two-patch resource geography.

**Advanced** includes Gaussian spread when applicable, renewable resource
quantity/cadence, explicit two-patch geometry when applicable, mutation enablement
and mutation parameters when applicable, and recombination probability.

**Expert** remains empty. WB6 found no stable official choice that requires an
Expert tier merely to fill the category.

**Extension/internal** remains the broader engine-representable space: arbitrary
resource-placement policies, arbitrary patch topology, extra reference traits and
tradeoffs, arbitrary genetics/ploidy/expression, inheritance switching,
reproduction-system composition, targeted-movement graphs, lifecycle-process
composition, and development/G×E editing.

## 7. Guided / Advanced / Expert / Extension audit

WB6 does not promote any existing capability to a broader tier.

The reason is evidence, not conservatism for its own sake. A Guided choice should
have stable semantic meaning, tested typed composition, deterministic persistence,
transparent derivation, useful evidence, strong validation/diagnostics, deliberate
supported ranges, and sufficient scientific characterization. WB4's existing
Guided values meet those requirements within the bounded recipe. Its Advanced
values are fully supported but require more scientific judgment or conditional
applicability. The B3 radius-2 fork is a scenario-specific sensitivity, not a
candidate general authoring tier.

Thus the durable distinction remains:

```text
engine-valid
    ≠ Workbench-supported
    ≠ Guided
    ≠ experiment factor levels
```

## 8. Diagnostic ownership model

WB6 promotes one earned shared Workbench concept:

```text
WorkbenchDiagnostic
    code
    severity
    optional semantic slot
    optional context
    concise message
    optional remediation
```

This value is owned only by Workbench-facing support behavior. It is used for
concrete cases demonstrated across WB1–WB5:

- incomplete required selection;
- unsupported Workbench value/evidence choice;
- irrelevant stale parameter that a recipe will normalize away;
- exact saved-manifest reproduction incompatibility;
- B3 validated-scenario identity loss;
- unavailable analysis because required evidence was not recorded.

`WorkbenchReadiness` remains small: Draft, Blocked, or Ready. Readiness diagnostics
are blocking errors. Non-blocking warnings such as irrelevant-state notices,
scenario-identity loss, and evidence-volume advisories remain separate from
readiness.

Lower layers continue to own their own facts and errors. Workbench does not parse
arbitrary exception strings into codes.

## 9. Structured lower-layer diagnostics decision

No new lower-layer diagnostic API is justified.

`DependencyReport` already structurally represents required, provided, and missing
capabilities plus the component type declaring each requirement. The generic
`SimulationSpecValidator` builds that report and intentionally raises when it is
unsatisfied. `BiologicalSimulationSpec` separately owns biological preflight and
`GeneticArchitecture` owns genetic coherence.

WB1–WB5 did not require a second non-raising generic preflight path. Adding one in
WB6 would duplicate an existing representation and create architecture for a
hypothetical consumer. Lower layers therefore remain unchanged.

## 10. Exact-reproduction behavior

Exact reproduction means:

```text
stored immutable manifest
    + compatible recipe/compiler/software identity
        ↓
reconstruction of the same supported scientific configuration
```

It never means re-resolving historical intent using current defaults.

WB6 adds structured Workbench remediation to exact-reproduction incompatibility but
leaves recipe-specific compatibility checks where they already belong. The
remediation distinguishes two honest operations:

- use a compatible implementation to reproduce the stored manifest exactly; or
- create a new Study revision under current software.

A migration/upgrading framework remains unnecessary. If one is eventually needed,
it must create new scientific identity rather than masquerade as exact reproduction.

## 11. Scenario and fork semantics

Canonical B3 persists both scientific origin and exact validated scenario identity.
A radius-2 fork keeps B3 origin but loses validated radius-1 identity.

WB6 makes that loss explicitly diagnosable as a warning. The warning does not infer
new claims; it simply reports the already-established status and tells downstream
consumers not to treat scientific lineage as validation.

WB5's cinematic adapter continues to require canonical validated B3 identity for
the original representative/headline story. A derived fork can still be inspected
descriptively using recorded evidence.

## 12. Experiment and factor architecture

WB3 remains concrete and healthy:

```text
parameter
    ≠ factor
    ≠ treatment
    ≠ counterbalance / blocking
    ≠ replicate
    ≠ measurement
```

The E3 sweep factor is the stable max-speed semantic slot. The E4 primary factor is
resource geography; founder speed-to-ID ordering remains counterbalance metadata.
B3 confirmation seeds, counterbalance, representative storytelling, and radius
sensitivity retain distinct roles.

E5/E6 add useful scientific designs but do not create a repeated Workbench pattern
requiring a generic experiment DSL. They remain science-layer pressure for future
concrete Workbench consumers, not permission to generalize now.

## 13. Evidence architecture

Evidence remains a separate Study concern:

```text
EvidencePlan
        ↓
fresh concrete existing recorders
        ↓
attached before biological/generic preflight
        ↓
committed evidence
        ↓
existing measurement/result consumers
```

No evidence registry or solver exists. Concrete recipes and experiments declare the
specific evidence they support or require.

WB5 established post-run `AnalysisAvailability`. WB6 adds structured remediation:
when required evidence was not recorded, the user is told which evidence is
missing and to rerun the same scientific Study revision with an appropriate
EvidencePlan. Missing events, genetics, pedigree, or spatial history are never
reconstructed from weaker artifacts.

WB4's spatial replay advisory remains a distinct non-blocking storage-volume
warning rather than a readiness error.

## 14. Results architecture

Results remain authoritative in their existing science packages. Workbench result
views own only association and navigation:

- exact revision/manifest/EvidencePlan attachment;
- stable treatment/factor/replicate/counterbalance identity;
- evidence availability;
- direct references to existing replicate outcomes and summaries;
- scenario status needed for downstream routing.

The Workbench does not calculate E1 locomotion measurements, E3 treatment summaries,
E4 evolutionary outcomes, B3 genetic summaries, founder contribution, robustness,
or causal interpretation.

No metric registry, statistics DSL, scalar fitness result, or universal result
hierarchy is earned.

## 15. Presentation boundary

The presentation path remains:

```text
scientific evidence / existing result
        ↓
renderer-neutral scientific meaning
        ↓
renderer-specific interaction or choreography
```

`ContinuousTraitEncoding` remains the shared fixed scientific scale where it is
actually useful. The V2 adapter consumes recorded evidence to build existing
`WorldPresentationFrame` values. The V3 adapter passes validated B3 evidence into
the existing B3-specific director.

WB6 lets presentation-unavailable errors carry the Workbench structured diagnostic
that explains missing evidence. That is routing/remediation metadata, not scientific
calculation.

Renderer settings still do not enter manifests or exact-reproduction identity. No
universal replay scene graph or broad `ScenarioPresentationSpec` is needed.

## 16. Architectural violations discovered and corrected

WB6 found no violation of the core simulation/evidence dependency direction.

It did find one layering smell: Workbench diagnostic primitives originally created
for WB1 had become shared by WB2 and WB4 while still physically living in the
controlled-locomotion recipe module. Three concrete consumers now demonstrate a
truly shared Workbench responsibility, so WB6 moves the implementation to a neutral
`workbench.diagnostics` module and strengthens it with the fields current user
flows need.

WB6 also makes two previously prose-only support states structured without changing
scientific authority:

- irrelevant WB4 values that will be normalized away;
- WB5 analysis/presentation unavailability and rerun remediation.

No lower scientific/model violation required repair.

## 17. Rejected abstractions that remain rejected

WB6 re-evaluated the major WD5 non-goals. The following remain unearned:

- `SimulationBlueprint` or universal simulation configuration;
- composition graph or universal policy descriptor;
- generic configuration DSL;
- global capability graph / compatibility matrix;
- plugin architecture or reflection-based discovery;
- arbitrary policy composer;
- generic genetics/inheritance editor;
- generic environment/population hierarchy;
- generic factorability interface or experiment DSL;
- generic factorial builder;
- generic config-diff system;
- evidence registry/solver;
- metric registry or statistics DSL;
- intervention language;
- universal diagnostics framework;
- migration engine;
- universal replay/scene graph;
- broad scenario-presentation specification.

The concrete contracts still own their responsibilities cleanly, and the generic
alternatives would either steal lower-layer authority or introduce persistence/API
semantics unsupported by real users.

## 18. Newly earned abstraction

Exactly one new shared abstraction is earned: the small Workbench diagnostic value.

It passes the generalization test:

1. WB1, WB2/WB5 B3 flows, WB4, and WB5 analysis availability need the same
   user-facing responsibility;
2. the repeated responsibility is genuinely identical—describe a Workbench-owned
   support/status fact and optional remediation;
3. keeping the value under WB1 created misleading ownership;
4. sharing it reduces duplication and clarifies downstream UI handling;
5. it does not validate biology, genetics, experiment science, or kernel contracts;
6. it has no scientific persistence role and no registry semantics.

No second abstraction meets the same threshold.

## 19. Persistence audit

The existing persistence designs remain intentionally concrete:

- WB1 controlled-locomotion saved revision;
- WB2 B3-specific saved revision;
- WB3 concrete experiment definitions;
- WB4 reference-ecology saved revision.

Across them, semantic intent remains separate from resolved meaning, manifests are
immutable/canonical, stable IDs avoid Python paths, forks create new revisions,
parent revisions remain unchanged, and exact load does not silently inherit new
defaults.

The shapes still differ enough that a universal persisted Study root would add
abstraction without reducing real ambiguity. WB5 Results and Presentation did not
create a new persistence need.

## 20. Performance review

WB6 found no measured Workbench performance regression requiring optimization.
Existing performance guards cover reference simulation, kernel behavior, and world
presentation. WB4 already flags spatial replay as potentially high-volume. Experiment
matrix size and evidence payloads can become future product concerns, but no current
profile demonstrates a bottleneck that justifies caching manifest compilation,
changing persistence, or touching the kernel.

The correct WB6 performance change is therefore **none**.

## 21. Remaining risks

The main remaining risks are product breadth rather than foundational instability:

- future recipes may eventually demonstrate repeated persistence shape worth
  extracting, but four concrete persistence forms still differ materially;
- a future UI may need richer aggregated readiness over simulation, evidence,
  experiment, and analysis, but WB6 deliberately avoids inventing workflow states
  before that UI exists;
- E5/E6/E7 may eventually justify new concrete Workbench experiment patterns, but
  they should be added one at a time before considering generic design language;
- presentation preference persistence remains unearned;
- broader biological authoring needs scientific/support characterization before
  support-tier promotion.

## 22. Deferred scientific capabilities

WB6 deliberately adds no biology. Richer genetics/expression, chromosome pairing
and recombination, mating systems, development/G×E, evolutionary ecology, and
mutation-driven E7 science remain separate modeled/scientific milestones. Workbench
support should follow demonstrated scientific capability rather than drive lower
architecture.

## 23. Recommended next roadmap direction

The Workbench foundation should enter maintenance-and-extension mode.

A future Workbench milestone should start from a real user/scientific need and
normally take one of these forms:

```text
add bounded recipe
or
add semantic choice to an existing recipe
or
add evidence option with an existing recorder
or
add concrete experiment pattern
or
promote a support tier with evidence
or
add a downstream result/presentation consumer
```

Architecture redesign should require a repeated responsibility that cannot be owned
cleanly by current concrete contracts.

The controlled-science roadmap may continue independently. In particular, E7 can
advance mutation-driven adaptation science without acquiring a Workbench dependency.

## Final stability judgment

**Yes.** After WB6, the Workbench architecture is stable enough that ordinary future
growth should be incremental rather than foundational.

That judgment is conditional in the useful engineering sense: if multiple future
consumers expose the same new responsibility and current contracts cannot own it
cleanly, a new abstraction may become justified. The default, however, is no longer
"design the Workbench." The default is "add the next scientifically supported
capability through the existing Workbench boundaries."

# Evolution Experiment Workbench UI Reference

This document describes the settled **WU1–WU5 Streamlit reference product**. The
product semantics remain authoritative inputs to native migration, but Streamlit is
no longer the primary final-product frontend. ADR 0010 establishes PySide6 + Qt
Quick/QML as the primary application architecture; see `docs/desktop_workbench.md`
for the native boundary and Q-series handoff.

The application product model is organized around a persistent **Study** shell.
`Study` is a navigation concept, not a new scientific domain class or persistence
schema.

## Application structure

```text
HOME
├── New Study
└── Open Study

STUDY
├── Simulation
├── Evidence
├── Experiment
├── Results
└── Presentation

Run = action
```

WU1–WU5 prove this structure in Streamlit. The former top-level
Configuration → DashboardRun → Workspace mode switch is not the Workbench entry
architecture. Existing world-workspace and renderer modules are reused downstream
rather than becoming scientific ownership layers.

## Supported entry families

The reference shell exposes only concrete Workbench-supported entry paths:

- **Curated** — canonical radius-1 B3 Flagship;
- **Controlled** — one controlled-locomotion Study revision, the concrete max-speed
  sweep definition, or the concrete environment-selection comparison definition;
- **Custom** — the bounded Reference Ecology recipe.

The B3 radius-2 sensitivity is not an ordinary New Study choice.
Extension/internal reference-ecology composition is not exposed.

## Concrete persistence routing

The frontend inspects only persisted format identity, plus the existing concrete
experiment pattern identity when needed, and dispatches directly to the owning
loader:

```text
Workbench JSON
    ↓ inspect format_id / concrete pattern_id
    ├─ StudyRevision.from_json()
    ├─ B3StudyRevision.from_json()
    ├─ ReferenceStudyRevision.from_json()
    ├─ MaxSpeedSweepDefinition.from_json()
    └─ EnvironmentSelectionComparisonDefinition.from_json()
```

Downloading a saved Study calls the active concrete artifact's `to_json()` directly.
There is no universal Study envelope, generic recipe schema, manifest translation, or
UI migration layer. Historical manifests are never rebuilt from stored intent during
Open Study.

If a concrete loader reports an exact-reproduction incompatibility, the frontend
surfaces that failure and its Workbench remediation. It does not silently upgrade,
fix, or re-resolve the artifact.

## Simulation authoring

WU2 makes the Simulation section a concrete scientific-authoring surface without
introducing another configuration architecture.

The durable distinction is:

```text
explicit authoring intent
        ↓
resolved / derived scientific meaning
        ↓
frozen recipe assumptions
```

Authoring controls are presented separately from scientific meaning. Renderer
settings, package/class names, builders, and lower engine objects are not authoring
controls.

### Controlled locomotion

One controlled-locomotion Study exposes only the stable WB1 semantic slots:

- maximum speed;
- resource geography;
- reproducibility seed.

Draft readiness and resolution come from existing WB1 contracts. The frontend shows
resulting explicit values, derived treatment meaning, and fixed assumptions such as
clonal inheritance, mutation-off state, sensing/targeting, horizon, energetics, and
other fixed nonfocal biology from the resolved manifest.

### Reference Ecology Guided / Advanced disclosure

Reference Ecology consumes the current WB4 slot metadata, support tiers,
applicability, readiness, normalization, and manifest resolution.

**Guided** shows the supported core choices organized by scientific intent:
environment, population, movement/sensing, and run controls.

**Advanced** is disclosure over the same `ReferenceEcologyIntent`; it adds only
currently supported Advanced slots such as conditional Gaussian movement parameters,
renewable-resource settings, two-patch geometry, mutation controls, and
recombination. Switching disclosure mode does not itself change scientific state.

There is no manufactured Expert editor while the bounded recipe exposes no Expert
slots. Extension/internal engine capabilities remain outside official authoring.

Conditional fields use WB4's existing `is_slot_applicable()` contract. Hidden stale
values are normalized away by the existing reference-study persistence boundary and
never survive as saved scientific meaning.

## Immutable editing and semantic diff

The active saved revision is never edited in place.

```text
immutable saved revision
        ↓
private frontend draft
        ↓ existing Workbench readiness / resolution
        ↓
Save new revision
        ↓ existing concrete fork API
        ↓
immutable child revision
```

Controlled edits use `fork_study_revision()`. Reference Ecology edits use
`fork_reference_study_revision()`. The frontend does not invent revision semantics
for experiment definitions that do not already own them.

After a child is created, the Simulation section renders the existing concrete
semantic diff: `diff_study_revisions()`, `diff_reference_study_revisions()`, or
`diff_b3_study_revisions()`. It labels explicit/derived changes for readability but
does not implement a second diff engine.

## Curated B3 behavior

Canonical B3 is a validated, mostly read-only scientific Study rather than a custom
simulation form. The Simulation section exposes exact scenario identity/origin,
matched environments, focal trait/founder design, horizon, mutation/inheritance
assumptions, treatment integrity, and counterbalance design from the stored manifest.

The one supported sensitivity operation is explicit:

```text
validated radius-1 B3
        ↓ fork_b3_study_revision()
radius-2 B3-derived Study
```

The child preserves B3 origin but loses validated radius-1 identity. The frontend
does not call the child the B3 flagship.

## Evidence authoring

WU3 makes Evidence a first-class Study section. Evidence remains separate from
Simulation intent and uses only concrete evidence contracts already owned by the
Workbench.

Controlled single-run and Reference Ecology revisions expose their current supported
evidence streams in scientific language. Changing either evidence plan creates a new
immutable child revision through the existing concrete fork API. Reference Ecology
surfaces existing non-blocking advisories such as the high-volume spatial-history
warning without turning Ready into Blocked.

Frozen or experiment-required evidence remains locked:

- canonical B3 uses its frozen required evidence set;
- E3 uses its exact sweep-required evidence;
- E4 uses its exact comparison-required evidence.

The frontend does not manufacture recorder choices, infer missing evidence after a
run, or create invalid experiment evidence plans.

## Concrete Experiment design

WU3 renders only experiment patterns that already exist.

### E3 max-speed sweep

Maximum speed remains the scientific factor and replicate seed remains replicate
identity. Editable levels and seeds validate through `MaxSpeedSweepDefinition`; the
displayed run matrix comes from `expand_max_speed_sweep()`.

### E4 environment-selection comparison

Resource geography remains the primary factor. Control/treatment role, replicate
seed, standing focal composition `(1, 3, 9)`, and founder-order counterbalance remain
separate design semantics. Only the supported replicate-seed choice is editable. The
displayed matched design comes from `expand_environment_selection_comparison()`.

### B3 curated design

B3 remains read-only. Its primary confirmation, radius sensitivity when applicable,
counterbalance, and total simulation count come from `compile_b3_curated()`. Same-seed
control/treatment pairs are described as matched/blocked by seed; the frontend does
not claim their trajectories remain lockstep-identical after treatment divergence.

Controlled single-run has no multi-treatment experiment. Reference Ecology has no
generic controlled-experiment definition in the current support envelope.

## Readiness, Run Plan, and execution

The reference shell uses existing concrete Workbench readiness as authoring authority.
Draft / Blocked / Ready and Workbench-owned diagnostics/remediation are surfaced
without duplicating lower generic, biological, genetic, or scientific preflight.

`Run` remains an action. It binds owned transient scientific draft state to an exact
immutable owner and opens a reviewable Run Plan derived from that artifact. Execution
delegates only to existing concrete Workbench runners:

```text
StudyRevision                         → run_study_revision()
ReferenceStudyRevision                → run_reference_study_revision()
B3StudyRevision                       → run_b3_study_revision()
MaxSpeedSweepDefinition               → run_max_speed_sweep()
EnvironmentSelectionComparisonDefinition
                                      → run_environment_selection_comparison()
```

The frontend does not instantiate `SimulationEngine`, rebuild run configurations,
reproduce experiment expansion, or add a second preflight system.

Successful revision-owned runs retain the authoritative result object in session and
replace the active revision with the existing immutable `.with_run(...)` snapshot
using returned provenance. E3/E4 results remain authoritative concrete result
objects without invented Study-level run identity. Failure leaves the exact saved
artifact unchanged.

The Streamlit reference currently invokes these runners synchronously. Q0 proves that
the native frontend can adapt the same synchronous Workbench runner through a narrow
Qt worker without changing scientific execution semantics.

## Results and run exploration

WU4 makes Results a first-class scientific workspace without adding another result
hierarchy or scientific-analysis framework. It binds active artifacts and current
result objects through existing WB5 `inspect_*_results()` contracts.

Every supported family follows:

```text
Overview → Explore → Analysis → Provenance
```

Navigation remains scientifically concrete rather than flattened into a universal
replicate schema.

- **Controlled single-run** exposes recorded population history and existing E1
  locomotion replicate measurement behind evidence availability.
- **Reference Ecology** exposes population, committed events, pedigree/life history,
  allele/genotype composition, and committed spatial history independently.
- **E3** preserves maximum speed as factor, exact replicate seed, treatment ID, and
  manifest digest, and passes through existing `E3TreatmentSummary` values.
- **E4** preserves resource geography as factor while keeping arm, seed, standing
  composition, and founder-order counterbalance distinct, passing through existing
  `E4EnvironmentSummary` values.
- **B3** keeps primary confirmation, radius sensitivity, and founder-label
  counterbalance separate and preserves scenario origin versus validated identity.

Missing evidence is never inferred or reconstructed. An unavailable analysis names
the missing evidence and requires a **new run** with an appropriate EvidencePlan.
Current-session Results are rejected when they no longer belong to the active
scientific owner.

Persisted run provenance is intentionally not a durable result archive. Reopened
saved revisions may identify historical runs while observations/measurements/results
are absent; the reference frontend reports that honestly and never reruns implicitly.

## Presentation

WU5 makes Presentation a first-class downstream Study experience over exact WB5/WU4
result association. It does not add a `PresentationSpec`, replay database, scene
graph, camera/storyboard DSL, or universal renderer adapter.

Reference Ecology routes authoritative recorded evidence through the existing
Workbench world adapter to `WorldPresentationFrame` and then to the retained Plotly
renderer. Canonical validated B3 can route to a matched Interactive World and to the
existing B3 cinematic director/optional Manim renderer.

The durable renderer-neutral contract is now shared by the Streamlit reference
frontend and the native QML product:

```text
recorded scientific evidence
        ↓
Workbench presentation adapter
        ↓
WorldPresentationFrame
        ↓
renderer-specific presentation
```

Q0 moves the frontend-neutral Workbench world adapter into `evo_engine.presentation`
only because two real consumers now exist. Plotly remains a renderer, not a desktop
scientific contract.

### Reference Ecology Interactive World

Replay requires recorded spatial evidence. Presentation operations may change
committed-step selection, playback, visibility, trail controls, labels, organism
selection, and focus mode. None changes manifest, EvidencePlan, experiment identity,
or scientific provenance.

### B3 matched Interactive World

Canonical B3 constructs control and treatment worlds independently for one
authoritative confirmation seed at one shared recorded committed step. Both arms use
the same science-owned fixed `max_speed` encoding. Same-seed arms are matched/blocked
by seed, not assumed to remain RNG-lockstep after treatment divergence.

### B3 Scientific Story

Only canonical validated B3 is eligible for the established headline cinematic
handoff. Representative seed, scientific episodes, comparison structure, fixed trait
scale, and bounded conclusion remain B3 science/director responsibilities. Optional
renderer availability is distinct from scientific handoff availability.

## Session ownership in the Streamlit reference

Streamlit session state owns only transient application concerns: route, active
artifact/section, current authoritative result, private scientific drafts, Run Plan
state, disclosure/widget state, immediate parent used for in-session diff, and
Presentation replay/focus/renderer state.

These values are not a persisted scientific schema. Returning Home or replacing the
active Study clears transient state so scientific or renderer state cannot leak
across Studies.

The native frontend does not need to copy Streamlit's session-state implementation;
it must preserve the same ownership semantics through Qt application/controller
state.

## Readiness and result honesty

Where a revision exposes Workbench readiness, the frontend displays that authority.
Slot diagnostics remain Workbench diagnostics; frontends do not duplicate lower
scientific validation or predict full compile/preflight failures. Non-blocking
evidence advisories remain warnings rather than Blocked state.

Saved revisions may preserve run provenance without complete result payloads.
Reopening such a Study does not reconstruct missing evidence or rerun automatically.
Results and Presentation must state that limitation explicitly.

## Native migration after WU5

WU1–WU5 are complete as the Streamlit reference sequence. The next primary product
front is the Q-series native migration rather than WU6-specific Streamlit polish.

Q0 proves PySide6/QML technology, exact Workbench reuse, nonblocking execution,
native `WorldPresentationFrame` rendering, and standalone packaging. Q1 next builds
the native Home + persistent five-section Study shell with concrete artifact routing
while keeping Q0 Reference Ecology as the deep slice. See `docs/desktop_workbench.md`.

Accessibility, visual completion, remediation clarity, renderer failure UX, and
release hardening remain required product concerns. They should be applied to the
native product after sufficient Q-series breadth exists, not used as a reason to
redesign settled Workbench, science, Results, replay, or cinematic ownership.

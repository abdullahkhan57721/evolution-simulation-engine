# Evolution Experiment Workbench UI

The interactive application is organized around a persistent **Study** product shell.
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

The application remains Streamlit-based. The former top-level
Configuration → DashboardRun → Workspace mode switch is no longer the application
entry architecture. Existing world-workspace and renderer modules remain available
for reuse by the Study Presentation experience rather than being rewritten by the
shell milestones.

## Supported entry families

The shell exposes only concrete Workbench-supported entry paths:

- **Curated** — canonical radius-1 B3 Flagship;
- **Controlled** — one controlled-locomotion Study revision, the concrete max-speed
  sweep definition, or the concrete environment-selection comparison definition;
- **Custom** — the bounded Reference Ecology recipe.

The B3 radius-2 sensitivity is not an ordinary New Study choice.
Extension/internal reference-ecology composition is not exposed.

## Concrete persistence routing

The UI inspects only persisted format identity, plus the existing concrete experiment
pattern identity when needed, and dispatches directly to the owning loader:

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

If a concrete loader reports an exact-reproduction incompatibility, the UI surfaces
that failure and its Workbench remediation. It does not silently upgrade, fix, or
re-resolve the artifact.

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

The page presents authoring controls separately from scientific meaning. Renderer
settings, package/class names, builders, and lower engine objects are not authoring
controls.

### Controlled locomotion

One controlled-locomotion Study exposes only the stable WB1 semantic slots:

- maximum speed;
- resource geography;
- reproducibility seed.

Draft readiness and resolution come from the existing WB1 contracts. The page shows
the resulting explicit values, derived treatment meaning, and fixed assumptions such
as clonal inheritance, mutation-off state, sensing/targeting, horizon, energetics, and
other fixed nonfocal biology from the resolved manifest.

### Reference Ecology Guided / Advanced disclosure

The Reference Ecology page consumes the current WB4 slot metadata, support tiers,
applicability, readiness, normalization, and manifest resolution.

**Guided** shows the current supported core choices organized by scientific intent:
environment, population, movement/sensing, and run controls.

**Advanced** is disclosure over the same `ReferenceEcologyIntent`; it adds only
currently supported Advanced slots such as conditional Gaussian movement parameters,
renewable-resource settings, two-patch geometry, mutation controls, and
recombination. Switching disclosure mode does not itself change scientific state.

There is no manufactured Expert editor while the bounded recipe exposes no Expert
slots. Extension/internal engine capabilities remain informationally outside the
authoring recipe rather than becoming editable controls.

### Conditional applicability

Conditional fields use WB4's existing `is_slot_applicable()` contract.

Examples include:

```text
gaussian movement → gaussian standard deviation applies
two_patches       → patch geometry applies
mutation enabled  → mutation parameters apply
```

When a dependency change makes a value inapplicable, private UI draft state clears
that value according to the current WB4 applicability result. The saved child still
passes through the existing reference-study fork path, whose normalization remains
the authoritative persistence boundary. Hidden stale values therefore do not survive
as saved scientific meaning.

## Immutable editing and semantic diff

The active saved revision is never edited in place.

```text
immutable saved revision
        ↓
private UI draft
        ↓ existing Workbench readiness / resolution
        ↓
Save new revision
        ↓ existing concrete fork API
        ↓
immutable child revision
```

Controlled edits use `fork_study_revision()`. Reference Ecology edits use
`fork_reference_study_revision()`. The UI does not invent revision semantics for
experiment definitions that do not already own them.

After a child is created in the same application session, the Simulation page renders
the existing concrete semantic diff:

- controlled: `diff_study_revisions()`;
- reference ecology: `diff_reference_study_revisions()`;
- B3: `diff_b3_study_revisions()`.

The UI labels explicit and derived changes for readability but does not implement a
second diff engine. If only a persisted parent revision ID is available and the
parent artifact itself is not loaded, the UI states that a semantic diff cannot be
reconstructed.

## Curated B3 behavior

Canonical B3 is presented as a validated, mostly read-only scientific Study rather
than a custom simulation form. The Simulation section exposes the validated scenario
identity, scenario origin, matched control/treatment environments, focal trait and
founder design, horizon, mutation/inheritance assumptions, treatment-integrity
meaning, and counterbalance design from the exact B3 manifest.

The one supported sensitivity operation is an explicit action:

```text
validated radius-1 B3
        ↓ fork_b3_study_revision()
radius-2 B3-derived Study
```

The child preserves B3 scenario origin but loses the validated radius-1 scenario
identity. The UI presents that identity loss prominently and does not call the child
the B3 flagship.

## Evidence authoring

WU3 makes Evidence a first-class scientific Study section. Evidence remains separate
from Simulation intent and uses only the concrete evidence contracts already owned by
the Workbench.

Controlled single-run and Reference Ecology revisions expose their current supported
evidence streams in scientific language. Changing either evidence plan creates a new
immutable child revision through the existing concrete fork API; the saved parent is
never edited in place. Reference Ecology surfaces existing non-blocking evidence
advisories, including the high-volume spatial-history warning, without turning Ready
into Blocked.

Frozen or experiment-required evidence is not made artificially editable:

- canonical B3 uses its frozen required evidence set;
- E3 uses its exact sweep-required evidence;
- E4 uses its exact comparison-required evidence.

The UI does not manufacture recorder choices, infer missing evidence after a run, or
create invalid experiment evidence plans.

## Concrete Experiment design

WU3 renders only the experiment patterns that already exist.

### E3 max-speed sweep

Maximum speed remains the scientific factor and replicate seed remains replicate
identity. Neither is duplicated as an ordinary base-Simulation control. Editable
levels and seeds validate through `MaxSpeedSweepDefinition`; the displayed run matrix
comes from `expand_max_speed_sweep()`.

### E4 environment-selection comparison

Resource geography remains the primary factor. Control/treatment role, replicate
seed, standing focal composition `(1, 3, 9)`, and founder-order counterbalance remain
separate design semantics. Only the supported replicate-seed choice is editable. The
displayed matched design comes from `expand_environment_selection_comparison()`.

### B3 curated design

B3 remains read-only. Its primary confirmation, radius sensitivity when applicable,
counterbalance, and total simulation count come from `compile_b3_curated()`. Same-seed
control/treatment pairs are described as matched or blocked by seed; the UI does not
claim that their trajectories remain lockstep-identical after treatment divergence.

Controlled single-run explicitly has no multi-treatment experiment. Reference Ecology
explicitly has no generic controlled-experiment definition in the current support
envelope.

## Readiness, Run Plan, and execution

The shell uses existing concrete Workbench readiness as the authoring authority.
Draft / Blocked / Ready and Workbench-owned diagnostic messages/remediation are
surfaced without predicting or duplicating lower generic, biological, genetic, or
scientific preflight.

`Run` remains an action. It first binds any owned transient scientific draft to an
exact immutable owner and then opens a reviewable Run Plan derived from that exact
artifact. Revision-backed controlled/reference edits therefore become one immutable
child revision before execution; E3/E4 retain their existing immutable
experiment-definition value semantics rather than gaining invented revision lineage.

Execution is synchronous and delegates only to existing concrete Workbench runners:

```text
StudyRevision                         → run_study_revision()
ReferenceStudyRevision                → run_reference_study_revision()
B3StudyRevision                       → run_b3_study_revision()
MaxSpeedSweepDefinition               → run_max_speed_sweep()
EnvironmentSelectionComparisonDefinition
                                      → run_environment_selection_comparison()
```

The UI does not instantiate `SimulationEngine`, rebuild run configurations, reproduce
experiment expansion, or add a second preflight system.

Successful revision-owned runs retain the authoritative result object in session and
replace the active revision with the existing immutable `.with_run(...)` snapshot
using returned provenance. E3/E4 results remain their authoritative concrete result
objects in session without invented Study-level run identity. Compile/preflight/run
failure leaves the exact saved artifact unchanged and surfaces the failure honestly.

## Results and run exploration

WU4 turns the WU3 completion handoff into a first-class scientific Results workspace
without adding another result hierarchy or scientific-analysis framework. The UI
binds the active artifact and session-owned result through the existing WB5
`inspect_*_results()` contracts. Revision-backed controlled, Reference Ecology, and
B3 Results must match the exact active revision/manifest/evidence identity; E3/E4
must match the exact immutable experiment definition before their WB5 inspectors are
used.

Every supported family follows the product rhythm:

```text
Overview → Explore → Analysis → Provenance
```

The internal navigation remains family-specific rather than being flattened into a
universal replicate schema.

### Controlled single-run Results

Controlled Results expose the recorded population trajectory and the existing E1
locomotion replicate measurement. Both are gated by WB5 `AnalysisAvailability`.
The UI does not recalculate movement or energetic measurements from event rows.

### Reference Ecology Results

Reference Ecology keeps its recorded evidence streams independent:

- population history;
- committed events, including process filtering;
- pedigree / individual life history;
- allele and genotype composition;
- committed spatial-history frames.

Each stream is gated independently by its authoritative availability. Spatial
inspection is committed evidence inspection, not interpolated world replay.

### E3 ecological-performance Results

E3 preserves maximum speed as the factor. Users choose a factor level and then an
exact replicate seed while the view retains treatment ID, manifest digest, and the
unchanged replicate outcome. Treatment-level tables/charts copy existing
`E3TreatmentSummary` values. Organisms within a run are not promoted to independent
replicates and WU4 does not recompute treatment summaries.

### E4 standing-variation Results

E4 preserves resource geography as the factor while keeping control/treatment role,
replicate seed, standing focal composition, and founder-speed-order counterbalance as
separate identities. Replicate exploration shows the existing focal trajectory and
mechanism evidence; environment-level views copy existing `E4EnvironmentSummary`
values. Founder-order counterbalance is never presented as another factor.

### B3 curated Results

B3 keeps three scientific roles visibly separate:

- primary matched confirmation;
- radius sensitivity;
- founder-label counterbalance.

Primary matched arms are described as blocked/matched by seed without implying their
RNG trajectories remain lockstep after treatment divergence. Scenario origin and
validated canonical scenario identity are shown separately. Results only reports
whether the existing canonical cinematic scientific handoff is available; cinematic
execution and choreography remain downstream Presentation responsibilities. A
noncanonical B3-derived fork therefore does not inherit canonical cinematic/headline
claims merely because it shares B3 origin.

### Evidence gaps, provenance, and historical Results

Missing evidence is never inferred or reconstructed. An unavailable analysis names
the missing evidence and states that obtaining it requires a **new run** with an
appropriate EvidencePlan; evidence cannot be added retroactively to a completed run.

Provenance views expose only existing Workbench and scientific provenance values.
Current-session Results are rejected when they no longer belong to the active
scientific owner rather than being displayed under a stale Study or Experiment.

Persisted run provenance is intentionally not a durable result archive. A reopened
saved revision may identify historical runs while the observations, events,
measurements, or experiment payloads are absent from the current session. Results
shows those references honestly and does not regenerate or rerun them automatically.
E3/E4 definitions likewise do not gain invented persisted result payloads or
Study-level run identities.

## Presentation

WU5 makes Presentation a first-class downstream Study experience over the exact
WU4/WB5 result association. It does not add a `PresentationSpec`, replay database,
scene graph, camera/storyboard DSL, or universal renderer adapter.

Presentation currently has concrete behavior only where real adapters exist:

```text
Reference Ecology authoritative result
        ↓ existing Workbench world adapter
WorldPresentationFrame
        ↓ retained Plotly renderer
Interactive World

canonical validated B3 result
        ├─ existing B3 Workbench world adapter → matched Interactive World
        └─ prepare_b3_workbench_cinematic()
              ↓ existing B3 director
              ↓ optional existing Manim renderer
           Scientific Story
```

Unsupported Study families remain honest rather than receiving fake disabled
symmetry.

### Reference Ecology Interactive World

Reference replay requires recorded spatial evidence. Missing spatial evidence uses
the existing Workbench availability diagnostic/remediation and requires a new run
with an appropriate EvidencePlan; historical provenance alone is never treated as
replay data.

The interactive world exposes only presentation operations over exact committed
frames:

- previous / next / committed-step selection;
- play / pause and playback speed across recorded committed steps;
- resources, carcasses, trails, trail length, and labels where supported;
- organism selection and authoritative committed-state inspection;
- run, seed, and committed-step context;
- Focus Mode inside the same Study product.

Those controls never change a manifest, EvidencePlan, experiment definition, or
scientific provenance.

### B3 matched Interactive World

Canonical B3 presents independently constructed control and treatment worlds for one
authoritative confirmation seed at one shared recorded committed step. Arm-local
organism selection remains presentation focus only. Both arms must use the same
science-owned fixed `max_speed` encoding.

The UI states the matched design accurately: arms are blocked/matched by seed, but
treatment-driven divergence means their subsequent RNG trajectories are not assumed
to remain lockstep-identical.

### B3 Scientific Story

Only canonical validated B3 is eligible for the established headline cinematic
handoff. The UI invokes the existing
`prepare_b3_workbench_cinematic(...)` → B3 director → renderer path. Representative
seed, scientific episodes, comparison structure, fixed trait scale, and bounded
conclusion remain owned by B3 science/director code.

Renderer quality and MP4/GIF output are presentation-only choices already supported
by the renderer API. Scientific handoff availability is distinct from whether the
optional Manim dependency is installed. A radius-2 B3-derived fork preserves B3
origin but does not inherit canonical cinematic eligibility.

### Presentation session ownership

Presentation state is transient and namespaced. It includes focus mode, subexperience,
selected seed/step/organism, playback, renderer visibility/trail/label controls, and
renderer output options. State is reconciled to exact revision + manifest digest +
run ownership and is cleared when an active Study/run is replaced or the user returns
Home. Changing B3 confirmation seed resets timeline and organism-selection state.

Programmatic committed-step changes explicitly synchronize the keyed Streamlit step
widget so Previous/Next and playback cannot be undone by stale widget state.

## Session ownership

Streamlit session state owns only transient application concerns:

- current route;
- active concrete artifact;
- active Study section;
- session-owned current authoritative result;
- private concrete Simulation and Evidence draft intent/plan;
- private concrete E3/E4 experiment draft values;
- Run Plan state and binding/failure notices;
- disclosure/widget state;
- the immediately loaded parent artifact used for an in-session semantic diff;
- Presentation focus/replay/renderer state.

These values are not a persisted scientific schema. Returning Home, opening another
Study, or starting another Study clears transient WU2–WU5 draft/run/result/presentation
state so scientific or renderer state cannot leak across Studies.

## Readiness and results honesty

Where a concrete revision exposes a Workbench readiness API, the shell and scientific
authoring pages display Draft / Blocked / Ready using that authority. Slot diagnostics
remain Workbench diagnostics; the UI does not duplicate lower scientific validation
or try to predict full compile/preflight failures.

Non-blocking evidence advisories remain warnings and do not turn Ready into Blocked.

Saved revision formats may preserve run provenance and result references without
serializing complete result payloads. Reopening such a Study does not reconstruct
missing evidence and does not rerun the simulation automatically. The Results and
Presentation pages state that limitation explicitly.

## Work after WU5

WU5 completes the first concrete Presentation integration while deliberately leaving
broader product hardening and release polish outside its scope. It does not add
durable result storage, a background render queue, generic statistics/chart/query
frameworks, a universal Study/Result/Presentation schema, or a generic cinematic
scene model.

The next UI milestone is **WU6 — Product Hardening, Accessibility, Visual Completion,
and Release Readiness**. WU6 should exercise and polish the existing end-to-end Study
product rather than redesign settled scientific or presentation ownership. Relevant
work includes navigation coherence, accessibility, responsive/focus behavior,
visual consistency, error/remediation clarity, renderer availability/failure UX,
release smoke paths, and launch/packaging guidance where already supported.

Renderer state, interpolation, cameras, playback controls, storyboard/choreography,
and export remain Presentation responsibilities. Future work should continue to
consume the authoritative Workbench/Results boundary rather than reopening science or
moving presentation mechanics into Results.

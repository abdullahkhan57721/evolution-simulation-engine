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
for later integration rather than being rewritten by the shell milestones.

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

## Results handoff

WU3 deliberately keeps Results thin. The session-owned authoritative result exposes
only the completion handoff needed for the next product work: existing run/revision
identity when owned, the recorded evidence IDs, and the number of concrete
simulations represented by the result.

WU3 does not recalculate E1/E3/E4/B3 science, build a durable result archive, or
invent historical payloads. Reopened saved revisions may contain run-provenance
references while lacking complete result payloads; the Results page says so and does
not rerun automatically.

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
- presentation state owned by downstream UI modules.

These values are not a persisted scientific schema. Returning Home, opening another
Study, or starting another Study clears transient WU2/WU3 draft/run/result state so
scientific state cannot leak across Studies.

## Readiness and results honesty

Where a concrete revision exposes a Workbench readiness API, the shell and scientific
authoring pages display Draft / Blocked / Ready using that authority. Slot diagnostics
remain Workbench diagnostics; the UI does not duplicate lower scientific validation
or try to predict full compile/preflight failures.

Non-blocking evidence advisories remain warnings and do not turn Ready into Blocked.

Saved revision formats may preserve run provenance and result references without
serializing complete result payloads. Reopening such a Study does not reconstruct
missing evidence and does not rerun the simulation automatically. The Results page
states that limitation explicitly.

## Deferred work after WU3

WU3 intentionally does not implement complete Study Analysis/Run Explorer workflows,
durable result storage, B3 storytelling UI, V2 world embedding, V3 cinematic
integration, or renderer settings.

Those continue through later WU milestones on top of the same Study shell, exact
scientific result ownership, and concrete Workbench contracts. Future Results or
Presentation integration must consume authoritative existing science rather than
reopening the Workbench backend architecture.

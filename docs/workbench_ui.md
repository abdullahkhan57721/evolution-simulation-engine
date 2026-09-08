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

## Session ownership

Streamlit session state owns only transient application concerns:

- current route;
- active concrete artifact;
- active Study section;
- session-only current result placeholder;
- private concrete Simulation draft intent;
- disclosure/widget state;
- the immediately loaded parent artifact used for an in-session semantic diff;
- presentation state owned by downstream UI modules.

These values are not a persisted scientific schema. Returning Home, opening another
Study, or starting another Study clears WU2 draft/diff state so authoring state cannot
leak across Studies.

## Readiness and results honesty

Where a concrete revision exposes a Workbench readiness API, the shell and Simulation
page display Draft / Blocked / Ready using that authority. Slot diagnostics remain
Workbench diagnostics; the UI does not duplicate lower scientific validation or try
to predict full compile/preflight failures.

Non-blocking evidence advisories remain warnings and do not turn Ready into Blocked.

Saved revision formats may preserve run provenance and result references without
serializing complete result payloads. Reopening such a Study does not reconstruct
missing evidence and does not rerun the simulation automatically. The Results page
states that limitation explicitly.

## Deferred work after WU2

WU2 intentionally does not implement complete Evidence-plan authoring, E3/E4
Experiment-page authoring, run matrices/planning/execution, Study Analysis, Run
Explorer, V2 world embedding, V3 cinematic integration, or renderer settings.

Those continue through WU3 and later WU milestones on top of the same Study shell and
concrete Workbench contracts.

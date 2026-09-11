# Native Desktop Evolution Experiment Workbench

Q0 establishes **PySide6 + Qt Quick/QML** as the primary product frontend architecture
for the Evolution Experiment Workbench. Q1 establishes the persistent native Study
shell and concrete routing; Q2 completes the supported pre-execution
Simulation/Evidence/Experiment authoring surface; Q3 completes native Run planning,
five-family execution, and authoritative Results breadth. The Streamlit WU1–WU5
application remains a reference frontend during migration; it does not become a
second scientific model.

## Dependency direction

```text
Qt Quick / QML
        ↓
PySide6 controller / view-model boundary
        ↓
existing Workbench and frontend-neutral application semantics
        ↓
experiments / presets / renderer-neutral presentation
        ↓
biology
        ↓
frozen kernel
```

The native frontend is downstream application/presentation code. Lower packages must
not depend on `evo_engine.desktop` or PySide6.

## Q0 vertical

The first native slice deliberately uses bounded Reference Ecology because one
existing `ReferenceStudyRevision` already owns exact persistence and forking, one
existing runner owns execution/provenance, existing Results inspection owns the
headline population value, and recorded spatial evidence already feeds the shared
`WorldPresentationFrame` contract.

Q0 proves:

```text
launch native app
  → create/open exact Reference Ecology Study
  → display semantic scientific state
  → edit max_speed as transient authoring intent
  → show Workbench-owned explicit + derived meaning
  → save an immutable Workbench child revision
  → run the exact saved revision off the GUI thread
  → read authoritative Results
  → prepare WorldPresentationFrame from recorded evidence
  → render organisms/resources natively in QML
  → build and launch-smoke a standalone desktop executable
```

This is a technology and dependency-boundary proof, not desktop feature parity.

## Qt boundary contracts

### Values cross the boundary; mutable scientific graphs do not

The Python controller may retain concrete Workbench result/revision objects privately,
but QML receives only deliberately exposed Qt values:

- scalar `Property` values;
- `Signal`s;
- `Slot`s representing supported application actions;
- item-model rows made from renderer-neutral presentation primitives.

Do not bind QML directly to arbitrary Workbench, simulation, biology, genetics,
experiment, or kernel object graphs.

### Scientific mutation remains Workbench-owned

A QML control may change transient frontend draft state. Committing scientific
meaning must call an existing concrete Workbench authoring/fork API. The active saved
revision is never mutated in place, and QML cannot assign revision identity, manifest
identity, provenance, or scientific Results.

Exact persistence remains the concrete Workbench serializer/loader. Opening a saved
artifact must not rebuild or silently upgrade its historical manifest from intent.

### Frontend-neutral extraction is demand-driven

The Streamlit and Qt frontends may both consume a helper when the helper is genuinely
frontend-neutral and a second consumer has appeared. Q0 earned the relocation of the
Workbench world-presentation adapter into `evo_engine.presentation` because both
frontends consume the same renderer-neutral frame contract.

Do not create a generic `application` framework, universal frontend schema, generic
form generator, or generic scene model in anticipation of future reuse.

## Execution contract

Existing Workbench runners are synchronous scientific APIs. Native execution must not
block the Qt GUI thread. A narrow worker/thread adapter is sufficient until concrete
requirements earn cancellation, progress reporting, queues, multiprocessing, or a
broader job architecture.

The worker returns the authoritative existing Workbench result. The controller must
verify run provenance against the active saved revision before attaching or displaying
it.

## Native world contract

`WorldPresentationFrame` is the desktop renderer input. It is already downstream of
committed spatial/trait evidence and renderer-neutral scientific encoding.

QML may decide how to draw:

- world bounds;
- resources;
- organisms;
- focal scientific encoding already present in the frame;
- selected-object emphasis and other renderer-only state.

QML must not reconstruct unrecorded spatial history, calculate scientific outcomes,
or treat a Plotly figure as the scientific data contract.

## Dependencies and deployment

PySide6 is an optional application dependency, currently pinned by
`requirements-desktop.txt`; it is not a core engine dependency. The general quality
environment therefore does not need Qt installed. The dedicated desktop workflow
owns Qt-specific typing, QML-load, offscreen launch, compatibility, and deployment
checks.

Q0 uses Qt for Python's `pyside6-deploy` path to build a standalone artifact and
launch-smokes the produced executable. This proves deployment architecture on the CI
development platform only. It does not establish signing, notarization, installers,
auto-update, or a cross-platform release matrix.

### Local reproduction

Install the project plus the optional desktop and retained reference-UI dependencies:

```bash
python -m pip install -e ".[dev]" -r requirements-desktop.txt -r requirements-ui.txt
```

Launch the native application from source:

```bash
python -m evo_engine.desktop.main
```

A headless/offscreen startup smoke can be reproduced with:

```bash
QT_QPA_PLATFORM=offscreen python -m evo_engine.desktop.main --smoke-test
```

Build the standalone artifact through the same Qt for Python deployment path used by
CI:

```bash
pyside6-deploy src/evo_engine/desktop/main.py --force --name EvolutionExperimentWorkbench
```

The deployment output is platform-specific. On the Ubuntu CI proof host, the desktop
workflow also installs `libegl1` before Qt offscreen launch, then launch-smokes the
produced executable itself. Q0 does not claim signed distribution or a cross-platform
installer/release matrix.

## Q1 native Study shell

Q1 turns the Q0 vertical into persistent native product structure without moving
scientific ownership into Qt:

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

`Study` remains a navigation/product concept. The desktop package has no universal
persisted `Study`, `DesktopStudy`, common Qt scientific schema, or wrapper JSON.

### Concrete artifact routing

`evo_engine.desktop.artifacts` explicitly recognizes only the current WU support
envelope:

- controlled single-run `StudyRevision`;
- E3-pattern `MaxSpeedSweepDefinition`;
- E4-pattern `EnvironmentSelectionComparisonDefinition`;
- curated/derived `B3StudyRevision`;
- bounded `ReferenceStudyRevision`.

New Study creates one of those concrete artifacts through existing constructors.
Open Study inspects only existing format/pattern identity and delegates to that
artifact's own `from_json()`. Save and Save As write only the artifact's own
`to_json()`. Unknown formats, unknown experiment patterns, and exact-incompatible
historical manifests fail explicitly; no fallback resolution or migration occurs.

The canonical B3 entry alone exposes the already-established radius-2 sensitivity
fork. A saved radius-2 B3-derived artifact remains openable through the B3 loader but
is not another New Study family.

### Transient application ownership

`ApplicationController` is the native shell boundary. It owns only transient
application values over the active concrete artifact:

```text
ApplicationController
├── route
├── active concrete artifact
├── active Study section
├── current-session authoritative result
├── Run Plan placeholder state
├── presentation owner / reset epoch
├── file location
└── family-specific child controller(s)
```

A successful new/open/fork/revision commit replaces scientific ownership and clears
stale current-session result, Run Plan, and presentation state. Section navigation
does not change the concrete artifact. Return Home clears the active context.

Result binding uses the existing WB5 inspectors and immutable E3/E4 definition
matching rather than a desktop result hierarchy. Revision-backed presentation state
is identified by the exact scientific owner (`revision + manifest + run`) and resets
when that owner changes. Saved run references do not recreate result payloads.

Opening and saving are atomic with respect to the active artifact: loader,
compatibility, or filesystem failure does not replace the currently active scientific
owner. `IncompatibleManifestError` remains Workbench-owned; Q1 surfaces its existing
diagnostic message/remediation.

### Family-specific controller seam

Q1 originally kept `ReferenceStudyController` as the one deep family slice: a
transient `max_speed` draft, immutable child commit, narrow worker-thread run,
authoritative Reference result, and renderer-neutral world preparation. It receives
an exact active `ReferenceStudyRevision` from `ApplicationController`; it is not the
application router or persistence dispatcher. Q2 preserves that family boundary while
expanding Reference authoring and adding separate concrete Simulation, Evidence, and
Experiment controllers, as described below.

### QML shell and design system

`Main.qml` consumes only curated scalar/controller values. The reusable QML layer now
contains deliberate Workbench primitives for theme tokens, buttons, panels, section
headers, sidebar navigation, status badges, diagnostics, field labels, and disclosure
sections. These are visual/application primitives, not reflection-driven scientific
forms.

The native window provides Home/New/Open routing, five-section Study navigation,
File-menu New/Open/Save/Save As actions, native file dialogs, minimum window sizing,
readiness/revision/scenario identity, the existing supported B3 fork, and the retained
Reference Ecology Q0 slice. Sections without Q1 feature parity state that explicitly
instead of manufacturing data or generic editors.

Native Reference world rendering remains evidence-dependent. If the exact active
result did not record spatial evidence, Q1 reports that replay is unavailable and
does not reconstruct world history.

## Q2 native scientific authoring

Q2 fills the three pre-execution scientific sections while preserving the Q1
application and persistence boundaries:

```text
ApplicationController
├── SimulationAuthoringController
├── EvidenceAuthoringController
├── ExperimentAuthoringController
└── ReferenceStudyController
```

These are concrete application seams, not a common scientific object model. The
application controller activates all four against one exact concrete artifact and
resets stale current-session result, Run Plan, and presentation state whenever a
scientific draft or exact owner changes. Section navigation itself remains inert.

### Simulation authoring

`SimulationAuthoringController` owns controlled-locomotion transient intent for only
maximum speed, resource geography, and seed. It delegates readiness, immutable child
creation, and semantic diff to the existing Workbench/frontend-neutral authoring
contracts. E3/E4 Simulation factor assumptions remain read-only because their
experiment definitions own those semantics. B3 remains curated/read-only except for
the already-supported radius-2 sensitivity fork, whose existing diff exposes loss of
validated canonical identity.

Reference Ecology remains family-specific in `ReferenceStudyController`. Q2 expands
that controller from the Q0 max-speed proof to the bounded WB4 Guided/Advanced
surface, including Gaussian, two-patch, and mutation applicability. Inapplicable
transient values reconcile through the existing normalization helper; saved
normalization and readiness remain Workbench-owned. Expert remains empty and
Extension/Internal capability is not exposed. The retained Reference run/result/world
vertical remains in the same family controller and still runs only exact saved
science.

The native Simulation view consumes separate read-only item models for **You
selected**, **Derived configuration**, **Frozen recipe assumptions**, and the existing
semantic diff. QML never receives the mutable Workbench manifest/revision graph.

### Evidence authoring

`EvidenceAuthoringController` owns only transient evidence IDs for controlled and
Reference revision-backed Studies. Option rows come from the existing concrete
evidence authoring helpers and carry scientific label, meaning, enabled analysis,
required/editable state, and selection. Saving creates a new immutable child through
the owning concrete evidence-plan contract.

Reference advisories, including high-volume spatial evidence warnings, are passed
through existing Workbench diagnostics. Missing optional evidence explicitly states
that the corresponding analysis cannot be reconstructed later. B3, E3, and E4
required evidence remains locked/read-only.

### Experiment authoring

`ExperimentAuthoringController` owns only the existing concrete experiment
definitions. E3 edits supported maximum-speed levels and replicate seeds. E4 edits
replicate seeds while resource geography, control/treatment roles, standing focal
composition, and founder-order counterbalance remain fixed and separately visible.
The controller rebuilds its run rows only through the existing Workbench expansion
helpers.

B3 remains a read-only curated compiled design with authoritative case counts. A
controlled Study and Reference Ecology explicitly remain single-run workflows; Q2
does not invent a generic experiment object for them.

### Qt model boundary

`evo_engine.desktop.models.authoring` contains only small read-only Qt item models for
scientific meaning, semantic diff rows, evidence choices, factor levels, and
experiment-run rows. They are scalar presentation values over existing scientific
contracts, not persistence or validation schemas. QML authoring is split into
`SimulationAuthoringView.qml`, `EvidenceAuthoringView.qml`, and
`ExperimentAuthoringView.qml`, with `SemanticDiffView.qml` as the one reusable diff
presentation primitive earned by multiple concrete families.

## Q3 native execution and Results

Q3 completes the first native `Run → Results` breadth across all five supported
concrete Study families without creating a common scientific result hierarchy.

`ApplicationController` binds pending scientific state to one exact immutable owner
before Run Plan review. Controlled and Reference Simulation/Evidence drafts therefore
produce one child revision containing the complete pending scientific state rather
than a chain of intermediate revisions. Pending E3/E4 experiment edits become the
exact immutable experiment definition. B3 remains its exact curated revision.

`RunController` owns only transient native execution coordination:

```text
exact active scientific owner
        ↓
reviewable Run Plan
        ↓
QThread worker
        ↓
frontend-neutral Workbench execution dispatcher
        ↓
existing concrete runner
        ↓
authoritative result + provenance
```

The Workbench execution dispatcher is shared by Streamlit and Qt only because the
second real frontend earned that extraction. It still dispatches explicitly to the
five existing concrete runners. The Qt adapter adds no generic queue, cancellation,
progress, multiprocessing, or background-job protocol.

Completion is accepted only while the same exact scientific owner remains active and
the existing WB5 association rules accept the returned result. Scientific edits,
owner replacement, or Home navigation invalidate stale Run Plans, Results, and
presentation ownership.

`ResultsController` is intentionally family-dispatched. Controlled, Reference, E3,
E4, and B3 Results all use the familiar `Overview / Explore / Analysis / Provenance`
product rhythm while preserving their different scientific structures:

- controlled Results expose recorded population plus existing E1 locomotion
  measurements only when their evidence exists;
- Reference Results expose independent availability for population, committed events,
  pedigree, genetics, and spatial replay;
- E3 preserves maximum speed as factor plus factor-level, seed, treatment, and
  manifest identity;
- E4 preserves resource geography as factor while keeping control/treatment role,
  seed, standing focal composition, and founder-order counterbalance distinct;
- B3 preserves scenario origin versus validated scenario identity and keeps primary
  confirmation, radius sensitivity, and founder counterbalance separate.

Missing evidence stays visibly unavailable and requires a new run with an appropriate
EvidencePlan. Native Reference world rendering remains contingent on actual recorded
spatial observations. Persisted run provenance remains a reference to a historical
run, not a persisted observations/result archive, so reopened Studies never
reconstruct or implicitly rerun historical Results.

### Q4 Presentation handoff

Q4 should now broaden native Presentation from the exact current-session evidence and
result ownership settled by Q3. Begin with the existing renderer-neutral Reference
world path and canonical B3 matched-presentation/cinematic contracts. Preserve
committed-step semantics, science-owned encodings, matched-arm identity, and
presentation-only interaction state.

Do not infer a universal scene/camera/replay model, generic chart framework, or
cross-family presentation schema from Q3. Shared presentation helpers should be
promoted only when multiple concrete native consumers demonstrate the same
responsibility. Accessibility, visual completion, installer/signing/update work, and
the final Streamlit parity/removal decision remain later product-hardening work.

## References

- `docs/workbench_ui.md`
- `docs/evolution_experiment_workbench.md`
- `docs/workbench_architecture_review.md`
- `docs/wb5_results_presentation.md`
- `docs/architecture/scientific_visualization.md`
- ADR 0009
- ADR 0010
- GitHub Issue #197 / PR #198
- GitHub Issue #201 / PR #202
- GitHub Issue #203 / PR #204
- GitHub Issue #205 / PR #206

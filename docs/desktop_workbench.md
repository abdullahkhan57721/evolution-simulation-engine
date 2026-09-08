# Native Desktop Evolution Experiment Workbench

Q0 establishes **PySide6 + Qt Quick/QML** as the primary product frontend architecture
for the Evolution Experiment Workbench. The Streamlit WU1–WU5 application remains a
reference frontend during migration; it does not become a second scientific model.

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

## Q1 handoff — Native Study shell and concrete routing

Q1 should expand product breadth without changing the contracts above. Its target is
the first persistent native **Study shell** over the existing WU product model:

```text
HOME
    ↓
Study
├── Simulation
├── Evidence
├── Experiment
├── Results
└── Presentation

Run = action
```

Q1 should focus on application navigation and concrete artifact ownership, not full
feature parity inside every section.

### Required Q1 contracts

1. **Concrete routing, no universal Study schema.** New/Open must dispatch to the
   existing concrete persisted Workbench artifact families and their canonical
   loaders. Qt must not introduce a common persistence envelope merely to simplify
   navigation.
2. **Persistent native shell.** Home, active-artifact identity, the five Study
   sections, and Run-as-action should exist as native application state independent
   of any one scientific family.
3. **Reference Ecology remains the proven deep slice.** Preserve Q0 create/edit/fork,
   exact run/results, and native world behavior while moving it inside the shell.
4. **Add breadth only through concrete consumers.** Introduce the smallest additional
   curated/controlled entry routes needed to prove the shell is not Reference-
   specific. Reuse their existing loaders/readiness contracts; do not manufacture
   generic authoring metadata.
5. **No duplicated execution/result authority.** Section navigation may select or
   display existing results, but Workbench runners, provenance, Results inspectors,
   and presentation adapters remain authoritative.
6. **Preserve draft versus saved scientific identity.** Section changes may maintain
   transient Qt draft state, but Run targets an exact saved/owned artifact according
   to the already-settled WU/WB semantics.
7. **Keep QML curated.** Prefer small controller/view-model APIs and typed Qt item
   models over exposing Python object graphs or reflection-driven forms.
8. **Streamlit remains a compatibility oracle during migration.** Q1 should keep the
   reference frontend green and compare semantics where useful; do not remove it.
9. **Validation remains layered.** Use focused native tests and the repository's
   current staged validation workflow; frozen scientific matrices run only if Q1
   actually changes their inputs/contracts.
10. **Packaging remains narrow.** Keep the standalone desktop proof working; do not
    turn Q1 into a signing/installer/release-matrix milestone.

### Q1 non-goals

- no complete desktop parity;
- no Workbench redesign;
- no generic frontend abstraction;
- no generic QML form generator;
- no new experiment DSL or statistics layer;
- no 3D/C++ renderer;
- no Streamlit removal;
- no generalized background-job infrastructure.

Later Q milestones can fill the five sections family-by-family and then address
native visual/accessibility/release hardening once repeated desktop use has shown what
should actually be shared.

## References

- `docs/workbench_ui.md`
- `docs/evolution_experiment_workbench.md`
- `docs/workbench_architecture_review.md`
- `docs/wb5_results_presentation.md`
- `docs/architecture/scientific_visualization.md`
- ADR 0009
- ADR 0010
- GitHub Issue #197 / PR #198

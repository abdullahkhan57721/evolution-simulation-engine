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
for later integration rather than being rewritten by the shell milestone.

## Supported entry families

WU1 exposes only concrete Workbench-supported entry paths:

- **Curated** — canonical radius-1 B3 Flagship;
- **Controlled** — one controlled-locomotion Study revision, the concrete max-speed
  sweep definition, or the concrete environment-selection comparison definition;
- **Custom** — the bounded Reference Ecology recipe.

The B3 radius-2 sensitivity remains openable when it is already present in a saved
B3 revision, but it is not an ordinary New Study choice. Extension/internal
reference-ecology composition is not exposed.

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

Saving calls the same concrete artifact's `to_json()` directly. There is no universal
Study envelope, generic recipe schema, manifest translation, or UI migration layer.
Historical manifests are never rebuilt from stored intent during Open Study.

If a concrete loader reports an exact-reproduction incompatibility, the UI surfaces
that failure and its Workbench remediation. It does not silently upgrade, fix, or
re-resolve the artifact.

## Session ownership

Streamlit session state owns only transient application concerns:

- current route;
- active concrete artifact;
- active Study section;
- session-only current result placeholder;
- presentation state owned by downstream UI modules.

Returning Home or starting another Study clears the active artifact/result context so
scientific state from a previous Study cannot leak into the next one. No Recent
Studies database or durable UI session schema exists.

## Readiness and results honesty

When a concrete revision exposes a Workbench readiness API, the shell displays its
Draft / Blocked / Ready state and authoritative blocking diagnostics. Experiment
definitions without that API do not receive invented readiness semantics.

Saved revision formats may preserve run provenance and result references without
serializing complete result payloads. Reopening such a Study does not reconstruct
missing evidence and does not rerun the simulation automatically. The Results page
states that limitation explicitly.

## Deferred work

WU1 intentionally does not implement scientific authoring forms, Guided/Advanced
controls, forking/diff UI, evidence-plan editing, execution integration, result
analysis, Run Explorer, V2 world embedding, V3 cinematic integration, or renderer
settings. Those build on this shell in later WU milestones.
